# Auto-Coordinator - Système Automatique d'Assignation des Tasks

## 🎯 Objectif
Bach nta ma tb9ach tktb f chat kol mra "3ti task l agent X", had system kaydirha automatiquement mli agent ydir push.

## 🔧 Kifach Kaykhdem? (2 Options)

### Option 1: GitHub Actions (Recommandé - Simple, Gratuit, Pas de Serveur)

**Déjà configuré f `.github/workflows/auto-assign.yml`**

**Flow:**
```
Agent A ykhdem task -> ydir push l main
       ↓
GitHub Action kay-trigger automatiquement
       ↓
Kay-run scripts/auto-assign.js
       ↓
Kay-chouf:
  - Wach task dial Agent A wla DONE? -> release locks
  - Wach kayn tasks TODO li dependencies dialhom DONE? -> auto-assign
       ↓
Ila kayn tasks jdad, kay-commit w kay-push automatically
       ↓
Kay-creer GitHub Issues l agents jdad b details
       ↓
Agents jdad kay-shoufo Issue w kay-bdaw khdma
```

**Avantages:**
- ✅ Gratuit, intégré f GitHub
- ✅ Ma kay7tajch serveur
- ✅ Kaykhdem 24/7
- ✅ Kay-creer Issues automatiquement
- ✅ Schedule kol 30min bach y-checki tasks bloqués

**Activation:**
1. Push had files l GitHub (workflow deja kayn)
2. GitHub ghadi y-activi Action automatically
3. C'est tout! Ma kayn walo khassk dir

**Test:**
- Dir push l main (bhal daba)
- Sir l GitHub -> Actions tab -> chouf "Auto-Coordinator" kaykhdem

---

### Option 2: Webhook Server (Avancé - Control Ktr, Real-time)

**Fichier:** `bridge/auto-coordinator/webhook-server.js`

**Flow:**
```
Agent push -> GitHub Webhook -> Your Server /webhook
                                ↓
                          Pull + auto-assign + push
                                ↓
                          Real-time (1-2 sec)
```

**Quand l'utiliser:**
- Ila bghiti real-time (GitHub Actions kayakhud 30-60s)
- Ila bghiti custom logic (Slack notifications, etc)
- Ila bghiti dashboard live

**Deploy:**

**Sur Vercel (gratuit):**
```bash
# Creer vercel.json
{
  "functions": {
    "bridge/auto-coordinator/webhook-server.js": {
      "includeFiles": "bridge/**,scripts/**"
    }
  }
}

# Deploy
vercel --prod
# Zid env vars: WEBHOOK_SECRET, GITHUB_TOKEN
```

**Sur Railway / Render / VPS:**
```bash
npm install
PORT=3000 WEBHOOK_SECRET=ton_secret GITHUB_TOKEN=ghp_... REPO_PATH=/path/to/repo node bridge/auto-coordinator/webhook-server.js
```

**Configurer GitHub Webhook:**
1. GitHub repo -> Settings -> Webhooks -> Add webhook
2. Payload URL: `https://your-server.com/webhook`
3. Content type: `application/json`
4. Secret: nafs li f WEBHOOK_SECRET env var
5. Events: Just push events
6. Active: ✅

---

### Option 3: Agent-specific Watchers

The coordinator assigns tasks; each agent can run a read-only watcher that polls
`origin/main` and creates a local alert only for its own assignment.

```bash
# Direct checkout of artisanpro-shared
python3 bridge/auto-coordinator/client-watcher.py
python3 bridge/auto-coordinator/admin-watcher.py

# Or use one generic watcher for any role
AGENT_ID=client-agent python3 bridge/auto-coordinator/agent-watcher.py
```

The watcher checks every 60 seconds by default and writes:

- client: `~/NEW_CLIENT_TASK.json`, `~/CHECK_QUESTIONS.flag`
- admin: `~/NEW_ADMIN_TASK.json`, `~/CHECK_QUESTIONS_ADMIN.flag`
- all roles: `~/<agent>-watch.log`

Use `--once` for a safe smoke test. Set `SHARED_REPO`, `POLL_SECONDS`,
`WATCH_LOG`, `WATCH_ALERT`, and `WATCH_QFLAG` to override paths. Git credentials
must come from SSH, a credential helper, `GITHUB_TOKEN`, or `GH_TOKEN`; no token
is stored in the watcher source.

