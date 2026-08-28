// ArtisanPro Shared Content & SEO Constants
// Matches supabase/content-seo.sql

export const CONTENT_TABLES = {
  SECTIONS: 'content_sections',
  SEO: 'seo_metadata',
} as const;

/** Public pages managed from the admin Content & SEO panel. */
export const PUBLIC_PAGE_SLUGS = ['home', 'calculateur-peinture', 'tarifs', 'lead'] as const;

export type PublicPageSlugValue = (typeof PUBLIC_PAGE_SLUGS)[number];
