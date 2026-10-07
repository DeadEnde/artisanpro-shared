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

### D20: Bridge Reconciliation Against Real Code — Sprint 2 Closure
**Date:** 2026-10-07
**Decided by:** Engineer (Arena Agent) — acting as source of truth
**Context:** The bridge was frozen at 2026-08-29 while the client repo advanced to 2026-09-11. Two bridges disagreed: the client's pinned copy (`bcfda11`) was 5 tasks BEHIND the code; the remote copy (`669a4f2`) claimed 10/10 Sprint 2 done while 2 tasks did not exist in the code. Three locks were held by an empty `agent:""` string since 2026-08-29.
**Decision:** The bridge is verified against the code by executable assertions, not by trust in prior reports. The tool is `bridge/verify-claims.py`; it runs greppable assertions per task and rewrites `tasks.json`/`locks.json` from the result.
**Rule (anti-drift):** the bridge is reconciled at the start of *every* session. If bridge and code disagree, **the code is the fact and the bridge is the bug**. A task is only `done` with recorded command output — "the code looks complete" is not evidence.

### D21: Engine Test Coverage — Restored
**Date:** 2026-10-07
**Context:** D16 claimed "test suite verified passing 20/20". The repo contained 2 tests. `carrelage`, `electricite` and `plomberie` engines — which produce customer-facing quotes — had **zero**.
**Decision:** `tests/engines.test.ts` added: 22 tests pinning the arithmetic invariants of the three engines. Total now 24. Four known engine defects are captured as `[caractérisation]` tests so they cannot change silently:
1. `carrelage` ignores `wastePct` in diagonale/décalée layout (multiplier hard-frozen at 1.15/1.12).
2. `carrelage` displays `ragreageCost = surface × prix/m²` but charges `ceil(surface/5) × 85` — the quote detail does not reconcile with the cost.
3. `carrelage` applies the `hasJointEpoxy` surcharge to **plinthes** instead of jointing.
4. `electricite` applies **no margin, no overhead, no VAT** — its `totalDevis` is a raw cost price. Carrelage and plomberie apply all three.
**Status:** defects are documented and frozen, **not yet fixed** — they change customer prices and require an owner decision.

### D22: Submodule Pin Advanced bcfda11 → 669a4f2
**Date:** 2026-10-07
**Decision:** The client's `shared` submodule pin was 16 commits behind remote main. Diff `bcfda11..669a4f2` touches **only** `bridge/*` — no file imported by the client. The pin was advanced, so both apps now resolve `shared/supabase/types.ts` from the same place.
**Checked:** `tsc -b` exit 0 and `npm run build` green after the bump.

### D23: The Four Engine Defects — FIXED
**Date:** 2026-10-07
**Decided by:** repo owner ("Ok slhom" / صلّحهم) after the D21 audit surfaced them.
**Context:** D21 documented four defects in the quoting engines. They were frozen by characterisation tests pending an owner decision because every fix changes real customer prices.

**What changed**

1. **carrelage — wastePct ignored on diagonal/offset layouts.**
   The multiplier was hard-frozen at 1.15 / 1.12, silently discarding the user's setting.
   Now **additive**: `1 + (wastePct + layoutBonus)/100`, where the bonus is +5 pts diagonal, +2 pts offset.
   At the default `wastePct = 10` this yields exactly 1.15 and 1.12 — **so no existing quote changes** — but the control now has an effect at every other value.

2. **carrelage — displayed ragréage ≠ charged ragréage.**
   The quote showed `surface × ragreagePriceMeter` while the cost used `ceil(surface/5) × 85`, a hardcoded bag price that ignored the setting. A 45 m² job displayed 3 825 MAD and charged 765 MAD.
   Now the user's MAD/m² rate is authoritative and `ragreageCost` **is** the charged amount. The bag count survives as `ragreageBags`, informational only (purchasing).
   ⚠️ **Price impact:** ragréage lines rise sharply (3 825 instead of 765 on the 45 m² example). If 85 was meant as a *per bag* price rather than per m², lower `ragreagePriceMeter` to ~17 in the UI.

3. **carrelage — epoxy surcharge on the wrong line.**
   `hasJointEpoxy` multiplied **plinthes** by 1.7. Epoxy is a jointing product. The ×1.7 now applies to the grout line; plinthes are untouched.

4. **electricite — no margin, no overhead, no VAT.**
   `totalDevis` was a raw cost price. The module now runs the same chain as plomberie: `costDirect → overhead → contingency → totalAvantMarge → saleBeforeTax → vat → totalDevis`. Four new inputs (`overheadPct`, `contingencyPct`, `marginPct`, `vatPct`) with a FR/EN/AR UI section, and HT / TVA / marge rows in the synthesis.
   Two *additional* export-layer defects were found and fixed while wiring it:
   - the PDF hardcoded `+20%` VAT on top of the total while the CSV labelled that same pre-VAT number "Total TTC" — three places, three different answers. The exporters now read `vat` / `saleBeforeTax` from the engine;
   - the PDF listed **cost** lines under a **sale-price** subtotal. Line items are now scaled by the markup factor, with the last line absorbing rounding drift so the column sums exactly to the HT subtotal.
   ⚠️ **Price impact:** with the defaults (overhead 10 %, contingency 5 %, margin 30 %, VAT 20 %) an electrician's quote goes from 12 072 to 21 658 MAD — **+79 %**. That is the corrected price, not an increase: the previous figure was the cost price.

**Also fixed (found during this work):** `setInputs(item.inputs)` in the carrelage, electricite and plomberie workspaces replaced the whole input object with the *saved* one. Any quote stored before today lacks the new electricite fields, so opening it would have produced `undefined/100` → **NaN across the entire quote**. All three now merge over defaults, matching what peinture already did.

**Verification:** `tsc -b` exit 0 · `npm test` **28/28** · `vite build` green (931 ms). The four characterisation tests were rewritten as assertions on the corrected behaviour.
