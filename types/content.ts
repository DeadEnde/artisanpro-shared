// ArtisanPro Shared Content & SEO Types
// Matches supabase/content-seo.sql (content_sections + seo_metadata)

/** Known public pages that can carry SEO metadata. */
export type PublicPageSlug = 'home' | 'calculateur-peinture' | 'tarifs' | 'lead';

/** Editable localized content block rendered on public pages. */
export interface ContentSection {
  id: string;
  slug: string;
  title_fr: string;
  title_en: string;
  title_ar: string;
  body_fr: string | null;
  body_en: string | null;
  body_ar: string | null;
  metadata: Record<string, unknown>;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export type ContentSectionInsert = Omit<ContentSection, 'id' | 'created_at' | 'updated_at'> & {
  id?: string;
  created_at?: string;
  updated_at?: string;
};

export type ContentSectionUpdate = Partial<ContentSectionInsert>;

/** Per-page SEO title + description, one row per public page. */
export interface SeoMetadata {
  id: string;
  page_slug: string;
  title_fr: string;
  title_en: string;
  title_ar: string;
  description_fr: string | null;
  description_en: string | null;
  description_ar: string | null;
  created_at: string;
  updated_at: string;
}

export type SeoMetadataInsert = Omit<SeoMetadata, 'id' | 'created_at' | 'updated_at'> & {
  id?: string;
  created_at?: string;
  updated_at?: string;
};

export type SeoMetadataUpdate = Partial<SeoMetadataInsert>;
