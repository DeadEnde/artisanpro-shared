# 🤖 REPORT FOR AI AGENTS - ArtisanPro Multi-Agent Workspace
**From:** Lead Engineer (Coordinator)
**Date:** 2026-08-25 19:35 UTC
**Version:** 2.0
**Repo:** DeadEnde/artisanpro-shared (shared module)
**Status:** Shared sync DONE, 3 agents IN_PROGRESS, Auto-Coordinator deployed

---

## 📋 TL;DR FOR AGENTS - READ THIS FIRST

**You are an AI agent working on ArtisanPro SaaS. This is a multi-agent system.**

1. **Read `bridge/tasks.json`** - Find your assigned task (filter by assignee)
2. **Read `bridge/agents.md`** - Find your role definition
3. **Read `bridge/locks.json`** - Check which files are locked for you vs others
4. **Read `bridge/roadmap.md`** - Understand phases P0-P3
5. **Do NOT edit files locked by other agents** - Ask in `bridge/questions.md` if conflict
6. **When you finish:** Update `tasks.json` status to `done`, add to `done[]`, release locks, push
7. **Auto-Coordinator will auto-assign next tasks** - No need to ask lead engineer in chat

**Current active tasks:**
- `i18n-complete-audit` (P0) -> i18n-agent IN_PROGRESS
- `security-center-sessions` (P1) -> security-agent IN_PROGRESS  
- `edge-function-security-logs` (P1) -> api-agent IN_PROGRESS
- Next auto: peinture + admin when i18n DONE, client when security DONE, billing when admin DONE

---

## 🏗️ PROJECT OVERVIEW

### What is ArtisanPro?
SaaS for Moroccan artisans (painters, tilers) - Fast quotes, client/project management, module subscriptions.

### Stack (REALITY - Not Next.js)
- **2x Vite + React + TypeScript** (not Next.js as originally assumed)
  - Client: `artissan-pro.vercel.app` (double s) - Landing + calculator + dashboard (localStorage MVP)
  - Admin: `artisanpro-admin.vercel.app` - Google OAuth, role=admin, block/unblock, modules placeholder
- **Supabase:** Auth, DB, RLS, RPC functions, Edge Functions (future)
- **Vercel:** Deployment, env vars VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY
- **Shared Module:** `artisanpro-shared` - Types, constants, utils as git submodule in all projects

### Supabase Schema (Real - from SQL files)
**Tables:**
- `profiles` (id, full_name, email, role: client|admin, status: active|blocked|pending, company, phone, avatar_url, created_at, updated_at)
- `modules` (id, slug: peinture|carrelage, name_fr/en/ar, monthly_price, is_published, created_at)
- `app_sessions` (id, user_id, device_name, is_active, started_at, last_seen_at, ended_at, browser, os, device_type, user_agent, status: active|expired|forced_logout|ended)
- `user_modules` (id, user_id, module_id, status: active|paused|expired|revoked|pending, starts_at, expires_at, source: manual|stripe|admin_grant, granted_by, created_at)
- `subscriptions` (id, user_id, plan_name, amount, currency: MAD, status: pending|active|paused|cancelled|expired, payment_source: manual|stripe, starts_at, expires_at, created_by, created_at)
- `admin_activity_logs` (id, admin_id, action, target_user_id, metadata jsonb, created_at)
- `security_logs` (id, occurred_at, app: client|admin, event: login_success|login_failed|access_denied|account_blocked|logout|forced_logout, email, user_id, provider: google|email, device_type, browser, os, ip_hash, reason, metadata)

**View:**
- `module_entitlements` (user_id, module_slug, status, starts_at, expires_at, is_unlocked boolean)

**Functions:**
- `is_admin()` -> bool
- `claim_single_session(p_device_name)` -> uuid
- `is_session_active(p_session_id)` -> bool
- `heartbeat_session(p_session_id)` -> bool
- `end_own_session(p_session_id)` -> void
- `admin_force_logout_session(p_session_id)` -> void
- `admin_set_user_status(p_user_id, p_status)` -> void
- `admin_set_module_access(p_user_id, p_module_slug, p_status, p_expires_at)` -> void
- `admin_set_subscription_status(p_user_id, p_plan_name, p_status, p_expires_at, p_amount)` -> void
- `cleanup_security_logs()` -> void (delete >90 days)

