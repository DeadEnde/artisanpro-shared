# 🤖 Auto-Coordinator - Kifach Tkhdem Bla Chat

**Question dialk:** Wax kayna chi tare9a bax nta automatically tb9a t3ti task l agents l5ren mli idero push bla manb9a nktbha kol mra f chat?

**Jawab:** IYEH! Dert lik system kamil daba - 2 options.

---

## ✅ Option 1: GitHub Actions (Daba Ready - Ma Kay7taj Walo)

### Achno dert lik?
- ✅ Fichier `.github/workflows/auto-assign.yml` - kaykhdem bou7do f GitHub
- ✅ Script `scripts/auto-assign.js` - logic dial auto-assign
- ✅ Testito local - kaykhdem mzyan

### Kifach kaykhdem bla chat?

```
YOUM 1:
- i18n-agent khdam FR/EN/AR
- security-agent khdam sessions
- api-agent khdam Edge Functions
       ↓ push l main

GitHub Action kay-trigger AUTOMATIQUEMENT (30-60s)
       ↓
Kay-qra tasks.json:
  - i18n DONE? -> release lock + assign peinture + admin
  - security DONE? -> assign client
  - admin DONE? -> assign billing
       ↓
Kay-push changes + kay-creer GitHub Issues
       ↓
peinture-agent, admin-agent, client-agent kay-shoufo Issues w kay-bdaw
       ↓
NTA MA KTBT WALO F CHAT!

YOUM 2, 3, 4... nafs l7aja - automatique!
```

### Daba fin kaynin tasks?

**3 IN_PROGRESS (khdamin daba):**
- `i18n-complete-audit` -> i18n-agent
- `security-center-sessions` -> security-agent  
- `edge-function-security-logs` -> api-agent

**2 WAITING FOR i18n:**
- `peinture-workspace-premium` -> ghadi y-assigni automatically mli i18n ykmmel
- `admin-modules-subscriptions` -> ghadi y-assigni automatically mli i18n ykmmel

**1 WAITING FOR security:**
- `client-supabase-migration` -> ghadi y-assigni mli security ykmmel

**1 WAITING FOR admin:**
- `manual-payments-stripe-prep` -> ghadi y-assigni mli admin ykmmel

### Kifach t-activi?

```bash
cd artisanpro-shared

# Push daba
git add .
git commit -m "feat: auto-coordinator system"
git push origin main
# Token: ghp_***REDACTED***

# Sir l GitHub
https://github.com/DeadEnde/artisanpro-shared/actions
# Ghadi tchouf workflow "Auto-Coordinator" kaykhdem

# Sir l Issues
https://github.com/DeadEnde/artisanpro-shared/issues
# Ghadi tchouf Issues auto-creés l agents
```

**Après had push, MA KHASSK DIR WALO - system kaykhdem bou7do!**

---

## 🔥 Option 2: Webhook Server (Real-time, 1-2 sec)

Ila bghiti real-time machi 30-60s:

### Deploy f Vercel (5min):

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy
cd artisanpro-shared
vercel --prod
# Zid env vars f Vercel dashboard:
# WEBHOOK_SECRET=artisanpro-2026-secret
# GITHUB_TOKEN=ghp_***REDACTED***
# REPO_PATH=/tmp/artisanpro-shared (ou /vercel/path)

# 3. Khud URL li 3tak Vercel: https://your-app.vercel.app

