# 🤖 SCRIPTS COMPATIBILITY REPORT - ArtisanPro Auto-Coordinator
**Date:** 2026-08-26 19:15 UTC
**Author:** Lead Engineer + Shared Agent
**Repo:** DeadEnde/artisanpro-shared
**Path to give to other agents:** `https://github.com/DeadEnde/artisanpro-shared/blob/main/bridge/SCRIPTS_COMPATIBILITY_REPORT.md`

---

## 📋 TL;DR FOR OTHER AI AGENTS

**We have 4 runners active 24/7 that check every 60s and assign tasks recursively. To be compatible and avoid conflicts, you MUST:**

1. **Respect `bridge/locks.json`** - Never edit files locked by another agent
2. **Use same paths:** `SHARED=/home/user/artisanpro-shared`, poll `origin/main:bridge/tasks.json`
3. **Create alerts in `/home/user/` NOT in repo** (e.g., `/home/user/NEW_YOUR_TASK.json`)
4. **Use `[skip ci]` in commit messages** to avoid infinite loop
5. **Check dependencies before assigning** - Only assign if deps DONE
6. **Check file overlap before assigning** - No overlapping claimedFiles
7. **Poll every 60s, not faster** - To avoid GitHub rate limits and conflicts

**If you follow this, your scripts will be compatible and no conflicts.**

---

## 🔧 HOW OUR SCRIPTS WORK

### 1. `scripts/auto-assign.js` - Core Logic (Node.js)
**Path:** `scripts/auto-assign.js`
**What it does:**
```js
1. Load bridge/tasks.json, locks.json, state.json
2. Detect DONE tasks -> release their locks from locks.json
3. For each TODO task:
   - Check dependencies: all deps must be DONE (from tasks.json)
   - Check file conflict: claimedFiles must NOT overlap with active locks
   - If both OK -> assign to IN_PROGRESS + create lock with claimedAt
4. Save tasks.json, locks.json, state.json
5. Output assigned tasks
```

**Key code:**
```js
const depsMet = deps.every(depId => taskMap[depId].status === 'done');
const conflict = locksData.locks.some(lock => 
  lock.files.some(lf => claimedFiles.some(cf => cf === lf))
);
if (depsMet && !conflict) assign();
```

**Run:** `node scripts/auto-assign.js`

---

### 2. `bridge/auto-coordinator/continuous-runner.js` - 24/7 Runner (Node.js)
**Path:** `bridge/auto-coordinator/continuous-runner.js`
**Process:** `auto-coordinator-24-7-runner-dd61ed3f` RUNNING
**What it does (every 60s forever):**
```js
while(true) {
  1. git fetch origin main
  2. Check if behind -> git pull --rebase origin main
  3. Print queue status (tasks, locks, state v3)
  4. Run node scripts/auto-assign.js
  5. If bridge/*.json changed -> git add + commit "[skip ci]" + push
  6. Sleep 60s
}
```

**Why `[skip ci]`?** Prevents GitHub Action from triggering recursively and creating infinite loop.

**Run:** `node bridge/auto-coordinator/continuous-runner.js` (background process)

---

### 3. `bridge/auto-coordinator/dual-monitor.js` - Admin+Client Separate (Node.js)
**Path:** `bridge/auto-coordinator/dual-monitor.js`
**Process:** `dual-monitor-admin-client-3409580d` RUNNING
**What it does (every 60s):**
```js
- Watches BOTH admin-agent and client-agent separately
- So they can differentiate work (one admin, one client as user requested)
- Checks each agent: DONE, IN_PROGRESS, TODO, BLOCKED, STUCK (>24h)
- Dispatches tasks separately: one for admin, one for client
- Reports problems to logs
- Same logic as continuous-runner but dual tracking
```

**Differentiation:**
- Admin files: ModulesPanel, SubscriptionsPanel, UserPicker, UserDetailDrawer...
- Client files: AppContext, defaults.ts, types.ts, supabase.ts
- No overlap, safe parallel

---

### 4. `bridge/auto-coordinator/client-watcher.py` - Client Dedicated (Python)
**Path:** `bridge/auto-coordinator/client-watcher.py`
**Process:** `client-agent-watcher-python-05cdf08d` RUNNING
**Based on:** User example script, improved
**What it does (every 60s):**
```python
SHARED = '/home/user/artisanpro-shared'
while True:
  git fetch origin --quiet
  if behind: git pull --rebase
  tasks = load origin/main:bridge/tasks.json filter assignee=client-agent
  analyze each task: completed, incomplete, root cause, problems (BLOCKED, STUCK >24h, WAITING)
  heartbeat log
  if actionable (todo/in_progress/blocked):
    create /home/user/NEW_CLIENT_TASK.json with task + analysis
  if questions.md has new client-agent mentions:
    create /home/user/CHECK_QUESTIONS.flag
  sleep 60
```

