#!/usr/bin/env python3
"""
admin-agent watcher for ArtisanPro multi-agent bridge.
Same logic as client-watcher but for admin-agent.
Watches for admin tasks separately so admin and client can differentiate.

Polls every 60s, reports problems, creates alerts.
"""

import json
import os
import subprocess
import time
from datetime import datetime, timezone

SHARED = '/home/user/artisanpro-shared'
LOG = '/home/user/artisanpro-shared/bridge/auto-coordinator/admin-agent-watch.log'
ALERT = '/home/user/NEW_ADMIN_TASK.json'
QFLAG = '/home/user/CHECK_QUESTIONS_ADMIN.flag'
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

def admin_tasks():
    raw = show_origin('bridge/tasks.json')
    if not raw:
        try:
            with open(os.path.join(SHARED, 'bridge/tasks.json'), 'r') as f:
                raw = f.read()
        except:
            return None, []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        log(f'JSON decode error: {e}')
        return None, []
    tasks = [t for t in data.get('tasks', []) if t.get('assignee') == 'admin-agent']
    return data.get('lastUpdate'), tasks

def state_curr_for_admin():
    raw = show_origin('bridge/state.json')
    if not raw:
        try:
            with open(os.path.join(SHARED, 'bridge/state.json'), 'r') as f:
                raw = f.read()
        except:
            return None
    try:
        st = json.loads(raw)
    except:
        return None
    for key in ['currTask', 'nextTask']:
        curr = st.get(key) or {}
        if curr.get('assignee') == 'admin-agent':
            return curr
    return None

def questions_mentions():
    raw = show_origin('bridge/questions.md')
    if not raw:
        try:
            with open(os.path.join(SHARED, 'bridge/questions.md'), 'r') as f:
                raw = f.read()
        except:
            return -1
    return raw.count('admin-agent')

def analyze_task(t):
    status = t.get('status')
    done = t.get('done', [])
    blocked = t.get('blocked', [])
    analysis = {
        'id': t.get('id'),
        'status': status,
        'done_count': len(done),
        'blocked': blocked,
        'is_actionable': status in ACTIONABLE
    }
    problems = []
    if status == 'blocked' and blocked:
        problems.append(f"BLOCKED: {', '.join(blocked)}")
    if status == 'in_progress' and t.get('claimedAt'):
        try:
            claimed_dt = datetime.fromisoformat(t.get('claimedAt').replace('Z', '+00:00'))
            hours = (datetime.now(timezone.utc) - claimed_dt).total_seconds() / 3600
            if hours > 24:
                problems.append(f"STUCK: {hours:.1f}h no push")
        except:
            pass
    analysis['problems'] = problems
    return analysis

def main() -> None:
    log('=== admin-agent watcher started (bridge poll every 60s) ===')
    log(f'SHARED: {SHARED}')
    last_task_sig = None
    last_mentions = None

    while True:
        try:
            r = git('fetch', 'origin', '--quiet')
            if r.returncode != 0:
                log(f'fetch failed: {r.stderr.strip()[:120]}')
                git('remote', 'add', 'origin', 'https://ghp_***REDACTED***@github.com/DeadEnde/artisanpro-shared.git')
            
            r = git('rev-list', 'HEAD..origin/main', '--count')
            if r.returncode == 0 and r.stdout.strip().isdigit() and int(r.stdout.strip()) > 0:
                log(f'Behind by {r.stdout.strip()}, pulling...')
                git('pull', '--rebase', 'origin', 'main')

            last_update, tasks = admin_tasks()
            if tasks is None and last_update is None:
                log('could not read tasks.json')
            else:
                sig = json.dumps([[t.get('id'), t.get('status')] for t in tasks], ensure_ascii=False)
                if sig != last_task_sig:
                    if not tasks:
                        log('no admin-agent tasks (waiting)')
                    for t in tasks:
                        analysis = analyze_task(t)
                        log(f"task {t.get('id')} status={t.get('status')} done={analysis['done_count']} problems={analysis['problems']}")
                    last_task_sig = sig

                mine = (f"{len(tasks)} task(s), " + ', '.join(f"{t.get('id')}={t.get('status')}" for t in tasks) if tasks else 'none')
                log(f'heartbeat - lastUpdate={last_update} | admin-agent: {mine}')

                actionable = [t for t in tasks if t.get('status') in ACTIONABLE]
                if actionable:
                    def sort_key(t):
                        prio_order = {'P0':0, 'P1':1, 'P2':2, 'P3':3}
                        status_order = {'in_progress':0, 'todo':1, 'blocked':2}
                        return (prio_order.get(t.get('priority','P3'),3), status_order.get(t.get('status'),5))
                    actionable_sorted = sorted(actionable, key=sort_key)
                    t = actionable_sorted[0]
                    with open(ALERT, 'w') as f:
                        json.dump({
                            'timestamp': now(),
                            'task': t,
                            'analysis': analyze_task(t),
                            'message': f"Admin has actionable task: {t.get('id')} ({t.get('status')})"
                        }, f, indent=2, ensure_ascii=False)
                    log(f'*** NEW/ACTIONABLE ADMIN TASK: {t.get("id")} ({t.get("status")}) - {t.get("title")} ***')
                    if t.get('status') == 'blocked':
                        log(f"!!! ADMIN TASK BLOCKED: {t.get('id')} - {t.get('blocked')}")
                elif os.path.exists(ALERT):
                    os.remove(ALERT)
                    log('alert cleared - no actionable admin task')

            curr = state_curr_for_admin()
            if curr and curr.get('status') in ACTIONABLE:
                known_ids = {t.get('id') for t in tasks} if tasks else set()
                if curr.get('id') not in known_ids:
                    with open(ALERT, 'w') as f:
                        json.dump(curr, f, indent=2, ensure_ascii=False)
                    log(f"*** STATE ASSIGNED TO ADMIN: {curr.get('id')} ({curr.get('status')}) ***")

            m = questions_mentions()
            if last_mentions is not None and m > last_mentions:
                with open(QFLAG, 'w') as f:
                    f.write(f'{now()} new admin-agent mentions ({last_mentions} -> {m})\n')
                log(f'NEW admin mentions in questions.md ({last_mentions} -> {m})')
            if m >= 0:
                last_mentions = m

        except Exception as e:
            log(f'error: {type(e).__name__}: {e}')
            import traceback
            log(traceback.format_exc()[:500])

        time.sleep(POLL_SECONDS)

if __name__ == '__main__':
    main()