# 4. Zid webhook f GitHub
# GitHub repo -> Settings -> Webhooks -> Add webhook
# Payload URL: https://your-app.vercel.app/webhook
# Content type: application/json
# Secret: artisanpro-2026-secret (nafs li f env var)
# Events: Push only
# Active: Yes
```

**Daba mli agent ydir push, GitHub y3ayet l server dialk f 1sec, server ydir auto-assign f 2sec!**

### Files li dert:
- `bridge/auto-coordinator/webhook-server.js` - server Node.js
- `bridge/auto-coordinator/README.md` - docs kaml

---

## 📊 Kifach T-Monitori Bla Chat?

### 1. GitHub Actions Tab
```
https://github.com/DeadEnde/artisanpro-shared/actions
- Chouf kol push + auto-assign logs
- Summary fih current tasks status
```

### 2. GitHub Issues
```
https://github.com/DeadEnde/artisanpro-shared/issues
- Kol task jdid kay-creer Issue automatiquement
- Assignee kay-shouf Issue + details
- Labels: auto-assigned, role, priority
```

### 3. Bridge Files (Source of Truth)
```bash
# Local ou GitHub web UI
cat bridge/tasks.json | python3 -m json.tool
cat bridge/locks.json
cat bridge/state.json
```

### 4. Webhook Server Dashboard (ila deployiti Option 2)
```
GET https://your-server.com/
-> HTML dashboard

GET https://your-server.com/status
-> JSON: tasks, locks, lastUpdate
```

---

## 🎯 Workflow Kamil Bla Chat - Exemple

**Sans Auto-Coordinator (9bel):**
```
Agent A push -> NTA khassk tdkhol chat -> tktb "3ti task l Agent B"
Agent B push -> NTA khassk tdkhol chat tani -> tktb "3ti task l Agent C"
... kol mra khassk tktb
```

**M3a Auto-Coordinator (daba):**
```
Agent A push (i18n DONE)
  ↓ AUTOMATIC (GitHub Action)
  - Release lock i18n
  - Check deps: peinture waiting i18n? YES -> assign
  - Check deps: admin waiting i18n? YES -> assign
  - Push + create Issues
  ↓
Agent B (peinture) + Agent C (admin) kay-bdaw bla ma nta tktb walo

Agent B push (peinture DONE)
  ↓ AUTOMATIC
  - Release lock peinture
  - No next deps (peinture ma 3ndo ta7ed kay-tsnah)
  ↓
...

Agent C push (admin DONE)
  ↓ AUTOMATIC
  - Release lock admin
  - Check deps: billing waiting admin? YES -> assign billing
  - Push + create Issue for billing-agent
  ↓
Billing-agent kay-bda

... kamil automatique 7ta akhir task!
```

---

## 🛠️ Customization

### Bghiti tzid notification Slack?

Zid f `bridge/auto-coordinator/webhook-server.js`:

```js
// Après runCoordinator()
if (newlyAssigned.length > 0) {
  await fetch('https://hooks.slack.com/services/YOUR/WEBHOOK', {
    method: 'POST',
    body: JSON.stringify({
      text: `🤖 Auto-assigned ${newlyAssigned.length} tasks: ${newlyAssigned.map(t=>t.id).join(', ')}`
    })
  });
}
```

### Bghiti tzid Discord?

```js
await fetch('https://discord.com/api/webhooks/YOUR/WEBHOOK', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content: `🤖 Tasks auto-assigned: ${newlyAssigned.map(t=>t.title).join(', ')}`
  })
});
```

### Bghiti tbdl logic?

Sir l `scripts/auto-assign.js` - code simple, modifi kima bghiti.

---

## ✅ Résumé

| Avant | Daba M3a Auto-Coordinator |
|-------|---------------------------|
| Khassk tktb f chat kol mra | **Automatique bla chat** |
| Khassk t-tracki tasks manuel | **GitHub Issues automatique** |
| Risque conflit files | **Locks.json automatique** |
| Ma 3arfch fin wsal agents | **GitHub Actions logs + status** |
| 30min f nhar katb tasks | **0min - system kaydirha** |

**Daba system READY - ghir push w khlli ykhdem bou7do!**

---

## 🚀 Action Daba

```bash
# 1. Push system
cd /home/user/artisanpro-shared
git add .
git commit -m "feat: auto-coordinator - automatic task assignment without chat

- GitHub Action auto-assigns next tasks on push
- Webhook server option for real-time
- No need to write in chat anymore
- Monitors via GitHub Actions + Issues"
git push origin main

# 2. Check GitHub Actions
# https://github.com/DeadEnde/artisanpro-shared/actions

# 3. Enjoy - ma b9ach khassk tktb tasks f chat!
```

**Lead Engineer - 2026-08-25**
