#!/usr/bin/env python3
"""
Agent-specific watcher for the ArtisanPro multi-agent bridge.

The coordinator assigns work in the shared repository; this watcher only
observes origin/main and creates a small alert for one configured agent. It
never edits application files, tasks, locks, or bridge state.

Usage:
    AGENT_ID=client-agent python3 bridge/auto-coordinator/agent-watcher.py
    AGENT_ID=admin-agent python3 bridge/auto-coordinator/agent-watcher.py --once

Environment:
    AGENT_ID       Agent to watch. Defaults to client-agent.
    SHARED_REPO    Direct shared checkout. Defaults to this repository root.
    POLL_SECONDS   Poll interval. Defaults to 60.
    WATCH_LOG      Activity log path.
    WATCH_ALERT    JSON alert path for actionable tasks.
    WATCH_QFLAG    Flag path for new questions mentioning the agent.

Git authentication is intentionally not stored in this file. Use an existing
Git credential helper, SSH configuration, or GITHUB_TOKEN/GH_TOKEN in the
watcher's process environment.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
AGENT_ID = os.environ.get("AGENT_ID", "client-agent")
SHARED = Path(os.environ.get("SHARED_REPO", str(ROOT))).expanduser().resolve()
POLL_SECONDS = max(5, int(os.environ.get("POLL_SECONDS", "60")))
ACTIONABLE = {"todo", "in_progress", "waiting_assignment", "blocked"}
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def safe_agent_name() -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", AGENT_ID).strip("-") or "agent"


AGENT_FILE_NAME = safe_agent_name().replace("-", "_").upper()

# Keep the conventional alert names used by the existing agent launchers while
# allowing any role to use this same watcher through environment overrides.
if AGENT_ID == "client-agent":
    DEFAULT_ALERT = "NEW_CLIENT_TASK.json"
    DEFAULT_QFLAG = "CHECK_QUESTIONS.flag"
elif AGENT_ID == "admin-agent":
    DEFAULT_ALERT = "NEW_ADMIN_TASK.json"
    DEFAULT_QFLAG = "CHECK_QUESTIONS_ADMIN.flag"
else:
    DEFAULT_ALERT = f"NEW_{AGENT_FILE_NAME}_TASK.json"
    DEFAULT_QFLAG = f"CHECK_{AGENT_FILE_NAME}_QUESTIONS.flag"

LOG = Path(os.environ.get("WATCH_LOG", str(Path.home() / f"{safe_agent_name()}-watch.log"))).expanduser()
ALERT = Path(os.environ.get("WATCH_ALERT", str(Path.home() / DEFAULT_ALERT))).expanduser()
QFLAG = Path(os.environ.get("WATCH_QFLAG", str(Path.home() / DEFAULT_QFLAG))).expanduser()
MEMORY = Path(
    os.environ.get(
        "WATCH_MEMORY",
        str(Path.home() / f".{safe_agent_name()}-watch-state.json"),
    )
).expanduser()
STOP = threading.Event()


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    token = env.get("GITHUB_TOKEN") or env.get("GH_TOKEN")
    auth_header = env.get("GIT_AUTH_HEADER")
    if token and not auth_header:
        encoded = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        auth_header = f"AUTHORIZATION: basic {encoded}"
    if auth_header:
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "http.extraheader"
        env["GIT_CONFIG_VALUE_0"] = auth_header
    return env


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(SHARED), *args],
        capture_output=True,
        text=True,
        timeout=60,
        env=git_env(),
    )


def log(message: str) -> None:
    line = f"[{now()}] {message}"
    print(line, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
    except OSError:
        pass


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        stream.write(content)
        temporary = Path(stream.name)
    os.replace(temporary, path)


def remove_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError as error:
        log(f"could not clear {path}: {error}")


def show_origin(path: str) -> str | None:
    result = git("show", f"origin/main:{path}")
    return result.stdout if result.returncode == 0 else None


def parse_json(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        log(f"invalid JSON in bridge data: {error}")
        return None
    return value if isinstance(value, dict) else None


def bridge_tasks() -> tuple[str | None, list[dict[str, Any]] | None]:
    data = parse_json(show_origin("bridge/tasks.json"))
    if data is None:
        return None, None
    tasks = [
        task
        for task in data.get("tasks", [])
        if isinstance(task, dict) and task.get("assignee") == AGENT_ID
    ]
    tasks.sort(
        key=lambda task: (
            task.get("status") not in ACTIONABLE,
            PRIORITY_ORDER.get(str(task.get("priority")), 99),
            str(task.get("id", "")),
        )
    )
    return data.get("lastUpdate"), tasks


def assigned_state_tasks() -> list[dict[str, Any]]:
    data = parse_json(show_origin("bridge/state.json")) or {}
    found: list[dict[str, Any]] = []
    for field in ("currTask", "nextTask"):
        task = data.get(field)
        if isinstance(task, dict) and task.get("assignee") == AGENT_ID:
            found.append(task)
    return found


def question_mentions() -> int:
    raw = show_origin("bridge/questions.md")
    if raw is None:
        return -1
    return len(re.findall(re.escape(AGENT_ID), raw, flags=re.IGNORECASE))


def load_memory() -> dict[str, Any]:
    try:
        value = json.loads(MEMORY.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_memory(value: dict[str, Any]) -> None:
    try:
        write_atomic(MEMORY, json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    except OSError as error:
        log(f"could not save watcher memory: {error}")


def task_signature(tasks: Iterable[dict[str, Any]]) -> str:
    return json.dumps(
        [
            [task.get("id"), task.get("status"), task.get("priority"), task.get("title")]
            for task in tasks
        ],
        ensure_ascii=False,
        sort_keys=True,
    )


def task_analysis(task: dict[str, Any]) -> dict[str, Any]:
    status = task.get("status")
    problems: list[str] = []
    if status == "blocked" and task.get("blocked"):
        problems.append("BLOCKED: " + "; ".join(str(item) for item in task["blocked"]))
    claimed_at = task.get("claimedAt")
    if status == "in_progress" and claimed_at:
        try:
            claimed = datetime.fromisoformat(str(claimed_at).replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - claimed).total_seconds() / 3600
            if age_hours > 24:
                problems.append(f"STUCK: {age_hours:.1f}h without an update")
        except (TypeError, ValueError):
            pass
    return {
        "id": task.get("id"),
        "status": status,
        "done_count": len(task.get("done", []) or []),
        "acceptance_total": len(task.get("acceptanceCriteria", []) or []),
        "dependencies": task.get("dependencies", []) or [],
        "blocked": task.get("blocked", []) or [],
        "problems": problems,
        "is_actionable": status in ACTIONABLE,
    }


def update_alert(tasks: list[dict[str, Any]], state_tasks: list[dict[str, Any]]) -> None:
    actionable = [task for task in tasks if task.get("status") in ACTIONABLE]
    known_ids = {task.get("id") for task in tasks}
    for task in state_tasks:
        if task.get("status") in ACTIONABLE and task.get("id") not in known_ids:
            actionable.append(task)

    if actionable:
        actionable.sort(
            key=lambda task: (
                PRIORITY_ORDER.get(str(task.get("priority")), 99),
                str(task.get("id", "")),
            )
        )
        selected = actionable[0]
        payload = {
            "agent": AGENT_ID,
            "timestamp": now(),
            "generatedAt": now(),
            "task": selected,
            "analysis": task_analysis(selected),
            "actionableTasks": actionable,
            "message": f"{AGENT_ID} has an actionable task: {selected.get('id')} ({selected.get('status')})",
        }
        write_atomic(ALERT, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        log(
            f"*** actionable {AGENT_ID} task: {actionable[0].get('id')} "
            f"({actionable[0].get('status')}) - {actionable[0].get('title', '')} ***"
        )
    else:
        if ALERT.exists():
            remove_if_exists(ALERT)
            log("no actionable task remains; alert cleared")


def poll_once(memory: dict[str, Any]) -> dict[str, Any]:
    fetch = git("fetch", "origin", "main", "--quiet")
    if fetch.returncode != 0:
        log(f"fetch failed: {fetch.stderr.strip()[:240]}")
    else:
        log("fetch ok")

    last_update, tasks = bridge_tasks()
    if tasks is None:
        log("could not read bridge/tasks.json from origin/main")
        tasks = []
    else:
        signature = task_signature(tasks)
        if signature != memory.get("taskSignature"):
            if not tasks:
                log(f"no {AGENT_ID} tasks in tasks.json (waiting for assignment)")
            for task in tasks:
                analysis = task_analysis(task)
                log(
                    f"task {task.get('id')} status={task.get('status')} "
                    f"done={analysis['done_count']} problems={analysis['problems']}"
                )
            memory["taskSignature"] = signature

    state_tasks = assigned_state_tasks()
    mentions = question_mentions()
    previous_mentions = memory.get("questionMentions")
    if isinstance(previous_mentions, int) and mentions > previous_mentions:
        write_atomic(
            QFLAG,
            f"{now()} new {AGENT_ID} mentions in bridge/questions.md "
            f"({previous_mentions} -> {mentions})\n",
        )
        log(f"questions.md has new {AGENT_ID} mentions ({previous_mentions} -> {mentions})")
    if mentions >= 0:
        memory["questionMentions"] = mentions

    update_alert(tasks, state_tasks)
    assigned = [task for task in tasks if task.get("status") in ACTIONABLE]
    assigned.extend(task for task in state_tasks if task.get("status") in ACTIONABLE)
    summary = ", ".join(
        f"{task.get('id')}={task.get('status')}" for task in assigned
    ) or "none"
    log(f"heartbeat - bridge lastUpdate={last_update} | {AGENT_ID}: {summary}")
    save_memory(memory)
    return memory


def handle_signal(signum: int, _frame: Any) -> None:
    log(f"signal {signum} received; stopping watcher")
    STOP.set()


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch one ArtisanPro agent bridge assignment")
    parser.add_argument("--once", action="store_true", help="poll once and exit")
    args = parser.parse_args()

    if not (SHARED / ".git").exists():
        log(f"shared checkout not found: {SHARED}")
        return 2

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    log(f"=== {AGENT_ID} watcher started (direct bridge poll every {POLL_SECONDS}s) ===")
    log(f"shared={SHARED}")
    log(f"alert={ALERT}")
    log(f"questions flag={QFLAG}")

    memory = load_memory()
    while True:
        cycle_started = time.monotonic()
        try:
            memory = poll_once(memory)
        except Exception as error:  # keep the watcher alive after one bad cycle
            log(f"watcher error: {type(error).__name__}: {error}")
        if args.once or STOP.is_set():
            break
        elapsed = time.monotonic() - cycle_started
        STOP.wait(max(0.0, POLL_SECONDS - elapsed))

    log("watcher stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
