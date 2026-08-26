-- ArtisanPro Client App Migration: clients, projects, quotes, paint_calculations
-- Run after artisanpro-supabase-setup.sql
-- Creates per-user RLS tables for client data

create extension if not exists pgcrypto;

-- Clients table
create table if not exists public.clients (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text not null,
  phone text,
  city text,
  email text,
  address text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists clients_user_id_idx on public.clients(user_id);
alter table public.clients enable row level security;
drop policy if exists "clients self or admin" on public.clients;
create policy "clients self or admin" on public.clients for all using (user_id = auth.uid() or public.is_admin()) with check (user_id = auth.uid() or public.is_admin());

-- Projects table
create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  client_id uuid references public.clients(id) on delete set null,
  name text not null,
  module text not null default 'peinture' check (module in ('peinture','carrelage')),
  status text not null default 'active' check (status in ('draft','active','completed','cancelled')),
  city text,
  address text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists projects_user_id_idx on public.projects(user_id);
create index if not exists projects_client_id_idx on public.projects(client_id);
alter table public.projects enable row level security;
drop policy if exists "projects self or admin" on public.projects;
create policy "projects self or admin" on public.projects for all using (user_id = auth.uid() or public.is_admin()) with check (user_id = auth.uid() or public.is_admin());

-- Quotes table
create table if not exists public.quotes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  project_id uuid references public.projects(id) on delete set null,
  client_id uuid references public.clients(id) on delete set null,
  number text not null,
  title text not null default 'Devis peinture',
  area numeric(10,2),
  liters numeric(10,2),
  total numeric(12,2),
  status text not null default 'draft' check (status in ('draft','sent','accepted','rejected','expired')),
  validity_date date,
  payment_terms text,
  notes text,
  terms text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists quotes_user_id_idx on public.quotes(user_id);
create index if not exists quotes_project_id_idx on public.quotes(project_id);
create index if not exists quotes_client_id_idx on public.quotes(client_id);
alter table public.quotes enable row level security;
drop policy if exists "quotes self or admin" on public.quotes;
create policy "quotes self or admin" on public.quotes for all using (user_id = auth.uid() or public.is_admin()) with check (user_id = auth.uid() or public.is_admin());

-- Paint calculations (saved library)
create table if not exists public.paint_calculations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text not null default 'Calcul peinture',
  area numeric(10,2) not null,
  coats int not null default 2,
  yield_rate numeric(6,2) not null default 10,
  waste_percent numeric(5,2) not null default 10,
  paint_price numeric(10,2) not null default 250,
  liters numeric(10,2),
  total numeric(12,2),
  room_type text,
  ceiling boolean default false,
  doors_trims boolean default false,
  interior_exterior text default 'interior' check (interior_exterior in ('interior','exterior')),
  wall_condition text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists paint_calcs_user_id_idx on public.paint_calculations(user_id);
alter table public.paint_calculations enable row level security;
drop policy if exists "paint_calculations self or admin" on public.paint_calculations;
create policy "paint_calculations self or admin" on public.paint_calculations for all using (user_id = auth.uid() or public.is_admin()) with check (user_id = auth.uid() or public.is_admin());

-- Updated_at trigger
create or replace function public.handle_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists clients_updated_at on public.clients;
create trigger clients_updated_at before update on public.clients for each row execute procedure public.handle_updated_at();
drop trigger if exists projects_updated_at on public.projects;
create trigger projects_updated_at before update on public.projects for each row execute procedure public.handle_updated_at();
drop trigger if exists quotes_updated_at on public.quotes;
create trigger quotes_updated_at before update on public.quotes for each row execute procedure public.handle_updated_at();
drop trigger if exists paint_calcs_updated_at on public.paint_calculations;
create trigger paint_calcs_updated_at before update on public.paint_calculations for each row execute procedure public.handle_updated_at();
