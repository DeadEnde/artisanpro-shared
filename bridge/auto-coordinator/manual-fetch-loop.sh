#!/bin/bash
# Manual fetch loop - per user request: 
# "Mli t3ti task jdeda matb9ax thbs ok b9a der f command line git fetch ou chof wax agent kml task ila kmlha 3tih new task ou ila no der git Fitch 3awtani"
# When you give new task don't stop, keep doing git fetch in command line and check if agent completed task, if completed give new task, if not fetch again

REPO="/home/user/artisanpro-shared"
cd $REPO

echo "=== MANUAL FETCH LOOP STARTED ==="
echo "Repo: $REPO"
echo "Interval: 60s"
echo "Logic: git fetch -> check if agent completed task -> if yes give new task -> if no fetch again"
echo "Runs forever, never stops"
echo ""

iteration=0

while true; do
  iteration=$((iteration+1))
  echo ""
  echo "--- ITERATION $iteration - $(date -u +"%Y-%m-%dT%H:%M:%SZ") ---"
  
  # Git fetch
  echo "[FETCH] git fetch origin main..."
  git fetch origin main 2>&1 | tail -n 5
  
  # Check if behind
  behind=$(git rev-list HEAD..origin/main --count 2>&1)
  if [[ "$behind" =~ ^[0-9]+$ ]] && [ "$behind" -gt 0 ]; then
    echo "[PULL] Behind by $behind commits, pulling..."
    git pull --rebase origin main 2>&1 | tail -n 10
  else
    echo "[PULL] Up to date with origin"
  fi
  
  # Check tasks status
  echo "[CHECK] Current tasks:"
  python3 -c "
import json
from collections import Counter
d=json.load(open('bridge/tasks.json'))
c=Counter(t['status'] for t in d['tasks'])
print(f\"  Total {len(d['tasks'])}: {dict(c)}\")
for t in d['tasks']:
    if t['status'] in ['done','in_progress','blocked'] and t['assignee'] in ['admin-agent','client-agent']:
        print(f\"    {t['id']}: {t['status']} ({t['assignee']}) done={len(t.get('done',[]))}\")
"
  
  # Check if any agent completed task (status changed from in_progress to done in last fetch)
  # For simplicity, we check current DONE tasks that have completedAt recent (<5min)
  echo "[CHECK] Checking for recently completed tasks..."
  python3 << 'PY'
import json, datetime
from datetime import timezone
d=json.load(open('bridge/tasks.json'))
now=datetime.datetime.now(timezone.utc)
recent_done=[]
for t in d['tasks']:
    comp=t.get('completedAt')
    if comp and t['status']=='done':
        try:
            dt=datetime.datetime.fromisoformat(comp.replace('Z','+00:00'))
            mins=(now-dt).total_seconds()/60
            if mins < 10:  # Completed in last 10 minutes
                recent_done.append((t['id'], t['assignee'], mins))
        except:
            pass

if recent_done:
    print(f"  Recently completed (last 10min):")
    for tid, assignee, mins in recent_done:
        print(f"    {tid} by {assignee} {mins:.1f}min ago")
else:
    print("  No recently completed tasks in last 10min")

# Check if admin or client waiting (no IN_PROGRESS)
admin_tasks=[t for t in d['tasks'] if t['assignee']=='admin-agent']
client_tasks=[t for t in d['tasks'] if t['assignee']=='client-agent']
admin_inprog=[t for t in admin_tasks if t['status']=='in_progress']
client_inprog=[t for t in client_tasks if t['status']=='in_progress']
admin_done=[t for t in admin_tasks if t['status']=='done']
client_done=[t for t in client_tasks if t['status']=='done']

print(f"  Admin: {len(admin_done)} DONE, {len(admin_inprog)} IN_PROGRESS - {'WAITING' if not admin_inprog else 'HAS TASK'}")
print(f"  Client: {len(client_done)} DONE, {len(client_inprog)} IN_PROGRESS - {'WAITING' if not client_inprog else 'HAS TASK'}")

if not admin_inprog:
    print("  -> Admin WAITING for new task! Need to dispatch")
if not client_inprog:
    print("  -> Client WAITING for new task! Need to dispatch")
PY
  
  # Run auto-assign to give new tasks if possible
  echo "[ASSIGN] Running auto-assign.py..."
  python3 scripts/auto-assign.py 2>&1 | tail -n 15
  
  # Check if changes and push
  changes=$(git status --porcelain 2>&1 | wc -l)
  if [ "$changes" -gt 0 ]; then
    echo "[PUSH] Changes detected, pushing..."
    git add bridge/tasks.json bridge/locks.json bridge/state.json
    git commit -m "auto: manual fetch loop - recursive assignment $(date -u +"%Y-%m-%dT%H:%M:%SZ") [skip ci]" 2>&1 | tail -n 3
    git push origin main 2>&1 | tail -n 5
    echo "[PUSH] Pushed new tasks!"
  else
    echo "[PUSH] No changes to push"
  fi
  
  echo "[SLEEP] Next fetch in 60s at $(date -u -d "+60 seconds" +"%Y-%m-%dT%H:%M:%SZ")"
  echo "--- Iteration $iteration complete ---"
  
  sleep 60
done
