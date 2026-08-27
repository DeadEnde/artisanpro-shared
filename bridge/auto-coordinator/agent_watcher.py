#!/usr/bin/env python3
import json
import os
import subprocess
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(os.getenv("REPO_PATH", Path(__file__).resolve().parents[2])).resolve()
AGENT_ID = os.getenv("AGENT_ID", "").strip()
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "30"))
EXEC_CMD = os.getenv("EXEC_CMD", "").strip()

STATE_FILE = REPO / "bridge" / "state.json"
TASKS_FILE = REPO / "bridge" / "tasks.json"

LOG_FILE = Path(os.getenv("WATCH_LOG", str(Path.home() / f"{AGENT_ID or 'agent'}-watch.log")))
LAST_SIG_FILE = Path(os.getenv("LAST_SIG_FILE", str(Path.home() / f".artisanpro_{AGENT_ID or 'agent'}_sig")))

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def log(msg):
    line = f"[{now_iso()}] {msg}\n"
    print(line, end="")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)

def run(cmd, cwd=REPO, env=None):
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        shell=True,
        env=env,
        text=True,
        capture_output=True
    )

def git_fetch():
    p = run("git fetch origin main --prune --quiet")
    if p.returncode != 0:
        log(f"git fetch failed: {p.stderr.strip() or p.stdout.strip()}")
        return False
    return True

def normalize_tasks(blob):
    if isinstance(blob, dict):
        return blob.get("tasks", [])
    if isinstance(blob, list):
        return blob
    return []

def priority_value(task):
    p = task.get("priority", "P3")
    if isinstance(p, int):
        return p
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return order.get(str(p).upper(), 99)

def pick_my_task(tasks):
    mine = [
        t for t in tasks
        if t.get("assignee") == AGENT_ID and t.get("status") in ("todo", "in_progress", "waiting_assignment", "waiting_dependency")
    ]
    mine.sort(key=lambda t: (
        0 if t.get("status") == "in_progress" else 1,
        priority_value(t),
        t.get("claimedAt", ""),
        t.get("id", "")
    ))
    return mine[0] if mine else None

def signature(task, state):
    payload = {
        "agent": AGENT_ID,
        "task": {
            "id": task.get("id"),
            "status": task.get("status"),
            "assignee": task.get("assignee"),
            "claimedAt": task.get("claimedAt"),
            "completedAt": task.get("completedAt"),
        },
        "stateVersion": state.get("version"),
        "stateSha": state.get("lastSeenSha", "")
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def main():
    if not AGENT_ID:
        raise SystemExit("Set AGENT_ID (example: client-agent / admin-agent / shared-agent)")

    last_sig = LAST_SIG_FILE.read_text(encoding="utf-8").strip() if LAST_SIG_FILE.exists() else ""

    while True:
        if not git_fetch():
            time.sleep(POLL_SECONDS)
            continue

        tasks_blob = read_json(TASKS_FILE, {"tasks": []})
        state = read_json(STATE_FILE, {"version": 0, "currTask": {"status": "waiting_assignment"}})

        tasks = normalize_tasks(tasks_blob)
        task = pick_my_task(tasks)

        if not task:
            log(f"{AGENT_ID}: no task yet, polling...")
            time.sleep(POLL_SECONDS)
            continue

        sig = signature(task, state)
        if sig == last_sig:
            time.sleep(POLL_SECONDS)
            continue

        last_sig = sig
        write_atomic(LAST_SIG_FILE, sig)

        log(f"{AGENT_ID}: new/updated task -> {task.get('id')} ({task.get('status')})")

        if EXEC_CMD:
            env = os.environ.copy()
            env["ARTISANPRO_AGENT_ID"] = AGENT_ID
            env["ARTISANPRO_REPO_PATH"] = str(REPO)
            env["ARTISANPRO_TASK_JSON"] = json.dumps(task, ensure_ascii=False)
            env["ARTISANPRO_STATE_JSON"] = json.dumps(state, ensure_ascii=False)
            env["ARTISANPRO_TASK_FILE"] = str(TASKS_FILE)
            env["ARTISANPRO_STATE_FILE"] = str(STATE_FILE)

            p = run(EXEC_CMD, env=env)
            if p.stdout.strip():
                log(p.stdout.strip())
            if p.stderr.strip():
                log(p.stderr.strip())
            log(f"{AGENT_ID}: EXEC_CMD exit={p.returncode}")

        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
