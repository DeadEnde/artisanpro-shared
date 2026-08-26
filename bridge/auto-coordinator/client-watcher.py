#!/usr/bin/env python3
"""
client-agent watcher for ArtisanPro multi-agent bridge.
Improved version - based on user example.

Polls the artisanpro-shared bridge (origin/main) every 60 seconds and watches
for new tasks/questions assigned to client-agent.

Outputs:
  - stdout / client-agent-watch.log : timestamped activity log
  - /home/user/NEW_CLIENT_TASK.json : alert file when actionable task
  - /home/user/CHECK_QUESTIONS.flag : alert when questions.md has new mentions
  - Auto-reports problems to lead engineer
"""

import json
import os
import subprocess
import time
from datetime import datetime, timezone
import sys

# Fixed paths - actual repo location
SHARED = '/home/user/artisanpro-shared'
LOG = '/home/user/artisanpro-shared/bridge/auto-coordinator/client-agent-watch.log'
ALERT = '/home/user/NEW_CLIENT_TASK.json'
QFLAG = '/home/user/CHECK_QUESTIONS.flag'
POLL_SECONDS = 60
ACTIONABLE = ('todo', 'in_progress', 'waiting_assignment', 'blocked')

def now() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(['git', '-C', SHARED, *args],
                          capture_output=True, text=True, timeout=60)

def show_origin(path: str):
    r = git('show', f'origin/main:{path}')
    return r.stdout if r.returncode == 0 else None

def log(msg: str) -> None:
    line = f'[{now()}] {msg}'
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, 'a') as f:
            f.write(line + '\n')
    except OSError:
        pass

def client_tasks():
    raw = show_origin('bridge/tasks.json')
    if not raw:
        # Fallback to local file
        try:
            with open(os.path.join(SHARED, 'bridge/tasks.json'), 'r') as f:
                raw = f.read()
        except:
            return None, []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        log(f'JSON decode error in tasks.json: {e}')
        return None, []
    tasks = [t for t in data.get('tasks', [])
             if t.get('assignee') == 'client-agent']
    return data.get('lastUpdate'), tasks

def state_curr_for_client():
    raw = show_origin('bridge/state.json')
    if not raw:
        try:
            with open(os.path.join(SHARED, 'bridge/state.json'), 'r') as f:
                raw = f.read()
        except:
            return None
    try:
        st = json.loads(raw)
    except json.JSONDecodeError:
        return None
    curr = st.get('currTask') or {}
    if curr.get('assignee') == 'client-agent':
        return curr
    # Also check nextTask
    nxt = st.get('nextTask') or {}
    if nxt.get('assignee') == 'client-agent':
        return nxt
    return None

def questions_mentions():
    raw = show_origin('bridge/questions.md')
    if not raw:
        try:
            with open(os.path.join(SHARED, 'bridge/questions.md'), 'r') as f:
                raw = f.read()
        except:
            return -1
    return raw.count('client-agent')

def analyze_task(t):
    """Analyze if task is completed, incomplete, root cause"""
    status = t.get('status')
    done = t.get('done', [])
    blocked = t.get('blocked', [])
    deps = t.get('dependencies', [])
    
    # Check acceptance criteria
    acceptance = t.get('acceptanceCriteria', [])
    
    analysis = {
        'id': t.get('id'),
        'status': status,
        'done_count': len(done),
        'blocked': blocked,
        'deps': deps,
        'acceptance_total': len(acceptance),
        'is_actionable': status in ACTIONABLE
    }
    
    # Determine problems
    problems = []
    if status == 'blocked' and blocked:
        problems.append(f"BLOCKED: {', '.join(blocked)}")
    if status == 'in_progress':
        claimed = t.get('claimedAt')
        if claimed:
            try:
                claimed_dt = datetime.fromisoformat(claimed.replace('Z', '+00:00'))
                hours = (datetime.now(timezone.utc) - claimed_dt).total_seconds() / 3600
                if hours > 24:
                    problems.append(f"STUCK: {hours:.1f}h no push")
            except:
                pass
    
    analysis['problems'] = problems
    return analysis

