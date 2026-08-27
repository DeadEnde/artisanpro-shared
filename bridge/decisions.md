# Decisions - ArtisanPro Multi-Agent Workspace

**Coordinator:** Lead Engineer
**Last Update:** 2026-08-25T19:30:00+00:00
**Version:** 2

## Previous Decisions (from v1)

- The active scope is the admin app; client code must remain untouched. [SUPERSEDED - now multi-agent scope]
- The parent repository is `Artissan-Pro-Admin`. [SUPERSEDED - now 3 repos: Admin, Client, API + Shared]
- The bridge files were initialized because the checked-out shared repository did not contain them.
- The current admin app passes `npm run build` before any code change.
- The Admin i18n audit keeps the existing Supabase auth/RPC flow and adds only localized presentation, validation, filters, and confirmation UI.
- The shared locale provider is consumed by the Admin app; no Client repository files were edited.
- The Admin i18n and RTL audit was completed in parent commit `acb8ec4`; all source changes remain Admin-scoped.
- The follow-up added a localized CSV report export and a Vitest test command without changing auth, Supabase contracts, or Client code.
- Live Supabase verification is intentionally deferred until environment variables are available.

## New Decisions v2 - Multi-Agent System

### D1: Multi-Agent Architecture Adopted
**Date:** 2026-08-25
**Decision:** Passer de single-agent (admin only) à multi-agent avec 9 rôles: lead-engineer, shared-agent, i18n-agent, peinture-agent, admin-agent, security-agent, client-agent, api-agent, billing-agent.
**Reason:** Projet trop grand pour un seul agent, besoin de parallélisation sans conflits.
**Impact:** bridge/tasks.json devient source of truth, locks.json obligatoire.

### D2: Shared Module is Source of Truth for Types
**Date:** 2026-08-25
**Decision:** `artisanpro-shared` est la seule source de vérité pour types, constants, utils, supabase types. Tous les autres repos l'utilisent comme git submodule.
**Reason:** Éviter divergence entre client/admin/api.
**Rule:** Aucun agent ne duplique types dans son repo, il importe depuis shared.

### D3: No Fake Data Policy - Confirmed
**Date:** 2026-08-25 (déjà décidé par user)
**Decision:** INTERDIT de générer fake users, fake revenue, fake KPIs. Utiliser real data depuis Supabase ou 0/empty state localisé.
**Example:** Overview cards: users count = real, active = real, revenue = 0 si pas de subscriptions, sessions = 0 si pas de tracking, activity = empty state.
**Reason:** User explicit requirement.

### D4: Manual Subscriptions First, Stripe Later
**Date:** 2026-08-25
**Decision:** Implémenter workflow manuel complet avant Stripe. Stripe seulement en Phase 4 après validation manual flow.
**Reason:** User strategy: manual now, Stripe later. Éviter complexité prématurée.

### D5: i18n - No Hardcoded Text Rule
**Date:** 2026-08-25
**Decision:** Aucun texte visible en JSX sans clé i18n. Tous les textes via t('key'). Safe fallback: retourner key si missing + console.warn dev.
**Namespaces:** common, nav, auth, dashboard, modules, subscriptions, security, forms, errors, pricing, profile, landing, seo, peinture, actions, empty, status, accessibility, print, validation
**Languages:** fr (ltr), en (ltr), ar (rtl - العربية الفصحى)
**RTL Rule:** Utiliser logical CSS (margin-inline, padding-inline, inset-inline, text-align: start/end) pas de hacks directionnels.

### D6: Security - No Sensitive Data in Browser
**Date:** 2026-08-25
**Decision:** Jamais stocker/collecter: raw IP, password, Google token, service_role dans browser code. IP hash côté serveur via Edge Function. Retention 90 jours.
**Reason:** Sécurité + RGPD.

### D7: Session Tracking - Single Session + Heartbeat
**Date:** 2026-08-25
**Decision:** 
- Login -> claim_single_session(device_name)
- Heartbeat 60s -> update last_seen_at
- Logout -> ended
- New device login -> old session forced_logout
- Online = last_seen_at < 2min
**Table:** app_sessions, Functions: claim_single_session, is_session_active

### D8: File Locking Protocol
**Date:** 2026-08-25
**Decision:** Chaque agent doit déclarer claimedFiles dans tasks.json + locks.json avant de coder. Pas de modification fichier locké par autre sans question dans questions.md.
**Lead engineer peut override mais doit documenter.**

### D9: Build Verification Required
**Date:** 2026-08-25
**Decision:** Avant chaque livraison: `npm run build` doit passer pour client + admin. Créer ZIP clairement nommé: `artisanpro-[phase]-v[X].zip`. Pas de promesse sans build réel.
**Reason:** User travaille depuis Android + Vercel, besoin de livrables testés.

### D10: Stack Preservation
**Date:** 2026-08-25 (from handoff doc)
**Decision:** Ne pas migrer de Vite + React vers Next.js. Préserver business/auth logic existante. Stack actuelle: Vite + React + TypeScript + Supabase + Vercel.
**Reason:** Handoff doc: requested stack was Next.js + next-intl but reality is Vite + React, do not migrate.

### D11: Mojibake Prevention
**Date:** 2026-08-25
**Decision:** Tous les fichiers sauvés en UTF-8. Chercher vrais artefacts mojibake: Ã© Ã¨ â€™ â€œ â€ Ø§ Ù„ � - pas les accents français valides é è.
**Reason:** Éviter corruption arabe/français.

### D12: Task Priority System
**Date:** 2026-08-25
**Decision:** P0 = bloquant (shared, i18n), P1 = core features (peinture, admin modules, security), P2 = data/security (client migration, edge functions), P3 = billing.
**Execution:** P0 d'abord, puis P1 en parallèle, puis P2, puis P3.

## Future Decisions To Make

- [ ] Faut-il créer repos séparés Artissan-Pro-Client et Artissan-Pro-API maintenant ou continuer depuis workspace zip?
- [ ] Structure finale dossiers admin après cleanup legacy components (AdminApp, Overview, Manage)?
- [ ] SQL pour clients/projects/quotes - créer nouvelle migration ou étendre setup existant?

- Admin task `admin-modules-subscriptions` completed in parent commit `5f9baba` at 2026-08-26T18:51:13+00:00; its locks were released after build/test verification.

- Admin overview task completed in parent commit `a5f037d` at 2026-08-26T19:57:35+00:00; real Supabase-backed overview reads were added and the security-agent `SecurityPanel.tsx` lock was respected.

- Admin Security Center completed in parent commit `11b3573` at 2026-08-26T20:11:39+00:00; sessions/logs UI is delivered and all admin locks were released.

- Admin revenue analytics completed in parent commit `da50f02` at 2026-08-27T13:11:33+00:00; Content/SEO stopped at the existing modules contract and is explicitly blocked pending a shared CMS schema.
