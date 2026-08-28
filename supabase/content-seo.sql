-- Content & SEO shared contract
create table if not exists public.content_sections (id uuid primary key default gen_random_uuid(), slug text unique not null, title_fr text not null, title_en text not null, title_ar text not null, body_fr text, body_en text, body_ar text, metadata jsonb default '{}'::jsonb, is_published boolean default true, created_at timestamptz default now(), updated_at timestamptz default now());
create table if not exists public.seo_metadata (id uuid primary key default gen_random_uuid(), page_slug text unique not null, title_fr text not null, title_en text not null, title_ar text not null, description_fr text, description_en text, description_ar text, created_at timestamptz default now(), updated_at timestamptz default now());
alter table public.content_sections enable row level security;
alter table public.seo_metadata enable row level security;

-- RLS policies (idempotent): public reads published content, admins manage all.
-- Requires the is_admin() security definer function from the setup migration.
drop policy if exists "public read published content_sections" on public.content_sections;
create policy "public read published content_sections" on public.content_sections
  for select using (is_published = true or public.is_admin());

drop policy if exists "admin manage content_sections" on public.content_sections;
create policy "admin manage content_sections" on public.content_sections
  for all using (public.is_admin()) with check (public.is_admin());

drop policy if exists "public read seo_metadata" on public.seo_metadata;
create policy "public read seo_metadata" on public.seo_metadata
  for select using (true or public.is_admin());

drop policy if exists "admin manage seo_metadata" on public.seo_metadata;
create policy "admin manage seo_metadata" on public.seo_metadata
  for all using (public.is_admin()) with check (public.is_admin());

-- Keep updated_at fresh on edits.
create or replace function public.touch_updated_at() returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

drop trigger if exists touch_content_sections on public.content_sections;
create trigger touch_content_sections before update on public.content_sections
  for each row execute function public.touch_updated_at();

drop trigger if exists touch_seo_metadata on public.seo_metadata;
create trigger touch_seo_metadata before update on public.seo_metadata
  for each row execute function public.touch_updated_at();
