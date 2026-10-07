-- ============================================================================
-- ArtisanPro — user_settings (Sprint 2, tâche `settings-supabase-sync`)
-- ============================================================================
-- Objectif : les réglages suivent le compte sur tous les appareils.
--   localStorage = cache hors-ligne instantané (jamais supprimé)
--   user_settings = source de vérité distante
--
-- RUN ORDER : après supabase/admin-migration.sql et supabase/client-migration.sql
-- Idempotent : peut être rejoué sans erreur.
--
-- Le propriétaire doit appliquer ce fichier au projet Supabase (Q6/Q15) :
--   supabase db execute --file supabase/user-settings.sql
--   — ou — copier/coller dans l'éditeur SQL du dashboard Supabase.
-- ============================================================================

create table if not exists public.user_settings (
  user_id              uuid primary key references auth.users(id) on delete cascade,
  company_name         text,
  company_logo         text,          -- URL publique Supabase Storage (ou dataURL de secours)
  phone                text,
  city                 text,
  full_name            text,
  avatar_url           text,          -- URL publique Supabase Storage (ou dataURL de secours)
  default_signature    text,
  default_vat          numeric(5,2) default 20,
  default_margin       numeric(5,2) default 30,
  quote_prefix         text          default 'DEV',
  validity_days        integer       default 30,
  payment_terms        text,
  monthly_revenue_goal numeric(12,2) default 20000,
  updated_at           timestamptz   default now()
);

-- Garde-fous : des valeurs aberrantes ne doivent jamais arriver en base.
alter table public.user_settings drop constraint if exists user_settings_vat_check;
alter table public.user_settings add  constraint user_settings_vat_check
  check (default_vat is null or (default_vat >= 0 and default_vat <= 30));

alter table public.user_settings drop constraint if exists user_settings_margin_check;
alter table public.user_settings add  constraint user_settings_margin_check
  check (default_margin is null or (default_margin >= 0 and default_margin < 90));

alter table public.user_settings drop constraint if exists user_settings_goal_check;
alter table public.user_settings add  constraint user_settings_goal_check
  check (monthly_revenue_goal is null or monthly_revenue_goal >= 0);

-- ---------------------------------------------------------------------------
-- updated_at : maintenu par trigger, jamais par le client
-- ---------------------------------------------------------------------------
create or replace function public.touch_user_settings()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists user_settings_touch on public.user_settings;
create trigger user_settings_touch
  before update on public.user_settings
  for each row execute function public.touch_user_settings();

-- ---------------------------------------------------------------------------
-- RLS — chacun ne voit et ne modifie QUE sa propre ligne
-- ---------------------------------------------------------------------------
alter table public.user_settings enable row level security;

drop policy if exists "user_settings: own row select" on public.user_settings;
create policy "user_settings: own row select" on public.user_settings
  for select using (user_id = auth.uid());

drop policy if exists "user_settings: own row insert" on public.user_settings;
create policy "user_settings: own row insert" on public.user_settings
  for insert with check (user_id = auth.uid());

drop policy if exists "user_settings: own row update" on public.user_settings;
create policy "user_settings: own row update" on public.user_settings
  for update using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Pas de policy delete : un utilisateur ne supprime pas ses réglages, il les vide.

drop policy if exists "user_settings: admin read all" on public.user_settings;
create policy "user_settings: admin read all" on public.user_settings
  for select using (public.is_admin());

-- ---------------------------------------------------------------------------
-- Storage — bucket `branding` pour logo et avatar (option Q16 (c))
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('branding', 'branding', true, 2097152,
        array['image/png','image/jpeg','image/webp','image/svg+xml'])
on conflict (id) do update
  set public             = excluded.public,
      file_size_limit    = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;

-- Convention de chemin : branding/<user_id>/logo.<ext> et branding/<user_id>/avatar.<ext>
drop policy if exists "branding: public read" on storage.objects;
create policy "branding: public read" on storage.objects
  for select using (bucket_id = 'branding');

drop policy if exists "branding: own folder insert" on storage.objects;
create policy "branding: own folder insert" on storage.objects
  for insert to authenticated
  with check (bucket_id = 'branding' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists "branding: own folder update" on storage.objects;
create policy "branding: own folder update" on storage.objects
  for update to authenticated
  using (bucket_id = 'branding' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists "branding: own folder delete" on storage.objects;
create policy "branding: own folder delete" on storage.objects
  for delete to authenticated
  using (bucket_id = 'branding' and (storage.foldername(name))[1] = auth.uid()::text);

-- ============================================================================
-- Vérification rapide après application
-- ============================================================================
--   select * from pg_policies where tablename = 'user_settings';
--   select id, public, file_size_limit from storage.buckets where id = 'branding';
--   insert into public.user_settings (user_id) values (auth.uid())
--     on conflict (user_id) do nothing returning *;
-- ============================================================================
