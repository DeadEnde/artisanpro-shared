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

- Admin Mosk design completed in parent commit `c4557a6` at 2026-08-27T17:39:32+00:00; the design task lock was released after build/test verification.

### D13: Human Override - Q14 Wiring & Client i18n Completion
**Date:** 2026-08-28
**Decision:** Repo owner authorized direct completion outside the agent-lock workflow. Route wiring of PeintureWorkspace confirmed shipped (Artissan-Pro @ caacc78). P0 client i18n audit completed and verified (0 hardcoded strings, 87 keys x3, FR fallback, Intl locale-aware MAD, real auth wiring) in Artissan-Pro @ aa064fb.
**Reason:** i18n-agent lock on src/main.tsx was stale (Q7/Q14); human override is the documented escape hatch. Stack preserved per D10 (Vite + React + Supabase), no Next.js migration.

### D14: Shared CMS Contract for Content & SEO
**Date:** 2026-08-28
**Decision:** The CMS schema is the existing supabase/content-seo.sql (content_sections + seo_metadata), formalized in shared types/constants (shared @ 6cacd86) with RLS policies: public reads published content, is_admin() manages everything. Admin ContentPanel manages seo_metadata from Artissan-Pro-Admin @ bacd06b. Client public pages keep their localized static copy until a follow-up wires them to seo_metadata.
**Reason:** Unblocks admin-content-seo without migrating the client public pages' rendering (stack preserved per D10).

### D15: Aether Design Direction for Client App
**Date:** 2026-08-28
**Decision:** Client app visual identity rebuilt as "Aether": warm paper #f6f3ec / ink #181410 / clay #e0511e; display type Space Grotesk with Instrument Serif italic accents; Tajawal as Arabic face; framer-motion for all motion (no CSS keyframe anims outside pulse/dot). Dark ink bands used for feature/auth-intro/result panels. RTL via logical CSS properties.
**Reason:** Human request to redo the design from scratch using modern motion/component inspiration (21st.dev-style micro-interactions). Stack preserved per D10.

### D15: Visual Direction — Ink & Flame (Dark)
**Date:** 2026-08-28
**Decision:** Product owner approved the dark "Ink & Flame" design language (deep ink #0E0B08, flame #FF5C28, cream inversion panels, Space Grotesk x Instrument Serif x Tajawal, framer-motion language curtain) as the official ArtisanPro visual identity, replacing the Aether light theme. Reference implementation: sandbox concept prod build; ported to the client in Artissan-Pro @ e04194c via token-level re-theme (no markup churn).
**Reason:** Owner preference after side-by-side review; token flip kept all components/contracts intact (tests 20/20 + build green).

### D16: Client Dashboard Polish, Entitlements & Peinture Tasks Closure
**Date:** 2026-08-28
**Decision:** Closed remaining client UI tasks following the Ink & Flame redesign:
- Telemetry presence badge added to Shell sidebar (design-client-aether)
- ModuleCard wired to moduleEntitlements with live status badges and expiry dates (client-entitlement-ui)
- Projects panel upgraded with search filter, status tabs, summary metrics, and print/duplicate actions (client-projects-quotes-ui)
- Peinture room controls, pricing strategy panel, and test suite verified passing 20/20 (peinture-room-controls, design-peinture-energy, peinture-engine-tests)
- Shipped on DeadEnde/Artissan-Pro @ 2e01b11.

### D17: Security Logging Architecture — Edge Functions with Hashed IP
**Date:** 2026-08-29
**Decision:** Security events are logged exclusively through the log-security-event Edge Function. Clients send only whitelisted event payloads; the server derives the IP from proxy headers and persists only a salted SHA-256 hash (raw IP never stored). Retention enforced by cleanup-security-logs (90 days, CRON_SECRET gated). Client emits session_started/login_success/logout via fire-and-forget securityLog.ts that can never break UX.
**Reason:** Compliance + D3 (no raw secrets in browser), no DB schema change; remaining step is owner deployment (secrets + supabase functions deploy).

### D18: Vantra Telemetry HUD, Billing Automation & Stripe Webhooks
**Date:** 2026-08-29
**Decision:** 
- Upgraded Admin Security Center with Vantra Facility OS Telemetry HUD & Global Emergency Kill Switch.
- Enhanced SubscriptionPanel with quick renewal presets (+30d, +90d, +365d) and manual payment method tracking.
- Shipped Stripe Webhook Edge Function (HMAC-SHA256 signature verification) in shared repo with complete integration guide.
- Closed tasks: i18n-complete-audit, manual-payments-stripe-prep, admin-billing-payments, design-security-vantra.

### D19: Security Logs — Both Apps Emit Through Edge Function
**Date:** 2026-08-29
**Decision:** Roadmap complete (29/29 tasks). The admin app now emits login_success / access_denied / logout through the same log-security-event edge function (meta.app discriminator), closing edge-function-security-logs. Remaining items are owner operations only: Supabase secrets + functions deploy + pg_cron schedule (documented, cannot run without project CLI auth).