def main() -> None:
    log('=== client-agent watcher started (bridge poll every 60s) ===')
    log(f'SHARED repo: {SHARED}')
    log(f'Log file: {LOG}')
    log(f'Alert file: {ALERT}')
    log(f'Questions flag: {QFLAG}')
    last_task_sig = None
    last_mentions = None

    while True:
        try:
            r = git('fetch', 'origin', '--quiet')
            if r.returncode != 0:
                log(f'fetch failed: {r.stderr.strip()[:120]}')
                # Try to fix remote if missing
                git('remote', 'add', 'origin', 'https://ghp_***REDACTED***@github.com/DeadEnde/artisanpro-shared.git')
            
            # Check if behind and pull
            r = git('rev-list', 'HEAD..origin/main', '--count')
            if r.returncode == 0 and r.stdout.strip().isdigit() and int(r.stdout.strip()) > 0:
                log(f'Behind origin by {r.stdout.strip()} commits, pulling...')
                pr = git('pull', '--rebase', 'origin', 'main')
                if pr.returncode != 0:
                    log(f'pull failed: {pr.stderr[:200]}')
                else:
                    log('Pulled latest')

            last_update, tasks = client_tasks()
            if tasks is None and last_update is None:
                log('could not read bridge/tasks.json from origin/main')
            else:
                sig = json.dumps([[t.get('id'), t.get('status')] for t in tasks], ensure_ascii=False)
                if sig != last_task_sig:
                    if not tasks:
                        log('no client-agent tasks in tasks.json (waiting for coordinator assignment)')
                    for t in tasks:
                        analysis = analyze_task(t)
                        log(f"task {t.get('id')} status={t.get('status')} done={analysis['done_count']} problems={analysis['problems']}")
                    last_task_sig = sig
                
                # heartbeat
                mine = (f"{len(tasks)} task(s), " + ', '.join(f"{t.get('id')}={t.get('status')}" for t in tasks) if tasks else 'none')
                log(f'heartbeat - bridge lastUpdate={last_update} | client-agent: {mine}')

                actionable = [t for t in tasks if t.get('status') in ACTIONABLE]
                if actionable:
                    # Prefer todo/in_progress over blocked, and P2 over others for client
                    # Sort by priority and status
                    def sort_key(t):
                        prio_order = {'P0':0, 'P1':1, 'P2':2, 'P3':3}
                        status_order = {'in_progress':0, 'todo':1, 'blocked':2, 'waiting_assignment':1}
                        return (prio_order.get(t.get('priority','P3'),3), status_order.get(t.get('status'),5))
                    
                    actionable_sorted = sorted(actionable, key=sort_key)
                    t = actionable_sorted[0]
                    
                    with open(ALERT, 'w') as f:
                        json.dump({
                            'timestamp': now(),
                            'task': t,
                            'analysis': analyze_task(t),
                            'message': f"Client agent has actionable task: {t.get('id')} ({t.get('status')})"
                        }, f, indent=2, ensure_ascii=False)
                    log(f'*** NEW/ACTIONABLE CLIENT TASK: {t.get("id")} ({t.get("status")}) - {t.get("title")} ***')
                    
                    # Also check if blocked - report problem
                    if t.get('status') == 'blocked':
                        log(f"!!! CLIENT TASK BLOCKED: {t.get('id')} - {t.get('blocked')} - needs unblocking")
                elif os.path.exists(ALERT):
                    os.remove(ALERT)
                    log('previous actionable task no longer actionable (alert cleared)')

            # state.json direct assignment (secondary signal)
            curr = state_curr_for_client()
            if curr and curr.get('status') in ACTIONABLE:
                known_ids = {t.get('id') for t in tasks} if tasks else set()
                if curr.get('id') not in known_ids:
                    with open(ALERT, 'w') as f:
                        json.dump(curr, f, indent=2, ensure_ascii=False)
                    log(f"*** STATE currTask/nextTask ASSIGNED TO CLIENT-AGENT: {curr.get('id')} ({curr.get('status')}) ***")

            # questions.md new mentions of client-agent
            m = questions_mentions()
            if last_mentions is not None and m > last_mentions:
                with open(QFLAG, 'w') as f:
                    f.write(f'{now()} new client-agent mentions in bridge/questions.md ({last_mentions} -> {m})\n')
                log(f'questions.md has NEW client-agent mentions ({last_mentions} -> {m}) - review needed')
            if m >= 0:
                last_mentions = m

        except Exception as e:
            log(f'error: {type(e).__name__}: {e}')
            import traceback
            log(traceback.format_exc()[:500])

        time.sleep(POLL_SECONDS)

if __name__ == '__main__':
    main()
