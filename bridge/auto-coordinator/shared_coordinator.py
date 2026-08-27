#!/usr/bin/env python3
import copy
import fnmatch
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(os.getenv("REPO_PATH", Path(__file__).resolve().parents[2])).resolve()
BRIDGE = REPO / "bridge"
TASKS_FILE = BRIDGE / "tasks.json"
STATE_FILE = BRIDGE / "state.json"
LOCKS_FILE = BRIDGE / "locks.json"

POLL_SECONDS = int(os.getenv("POLL_SECONDS", "30"))
BRANCH = os.getenv("PUSH_BRANCH", "main")
COMMIT_MSG = os.getenv("COMMIT_MSG", "auto: assign next tasks [skip ci]")

ROLE_TO_AGENT = {
    "shared": "shared-agent",
    "i18n": "i18n-agent",
    "peinture": "peinture-agent",
    "admin": "admin-agent",
    "security": "security-agent",
    "client": "client-agent",
    "api": "api-agent",
    "billing": "billing-agent",
}

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return copy.deepcopy(default)

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)

def run(cmd):
    return subprocess.run(cmd, cwd=str(REPO), shell=True, text=True, capture_output=True)

def git_fetch():
    p = run("git fetch origin main --prune --quiet")
    if p.returncode != 0:
        return False, p.stderr.strip() or p.stdout.strip()
    return True, ""

def git_push_with_rebase():
    p = run(f"git push origin {BRANCH}")
    if p.returncode == 0:
        return True, ""
    # try rebase once
    p2 = run(f"git pull --rebase --autostash origin {BRANCH}")
    if p2.returncode != 0:
        return False, p.stderr.strip() or p.stdout.strip() or p2.stderr.strip() or p2.stdout.strip()
    p3 = run(f"git push origin {BRANCH}")
    if p3.returncode != 0:
        return False, p3.stderr.strip() or p3.stdout.strip()
    return True, ""

def priority_value(task):
    p = task.get("priority", "P3")
    if isinstance(p, int):
        return p
    return PRIORITY_ORDER.get(str(p).upper(), 99)

def normalize_tasks(blob):
    if isinstance(blob, dict):
        blob.setdefault("version", 1)
        blob.setdefault("tasks", [])
        return blob
    return {"version": 1, "tasks": blob if isinstance(blob, list) else []}

def normalize_locks(blob):
    if isinstance(blob, dict):
        blob.setdefault("version", 1)
        blob.setdefault("locks", [])
        return blob
    return {"version": 1, "locks": blob if isinstance(blob, list) else []}

def normalize_state(blob):
    if not isinstance(blob, dict):
        blob = {}
    blob.setdefault("version", 0)
    blob.setdefault("coordinator", "shared-agent")
    blob.setdefault("mode", "coordinator")
    blob.setdefault("prevTask", {"id": "", "status": "waiting_assignment"})
    blob.setdefault("currTask", {"id": "", "status": "waiting_assignment"})
    blob.setdefault("nextTask", {"id": "", "status": "waiting_assignment"})
    blob.setdefault("currentTasks", {})
    blob.setdefault("queue", {"done": 0, "inProgress": 0, "todo": 0, "blocked": 0})
    blob.setdefault("lastSeenSha", "")
    blob.setdefault("updatedAt", now_iso())
    return blob

def summarize(task):
    if not task:
        return {"id": "", "status": "waiting_assignment", "assignee": "", "role": "", "claimedFiles": []}
    return {
        "id": task.get("id", ""),
        "title": task.get("title", ""),
        "status": task.get("status", ""),
        "assignee": task.get("assignee", ""),
        "role": task.get("role", ""),
        "parentRepo": task.get("parentRepo", ""),
        "priority": task.get("priority", ""),
        "claimedFiles": task.get("claimedFiles") or task.get("files") or [],
        "claimedAt": task.get("claimedAt", ""),
        "completedAt": task.get("completedAt", ""),
    }

def task_map(tasks):
    return {t.get("id"): t for t in tasks if t.get("id")}

def deps_done(task, tasks_by_id):
    for dep in task.get("dependencies", []):
        if tasks_by_id.get(dep, {}).get("status") != "done":
            return False
    return True

def static_prefix(pattern):
    pattern = pattern.replace("\\", "/")
    for i, ch in enumerate(pattern):
        if ch in "*?[":
            return pattern[:i].rstrip("/")
    return pattern.rstrip("/")

def overlap(a, b):
    a = (a or "").replace("\\", "/")
    b = (b or "").replace("\\", "/")
    if not a or not b:
        return False
    if a == b:
        return True
    pa, pb = static_prefix(a), static_prefix(b)
    if pa and pb and (pa.startswith(pb) or pb.startswith(pa)):
        return True
    return fnmatch.fnmatchcase(pa or a, b) or fnmatch.fnmatchcase(pb or b, a)

def task_conflicts(task, active_locks):
    files = task.get("claimedFiles") or task.get("files") or []
    for lock in active_locks:
        lock_files = lock.get("files") or lock.get("claimedFiles") or []
        for tf in files:
            for lf in lock_files:
                if overlap(tf, lf):
                    return True
    return False

def release_done_locks(tasks, locks_blob):
    done_ids = {t.get("id") for t in tasks if t.get("status") == "done"}
    before = len(locks_blob["locks"])
    locks_blob["locks"] = [l for l in locks_blob["locks"] if l.get("taskId") not in done_ids]
    return len(locks_blob["locks"]) != before

