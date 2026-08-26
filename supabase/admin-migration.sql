-- =============================================================================
-- ArtisanPro ADMIN DATABASE MIGRATION (consolidated)
-- =============================================================================
-- Created by client-agent on user request (2026-08-26).
-- Consolidates the 5 legacy SQL files from the workspace zip into ONE
-- idempotent migration for the ADMIN app:
--   1. artisanpro-supabase-setup.sql          (base tables + RPCs + RLS)
--   2. artisanpro-session-security-upgrade.sql (heartbeat, force logout)
--   3. artisanpro-security-logs.sql            (security_logs + cleanup)
--   4. artisanpro-module-subscription-upgrade.sql (paused status, view, RPC)
--   5. artisanpro-admin-profile-update.sql     (company/phone/avatar)
--
-- RUN ORDER:
--   1. supabase/admin-migration.sql   (this file - core + admin)
--   2. supabase/client-migration.sql  (client data tables, by shared-agent)
--
-- Contract: shared/supabase/types.ts is the source of truth.
-- This file matches it exactly:
--   Tables:  profiles, modules, app_sessions, user_modules, subscriptions,
--            admin_activity_logs, security_logs
--   View:    module_entitlements
--   Functions: is_admin, claim_single_session, is_session_active,
--            heartbeat_session, end_own_session, admin_force_logout_session,
--            admin_set_user_status, admin_set_module_access,
--            admin_set_subscription_status, cleanup_security_logs,
--            handle_new_user (trigger)
--
-- Safe to re-run: uses IF NOT EXISTS / CREATE OR REPLACE / DROP ... IF EXISTS.
-- =============================================================================

create extension if not exists pgcrypto;

-- =============================================================================
-- 1) TABLES
-- =============================================================================

-- Profiles: one row per auth user (created automatically by trigger).
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null default 'Nouveau client',
  email text unique,
  role text not null default 'client' check (role in ('client','admin')),
  status text not null default 'active' check (status in ('active','blocked','pending')),
  company text,
  phone text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
-- Legacy installs: add the editable business columns.
alter table public.profiles
  add column if not exists company text,
  add column if not exists phone text,
  add column if not exists avatar_url text;

-- Modules catalog.
create table if not exists public.modules (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  name_fr text not null,
  name_en text not null,
  name_ar text not null,
  monthly_price numeric(10,2) not null default 0,
  is_published boolean not null default true,
  created_at timestamptz not null default now()
);

insert into public.modules (slug,name_fr,name_en,name_ar,monthly_price,is_published)
values ('peinture','Peinture','Painting','الصباغة',99,true),
       ('carrelage','Carrelage','Tiling','التبليط',119,false)
on conflict (slug) do nothing;

-- Application sessions (single active session per user, forced logout support).
create table if not exists public.app_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  device_name text not null default 'Unknown device',
  is_active boolean not null default true,
  started_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  ended_at timestamptz,
  browser text,
  os text,
  device_type text,
  user_agent text,
  status text not null default 'active'
);
-- Legacy installs: add the session-tracking columns.
alter table public.app_sessions
  add column if not exists browser text,
  add column if not exists os text,
  add column if not exists device_type text,
  add column if not exists user_agent text,
  add column if not exists status text not null default 'active';
alter table public.app_sessions drop constraint if exists app_sessions_status_check;
alter table public.app_sessions add constraint app_sessions_status_check
  check (status in ('active','expired','forced_logout','ended'));
create unique index if not exists one_active_session_per_user
  on public.app_sessions(user_id) where is_active=true;

-- Per-user module access.
create table if not exists public.user_modules (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  module_id uuid not null references public.modules(id) on delete cascade,
  status text not null default 'active',
  starts_at timestamptz not null default now(),
  expires_at timestamptz,
  source text not null default 'manual' check (source in ('manual','stripe','admin_grant')),
  granted_by uuid references public.profiles(id),
  created_at timestamptz not null default now(),
  unique(user_id,module_id)
);
-- Widen the status check (adds paused/pending, legacy installs included).
alter table public.user_modules drop constraint if exists user_modules_status_check;
alter table public.user_modules add constraint user_modules_status_check
  check (status in ('active','paused','expired','revoked','pending'));

-- Manual subscriptions (Stripe later - Phase 4).
create table if not exists public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  plan_name text not null,
  amount numeric(10,2) not null default 0,
  currency text not null default 'MAD',
  status text not null default 'active',
  payment_source text not null default 'manual' check (payment_source in ('manual','stripe')),
  starts_at timestamptz not null default now(),
  expires_at timestamptz,
  created_by uuid references public.profiles(id),
  created_at timestamptz not null default now()
);
-- Widen the status check (adds paused, legacy installs included).
alter table public.subscriptions drop constraint if exists subscriptions_status_check;
alter table public.subscriptions add constraint subscriptions_status_check
  check (status in ('pending','active','paused','cancelled','expired'));

