# Questions - ArtisanPro Multi-Agent Workspace

**Coordinator:** Lead Engineer + Shared Agent + Auto-Coordinator 24/7 Runner
**Last Update:** 2026-08-26T18:30:00+00:00
**Runner:** ACTIVE - checks every 60s

## Resolved Questions (v1)

- Requester: the task was marked as a bug fix, but no failing behavior, error message, affected screen, or acceptance criteria was supplied. Which admin bug should be fixed?
  - **Resolution:** Superseded by i18n and RTL audit task; no active blocker.

- Live Supabase verification is blocked in this environment because `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are absent; no secrets were requested or printed.
  - **Resolution:** Intentionally deferred until env vars available. Still blocked in v2 - need Vercel env.

## Resolved in v3 (2026-08-26)

### Q4: Client Data Schema - RESOLVED
**From:** client-agent
**To:** shared-agent
**Date:** 2026-08-26
**Question:** Required clients/projects/quotes/paint_calculations tables and RLS migration are not available
**Resolution:** 
- Created `supabase/client-migration.sql` with 4 tables: clients, projects, quotes, paint_calculations + RLS policies (self or admin) + updated_at triggers
- Updated `supabase/types.ts` with 4 new tables: clients, projects, quotes, paint_calculations (Row, Insert, Update)
- Build PASS (tsc --noEmit)
- Task `client-supabase-migration` unblocked: status blocked -> todo
- Files: supabase/client-migration.sql, supabase/types.ts

### Q1: Repository Structure - PARTIALLY RESOLVED
**From:** lead-engineer
**To:** user
**Date:** 2026-08-25
**Question:** Where are real repos for Client/Admin/API? Only shared + zip snapshot exists.
**Resolution (2026-08-26):**
- Extracted `artisanpro-workspace-source.zip` to create parent repos locally:
  - `/home/user/Artissan-Pro-Client` (from zip src + package.json)
  - `/home/user/Artissan-Pro-Admin` (from zip artisanpro-admin)
- Now i18n-agent, peinture-agent, admin-agent, security-agent, client-agent can work on real files
- Still need GitHub repos for Client/Admin/API if user wants separate remotes - currently local only
- Locks valid, no overlap

## Open Questions v2 - For User / Agents

### Q2: Supabase Env Vars
**From:** lead-engineer
**To:** user
**Date:** 2026-08-25
**Question:** VITE_SUPABASE_URL et VITE_SUPABASE_ANON_KEY manquent localement. Tu peux les mettre dans Vercel env pour artissan-pro et artisanpro-admin? Ou tu veux qu'on teste en local avec .env?
**Impact:** Bloque live verification sessions/logs/RPC.
**Status:** OPEN - still blocked, need Vercel env

### Q3: Stripe Confirmation
**From:** lead-engineer
**To:** user
**Date:** 2026-08-25
**Question:** Confirmé: on reste en manual subscriptions pour Phase 1-3, Stripe seulement Phase 4 après validation manual flow? C'est bien ta stratégie?
**Status:** Assumed YES, awaiting confirmation - OPEN

### Q5: Peinture Workspace - Priority
**From:** lead-engineer (future: peinture-agent)
**To:** user
**Date:** 2026-08-25
**Question:** Peinture workspace premium - tu veux qu'on finalise tout (validation, exports PDF/XLSX, saved library) avant de le brancher dans route, ou on branche version basique d'abord puis on améliore?
**Recommendation:** Finaliser tout avant wiring pour éviter régression.
**Status:** OPEN

### Q6: Security Logs - Edge Function Deployment
**From:** lead-engineer (future: api-agent)
**To:** user
**Date:** 2026-08-25
**Question:** Edge Functions Supabase - tu as déjà Supabase CLI configuré? Ou tu veux que je crée les fonctions et tu déploies via dashboard?
**Needed:** log-security-event + cleanup-logs (90j).
**Status:** OPEN

### Q7: i18n Agent Stuck - NEW
**From:** auto-coordinator
**To:** i18n-agent
**Date:** 2026-08-26
**Question:** i18n-complete-audit IN_PROGRESS since 2026-08-25T19:31:19 (1 day) - no push. Parent repos now created locally from zip. Are you blocked? Need help with hardcoded text scan?
**Impact:** Blocks peinture and admin (both waiting i18n DONE). P0 critical path.
**Status:** OPEN - i18n is bottleneck

### Q8: Security & API Agents Stuck - NEW
**From:** auto-coordinator
**To:** security-agent, api-agent
**Date:** 2026-08-26
**Question:** security-center-sessions and edge-function-security-logs IN_PROGRESS since same date, no push. Need help? Parent repos now available.
**Impact:** Blocks client (waiting security)
**Status:** OPEN

## How to Ask Questions

1. Ajoute question ici avec From/To/Date/Question/Impact
2. Update tasks.json -> questions[]
3. Attends réponse dans decisions.md ou ici en Resolution
4. Ne bloque pas tout - travaille sur autre task si bloqué
