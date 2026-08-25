# Questions - ArtisanPro Multi-Agent Workspace

**Coordinator:** Lead Engineer
**Last Update:** 2026-08-25T19:30:00+00:00

## Resolved Questions (v1)

- Requester: the task was marked as a bug fix, but no failing behavior, error message, affected screen, or acceptance criteria was supplied. Which admin bug should be fixed?
  - **Resolution:** Superseded by i18n and RTL audit task; no active blocker.

- Live Supabase verification is blocked in this environment because `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are absent; no secrets were requested or printed.
  - **Resolution:** Intentionally deferred until env vars available. Still blocked in v2 - need Vercel env.

## Open Questions v2 - For User / Agents

### Q1: Repository Structure - URGENT
**From:** lead-engineer
**To:** user
**Date:** 2026-08-25
**Question:** Actuellement on a seulement `artisanpro-shared` repo cloné + `artisanpro-workspace-source.zip` qui contient snapshot client + admin. Est-ce qu'on a les vrais repos GitHub pour:
- `Artissan-Pro-Admin` (ou ArtisanPro-Admin?)
- `Artissan-Pro-Client` (ou ArtisanPro-Client?)
- `Artissan-Pro-API`?

Ou on doit recréer les repos à partir du zip? Donne moi les liens GitHub si existent.

**Impact:** Bloque assignation tasks aux agents - ils ont besoin de parentRepo.

### Q2: Supabase Env Vars
**From:** lead-engineer
**To:** user
**Date:** 2026-08-25
**Question:** VITE_SUPABASE_URL et VITE_SUPABASE_ANON_KEY manquent localement. Tu peux les mettre dans Vercel env pour artissan-pro et artisanpro-admin? Ou tu veux qu'on teste en local avec .env?

**Impact:** Bloque live verification sessions/logs/RPC.

### Q3: Stripe Confirmation
**From:** lead-engineer
**To:** user
**Date:** 2026-08-25
**Question:** Confirmé: on reste en manual subscriptions pour Phase 1-3, Stripe seulement Phase 4 après validation manual flow? C'est bien ta stratégie?

**Status:** Assumed YES from previous docs, awaiting confirmation.

### Q4: Client Data Schema
**From:** lead-engineer (future: client-agent)
**To:** user
**Date:** 2026-08-25
**Question:** Pour migration localStorage -> Supabase, quelles tables tu veux exactement?
- clients (id, user_id, name, phone, city...)
- projects (id, user_id, client_id, name, module...)
- quotes (id, user_id, project_id, client_id, area, liters, total...)
- paint_calculations (saved calculations)

Ou tu as déjà SQL pour ça? Sinon je crée.

### Q5: Peinture Workspace - Priority
**From:** lead-engineer (future: peinture-agent)
**To:** user
**Date:** 2026-08-25
**Question:** Peinture workspace premium - tu veux qu'on finalise tout (validation, exports PDF/XLSX, saved library) avant de le brancher dans route, ou on branche version basique d'abord puis on améliore?

**Recommendation:** Finaliser tout avant wiring (comme dit dans TODOs) pour éviter régression.

### Q6: Security Logs - Edge Function Deployment
**From:** lead-engineer (future: api-agent)
**To:** user
**Date:** 2026-08-25
**Question:** Edge Functions Supabase - tu as déjà Supabase CLI configuré? Ou tu veux que je crée les fonctions et tu déploies via dashboard?

**Needed:** log-security-event + cleanup-logs (90j).

## Questions for Other Agents (Internal)

### For i18n-agent
- [ ] As-tu accès aux repos client + admin ou tu travailles depuis zip?
- [ ] Peux-tu scanner tous les fichiers pour hardcoded text et lister?
- [ ] RTL: tu utilises logical CSS ou tu as besoin de refacto CSS existant?

### For admin-agent
- [ ] ModuleAccessPanel et SubscriptionPanel de base existent - tu pars de là ou tu refais?
- [ ] UserDetailDrawer - tu le mets où? Nouveau fichier ou dans UsersPanel?
- [ ] ConfirmDialog localisé existe déjà - tu l'utilises?

### For security-agent
- [ ] artisanpro-session-security-upgrade.sql a été run en prod? Vérifie.
- [ ] Heartbeat 60s - tu le mets dans AppContext ou nouveau hook useSessionPresence?
- [ ] Force logout - comment tu gères côté client? Supabase auth signOut + clear session?

### For client-agent
- [ ] Migration douce localStorage -> Supabase: tu proposes import automatique ou bouton manuel?
- [ ] RLS policies - tu crées pour chaque table ou une policy générique?

### For api-agent
- [ ] IP hash - quel algo? SHA256? Tu hashes côté Edge Function avec secret?
- [ ] Cleanup 90j - cron daily ou via pg_cron?

## How to Ask Questions

1. Ajoute question ici avec From/To/Date/Question/Impact
2. Update tasks.json -> questions[]
3. Attends réponse dans decisions.md ou ici en Resolution
4. Ne bloque pas tout - travaille sur autre task si bloqué

## Template

```
### Q[X]: [Titre]
**From:** [agent]
**To:** [user ou agent]
**Date:** [date]
**Question:** [question claire]
**Impact:** [ce qui est bloqué]
**Status:** [open / resolved]
**Resolution:** [si résolu]
```