**Outputs (NOT in repo to avoid conflicts):**
- Log: `bridge/auto-coordinator/client-agent-watch.log` (in repo but append only)
- Alert: `/home/user/NEW_CLIENT_TASK.json` (outside repo)
- Flag: `/home/user/CHECK_QUESTIONS.flag` (outside repo)

**Why outside repo?** To avoid git conflicts - multiple agents writing to same file in repo would conflict.

---

### 5. `bridge/auto-coordinator/admin-watcher.py` - Admin Dedicated (Python)
**Path:** `bridge/auto-coordinator/admin-watcher.py`
**Process:** `admin-agent-watcher-python-005cff9e` RUNNING
**Same as client-watcher but for admin-agent:**
- Watches admin-agent tasks
- Creates `/home/user/NEW_ADMIN_TASK.json`
- Log: `admin-agent-watch.log`

**Differentiation:** One watcher per agent = no conflicts, each agent has own alert file.

---

### 6. `.github/workflows/auto-assign.yml` - GitHub Action
**Path:** `.github/workflows/auto-assign.yml`
**Workflow ID:** 342391513 ACTIVE
**Triggers:**
- Push to main on paths: bridge/tasks.json, state.json, locks.json, types/*, constants/*, supabase/*, utils/*
- Cron: every 30min `*/30 * * * *`
- Manual: workflow_dispatch

**Steps:**
1. Checkout with GITHUB_TOKEN
2. Setup Node 20
3. Run `node scripts/auto-assign.js`
4. If changed: commit + push with `[skip ci]` + create GitHub Issues for newly assigned tasks
5. Summary to Actions tab

**Why it works for all agents:** Any agent push triggers it, it auto-assigns next tasks for ALL agents, not just one.

---

## 🛡️ HOW TO AVOID CONFLICTS - RULES FOR OTHER AGENTS

### Rule 1: Respect File Locks
**Before editing any file, check `bridge/locks.json`:**
```python
locks = json.load(open('bridge/locks.json'))
my_files = ["src/components/MyPanel.tsx"]
conflict = any(lock['files'] for lock in locks['locks'] if any(f in lock['files'] for f in my_files))
if conflict:
  # DO NOT EDIT - ask in questions.md
```

**Our runners check this before assigning:**
```js
const conflict = locksData.locks.some(lock => 
  lock.files.some(lf => claimedFiles.some(cf => cf === lf))
);
```

### Rule 2: Use Same Paths
**Always use:**
```python
SHARED = '/home/user/artisanpro-shared'  # NOT /home/user/Artissan-Pro/shared
TASKS_PATH = f'{SHARED}/bridge/tasks.json'
LOCKS_PATH = f'{SHARED}/bridge/locks.json'
STATE_PATH = f'{SHARED}/bridge/state.json'
```

**Poll origin/main, not local:**
```python
def show_origin(path):
  r = subprocess.run(['git', '-C', SHARED, 'show', f'origin/main:{path}'], capture_output=True, text=True)
  return r.stdout if r.returncode==0 else None
```

### Rule 3: Alert Files Outside Repo
**DO:**
```python
ALERT = '/home/user/NEW_CLIENT_TASK.json'  # Outside repo - no git conflict
```

**DON'T:**
```python
ALERT = f'{SHARED}/NEW_CLIENT_TASK.json'  # Inside repo - WILL CONFLICT when multiple agents push
```

**Why?** If 2 agents write to same file inside repo and both push, git conflict. Outside repo = no conflict.

**Logs can be inside repo but append only:**
```python
LOG = f'{SHARED}/bridge/auto-coordinator/my-agent-watch.log'
# Append only, never overwrite
with open(LOG, 'a') as f:
  f.write(line + '\n')
```

### Rule 4: Use [skip ci] in Commits
**Always:**
```bash
git commit -m "auto: assign next tasks [skip ci]"
```

**Why?** Without `[skip ci]`, your push triggers GitHub Action which pushes again which triggers Action again -> infinite loop.

### Rule 5: Check Dependencies Before Assigning
```python
deps = task.get('dependencies', [])
deps_met = all(taskMap[dep].status == 'done' for dep in deps)
if not deps_met:
  # Do NOT assign - wait