-- Admin audit trail.
create table if not exists public.admin_activity_logs (
  id uuid primary key default gen_random_uuid(),
  admin_id uuid references public.profiles(id),
  action text not null,
  target_user_id uuid references public.profiles(id),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- Security audit logs (client + admin). Insert only from secure backend/Edge
-- Functions - browser clients must NOT insert directly.
create table if not exists public.security_logs (
  id uuid primary key default gen_random_uuid(),
  occurred_at timestamptz not null default now(),
  app text not null check (app in ('client','admin')),
  event text not null check (event in ('login_success','login_failed','access_denied','account_blocked','logout','forced_logout')),
  email text,
  user_id uuid references public.profiles(id) on delete set null,
  provider text check (provider in ('google','email')),
  device_type text,
  browser text,
  os text,
  ip_hash text,
  reason text,
  metadata jsonb not null default '{}'::jsonb
);
create index if not exists security_logs_time_idx on public.security_logs(occurred_at desc);
create index if not exists security_logs_email_idx on public.security_logs(email);
create index if not exists security_logs_app_event_idx on public.security_logs(app,event);

-- =============================================================================
-- 2) TRIGGERS
-- =============================================================================

-- Each Auth user automatically receives a client profile.
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path=public as $$
begin
  insert into public.profiles (id,full_name,email)
  values (new.id,coalesce(new.raw_user_meta_data->>'full_name',new.raw_user_meta_data->>'name','Nouveau client'),new.email)
  on conflict (id) do update set email=excluded.email;
  return new;
end; $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Populate profiles for users created before this script.
insert into public.profiles (id,full_name,email)
select id,coalesce(raw_user_meta_data->>'full_name',raw_user_meta_data->>'name','Nouveau client'),email from auth.users
on conflict (id) do update set email=excluded.email;

-- updated_at maintenance (same function name as client-migration.sql).
create or replace function public.handle_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;
drop trigger if exists profiles_updated_at on public.profiles;
create trigger profiles_updated_at before update on public.profiles
  for each row execute procedure public.handle_updated_at();

-- =============================================================================
-- 3) HELPER + SESSION FUNCTIONS
-- =============================================================================

create or replace function public.is_admin()
returns boolean language sql stable security definer set search_path=public as $$
  select exists(select 1 from public.profiles where id=auth.uid() and role='admin' and status='active');
$$;

-- One active application session. A new device invalidates the previous device.
create or replace function public.claim_single_session(p_device_name text default 'Unknown device')
returns uuid language plpgsql security definer set search_path=public as $$
declare new_session uuid;
begin
  if auth.uid() is null then raise exception 'Not authenticated'; end if;
  if not exists(select 1 from profiles where id=auth.uid() and status='active') then raise exception 'Account is blocked or pending'; end if;
  update app_sessions set is_active=false,ended_at=now() where user_id=auth.uid() and is_active=true;
  insert into app_sessions(user_id,device_name) values(auth.uid(),left(coalesce(p_device_name,'Unknown device'),120)) returning id into new_session;
  return new_session;
end; $$;

create or replace function public.is_session_active(p_session_id uuid)
returns boolean language plpgsql security definer set search_path=public as $$
begin
  return exists(select 1 from app_sessions where id=p_session_id and user_id=auth.uid() and is_active=true);
end;
$$;

create or replace function public.heartbeat_session(p_session_id uuid)
returns boolean language plpgsql security definer set search_path=public as $$
begin
  update app_sessions set last_seen_at=now()
  where id=p_session_id and user_id=auth.uid() and is_active=true and status='active';
  return found;
end; $$;

create or replace function public.end_own_session(p_session_id uuid)
returns void language plpgsql security definer set search_path=public as $$
begin
  update app_sessions set is_active=false,status='ended',ended_at=now()
  where id=p_session_id and user_id=auth.uid();
end; $$;

create or replace function public.admin_force_logout_session(p_session_id uuid)
returns void language plpgsql security definer set search_path=public as $$
begin
  if not public.is_admin() then raise exception 'Admin permission required'; end if;
  update app_sessions set is_active=false,status='forced_logout',ended_at=now() where id=p_session_id;
  insert into admin_activity_logs(admin_id,action,metadata)
  values(auth.uid(),'force_logout_session',jsonb_build_object('session_id',p_session_id));
end; $$;

-- =============================================================================
-- 4) ADMIN RPCs (call only from the admin app while logged in as an admin)
-- =============================================================================

create or replace function public.admin_set_user_status(p_user_id uuid,p_status text)
returns void language plpgsql security definer set search_path=public as $$
begin
 if not is_admin() then raise exception 'Admin permission required'; end if;
 if p_status not in ('active','blocked','pending') then raise exception 'Invalid status'; end if;
 update profiles set status=p_status,updated_at=now() where id=p_user_id;
 if p_status='blocked' then update app_sessions set is_active=false,ended_at=now() where user_id=p_user_id and is_active=true; end if;
 insert into admin_activity_logs(admin_id,action,target_user_id,metadata) values(auth.uid(),'set_user_status',p_user_id,jsonb_build_object('status',p_status));
