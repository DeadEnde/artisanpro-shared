#!/usr/bin/env python3
"""
Auto-Coordinator - Python version
Automatically assigns next tasks when agents push
Compatible with JS version - same logic
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_PATH = Path(__file__).parent.parent
TASKS_PATH = REPO_PATH / 'bridge/tasks.json'
LOCKS_PATH = REPO_PATH / 'bridge/locks.json'
STATE_PATH = REPO_PATH / 'bridge/state.json'

def now():
    return datetime.now(timezone.utc).isoformat()

def log(msg):
    print(f"[AUTO-COORDINATOR {now()}] {msg}")

def load_json(p):
    try:
        with open(p, 'r') as f:
            return json.load(f)
    except Exception as e:
        log(f"Failed to load {p}: {e}")
        return None

def save_json(p, data):
    with open(p, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')

def main():
    log("Starting auto-assign check (Python)...")
    
    tasks_data = load_json(TASKS_PATH)
    locks_data = load_json(LOCKS_PATH)
    state_data = load_json(STATE_PATH)
    
    if not all([tasks_data, locks_data, state_data]):
        log("Missing bridge files, aborting")
        return False
    
    changed = False
    newly_assigned = []
    
    # 1. Release locks for done tasks
    done_ids = [t['id'] for t in tasks_data['tasks'] if t['status'] == 'done']
    active_locks = locks_data.get('locks', [])
    kept_locks = []
    
    for lock in active_locks:
        if lock['taskId'] in done_ids:
            log(f"Releasing lock for done task {lock['taskId']} (agent {lock['agent']})")
            changed = True
        else:
            kept_locks.append(lock)
    
    if len(kept_locks) != len(active_locks):
        locks_data['locks'] = kept_locks
        locks_data['lastUpdate'] = now()
        save_json(LOCKS_PATH, locks_data)
        changed = True
    
    # 2. Auto-assign next tasks where deps met
    task_map = {t['id']: t for t in tasks_data['tasks']}
    
    for task in tasks_data['tasks']:
        if task['status'] != 'todo':
            continue
        
        # Check dependencies
        deps = task.get('dependencies', [])
        deps_met = all(task_map.get(dep) and task_map[dep]['status'] == 'done' for dep in deps)
        
        if not deps_met:
            waiting = [d for d in deps if not task_map.get(d) or task_map[d]['status'] != 'done']
            log(f"Task {task['id']} waiting for: {', '.join(waiting)}")
            continue
        
        # Check file conflicts
        claimed = task.get('claimedFiles', [])
        conflict = False
        for lock in locks_data['locks']:
            for lf in lock['files']:
                for cf in claimed:
                    # Simple glob check
                    if '*' in cf or '*' in lf:
                        base1 = cf.split('*')[0]
                        base2 = lf.split('*')[0]
                        if base1 and base2 and (lf.startswith(base1) or cf.startswith(base2)):
                            conflict = True
                            break
                    elif cf == lf:
                        conflict = True
                        break
                if conflict:
                    break
            if conflict:
                break
        
        if conflict:
            log(f"Task {task['id']} has file lock conflict, skipping")
            continue
        
        # Auto-assign!
        log(f"Auto-assigning {task['id']} to {task['assignee']} (role: {task['role']})")
        task['status'] = 'in_progress'
        task['claimedAt'] = now()
        newly_assigned.append(task)
        
        locks_data['locks'].append({
            'agent': task['assignee'],
            'files': claimed,
            'since': now(),
            'taskId': task['id']
        })
        
        changed = True
    
    if newly_assigned:
        tasks_data['lastUpdate'] = now()
        save_json(TASKS_PATH, tasks_data)
        locks_data['lastUpdate'] = now()
        save_json(LOCKS_PATH, locks_data)
        
        # Update state.json
        state_data['lastUpdate'] = now()
        state_data['currentTasks'] = {t['id']: t['status'] for t in tasks_data['tasks']}
        state_data['lastCoordinatorMessage'] = f"Auto-assigned {len(newly_assigned)} tasks (Python): {', '.join(t['id'] for t in newly_assigned)} at {now()}"
        if 'inProgress' in state_data:
            state_data['inProgress'] = [i for i in state_data['inProgress'] if 'Auto-assigned' not in i]
            state_data['inProgress'].append(f"Auto-assigned {len(newly_assigned)} tasks (Python): {', '.join(t['id'] for t in newly_assigned)}")
        save_json(STATE_PATH, state_data)
        
        log(f"Successfully auto-assigned {len(newly_assigned)} tasks (Python)")
        
        # GitHub Actions output
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"assigned={','.join(t['id'] for t in newly_assigned)}\n")
                f.write(f"count={len(newly_assigned)}\n")
                f.write("changed=true\n")
    else:
        log("No new tasks to auto-assign")
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write("changed=false\n")
    
    # Summary
    log("=== CURRENT STATUS (Python) ===")
    for t in tasks_data['tasks']:
        log(f"{t['priority']} {t['id']}: {t['status']} ({t['assignee']}) deps:{','.join(t.get('dependencies',[])) or 'none'}")
    log(f"Locks: {len(locks_data['locks'])} active")
    for l in locks_data['locks']:
        log(f"  - {l['agent']} -> {l['taskId']}: {', '.join(l['files'][:2])}...")
    
    return changed

if __name__ == '__main__':
    changed = main()
    if changed:
        log("Changes made - should commit & push")
    else:
        log("No changes needed")
