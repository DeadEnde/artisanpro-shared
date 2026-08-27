-- Content & SEO shared contract
create table if not exists public.content_sections (id uuid primary key default gen_random_uuid(), slug text unique not null, title_fr text not null, title_en text not null, title_ar text not null, body_fr text, body_en text, body_ar text, metadata jsonb default '{}'::jsonb, is_published boolean default true, created_at timestamptz default now(), updated_at timestamptz default now());
create table if not exists public.seo_metadata (id uuid primary key default gen_random_uuid(), page_slug text unique not null, title_fr text not null, title_en text not null, title_ar text not null, description_fr text, description_en text, description_ar text, created_at timestamptz default now(), updated_at timestamptz default now());
alter table public.content_sections enable row level security;
alter table public.seo_metadata enable row level security;