end; $$;

create or replace function public.admin_set_module_access(p_user_id uuid,p_module_slug text,p_status text,p_expires_at timestamptz default null)
returns void language plpgsql security definer set search_path=public as $$
declare mod_id uuid;
begin
 if not is_admin() then raise exception 'Admin permission required'; end if;
 select id into mod_id from modules where slug=p_module_slug;
 if mod_id is null then raise exception 'Module not found'; end if;
 insert into user_modules(user_id,module_id,status,expires_at,source,granted_by)
 values(p_user_id,mod_id,p_status,p_expires_at,'manual',auth.uid())
 on conflict(user_id,module_id) do update set status=excluded.status,expires_at=excluded.expires_at,granted_by=auth.uid();
 insert into admin_activity_logs(admin_id,action,target_user_id,metadata) values(auth.uid(),'set_module_access',p_user_id,jsonb_build_object('module',p_module_slug,'status',p_status,'expires_at',p_expires_at));
end; $$;

-- Securely create/update the manual subscription record used by the admin app.
create or replace function public.admin_set_subscription_status(
  p_user_id uuid,
  p_plan_name text,
  p_status text,
  p_expires_at timestamptz default null,
  p_amount numeric default 0
)
returns void language plpgsql security definer set search_path=public as $$
begin
  if not public.is_admin() then raise exception 'Admin permission required'; end if;
  if p_status not in ('pending','active','paused','cancelled','expired') then
    raise exception 'Invalid subscription status';
  end if;

  insert into public.subscriptions(user_id,plan_name,amount,status,payment_source,expires_at,created_by)
  values(p_user_id,p_plan_name,coalesce(p_amount,0),p_status,'manual',p_expires_at,auth.uid());

  insert into public.admin_activity_logs(admin_id,action,target_user_id,metadata)
  values(auth.uid(),'set_subscription_status',p_user_id,
    jsonb_build_object('plan',p_plan_name,'status',p_status,'expires_at',p_expires_at,'amount',p_amount));
end;
$$;

-- =============================================================================
-- 5) SECURITY LOGS CLEANUP (90-day retention)
-- =============================================================================

create or replace function public.cleanup_security_logs()
returns void language sql security definer set search_path=public as $$
  delete from public.security_logs where occurred_at < now() - interval '90 days';
$$;
-- Run manually once a month, or schedule with Supabase Cron:
-- select public.cleanup_security_logs();

-- =============================================================================
-- 6) ENTITLEMENTS VIEW
-- =============================================================================

-- Read-only view. Clients see only rows allowed by existing RLS.
create or replace view public.module_entitlements with (security_invoker = true) as
select um.user_id, m.slug as module_slug, um.status, um.starts_at, um.expires_at,
  case
    when um.status <> 'active' then false
    when um.expires_at is not null and um.expires_at <= now() then false
    else true
  end as is_unlocked
from public.user_modules um
join public.modules m on m.id=um.module_id;

-- =============================================================================
-- 7) ROW LEVEL SECURITY
-- =============================================================================

alter table public.profiles enable row level security;
alter table public.modules enable row level security;
alter table public.app_sessions enable row level security;
alter table public.user_modules enable row level security;
alter table public.subscriptions enable row level security;
alter table public.admin_activity_logs enable row level security;
alter table public.security_logs enable row level security;

drop policy if exists "profile self or admin read" on public.profiles;
create policy "profile self or admin read" on public.profiles
  for select using (id=auth.uid() or public.is_admin());

drop policy if exists "modules public read" on public.modules;
create policy "modules public read" on public.modules
  for select using (true);

drop policy if exists "session self or admin read" on public.app_sessions;
create policy "session self or admin read" on public.app_sessions
  for select using (user_id=auth.uid() or public.is_admin());

drop policy if exists "session owner heartbeat" on public.app_sessions;
create policy "session owner heartbeat" on public.app_sessions
  for update using (user_id=auth.uid()) with check (user_id=auth.uid());

drop policy if exists "module access self or admin read" on public.user_modules;
create policy "module access self or admin read" on public.user_modules
  for select using (user_id=auth.uid() or public.is_admin());

drop policy if exists "subscriptions self or admin read" on public.subscriptions;
create policy "subscriptions self or admin read" on public.subscriptions
  for select using (user_id=auth.uid() or public.is_admin());

drop policy if exists "logs admin only" on public.admin_activity_logs;
create policy "logs admin only" on public.admin_activity_logs
  for select using (public.is_admin());

drop policy if exists "admins read security logs" on public.security_logs;
create policy "admins read security logs" on public.security_logs
  for select using (public.is_admin());

-- =============================================================================
-- 8) ADMIN BOOTSTRAP
-- =============================================================================
-- AFTER YOUR FIRST LOGIN (Google or email), promote your account:
-- update public.profiles set role='admin' where email='YOUR_ADMIN_EMAIL@gmail.com';
