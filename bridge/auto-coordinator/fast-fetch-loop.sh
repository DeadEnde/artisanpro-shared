#!/bin/bash
# Fast fetch loop - per user request: NOT 60s, keep doing git fetch, check if new, yes or no, work with time
# "La maxi 60 s b9a der git Fitch 9ra wax kayn chi haja jdida ah ola la ou nta 4adi mat5dmx b lw9t"
# Translation: Not 60s, keep doing git fetch, read if there's something new yes or no, and you will work with time (continuously)

REPO="/home/user/artisanpro-shared"
cd $REPO

# Ensure remote
git remote -v | grep origin > /dev/null 2>&1 || git remote add origin https://github.com/DeadEnde/artisanpro-shared.git

echo "=== FAST FETCH LOOP STARTED - NO 60s WAIT ==="
echo "Repo: $REPO"
echo "Interval: 10s (not 60s) - fast check"
echo "Logic: git fetch -> check new commits -> if yes pull and check tasks -> give new tasks -> fetch again"
echo "Runs forever, works with time continuously"
echo ""

iteration=0

while true; do
  iteration=$((iteration+1))
  echo ""
  echo "--- ITER $iteration - $(date -u +"%Y-%m-%dT%H:%M:%SZ") ---"
  
  echo "[FETCH] git fetch origin main..."
  fetch_out=$(git fetch origin main 2>&1)
  echo "$fetch_out" | tail -n 2
  
  # Check behind
  behind=$(git rev-list HEAD..origin/main --count 2>&1)
  if [[ "$behind" =~ ^[0-9]+$ ]] && [ "$behind" -gt 0 ]; then
    echo "[NEW] YES! $behind new commit(s) found! Pulling..."
    pull_out=$(git pull --rebase origin main 2>&1)
    echo "$pull_out" | tail -n 10
    
    echo "[CHECK] New tasks status after pull:"
    python3 -c "
import json
from datetime import datetime, timezone
d=json.load(open('bridge/tasks.json'))
print(f\"  Total {len(d['tasks'])} tasks, lastUpdate {d['lastUpdate'][:19]}\")
# Recently completed
now=datetime.now(timezone.utc)
recent=[]
for t in d['tasks']:
    comp=t.get('completedAt')
    if comp and t['status']=='done':
        try:
            dt=datetime.fromisoformat(comp.replace('Z','+00:00'))
            mins=(now-dt).total_seconds()/60
            if mins < 15:
                recent.append((t['id'], t['assignee'], mins))
        except: pass
if recent:
    print('  Recently DONE (<15min):')
    for tid, assignee, mins in recent:
        print(f'    {tid} by {assignee} {mins:.0f}min ago -> GIVE NEW TASK!')
else:
    print('  No recently DONE in last 15min')

# Check waiting agents
for agent in ['admin-agent','client-agent','peinture-agent','i18n-agent','security-agent','api-agent','billing-agent']:
    agent_tasks=[t for t in d['tasks'] if t['assignee']==agent]
    inprog=[t for t in agent_tasks if t['status']=='in_progress']
    todo=[t for t in agent_tasks if t['status']=='todo']
    done=[t for t in agent_tasks if t['status']=='done']
    if not inprog and not todo and done:
        print(f'  {agent}: WAITING - {len(done)} DONE, 0 IN_PROGRESS/TODO -> needs new task')
    elif inprog:
        print(f'  {agent}: HAS TASK - {len(inprog)} IN_PROGRESS ({[t[\"id\"] for t in inprog]})')
"
    
    echo "[ASSIGN] Running auto-assign.py to give new tasks..."
    python3 scripts/auto-assign.py 2>&1 | grep -E "Auto-assigning|No new|P0|P1|P2|P3|done|in_progress" | tail -n 20
    
    # Check if changes to push
    if [ -n "$(git status --porcelain 2>&1)" ]; then
      echo "[PUSH] Changes detected, pushing new tasks..."
      git add bridge/tasks.json bridge/locks.json bridge/state.json
      git commit -m "auto: fast fetch loop - new tasks $(date -u +"%Y-%m-%dT%H:%M:%SZ") [skip ci]" 2>&1 | tail -n 2
      git push origin main 2>&1 | tail -n 3
      echo "[PUSH] Done!"
    else
      echo "[PUSH] No changes"
    fi
    
  else
    echo "[NEW] NO - No new commits, no new tasks"
    echo "[CHECK] Current queue:"
    python3 -c "
import json
d=json.load(open('bridge/tasks.json'))
from collections import Counter
c=Counter(t['status'] for t in d['tasks'])
print(f\"  {len(d['tasks'])} tasks: {dict(c)}\")
# Show in_progress
for t in d['tasks']:
    if t['status']=='in_progress':
        print(f\"    IN_PROGRESS: {t['id']} ({t['assignee']})\")
"
  fi
  
  echo "[SLEEP] Next fetch in 10s (not 60s) at $(date -u -d '+10 seconds' +'%H:%M:%SZ')"
  sleep 10
done