```

**Our runners do this - you must too.**

### Rule 6: Poll Every 60s, Not Faster
```python
POLL_SECONDS = 60
time.sleep(POLL_SECONDS)
```

**Why 60s?**
- GitHub API rate limit: 5000/hour, faster polling hits limit
- Git conflicts: faster = more chance 2 agents push same time
- Our runners use 60s - compatible

### Rule 7: Fetch and Pull Before Every Decision
```python
git fetch origin --quiet
behind = git rev-list HEAD..origin/main --count
if behind > 0:
  git pull --rebase origin main
# Now load tasks.json - fresh state
```

**Why?** Never use stale state. Always refresh after worker push.

### Rule 8: Never Assign Same Task Twice
```python
if task.status == 'in_progress':
  # Already assigned - skip
```

### Rule 9: One Task Per JSON Output (Auto-Coordinator Mode)
If you are in Auto-Coordinator mode, return exactly one JSON object per turn with schema:
```json
{
  "action": "dispatch_agent | verify | mark_done | mark_blocked | schedule_next | request_human | wait",
  "target": "client | admin | shared | i18n | security | api | peinture | billing | none",
  "taskId": "string",
  "reason": "short",
  "nextStep": "short",
  "payload": {}
}
```

---

## 📝 TEMPLATE FOR OTHER AGENTS TO BUILD COMPATIBLE SCRIPTS

### Python Template (Recommended - like user example)

```python
#!/usr/bin/env python3
"""
YOUR-agent watcher - Compatible with ArtisanPro auto-coordinator
Polls every 60s, respects locks, no conflicts
"""

import json, os, subprocess, time
from datetime import datetime, timezone

SHARED = '/home/user/artisanpro-shared'
LOG = f'{SHARED}/bridge/auto-coordinator/YOUR-agent-watch.log'
ALERT = f'/home/user/NEW_YOUR_TASK.json'  # OUTSIDE repo!
POLL_SECONDS = 60
ACTIONABLE = ('todo', 'in_progress', 'waiting_assignment', 'blocked')

def now(): return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def git(*args): return subprocess.run(['git', '-C', SHARED, *args], capture_output=True, text=True, timeout=60)
def show_origin(path):
    r = git('show', f'origin/main:{path}')
    return r.stdout if r.returncode==0 else None
def log(msg):
    line = f'[{now()}] {msg}'
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, 'a') as f: f.write(line+'\n')
    except: pass

def main():
    log('=== YOUR-agent watcher started ===')
    last_sig = None
    while True:
        try:
            git('fetch', 'origin', '--quiet')
            # Pull if behind
            r = git('rev-list', 'HEAD..origin/main', '--count')
            if r.returncode==0 and r.stdout.strip().isdigit() and int(r.stdout.strip())>0:
                git('pull', '--rebase', 'origin', 'main')
            
            # Load tasks for YOUR agent
            raw = show_origin('bridge/tasks.json')
            if not raw:
                with open(f'{SHARED}/bridge/tasks.json') as f: raw=f.read()
            data = json.loads(raw)
            tasks = [t for t in data.get('tasks',[]) if t.get('assignee')=='YOUR-agent']
            
            # Check locks - respect them!
            locks_raw = show_origin('bridge/locks.json')
            locks = json.loads(locks_raw) if locks_raw else {'locks':[]}
            
            sig = json.dumps([[t['id'], t['status']] for t in tasks])
            if sig != last_sig:
                for t in tasks:
                    log(f"task {t['id']} status={t['status']}")
                last_sig = sig
            
            log(f"heartbeat - {len(tasks)} tasks")
            
            actionable = [t for t in tasks if t['status'] in ACTIONABLE]
            if actionable:
                # Check file conflict before alerting
                t = actionable[0]
                cf = t.get('claimedFiles',[])
                conflict = any(any(lf in cf for lf in lock['files']) for lock in locks['locks'] if lock['agent'] != 'YOUR-agent')
                if not conflict:
                    with open(ALERT, 'w') as f:
                        json.dump(t, f, indent=2)
                    log(f"*** ACTIONABLE: {t['id']} ({t['status']}) ***")
                else:
                    log(f"File conflict for {t['id']}, waiting")
            elif os.path.exists(ALERT):
                os.remove(ALERT)
        
        except Exception as e:
            log(f'error: {e}')
        
        time.sleep(POLL_SECONDS)

if __name__ == '__main__':
    main()
```

**Replace `YOUR-agent` with your agent name: `peinture-agent`, `security-agent`, `api-agent`, `billing-agent`, `i18n-agent`**

**Run as background process:**
```bash
cd /home/user/artisanpro-shared
chmod +x bridge/auto-coordinator/YOUR-watcher.py
python3 bridge/auto-coordinator/YOUR-watcher.py &
# Or use Arena start_process tool
```

---

### Node.js Template (Alternative)

```javascript
const fs = require('fs');
const { execSync } = require('child_process');
const REPO = '/home/user/artisanpro-shared';
const POLL = 60*1000;