---

## ✅ WHAT LEAD ENGINEER DID (2026-08-25)

### 1. Cloned & Audited
- Cloned `artisanpro-shared` with provided token
- Read all files: types, constants, supabase, utils, bridge
- Unzipped `artisanpro-workspace-source.zip` (80KB) containing client + admin snapshot + SQL schemas + handoff docs

### 2. Shared Module Sync - DONE (P0)
**Task `shared-types-sync` COMPLETED:**

- **Audited SQL:** `artisanpro-supabase-setup.sql` + `security-logs.sql` + `session-security-upgrade.sql` + `module-subscription-upgrade.sql` + `admin-profile-update.sql`
- **Updated `supabase/types.ts`:**
  - Before: Only 4 tables, incomplete, wrong roles (user|artisan)
  - After: All 7 tables + 1 view + 10 functions, correct types, matching real schema 100%
- **Updated `constants/index.ts`:**
  - Before: APP_VERSION 0.1.0, only 2 modules, basic constants
  - After: 0.2.0, added USER_STATUS, USER_ROLE, MODULE_STATUS, SUBSCRIPTION_STATUS, PAYMENT_SOURCE, MODULE_SOURCE, ONLINE_THRESHOLD_MINUTES=2, HEARTBEAT_INTERVAL_MS=60000, SECURITY_LOG_RETENTION_DAYS=90
- **Verified `types/index.ts`:** Already correct, matches real schema

### 3. Created Multi-Agent System v2

**Created 8 new files / updated 5:**

**`bridge/tasks.json` v2 (NEW - Source of Truth):**
- 8 tasks P0-P3 with full details: id, title, priority, role, parentRepo, status, assignee, claimedFiles, description, acceptanceCriteria, done, inProgress, blocked, next, dependencies
- P0: shared-types-sync DONE (lead-engineer)
- P0: i18n-complete-audit TODO->IN_PROGRESS (i18n-agent) deps: shared
- P1: peinture-workspace-premium TODO (peinture-agent) deps: i18n
- P1: admin-modules-subscriptions TODO (admin-agent) deps: shared+i18n
- P1: security-center-sessions TODO->IN_PROGRESS (security-agent) deps: shared
- P2: client-supabase-migration TODO (client-agent) deps: shared+security
- P2: edge-function-security-logs TODO->IN_PROGRESS (api-agent) deps: shared
- P3: manual-payments-stripe-prep TODO (billing-agent) deps: admin

**`bridge/agents.md` v2 (NEW):**
- 9 agent roles defined: lead-engineer, shared-agent, i18n-agent, peinture-agent, admin-agent, security-agent, client-agent, api-agent, billing-agent
- Communication protocol, file locking rules, build verification, user communication (Darija, Android, Vercel)

**`bridge/roadmap.md` v2 (NEW):**
- 4 phases: Phase1 P0 Foundation (shared+i18n), Phase2 P1 Core (peinture+admin+security), Phase3 P2 Data & Security (client migration+edge), Phase4 P3 Billing (manual+Stripe prep)
- Success criteria, deliverables, risks

**`bridge/state.json` v2 (UPDATED):**
- From single admin task to multi-agent coordinator state
- Version 2, overallStatus in_progress, 8 currentTasks, done[], inProgress[], blocked[], next[], questions[]

**`bridge/locks.json` v2 (UPDATED):**
- From empty to 3 active locks: i18n-agent, security-agent, api-agent
- Released shared files, availableForClaim list, rules

**`bridge/decisions.md` v2 (UPDATED):**
- From 8 old decisions to 12 new: D1 multi-agent, D2 shared source of truth, D3 no fake data, D4 manual first, D5 no hardcoded i18n+logical CSS, D6 no sensitive data+IP hash+90d, D7 single session+heartbeat, D8 file locking, D9 build verification, D10 stack preservation Vite, D11 mojibake UTF-8, D12 priority P0-P3

