#!/usr/bin/env python3
"""
Continuous Auto-Coordinator Runner - Python version - Runs forever
Checks every 60s if agents work and assigns tasks recursively
Compatible with JS version
"""

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_PATH = Path(__file__).parent.parent.parent if (Path(__file__).parent.parent.parent / 'bridge').exists() else Path(__file__).parent.parent
# Fix repo path - should be artisanpro-shared
if not (REPO_PATH / 'bridge').exists():
    REPO_PATH = Path('/home/user/artisanpro-shared')

TASKS_PATH = REPO_PATH / 'bridge/tasks.json'
LOCKS_PATH = REPO_PATH / 'bridge/locks.json'
STATE_PATH = REPO_PATH / 'bridge/state.json'

CHECK_INTERVAL = 60  # seconds

def now():
    return datetime.now(timezone.utc).isoformat()

def log(msg):
    print(f"[{now()}] {msg}", flush=True)

def exec_cmd(cmd):
    try:
        out = subprocess.run(cmd, cwd=REPO_PATH, shell=True, capture_output=True, text=True, timeout=30)
        return {'ok': out.returncode == 0, 'out': out.stdout.strip(), 'err': out.stderr.strip()}
    except Exception as e:
        return {'ok': False, 'err': str(e), 'out': ''}

def load_json(p):
    try:
        with open(p, 'r') as f:
            return json.load(f)
    except:
        return None

def run_auto_assign():
    log("Running auto-assign.py (Python)...")
    # Try Python first, fallback to JS
    res = exec_cmd('python3 scripts/auto-assign.py')
    if not res['ok']:
        log(f"Python auto-assign failed, trying JS: {res['err']}")
        res = exec_cmd('node scripts/auto-assign.js')
    
    if res['ok']:
        # Log last 10 lines
        lines = res['out'].split('\n')[-15:]
        for line in lines:
            if line.strip():
                log(line)
    else:
        log(f"auto-assign failed: {res['err']}")
    
    return res['ok']

def check_and_push():
    status = exec_cmd('git status --porcelain')
    if not status['ok']:
        log(f"git status failed: {status['err']}")
        return False
    
    if not status['out'].strip():
        log("No changes to push")
        return False
    
    log(f"Changes detected:\n{status['out']}")
    
    diff = exec_cmd('git diff --stat')
    log(f"Diff:\n{diff['out']}")
    
    commit = exec_cmd(f'git add bridge/tasks.json bridge/locks.json bridge/state.json && git commit -m "auto: continuous runner PY - recursive {now()} [skip ci]"')
    if not commit['ok']:
        log(f"Commit failed (maybe no changes to bridge): {commit['err']}")
        # Check if commit failed because no changes to those specific files
        # Try to see what files changed
        return False
    
    log(f"Committed: {commit['out'][:200]}")
    
    push = exec_cmd('git push origin main')
    if not push['ok']:
        log(f"Push failed, trying pull --rebase: {push['err']}")
        pull = exec_cmd('git pull --rebase origin main')
        log(f"Pull: {pull['out'][:300]}")
        push2 = exec_cmd('git push origin main')
        if not push2['ok']:
            log(f"Push still failed: {push2['err']}")
            return False
    
    log("Pushed successfully!")
    return True

def print_queue():
    tasks = load_json(TASKS_PATH)
    locks = load_json(LOCKS_PATH)
    state = load_json(STATE_PATH)
    
    if not tasks:
        log("Failed to load tasks.json")
        return
    
    log("=== QUEUE STATUS (Python Runner) ===")
    for t in tasks['tasks']:
        deps = ','.join(t.get('dependencies',[])) or 'none'
        blocked = f" BLOCKED:{';'.join(t.get('blocked',[]))}" if t.get('blocked') else ""
        log(f"  {t['priority']} {t['id']}: {t['status']} ({t['assignee']}) deps:{deps}{blocked}")
    
    if locks:
        log(f"Locks: {len(locks.get('locks',[]))} active")
        for l in locks.get('locks',[])[:5]:
            log(f"  - {l['agent']} -> {l['taskId']}")
    
    if state and state.get('version'):
        log(f"State v{state['version']} lastUpdate {state.get('lastUpdate')}")
        if state.get('prevTask'):
            log(f"  prev: {state['prevTask']['id']} {state['prevTask']['status']}")
        if state.get('currTask'):
            log(f"  curr: {state['currTask']['id']} {state['currTask']['status']}")
        if state.get('nextTask'):
            log(f"  next: {state['nextTask']['id']} {state['nextTask']['status']}")
    
    log("=====================================")

def main_loop():
    log("=== CONTINUOUS AUTO-COORDINATOR PYTHON STARTED ===")
    log(f"Repo: {REPO_PATH}")
    log(f"Interval: {CHECK_INTERVAL}s (60s)")
    log("Runs forever, checks if agents work and assigns recursively")
    log("Python version - compatible with JS version")
    
    iteration = 0
    
    while True:
        iteration += 1
        log(f"\n--- ITERATION {iteration} (Python) ---")
        
        # Fetch
        log("Fetching origin...")
        fetch = exec_cmd('git fetch origin main')
        if fetch['ok']:
            log("Fetch OK")
            behind = exec_cmd('git rev-list HEAD..origin/main --count')
            if behind['ok'] and behind['out'].strip().isdigit() and int(behind['out'].strip()) > 0:
                log(f"Behind by {behind['out'].strip()}, pulling...")
                pull = exec_cmd('git pull --rebase origin main')
                log(f"Pull: {pull['out'][:500]}")
            else:
                log("Up to date with origin")
        else:
            log(f"Fetch failed: {fetch['err']}")
            # Try to add remote
            exec_cmd('git remote add origin https://github.com/DeadEnde/artisanpro-shared.git 2>&1 || true')
        
        # Print queue
        print_queue()
        
        # Run auto-assign
        run_auto_assign()
        
        # Push if changed
        pushed = check_and_push()
        if pushed:
            log("Queue advanced! New tasks assigned and pushed.")
        else:
            log("No advancement this iteration")
        
        next_time = datetime.fromtimestamp(time.time() + CHECK_INTERVAL, tz=timezone.utc)
        log(f"Next check at {next_time.isoformat()} (in 60s)")
        log(f"Iteration {iteration} complete. Sleeping 60s...")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        log("Interrupted, shutting down...")
    except Exception as e:
        log(f"Fatal error: {e}")
        import traceback
        log(traceback.format_exc())