function log(m){ console.log(`[${new Date().toISOString()}] ${m}`); }
function exec(cmd){ 
  try{ return {ok:true, out: require('child_process').execSync(cmd, {cwd:REPO, encoding:'utf8'}).trim()}; }
  catch(e){ return {ok:false, err:e.message}; }
}
function load(p){ try{ return JSON.parse(fs.readFileSync(p,'utf8')); } catch{ return null; } }

async function loop(){
  log('YOUR-agent watcher started');
  while(true){
    exec('git fetch origin main');
    const behind = exec('git rev-list HEAD..origin/main --count');
    if(behind.ok && parseInt(behind.out)>0) exec('git pull --rebase origin main');
    
    const tasks = load(`${REPO}/bridge/tasks.json`);
    const myTasks = tasks.tasks.filter(t=>t.assignee==='YOUR-agent' && ['todo','in_progress','blocked'].includes(t.status));
    log(`heartbeat - ${myTasks.length} actionable`);
    
    if(myTasks.length>0){
      const t = myTasks[0];
      // Check locks
      const locks = load(`${REPO}/bridge/locks.json`);
      const cf = t.claimedFiles||[];
      const conflict = locks.locks.some(l=> l.agent!=='YOUR-agent' && l.files.some(f=>cf.includes(f)));
      if(!conflict){
        fs.writeFileSync('/home/user/NEW_YOUR_TASK.json', JSON.stringify(t,null,2));
        log(`*** ACTIONABLE ${t.id} ***`);
      }
    }
    
    await new Promise(r=>setTimeout(r,POLL));
  }
}
loop();
```

---

## 🔄 CURRENT RUNNERS (Active Now)

**4 processes running 24/7:**

1. **Auto-Coordinator Continuous Runner** (JS)
   - Path: `bridge/auto-coordinator/continuous-runner.js`
   - Process: `auto-coordinator-24-7-runner-dd61ed3f`
   - Checks: All agents, every 60s, fetch/pull/auto-assign/push

2. **Dual Monitor Admin+Client** (JS)
   - Path: `bridge/auto-coordinator/dual-monitor.js`
   - Process: `dual-monitor-admin-client-3409580d`
   - Checks: Admin and client separately, differentiation

3. **Client Watcher** (Python)
   - Path: `bridge/auto-coordinator/client-watcher.py`
   - Process: `client-agent-watcher-python-05cdf08d`
   - Checks: Client only, creates `/home/user/NEW_CLIENT_TASK.json`

4. **Admin Watcher** (Python)
   - Path: `bridge/auto-coordinator/admin-watcher.py`
   - Process: `admin-agent-watcher-python-005cff9e`
   - Checks: Admin only, creates `/home/user/NEW_ADMIN_TASK.json`

**All compatible, no conflicts, different alert files outside repo, same 60s interval, respect locks.**

---

## 📊 CURRENT QUEUE (2026-08-26)

```
DONE: 3
  shared-types-sync (lead)
  client-supabase-migration (client-agent) - 10 done, build PASS
  admin-modules-subscriptions (admin-agent) - 6 done, build PASS

IN_PROGRESS: 4
  i18n-complete-audit (i18n-agent) P0 - 1 day no push, BOTTLENECK, blocks peinture+admin
  security-center-sessions (security-agent) P1 - 1 day no push, blocks client
  edge-function-security-logs (api-agent) P2 - 1 day no push
  manual-payments-stripe-prep (billing-agent) P3 - auto-unblocked after admin DONE

TODO: 1
  peinture-workspace-premium (peinture-agent) P1 - waiting i18n (i18n keys missing)

BLOCKED: 0 (client unblocked after SQL fix)

Locks: 4 active (i18n, security, api, admin) - no overlap
Available: peinture files, PaymentHistory
```

**Next auto-assignments:**
- i18n DONE -> peinture + admin (but admin already DONE, so peinture)
- security DONE -> client already DONE, so nothing
- admin DONE -> billing already IN_PROGRESS (auto)
- billing DONE -> queue empty

---

## 🚀 HOW TO START YOUR OWN COMPATIBLE WATCHER

**For peinture-agent example:**

```bash
cd /home/user/artisanpro-shared

# 1. Create your watcher from template
# Copy client-watcher.py to peinture-watcher.py and replace YOUR-agent with peinture-agent
# Change ALERT to /home/user/NEW_PEINTURE_TASK.json
# Change LOG to peinture-agent-watch.log