**`bridge/questions.md` v2 (UPDATED):**
- 6 open questions for user: Q1 repo structure (where are Client/Admin/API repos?), Q2 Supabase env vars, Q3 Stripe confirmation, Q4 client data schema, Q5 peinture wiring priority, Q6 Edge Function deployment

**Plus Auto-Coordinator:**
- `scripts/auto-assign.js` - Core logic: checks done tasks releases locks, checks TODO deps met + no file conflict -> auto-assigns to in_progress
- `.github/workflows/auto-assign.yml` - GitHub Action triggers on push to main, runs auto-assign.js, commits+pushes, creates Issues (needs manual add via GitHub UI due to token scope)
- `bridge/auto-coordinator/webhook-server.js` - Optional real-time webhook server (1-2 sec) alternative to Actions
- `bridge/auto-coordinator/README.md` - Full docs for both options

### 4. Pushed to GitHub
- Pushed 14 files to main (66a19d5) - workflow file excluded due to token scope, needs manual add via GitHub UI
- Tested auto-assign.js locally: works, auto-assigned edge-function task correctly

---

## 🔄 CURRENT STATE (After Lead Engineer Push)

### Tasks Status
```
P0 shared-types-sync: done (lead-engineer) - NO DEPS
P0 i18n-complete-audit: in_progress (i18n-agent) - deps: shared DONE
P1 peinture-workspace-premium: todo (peinture-agent) - deps: i18n IN_PROGRESS -> waiting
P1 admin-modules-subscriptions: todo (admin-agent) - deps: shared DONE + i18n IN_PROGRESS -> waiting
P1 security-center-sessions: in_progress (security-agent) - deps: shared DONE
P2 client-supabase-migration: todo (client-agent) - deps: shared DONE + security IN_PROGRESS -> waiting
P2 edge-function-security-logs: in_progress (api-agent) - deps: shared DONE
P3 manual-payments-stripe-prep: todo (billing-agent) - deps: admin TODO -> waiting
```

### Locks Active
```
i18n-agent -> i18n-complete-audit: src/context/LanguageContext.tsx, src/i18n/*, artisanpro-admin/src/i18n/*, src/main.tsx, artisanpro-admin/src/main.tsx
security-agent -> security-center-sessions: src/lib/sessionPresence.ts, src/components/SecurityPanel.tsx
api-agent -> edge-function-security-logs: supabase/functions/log-security-event/*, supabase/functions/cleanup-logs/*, artisanpro-security-logs.sql
```

### What Auto-Coordinator Will Do Next (Automatic, No Chat Needed)