def sync_active_locks(tasks, locks_blob):
    active = {t.get("id"): t for t in tasks if t.get("status") == "in_progress"}
    existing = {l.get("taskId") for l in locks_blob["locks"]}
    changed = False
    for t in active.values():
        if t.get("id") not in existing:
            files = t.get("claimedFiles") or t.get("files") or []
            locks_blob["locks"].append({
                "agent": t.get("assignee") or ROLE_TO_AGENT.get(t.get("role"), "shared-agent"),
                "taskId": t.get("id"),
                "files": files,
                "since": t.get("claimedAt", now_iso())
            })
            changed = True
    return changed

def pick_next_task(tasks, active_locks, tasks_by_id):
    candidates = []
    for t in tasks:
        if t.get("status") not in ("todo", "waiting_assignment"):
            continue
        if not deps_done(t, tasks_by_id):
            continue
        if task_conflicts(t, active_locks):
            continue
        candidates.append(t)

    candidates.sort(key=lambda t: (
        priority_value(t),
        t.get("claimedAt", ""),
        t.get("id", "")
    ))
    return candidates[0] if candidates else None

def assign_task(task, locks_blob):
    agent = task.get("assignee") or ROLE_TO_AGENT.get(task.get("role"), "shared-agent")
    task["assignee"] = agent
    task["status"] = "in_progress"
    task["claimedAt"] = now_iso()
    task["claimedFiles"] = task.get("claimedFiles") or task.get("files") or []

    locks_blob["locks"].append({
        "agent": agent,
        "taskId": task["id"],
        "files": task["claimedFiles"],
        "since": task["claimedAt"]
    })
    return task

def counts(tasks):
    return {
        "done": sum(1 for t in tasks if t.get("status") == "done"),
        "inProgress": sum(1 for t in tasks if t.get("status") == "in_progress"),
        "todo": sum(1 for t in tasks if t.get("status") in ("todo", "waiting_assignment")),
        "blocked": sum(1 for t in tasks if t.get("status") == "blocked"),
    }

def main():
    while True:
        ok, err = git_fetch()
        if not ok:
            print(f"[coordinator] fetch failed: {err}")
            time.sleep(POLL_SECONDS)
            continue

        tasks_blob = normalize_tasks(read_json(TASKS_FILE, {"version": 1, "tasks": []}))
        locks_blob = normalize_locks(read_json(LOCKS_FILE, {"version": 1, "locks": []}))
        state = normalize_state(read_json(STATE_FILE, {}))

        tasks = tasks_blob["tasks"]
        tasks_by_id = task_map(tasks)

        before = json.dumps(
            {"tasks": tasks_blob, "locks": locks_blob, "state": state},
            sort_keys=True,
            ensure_ascii=False
        )

        changed = False

        if release_done_locks(tasks, locks_blob):
            changed = True
        if sync_active_locks(tasks, locks_blob):
            changed = True

        # Assign as many safe tasks as possible in this cycle
        while True:
            tasks_by_id = task_map(tasks)
            next_task = pick_next_task(tasks, locks_blob["locks"], tasks_by_id)
            if not next_task:
                break
            assign_task(next_task, locks_blob)
            changed = True

        # Update state summary
        done_tasks = [t for t in tasks if t.get("status") == "done"]
        active_tasks = [t for t in tasks if t.get("status") == "in_progress"]

        if done_tasks:
            latest_done = max(
                done_tasks,
                key=lambda t: (t.get("completedAt", ""), t.get("claimedAt", ""), t.get("id", ""))
            )
            state["prevTask"] = summarize(latest_done)

        if active_tasks:
            active_tasks.sort(key=lambda t: (priority_value(t), t.get("claimedAt", ""), t.get("id", "")))
            state["currTask"] = summarize(active_tasks[0])
            state["currentTasks"] = {t["id"]: summarize(t) for t in active_tasks}
        else:
            state["currTask"] = {"id": "", "status": "waiting_assignment", "assignee": "", "role": "", "claimedFiles": []}
            state["currentTasks"] = {}

        preview = pick_next_task(tasks, locks_blob["locks"], tasks_by_id)
        state["nextTask"] = summarize(preview) if preview else {"id": "", "status": "waiting_assignment", "assignee": "", "role": "", "claimedFiles": []}

        state["queue"] = counts(tasks)
        state["coordinator"] = "shared-agent"
        state["mode"] = "coordinator"
        state["version"] = int(state.get("version", 0)) + (1 if changed else 0)
        state["updatedAt"] = now_iso()

        after = json.dumps(
            {"tasks": tasks_blob, "locks": locks_blob, "state": state},
            sort_keys=True,
            ensure_ascii=False
        )

        if before != after:
            write_json(TASKS_FILE, tasks_blob)
            write_json(LOCKS_FILE, locks_blob)
            write_json(STATE_FILE, state)

            run("git add bridge/tasks.json bridge/locks.json bridge/state.json")
            p = run(f'git commit -m "{COMMIT_MSG}"')
            if p.returncode != 0 and "nothing to commit" not in (p.stdout + p.stderr).lower():
                print(f"[coordinator] commit: {p.stderr.strip() or p.stdout.strip()}")
            else:
                ok_push, err_push = git_push_with_rebase()
                if not ok_push:
                    print(f"[coordinator] push failed: {err_push}")
                else:
                    print("[coordinator] pushed updates")
        else:
            print("[coordinator] no changes")

        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