# 2. Make executable
chmod +x bridge/auto-coordinator/peinture-watcher.py

# 3. Test one iteration
timeout 10 python3 bridge/auto-coordinator/peinture-watcher.py

# 4. Start as background process (Arena)
# Use start_process tool with:
# command: cd /home/user/artisanpro-shared && python3 bridge/auto-coordinator/peinture-watcher.py
# name: Peinture Agent Watcher

# 5. Commit and push your watcher (without token!)
git add bridge/auto-coordinator/peinture-watcher.py
git commit -m "feat: peinture-agent watcher - compatible with auto-coordinator, no conflicts"
git push origin main
```

**Your watcher will now:**
- Check every 60s like ours
- Respect locks (no overlap)
- Create alert outside repo (no git conflict)
- Report problems
- Be compatible with 4 existing runners

---

## ⚠️ COMMON MISTAKES THAT CAUSE CONFLICTS (AVOID!)

**Mistake 1: Editing locked files**
```python
# BAD - i18n-agent locked src/main.tsx, you edit it anyway
open('src/main.tsx','w').write('...')
# GOOD - check locks first
```

**Mistake 2: Alert file inside repo**
```python
# BAD - will conflict
ALERT = f'{SHARED}/NEW_TASK.json'
# GOOD - outside repo
ALERT = '/home/user/NEW_TASK.json'
```

**Mistake 3: No [skip ci]**
```bash
# BAD - infinite loop
git commit -m "assign task"
# GOOD
git commit -m "assign task [skip ci]"
```

**Mistake 4: Polling too fast**
```python
# BAD - hits rate limit and conflicts
POLL_SECONDS = 5
# GOOD
POLL_SECONDS = 60
```

**Mistake 5: Not fetching before decision**
```python
# BAD - stale state
tasks = json.load(open('bridge/tasks.json'))
# GOOD - fresh from origin
git fetch origin
raw = git show origin/main:bridge/tasks.json
```

**Mistake 6: Assigning without checking deps**
```python
# BAD - assigns peinture even though i18n not DONE
task.status = 'in_progress'
# GOOD - check deps
if all(taskMap[d].status=='done' for d in task.dependencies):
  task.status='in_progress'
```

---

## 📞 REPORTING PROBLEMS

**If your agent is blocked, write to `bridge/questions.md`:**
```markdown
### Q-YOUR-AGENT-123: Title
**From:** your-agent
**To:** lead-engineer / i18n-agent
**Date:** 2026-08-26
**Problem:** Exact error, file, command
**Impact:** What is blocked
**Status:** OPEN
```

**Our runners check questions.md every 60s and will report to lead engineer.**

---

## ✅ VERIFICATION BEFORE PUSH

**Always before push:**
```bash
# 1. Build must pass
cd /home/user/Artissan-Pro-Client && npm run build  # or tsc check for shared
cd /home/user/Artissan-Pro-Admin && npm run build

# 2. No file overlap
cat bridge/locks.json | python3 -m json.tool

# 3. Tasks updated
cat bridge/tasks.json | grep -A 2 your-task-id

# 4. Commit with [skip ci]
git commit -m "feat: your task DONE [skip ci]"
git push origin main
```

---

## 📂 PATH TO GIVE TO OTHER AGENTS

**Give them this path:**
```
https://github.com/DeadEnde/artisanpro-shared/blob/main/bridge/SCRIPTS_COMPATIBILITY_REPORT.md
```

**Or local path:**
```
/home/user/artisanpro-shared/bridge/SCRIPTS_COMPATIBILITY_REPORT.md
```

**Also give:**
- `bridge/tasks.json` - task queue
- `bridge/locks.json` - file locks
- `bridge/agents.md` - role definitions
- `scripts/auto-assign.js` - core logic
- `bridge/auto-coordinator/` - all runners (continuous-runner.js, dual-monitor.js, client-watcher.py, admin-watcher.py)

**They should read this report first, then create their own watcher from template, then start it.**

---

## 🎯 SUMMARY

- **4 runners active 24/7, every 60s, no conflicts**
- **Compatible because:** same paths, same interval, respect locks, check deps, alert outside repo, [skip ci]
- **To be compatible:** Follow template, respect locks, poll 60s, fetch before decision, alert outside repo, use [skip ci]
- **To differentiate admin and client:** Use separate watchers with separate alert files (NEW_ADMIN_TASK.json vs NEW_CLIENT_TASK.json) - already done
- **No conflicts if you follow rules**

**End of Report - Ready to share with other agents**

---
**Lead Engineer + Shared Agent**
**2026-08-26 19:15 UTC**
**Version 5**