**When i18n-agent pushes DONE:**
- Release i18n lock
- Check peinture deps: i18n DONE? YES -> auto-assign peinture to IN_PROGRESS + lock src/features/peinture/*
- Check admin deps: shared DONE + i18n DONE? YES -> auto-assign admin to IN_PROGRESS + lock ModulesPanel, SubscriptionsPanel, etc
- Push + create Issues for peinture-agent and admin-agent

**When security-agent pushes DONE:**
- Release security lock
- Check client deps: shared DONE + security DONE? YES -> auto-assign client to IN_PROGRESS

**When admin-agent pushes DONE:**
- Release admin lock
- Check billing deps: admin DONE? YES -> auto-assign billing to IN_PROGRESS

**Full chain automatic until all DONE!**

---

## 🎯 WHAT EACH AGENT SHOULD DO NOW

### i18n-agent (P0 - CRITICAL - IN_PROGRESS)
**Your files:** LanguageContext, i18n/*, main.tsx (both client+admin)
**Mission:** Full i18n audit - 0 hardcoded text, FR/EN/AR, RTL logical CSS
**Steps:**
1. Scan client src/main.tsx: pricing, login/signup, dashboard, projects, quotes, lead, painting locked, validation, placeholders, empty states
2. Scan admin src/main.tsx: auth gate, header logout, profile settings, overview cards, security placeholder, legacy components
3. Create complete dictionaries FR/EN/AR for namespaces: common, nav, auth, dashboard, modules, subscriptions, security, forms, errors, pricing, profile, landing, seo, peinture, actions, empty, status, accessibility, print, validation
4. Replace all hardcoded JSX text with t('key'), safe fallback (return key + console.warn dev)
5. Fix RTL: Use margin-inline, padding-inline, inset-inline, text-align: start/end - NOT left/right
6. Use Intl for currency MAD/EUR/USD and dates
7. Test FR/EN/AR screen by screen + screenshots
8. Update tasks.json: status done, add done[], next[], push

**Acceptance:** grep hardcoded JSX = 0, 3 languages 100%, RTL perfect, build passes

### security-agent (P1 - IN_PROGRESS)
**Your files:** sessionPresence.ts, SecurityPanel.tsx
**Mission:** Session tracking + Security Center real UI
**Steps:**
1. Verify artisanpro-session-security-upgrade.sql was run (check Supabase)
2. Client AppContext: on login -> claim_single_session(device_name), heartbeat 60s update last_seen_at, logout -> ended, new device -> old forced_logout
3. Admin Security Center tab: active sessions list, online/offline (2min window), last seen, duration, device/browser/OS, force logout button, refresh, user inspection
4. Filters: app/client/admin, event type, empty/loading/error localized
5. Update tasks.json done + push

**Acceptance:** Client claims session, heartbeat works, admin sees real sessions, force logout works

### api-agent (P1 - IN_PROGRESS)
**Your files:** supabase/functions/*, security-logs.sql
**Mission:** Edge Functions for secure security logging
**Steps:**
1. Create supabase/functions/log-security-event/index.ts: receives event, email, app, provider, device, browser, OS, hashes IP server-side (SHA256), inserts into security_logs with RLS admin-only read
2. Create supabase/functions/cleanup-logs/index.ts: cron deletes >90 days, calls cleanup_security_logs()
3. Deploy via Supabase CLI or dashboard
4. Update client/admin to call Edge Function instead of direct insert
5. Events: login_success, login_failed, access_denied, account_blocked, logout, forced_logout, session_started, session_expired
6. NEVER store raw IP, password, Google token, service_role in browser
7. Update tasks.json done + push

**Acceptance:** Edge Functions deployed, logs inserted via function with hashed IP, 90d cleanup works, no sensitive data in browser

### peinture-agent (P1 - TODO - WAITING FOR i18n)
**Your files:** src/features/peinture/* (engine, types, storage, exporters, components, css)
**Mission:** Premium Peinture Workspace finalization
**Steps when auto-assigned:**
1. Add paint.* keys FR/EN/AR (depends on i18n-agent)
2. Wire PricingStrategyPanel into PeintureWorkspace
3. Package comparison, price floor/ceiling validation, profit target validation, VAT/discount validation
4. Room type, ceiling toggle, doors/trims, interior/exterior, wall condition, regional preset, upsell UI
5. My Calculations: save/open/rename/duplicate/delete/import JSON/export JSON/CSV + inline errors
6. Quote: number editor, validity, payment terms, notes, terms, client/project metadata, line-item detail
7. Exports: PDF, XLSX, CSV, print HTML
8. Route wiring: Replace Calculator() inside Painting() with PeintureWorkspace, keep entitlement gate + locked UX
9. Update tasks.json done + push

**Acceptance:** Workspace complete with validation, saved library, quote editors, exports, wired into protected route

### admin-agent (P1 - TODO - WAITING FOR i18n)
**Your files:** ModulesPanel, SubscriptionsPanel, UserPicker, UserDetailDrawer
**Mission:** Real Modules & Subscriptions UI
**Steps when auto-assigned:**
1. Create UserDetailDrawer with module badges + subscription badges + timeline
2. Module access: Grant Peinture, Revoke, Pause via admin_set_module_access + expiry editor (date input)
3. Subscription: Pause/Resume/Cancel via admin_set_subscription_status + expiry + amount input + plan selector
4. Manual payment history UI: amount, currency, date, plan, status badges
5. Status timeline: pending/active/paused/expired/revoked/cancelled
6. Localized ConfirmDialog + validation/errors
7. Test with real RPCs
8. Update tasks.json done + push

**Acceptance:** Admin can grant/revoke/pause modules, pause/resume subscriptions, edit expiry, see payment history, all localized

### client-agent (P2 - TODO - WAITING FOR security)
**Your files:** AppContext.tsx, defaults.ts, types.ts, supabase.ts
**Mission:** Migrate localStorage -> Supabase
**Steps when auto-assigned:**
1. Create SQL for clients, projects, quotes, paint_calculations tables + RLS policies (user sees only own, admin sees all)
2. Refactor AppContext from localStorage to Supabase
3. Soft migration: if localStorage exists, propose import
4. Show entitlement status/expiry in module card + upgrade/contact admin CTA
5. Refresh entitlement after admin changes
6. Update tasks.json done + push

**Acceptance:** Client data in Supabase with RLS, no shared data, entitlement status visible, migration works

### billing-agent (P3 - TODO - WAITING FOR admin)
**Your files:** SubscriptionsPanel, PaymentHistory
**Mission:** Manual payments workflow + Stripe prep
**Steps when auto-assigned:**
1. Payment history UI with amount/currency/date/plan
2. Confirmation workflow for admin
3. Expiry/renewal automation basic
4. Prep webhook Stripe architecture (DO NOT implement Stripe yet - manual first per decision D4)
5. Update tasks.json done + push

**Acceptance:** Manual payment history + confirmation + expiry automation, Stripe prep doc, no Stripe implementation yet

---

## 🔧 HOW TO WORK - PROTOCOL FOR ALL AGENTS

### 1. Claim Task
- Read tasks.json, find your task (status todo or in_progress with your assignee)
- Check locks.json: your files should be locked for you, no conflict
- If conflict, ask in questions.md, don't edit others' locked files

### 2. Code
- Work ONLY in your parentRepo (Artissan-Pro-Client, Artissan-Pro-Admin, or artisanpro-shared if shared-agent)
- Do NOT duplicate types from shared - import from artisanpro-shared
- Follow decisions.md: no fake data (real or 0/empty), logical CSS RTL, no sensitive data in browser, etc

### 3. Test Build
```bash
cd /home/user && npm run build
cd /home/user/artisanpro-admin && npm run build
```
Both must pass before push

### 4. Update Tasks
- In tasks.json: add completed items to done[], update inProgress[], next[], questions[] if blocked
- When finished: status = done, lastUpdate = now
- In locks.json: will be auto-released by coordinator when you push done, or manually remove your lock
- In state.json: update currentTasks, lastUpdate, lastCoordinatorMessage

### 5. Push
```bash
git add .
git commit -m "feat: [your-task-id] - description"
git push origin main
```
- Auto-Coordinator GitHub Action will trigger (if workflow file added) and auto-assign next tasks
- If no workflow, lead engineer or manual auto-assign.js will handle

### 6. Mojibake Check
- Ensure UTF-8, check for Ã© Ã¨ â€™ â€œ â€ Ø§ Ù„ � (real mojibake) not valid é è
- All .ts, .tsx, .css, .json, SQL, HTML UTF-8

---

## 🤖 AUTO-COORDINATOR SYSTEM

### What is it?
System that automatically assigns next tasks when agents push, so lead engineer doesn't need to write in chat every time.

### Components
- `scripts/auto-assign.js`: Core logic - checks done tasks releases locks, checks TODO where deps met + no file conflict -> assigns to in_progress + locks
- `.github/workflows/auto-assign.yml`: GitHub Action triggers on push to main (paths: bridge/*.json, types/*, constants/*, supabase/*, utils/*), runs auto-assign.js, commits+pushes if changed, creates Issues for newly assigned tasks. Needs manual add via GitHub UI due to token workflow scope.
- `bridge/auto-coordinator/webhook-server.js`: Optional real-time alternative (1-2 sec vs 30-60 sec Actions), deploy to Vercel/Railway, add webhook in GitHub Settings -> Webhooks -> Payload URL https://your-server.com/webhook

### How to test locally
```bash
cd artisanpro-shared
node scripts/auto-assign.js
# Shows current status, auto-assigns if possible
```

### Monitoring
- GitHub Actions tab: https://github.com/DeadEnde/artisanpro-shared/actions - logs + summary
- GitHub Issues: https://github.com/DeadEnde/artisanpro-shared/issues - auto-created for new assignments
- Bridge files: tasks.json source of truth, locks.json active locks, state.json global state
- Webhook server: GET / -> HTML dashboard, GET /status -> JSON tasks+locks

---

## ❓ OPEN QUESTIONS FOR USER (Need Answers)

Q1: Repo Structure - Where are real repos for Client/Admin/API? We have only shared + zip snapshot. Need GitHub links for Artissan-Pro-Admin, Artissan-Pro-Client, Artissan-Pro-API.

Q2: Supabase Env Vars - VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY missing locally, blocked live verification. Are they in Vercel env for both projects?

Q3: Stripe Confirmation - Confirm manual first, Stripe later (Phase 4) is strategy? Assumed YES.

Q4: Client Data Schema - For migration, what exact tables? clients, projects, quotes, paint_calculations? Or you have SQL?

Q5: Peinture Wiring Priority - Finalize all (validation, exports, library) before wiring into route, or wire basic first?

Q6: Edge Function Deployment - Supabase CLI configured or deploy via dashboard?

Agents: If blocked by these, work on other tasks and add questions to bridge/questions.md

---

## 📦 DELIVERABLES EXPECTED

Each phase:
- ZIP clearly named: artisanpro-[phase]-v[X].zip (e.g., artisanpro-admin-v1-i18n-complete.zip)
- Tests: npm test + npm run build pass
- Screenshots FR/EN/AR
- Update bridge/tasks.json + state.json + locks.json

---

## 🚨 CRITICAL RULES (From decisions.md)

D1: Multi-agent with 9 roles, tasks.json source of truth, locks.json mandatory
D2: Shared module is source of truth for types - import, don't duplicate
D3: NO FAKE DATA - real data or 0/empty localized state (user explicit)
D4: Manual subscriptions first, Stripe Phase 4 only after manual stable
D5: No hardcoded visible text - t('key') everywhere, safe fallback, logical CSS RTL, namespaces: common, nav, auth, dashboard, modules, subscriptions, security, forms, errors, pricing, profile, landing, seo, peinture, actions, empty, status, accessibility, print, validation
D6: No sensitive data in browser - never raw IP/password/Google token/service_role, IP hash server-side via Edge Function, 90d retention
D7: Single session + heartbeat 60s + online 2min window, login->claim_single_session, logout->ended, new device->forced_logout old
D8: File locking protocol - declare claimedFiles, no edit others' locked files without questions.md
D9: Build verification required before delivery
D10: Stack preservation - Vite+React, don't migrate to Next.js
D11: Mojibake prevention UTF-8
D12: Priority P0 blocking (shared+i18n), P1 core (peinture+admin+security), P2 data+security (client+edge), P3 billing

---

## 📞 COMMUNICATION

- **User:** Works from Android phone, deploys via GitHub+Vercel, prefers Moroccan Darija short practical, no promises without ZIP/build
- **Between agents:** Use bridge/questions.md for blocking questions, bridge/decisions.md for architectural decisions, GitHub Issues for task assignments
- **With lead engineer:** No need to chat if auto-coordinator active - push and next tasks auto-assign. If need lead, update questions.md

---

## ✅ CURRENT STATUS SUMMARY

- Lead engineer DONE: Shared sync + multi-agent system + auto-coordinator deployed + pushed to GitHub (66a19d5)
- 3 IN_PROGRESS: i18n-agent, security-agent, api-agent
- 2 WAITING FOR i18n: peinture-agent, admin-agent (will auto-assign when i18n DONE)
- 1 WAITING FOR security: client-agent (will auto-assign when security DONE)
- 1 WAITING FOR admin: billing-agent (will auto-assign when admin DONE)
- Workflow file needs manual add via GitHub UI to enable full auto (due to token scope)
- All bridge files ready, no conflicts, parallel work possible

**Next: Agents continue work, push, auto-coordinator assigns next, until all DONE.**

---

**Lead Engineer - 2026-08-25 19:35 UTC**
**End of Report**