The watcher never edits application files or bridge coordination data. It only
reads the remote bridge, records a heartbeat, and creates/clears local alerts.

---

## 📜 Script Principal: `scripts/auto-assign.js`

**Logique:**

```js
1. Load tasks.json, locks.json, state.json
2. Check done tasks -> release their locks
3. For each TODO task:
   - Check dependencies: all DONE?
   - Check file conflicts: no overlap with active locks?
   - If yes -> auto-assign to in_progress + create lock
4. Save files + update state.json
5. Commit & push (si GitHub Action)
6. Create Issues (si GitHub Action)
```

**Tu peux t-testi local:**
```bash
cd artisanpro-shared
node scripts/auto-assign.js
```

---

## 🔄 Exemple Concret

**État initial:**
```
shared-types-sync: DONE (lead-engineer)
i18n-complete-audit: IN_PROGRESS (i18n-agent)
admin-modules-subscriptions: IN_PROGRESS (admin-agent)
peinture-workspace-premium: TODO (deps: i18n)
client-supabase-migration: TODO (deps: shared, security)
```

**i18n-agent ykmmel w ydir push:**
```
git commit -m "i18n DONE"
git push
```

**Auto-Coordinator kay-trigger:**
```
- Chaf i18n DONE -> release locks dial i18n-agent
- Chaf peinture-workspace-premium deps met (i18n DONE) -> auto-assign to peinture-agent
- Chaf client-supabase-migration mazal waiting (security not DONE)
- Push changes + create Issue for peinture-agent
```

**Peinture-agent kay-shouf Issue f GitHub w kay-bda khdma bla ma nta tktb walo f chat!**

---

## 🛡️ Sécurité

- GitHub Action utilise `GITHUB_TOKEN` automatique (pas besoin token perso)
- Webhook server vérifie signature HMAC SHA256
- `[skip ci]` f commit message bach ma ydirch boucle infinie
- File locking empêche 2 agents ykhdmo nafs fichier

---

## 📊 Monitoring

**GitHub Actions:**
- GitHub -> Actions tab -> Auto-Coordinator
- Chouf logs, summary, status

**Webhook Server:**
- GET / -> HTML dashboard
- GET /status -> JSON status (tasks, locks, lastUpdate)

**Bridge files:**
- `tasks.json` -> source of truth
- `locks.json` -> qui khdam fin
- `state.json` -> état global

---

## 🚀 Installation Finale

**Daba li khassk dir:**

```bash
cd artisanpro-shared

# 1. Commit had auto-coordinator system
git add .github/workflows/auto-assign.yml scripts/auto-assign.js bridge/auto-coordinator/
git commit -m "feat: auto-coordinator system - automatic task assignment on push"

# 2. Push
git push origin main
# Utilise token: ghp_***REDACTED***

# 3. Vérifie GitHub Actions
# Sir l: https://github.com/DeadEnde/artisanpro-shared/actions
# Ghadi tchouf workflow kaykhdem

# 4. (Optionnel) Deploy webhook server si bghiti real-time
```

**Après push, system ghadi ykhdem bou7do!**

- Agent ydir push -> tasks jdad auto-assign
- Nta ma khassk tktb walo f chat
- Ghir monitori f GitHub Actions / Issues

---

## ❓ FAQ

**Q: Wach kayn risque boucle infinie?**
A: La, `[skip ci]` kay-mna3 trigger récursif. GitHub Action ma kay-triggerch 3la commits li fihom [skip ci].

**Q: Wach 2 agents y9dro ykhdmo nafs file?**
A: La, locks.json kay-mna3. Auto-assign kay-checki conflicts 9bel ma y-assigni.

**Q: Ila agent ma pushach, wach task ghadi yb9a bloqué?**
A: Schedule kol 30min kay-checki. Ila task DONE mais ma t-release-ch lock, ghadi y-release automatiquement.

**Q: Kayn notification Slack/Discord?**
A: Daba la, mais tu peux zidha f webhook-server.js - zid fetch l Slack webhook.

**Q: Wach n9der n-modifi logic auto-assign?**
A: Oui, sir l `scripts/auto-assign.js` w modifi. C'est du JS simple.

---

**Lead Engineer - 2026-08-25**
**Status: Ready to deploy**
