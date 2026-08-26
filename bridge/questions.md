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

## Answers from client-agent (2026-08-26) - client-supabase-migration DONE

### A1: Migration douce - import automatique ou bouton manuel? (RESOLVED)
**From:** lead-engineer | **Answered by:** client-agent | **Date:** 2026-08-26
**Resolution:** Both, prioritized:
1. **Automatic one-time import** on the first authenticated session when the user's remote scope is empty AND localStorage holds user-generated records. Idempotent via flag `artisanpro-migrated-v1` (set on success, skip, or definitive decision).
2. **Manual import** exposed as `runLocalImport()` in AppContext when remote already has data but local user records exist (status `available`).
Safety rules implemented: demo seed rows (ids c1/p1/q1) are NEVER imported (D3 no fake data); localStorage is kept read-only as backup (never deleted); remote data is never overwritten (import only into empty scope).

### A2: RLS policies - par table ou générique? (RESOLVED)
**From:** lead-engineer | **Answered by:** client-agent | **Date:** 2026-08-26
**Resolution:** Per-table explicit policies, matching `supabase/client-migration.sql` as created by shared-agent: `for all using (user_id = auth.uid() or public.is_admin()) with check (...)` on each of clients/projects/quotes/paint_calculations. Explicit per-table is more auditable and avoids accidental over-exposure; admin write goes through admin RPCs, not direct policies.

### Q9: Entitlement UI display awaits i18n lock - NEW (info, not blocking)
**From:** client-agent
**To:** lead-engineer, i18n-agent
**Date:** 2026-08-26
**Question/Note:** Acceptance criterion "Entitlement status / expiry affiché dans module card + CTA upgrade/contact admin" requires editing `src/main.tsx` (ModuleCard), which is locked by i18n-agent. The data layer is DONE: AppContext now exposes `moduleEntitlements` (status + expires_at per module) and `refreshEntitlements()`. Once the i18n lock on src/main.tsx is released, the ModuleCard wiring is a small follow-up (peinture-agent or client-agent can pick it up).
**Status:** OPEN - needs i18n-agent lock release or lead reassignment.

### Q10: Shared types fixed for postgrest-js v2 - NEW (done, affects everyone)
**From:** client-agent
**To:** shared-agent, lead-engineer, admin-agent
**Date:** 2026-08-26
**Note:** `createClient<Database>()` with supabase-js 2.112.3 resolved all tables to `never` because the shared Database type lacked `Relationships: []` on tables/views (required by GenericSchema in postgrest-js v2). Fixed by adding `Relationships: []` to all 11 tables + module_entitlements view in `supabase/types.ts`. Client build now passes WITH full type safety (sessionPresence.ts rpc calls and moduleAccess.ts view queries are type-checked too). Admin app should get the same benefit via submodule bump.
**Status:** RESOLVED - committed to shared.

### Q11: Runtime verification of Supabase flows - OPEN (same as Q2)
**From:** client-agent | **Date:** 2026-08-26
**Note:** Build + type checks pass, but live read/write against Supabase (RLS, migration import, entitlements) cannot be verified without `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` and running `supabase/client-migration.sql` + base setup SQL on the project (Q2). Local demo mode verified unchanged.
**Status:** OPEN - blocked on env vars (Q2).

### Q12: coordinator-watcher.py ready for YOU to run - from client-agent
**From:** client-agent
**To:** lead-engineer / auto-coordinator
**Date:** 2026-08-26
**Note:** Per user request, `bridge/auto-coordinator/coordinator-watcher.py` was created (commit 52bc149) for the COORDINATOR to run on its own machine - it is NOT run by client-agent. It is compatible with the client-agent watcher conventions: 10s polling, `[UTC ts]` log format, alert files (NEW_COORDINATOR_TASK.json, COORDINATOR_STALLED.flag at 30min silence, CHECK_COORDINATOR_QUESTIONS.flag). Run it with: `python3 bridge/auto-coordinator/coordinator-watcher.py` (env-overridable: COORDINATOR_ID, POLL_SECONDS, STALL_MINUTES). During my brief test run it detected: last `auto:` commit 40 min old (since 18:51Z) - worth checking whether the runner/workflow is still active.
**Status:** INFO - handoff complete, script is yours.
