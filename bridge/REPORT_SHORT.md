# ArtisanPro - Short Report for Agents
**Lead:** 2026-08-25 | **Repo:** artisanpro-shared | **Stack:** Vite+React+Supabase

## What I Did
- Cloned repo, read zip (client+admin apps + SQL)
- **Shared sync DONE:** Updated supabase/types.ts (7 tables + 10 funcs) + constants v2
- Created multi-agent v2: tasks.json (8 tasks P0-P3), agents.md (9 roles), roadmap, locks, state, decisions, questions
- Deployed auto-coordinator: auto-assign.js + GitHub Action + webhook server (auto assigns next tasks on push, no chat needed)

## Current Status
```
DONE: shared-types-sync (lead)
IN_PROGRESS: i18n (P0), security (P1), api (P1)
TODO→auto when i18n DONE: peinture, admin
TODO→auto when security DONE: client
TODO→auto when admin DONE: billing
```

## What Each Agent Does
- **i18n-agent [P0]:** 0 hardcoded text, FR/EN/AR dicts, RTL logical CSS, Intl MAD/dates
- **security-agent [P1]:** claim_single_session, heartbeat 60s, Security Center (online/offline 2min, force logout)
- **api-agent [P1]:** Edge Functions log-security-event (IP hash server-side) + cleanup 90d
- **peinture-agent [P1, wait i18n]:** Premium workspace, validation, saved calcs, quote editors, PDF/XLSX/CSV exports, wire route
- **admin-agent [P1, wait i18n]:** Grant/revoke/pause modules, pause/resume subs, expiry editor, payment history
- **client-agent [P2, wait security]:** localStorage → Supabase RLS
- **billing-agent [P3, wait admin]:** Manual payments + Stripe prep (no Stripe yet)

## How to Work
1. Read tasks.json (your task), agents.md (your role), locks.json (your files)
2. Code only your locked files, no fake data (real or 0/empty), no raw IP/password/token in browser
3. Build must pass: `npm run build` client+admin
4. Update tasks.json status→done, push → auto-coordinator assigns next

## Rules
- Shared is source of truth, import don't duplicate
- No hardcoded JSX → t('key'), safe fallback
- RTL: margin-inline/padding-inline, not left/right
- Session: login→claim, 60s heartbeat, logout→ended, new device→old forced_logout
- File locks mandatory, ask in questions.md if conflict

## Auto-Coordinator
Push → Action runs auto-assign.js → checks deps met + no lock conflict → assigns next + pushes + creates Issues. Monitor: /actions and /issues

## Open Q for User
Q1: Where are Client/Admin/API repos? Q2: Supabase env vars? Q3: Stripe manual first? Q4: Client tables? Q5: Peinture wiring? Q6: Edge deploy?

**End - Read tasks.json for your task details**
