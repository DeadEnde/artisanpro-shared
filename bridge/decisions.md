# Decisions

- The active scope is the admin app; client code must remain untouched.
- The parent repository is `Artissan-Pro-Admin`.
- The bridge files were initialized because the checked-out shared repository did not contain them.
- The current admin app passes `npm run build` before any code change.

- The Admin i18n audit keeps the existing Supabase auth/RPC flow and adds only localized presentation, validation, filters, and confirmation UI.
- The shared locale provider is consumed by the Admin app; no Client repository files were edited.

- The Admin i18n and RTL audit was completed in parent commit `acb8ec4`; all source changes remain Admin-scoped.

- The follow-up added a localized CSV report export and a Vitest test command without changing auth, Supabase contracts, or Client code.
- Live Supabase verification is intentionally deferred until environment variables are available.
