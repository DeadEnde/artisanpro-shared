# ArtisanPro Roadmap - Multi-Agent Execution Plan

**Date:** 2026-08-25
**Coordinator:** Lead Engineer
**Version:** 2.0

## Vision
SaaS pour artisans marocains (peinture, carrelage...) - Devis rapides, gestion clients/chantiers, abonnements par module.

## Phase 1: Foundation Fix (P0) - Semaine 1
**Objectif:** Stabiliser shared + i18n

### Task 1: shared-types-sync [P0] - Lead Engineer - EN COURS
- [ ] Auditer artisanpro-supabase-setup.sql + tous les upgrades SQL
- [ ] Mettre à jour supabase/types.ts avec toutes les tables réelles:
  - profiles, modules, user_modules, module_entitlements, app_sessions, subscriptions, admin_activity_logs, security_logs, clients, projects, quotes
- [ ] Mettre à jour types/index.ts pour matcher
- [ ] Ajouter constantes manquantes
- [ ] Vérifier utils: formatCurrency, hasModuleAccess, getDirection
- [ ] `npm run build` passe

### Task 2: i18n-complete-audit [P0] - i18n-agent - TODO
- [ ] Scanner client src/main.tsx: pricing, login, dashboard, projects, quotes, lead, painting locked
- [ ] Scanner admin src/main.tsx: auth gate, header, profile, overview, security, legacy components
- [ ] Créer dictionnaires complets FR/EN/AR avec namespaces
- [ ] Remplacer tous les textes hardcoded par t('key')
- [ ] Fix RTL: logical CSS partout
- [ ] Test screen by screen FR/EN/AR + screenshots
- **Dépend:** shared-types-sync

## Phase 2: Core Features (P1) - Semaine 2-3

### Task 3: peinture-workspace-premium [P1] - peinture-agent - TODO
- [ ] Ajouter paint.* keys FR/EN/AR
- [ ] Wire PricingStrategyPanel dans PeintureWorkspace
- [ ] Package comparison, price floor/ceiling, profit target, VAT/discount validation
- [ ] Room type, ceiling toggle, doors/trims, interior/exterior, wall condition UI
- [ ] My Calculations: save/open/rename/duplicate/delete/import/export JSON/CSV
- [ ] Quote: number, validity, payment terms, notes, terms, client/project metadata
- [ ] Exports: PDF, XLSX, CSV, print HTML
- [ ] Route wiring: remplacer Calculator() dans Painting()
- **Dépend:** i18n

### Task 4: admin-modules-subscriptions [P1] - admin-agent - TODO
- [ ] UserDetailDrawer avec badges
- [ ] Module access: grant/revoke/pause + expiry editor
- [ ] Subscription: pause/resume/cancel + expiry + amount input
- [ ] Manual payment history UI
- [ ] Status timeline + localized ConfirmDialog
- [ ] Tests avec vrais RPCs
- **Dépend:** shared-types-sync, i18n

### Task 5: security-center-sessions [P1] - security-agent - TODO
- [ ] Vérifier migration artisanpro-session-security-upgrade.sql
- [ ] Client: claim_single_session au login + heartbeat 60s
- [ ] Client: logout ended + new device forced_logout
- [ ] Admin: Security Center tab, active sessions, online/offline (2min), last seen, duration, device/browser/OS, force logout
- [ ] Filtres app/client/admin, event type
- **Dépend:** shared-types-sync

## Phase 3: Data & Security (P2) - Semaine 4

### Task 6: client-supabase-migration [P2] - client-agent - TODO
- [ ] Créer tables clients/projects/quotes/paint_calculations + RLS
- [ ] RLS: user voit seulement ses données, admin voit tout
- [ ] Refactor AppContext de localStorage vers Supabase
- [ ] Migration douce: import depuis localStorage
- [ ] Entitlement status dans module card + CTA upgrade
- **Dépend:** shared, security

### Task 7: edge-function-security-logs [P2] - api-agent - TODO
- [ ] Edge Function log-security-event: hash IP serveur, insert security_logs
- [ ] Edge Function cleanup-logs: cron 90j
- [ ] Brancher client/admin vers Edge Function
- [ ] Events: login_success, login_failed, access_denied, account_blocked, logout, forced_logout, session_started, session_expired
- [ ] Vérif: jamais raw IP/password/token/service_role dans browser
- **Dépend:** shared

## Phase 4: Billing (P3) - Semaine 5

### Task 8: manual-payments-stripe-prep [P3] - billing-agent - TODO
- [ ] Payment history UI avec amount/currency/date/plan
- [ ] Confirmation workflow admin
- [ ] Expiry/renewal automation basique
- [ ] Prep webhook Stripe (pas implémenter encore)
- **Dépend:** admin-modules-subscriptions

## Success Criteria Global

- [ ] `npm run build` passe pour client + admin
- [ ] 0 texte hardcoded visible
- [ ] FR/EN/AR 100% + RTL parfait
- [ ] Peinture workspace premium fonctionnel + exports
- [ ] Admin peut grant/revoke/pause modules + subscriptions réelles
- [ ] Security Center réel avec sessions online/offline + force logout
- [ ] Client data en Supabase avec RLS
- [ ] Security logs via Edge Function avec IP hash + 90j retention
- [ ] Manual payments workflow stable
- [ ] Deploy Vercel OK avec env vars

## Livrables

Chaque phase livre:
- ZIP clairement nommé: `artisanpro-[phase]-v[X].zip`
- Tests: `npm test` + `npm run build`
- Screenshots FR/EN/AR
- Update bridge/tasks.json + state.json

## Risques

- **Supabase env vars manquantes localement:** Bloque tests live -> utiliser Vercel env ou demander secrets
- **Conflits files entre agents:** Utiliser locks.json strict
- **Mojibake:** Vérifier UTF-8, chercher Ã© Ã¨ â€™
- **Fake data:** INTERDIT - utiliser real data ou 0/empty state (décision user)
