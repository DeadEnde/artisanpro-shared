# ArtisanPro Multi-Agent System - Agent Definitions

**Coordinator:** Lead Engineer (current session - 2026-08-25)
**Shared Repo:** `DeadEnde/artisanpro-shared` - source of truth for types/constants

## Agent Roles

### 1. `lead-engineer` - Coordinator (YOU ARE HERE)
- **Responsibility:** Orchestrer tous les agents, maintenir `artisanpro-shared`, gérer le bridge
- **Files:** `bridge/*`, `types/*`, `constants/*`, `supabase/*`, `utils/*`
- **Rules:** Ne jamais casser le build, toujours updater tasks.json, documenter decisions

### 2. `shared-agent`
- **Repo:** `artisanpro-shared`
- **Mission:** Garder les types/constants/utils sync avec Supabase schema réel
- **Key Files:** `types/index.ts`, `supabase/types.ts`, `constants/index.ts`

### 3. `i18n-agent`
- **Repos:** `Artissan-Pro-Client` + `Artissan-Pro-Admin`
- **Mission:** Full i18n audit - 0 hardcoded text, FR/EN/AR, RTL
- **Namespaces requis:** common, nav, auth, dashboard, modules, subscriptions, security, forms, errors, pricing, profile, landing, seo, peinture, actions, empty, status, accessibility, print, validation
- **Rules:** 
  - `t('key')` partout, pas de texte direct en JSX
  - Fallback safe: retourne key si missing + console.warn dev
  - Logical CSS: margin-inline, padding-inline, text-align: start
  - Intl: `new Intl.NumberFormat(locale, {style:'currency', currency:'MAD'})`

### 4. `peinture-agent`
- **Repo:** `Artissan-Pro-Client`
- **Mission:** Finaliser Premium Peinture Workspace
- **Source:** `src/features/peinture/` existe mais pas branché
- **Must:** Validation, saved calculations, quote editors, exports PDF/XLSX/CSV/print

### 5. `admin-agent`
- **Repo:** `Artissan-Pro-Admin`
- **Mission:** Modules & Subscriptions real UI
- **RPCs:** `admin_set_user_status`, `admin_set_module_access`, `admin_set_subscription_status`
- **UI:** UserDetailDrawer, ModuleAccessPanel, SubscriptionPanel, badges, expiry editor

### 6. `security-agent`
- **Repos:** Both Client + Admin
- **Mission:** Session tracking + Security Center
- **Tables:** `app_sessions`, `security_logs`
- **Functions:** `claim_single_session`, `is_session_active`
- **Logic:** login -> claim, heartbeat 60s, logout -> ended, new device -> forced_logout old

### 7. `client-agent`
- **Repo:** `Artissan-Pro-Client`
- **Mission:** Migration localStorage -> Supabase + RLS
- **Tables à créer:** clients, projects, quotes, paint_calculations
- **Rules:** per-user RLS, admin voit tout, pas de shared data

### 8. `api-agent` / `supabase-agent`
- **Repo:** `Artissan-Pro-API` / Supabase Edge Functions
- **Mission:** Edge Functions pour security logging sécurisé
- **Security:** IP hash côté serveur, jamais raw IP/password/token/service_role dans browser
- **Retention:** 90 jours cleanup cron

### 9. `billing-agent`
- **Repos:** Admin + Client
- **Mission:** Manual payments workflow, prep Stripe
- **Strategy:** Manual now, Stripe later (décision confirmée)

## Communication Protocol

### File Locking
Chaque agent DOIT déclarer `claimedFiles` dans tasks.json avant de coder. Pas de overlap sans sync via bridge/questions.md

### Bridge Files Usage
- `tasks.json` -> Source of truth pour tous les tasks (version 2)
- `state.json` -> État actuel du coordinator + dernier task global
- `locks.json` -> Files lockés actuellement (empêcher conflits)
- `decisions.md` -> Toutes décisions architecturales
- `questions.md` -> Questions bloquantes entre agents
- `agents.md` (ce fichier) -> Définition des rôles

### Workflow
1. Agent claim task: update tasks.json status = in_progress + claimedFiles + locks.json
2. Agent code dans son parentRepo (pas dans shared sauf shared-agent)
3. Agent teste: `npm run build` doit passer
4. Agent update tasks.json: done[] + next[]
5. Agent release locks: vide claimedFiles de locks.json
6. Lead engineer review et merge via shared

## Current Status 2026-08-25

- Admin i18n audit + RTL + CSV export + Vitest: DONE (commit acb8ec4)
- Shared types: NEEDS SYNC (supabase/types.ts incomplet)
- Client i18n: TODO (beaucoup hardcoded)
- Peinture workspace: TODO (structure existe, pas branché)
- Modules/Subscriptions: TODO (panels de base existent)
- Security Center: TODO (table prête, UI pas branchée)
- Client Supabase migration: TODO (toujours localStorage MVP)
- Edge Functions: TODO
- Manual payments: TODO

## Environment Variables Required (Vercel)

Pour TOUS les projets:
```
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
```

Jamais utiliser service_role dans browser.

## Build Verification

Avant chaque livraison:
```bash
cd /home/user && npm run build
cd /home/user/artisanpro-admin && npm run build
```

## User Communication

User travaille depuis téléphone Android, deploy via GitHub + Vercel. Expliquer en Darija courte et pratique. Pas de promesses sans ZIP/build réel.
