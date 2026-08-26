#!/usr/bin/env python3
"""
Coordinator watcher for the ArtisanPro multi-agent bridge.

Created by client-agent on user request: "create a watcher for the coordinator
compatible with your script". It follows the same conventions as the
client-agent watcher (10s polling, same log line format, same alert-file
pattern) and stays a pure observer: it never edits tasks, locks, or state.

Watches (all from origin/main of the shared repo):
  1. Tasks assigned to the coordinator (assignee == COORDINATOR_ID)
     -> alert file NEW_COORDINATOR_TASK.json when actionable
     (todo / in_progress / waiting_assignment / blocked)
  2. Auto-coordinator runner liveness: age of the last 'auto:' commit
     -> alert file COORDINATOR_STALLED.flag when older than STALL_MINUTES
  3. bridge/state.json movement (lastUpdate, overallStatus, activeTask)
     -> logged on change
  4. New coordinator/lead mentions in bridge/questions.md
     -> alert file CHECK_COORDINATOR_QUESTIONS.flag

Compatible with bridge/auto-coordinator/agent-watcher.py conventions:
  - Same entry-point style as client-watcher.py / admin-watcher.py
  - Alert/log paths overridable via environment
  - Git authentication not stored in this file (public repo fetch; set
    GITHUB_TOKEN/GH_TOKEN in the process environment if needed)

Environment:
  COORDINATOR_ID  Assignee to watch. Defaults to lead-engineer.
  SHARED_REPO     Shared checkout path. Defaults to this repository root.
  POLL_SECONDS    Poll interval. Defaults to 10 (matches client-agent watcher).
  STALL_MINUTES   Runner silence threshold. Defaults to 30.
  WATCH_LOG       Activity log path. Defaults to ~/coordinator-watch.log.
  WATCH_ALERT     Task alert path. Defaults to ~/NEW_COORDINATOR_TASK.json.
  WATCH_QFLAG     Questions flag path. Defaults to ~/CHECK_COORDINATOR_QUESTIONS.flag.
  WATCH_STALL     Stall flag path. Defaults to ~/COORDINATOR_STALLED.flag.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COORDINATOR_ID = os.environ.get('COORDINATOR_ID', 'lead-engineer')
SHARED = Path(os.environ.get('SHARED_REPO', str(ROOT))).expanduser().resolve()
POLL_SECONDS = max(5, int(os.environ.get('POLL_SECONDS', '10')))
STALL_MINUTES = max(1, int(os.environ.get('STALL_MINUTES', '30')))
ACTIONABLE = ('todo', 'in_progress', 'waiting_assignment', 'blocked')
RUNNER_COMMIT_RE = re.compile(r'^auto:', re.IGNORECASE)

LOG = Path(os.environ.get('WATCH_LOG',
                          str(Path.home() / 'coordinator-watch.log'))).expanduser()
ALERT = Path(os.environ.get('WATCH_ALERT',
                            str(Path.home() / 'NEW_COORDINATOR_TASK.json'))).expanduser()
QFLAG = Path(os.environ.get('WATCH_QFLAG',
                            str(Path.home() / 'CHECK_COORDINATOR_QUESTIONS.flag'))).expanduser()
STALL = Path(os.environ.get('WATCH_STALL',
                            str(Path.home() / 'COORDINATOR_STALLED.flag'))).expanduser()


def now() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def git(*args) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    return subprocess.run(['git', '-C', str(SHARED), *args],
                          capture_output=True, text=True, timeout=60, env=env)


def show_origin(path: str):
    r = git('show', f'origin/main:{path}')
    return r.stdout if r.returncode == 0 else None


def log(message: str) -> None:
    line = f'[{now()}] {message}'
    print(line, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open('a', encoding='utf-8') as stream:
            stream.write(line + '\n')
    except OSError:
        pass


def write_alert(path: Path, content: str) -> None:
    try:
        path.write_text(content, encoding='utf-8')
    except OSError:
        pass


def clear_alert(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def coordinator_tasks():
    raw = show_origin('bridge/tasks.json')
    if not raw:
        return None, []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, []
    tasks = [t for t in data.get('tasks', [])
             if t.get('assignee') == COORDINATOR_ID]
    return data.get('lastUpdate'), tasks


def last_runner_commit_age_seconds():
    """Age of the newest 'auto:' commit on origin/main, or None if absent."""
    r = git('log', 'origin/main', '--format=%H %cI %s', '-n', '200')
    if r.returncode != 0:
        return None
    for line in r.stdout.splitlines():
        parts = line.split(' ', 2)
        if len(parts) < 3:
            continue
        _sha, iso_date, subject = parts
        if RUNNER_COMMIT_RE.match(subject.strip()):
            try:
                committed = datetime.fromisoformat(iso_date)
                if committed.tzinfo is None:
                    committed = committed.replace(tzinfo=timezone.utc)
                return (datetime.now(timezone.utc) - committed).total_seconds()
            except ValueError:
                return None
    return None


def state_snapshot():
    raw = show_origin('bridge/state.json')
    if not raw:
        return None
    try:
        s = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return (s.get('lastUpdate'), s.get('overallStatus'),
            s.get('activeTask'), s.get('currentPhase'))


def questions_mentions():
    raw = show_origin('bridge/questions.md')
    if not raw:
        return -1
    return len(re.findall(r'coordinator|lead-engineer', raw, re.IGNORECASE))


def main() -> None:
    log(f'=== coordinator watcher started (bridge poll every {POLL_SECONDS}s, '
        f'watching {COORDINATOR_ID}) ===')
    last_task_sig = None
    last_state = None
    last_mentions = None
    polls = 0

    while True:
        try:
            r = git('fetch', 'origin', '--quiet')
            if r.returncode != 0:
                log(f'fetch failed: {r.stderr.strip()[:120]}')

            # 1) coordinator tasks
            last_update, tasks = coordinator_tasks()
            if tasks is None and last_update is None:
                log('could not read bridge/tasks.json from origin/main')
            else:
                sig = json.dumps([[t.get('id'), t.get('status')]
                                  for t in tasks], ensure_ascii=False)
                if sig != last_task_sig:
                    if not tasks:
                        log(f'no {COORDINATOR_ID} tasks in tasks.json')
                    for t in tasks:
                        log(f"task {t.get('id')} status={t.get('status')}")
                    last_task_sig = sig

                actionable = [t for t in tasks
                              if t.get('status') in ACTIONABLE]
                if actionable:
                    t = actionable[0]
                    write_alert(ALERT, json.dumps(t, indent=2,
                                                  ensure_ascii=False))
                    log(f'*** NEW/ACTIONABLE COORDINATOR TASK: {t.get("id")} '
                        f'({t.get("status")}) - {t.get("title")} ***')
                else:
                    clear_alert(ALERT)

            # 2) runner liveness
            age = last_runner_commit_age_seconds()
            if age is None:
                log('no auto: runner commit found in last 200 commits')
                clear_alert(STALL)
            elif age > STALL_MINUTES * 60:
                write_alert(STALL,
                            f'{now()} auto-coordinator silent for '
                            f'{int(age // 60)} min (threshold '
                            f'{STALL_MINUTES} min)\n')
                log(f'!! COORDINATOR STALLED: last auto: commit was '
                    f'{int(age // 60)} min ago !!')
            else:
                clear_alert(STALL)

            # 3) state.json movement
            snap = state_snapshot()
            if snap and snap != last_state:
                if last_state is not None:
                    log(f'state moved: lastUpdate={snap[0]} '
                        f'overallStatus={snap[1]} activeTask={snap[2]}')
                last_state = snap

            # 4) questions.md mentions
            m = questions_mentions()
            if last_mentions is not None and m > last_mentions:
                write_alert(QFLAG,
                            f'{now()} new coordinator/lead mentions in '
                            f'bridge/questions.md ({last_mentions} -> {m})\n')
                log(f'questions.md has NEW coordinator/lead mentions '
                    f'({last_mentions} -> {m}) - review needed')
            if m >= 0:
                last_mentions = m

            # heartbeat once a minute (keeps the 10s log readable)
            polls += 1
            if polls % 6 == 1:
                mine = (f'{len(tasks)} task(s), '
                        + ', '.join(f"{t.get('id')}={t.get('status')}"
                                    for t in tasks) if tasks else 'none')
                runner = (f'{int(age // 60)}m ago' if age is not None
                          else 'unknown')
                log(f'heartbeat - bridge lastUpdate={last_update} | '
                    f'{COORDINATOR_ID}: {mine} | runner: {runner}')

        except Exception as e:  # keep the loop alive no matter what
            log(f'error: {type(e).__name__}: {e}')

        time.sleep(POLL_SECONDS)


if __name__ == '__main__':
    main()
