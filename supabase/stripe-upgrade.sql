-- ============================================================================
-- ArtisanPro × Stripe — Phase auto-subscriptions (2026-08-29)
-- Profiles → stripe customer, subscriptions → stripe ids, webhook dedupe.
-- Idempotent: safe to re-run.
-- ============================================================================

-- 1) Stripe customer link on profiles
alter table public.profiles
  add column if not exists stripe_customer_id text;
create unique index if not exists profiles_stripe_customer_uidx
  on public.profiles (stripe_customer_id) where stripe_customer_id is not null;

-- 2) Stripe identifiers on subscriptions
alter table public.subscriptions
  add column if not exists stripe_subscription_id text,
  add column if not exists stripe_price_id text;
create unique index if not exists subscriptions_stripe_sub_uidx
  on public.subscriptions (stripe_subscription_id) where stripe_subscription_id is not null;

-- 3) Webhook idempotency (one row per Stripe event id, forever)
create table if not exists public.stripe_webhook_events (
  id text primary key,
  type text not null,
  created_at timestamptz not null default now()
);
alter table public.stripe_webhook_events enable row level security;
comment on table public.stripe_webhook_events is 'Stripe webhook dedupe (service-role only).';
