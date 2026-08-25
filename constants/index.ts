// ArtisanPro Shared Constants
// Matches the Supabase schema - Synced 2026-08-25

export const APP_NAME = 'ArtisanPro';
export const APP_VERSION = '0.2.0';

export const CURRENCIES = {
  MAD: { symbol: 'MAD', name: 'Dirham marocain' },
  EUR: { symbol: '€', name: 'Euro' },
  USD: { symbol: '$', name: 'Dollar US' },
} as const;

export const PLANS = {
  DISCOVERY: { name: 'Découverte', nameEn: 'Discovery', nameAr: 'اكتشاف', price: 0, currency: 'MAD' },
  PRO: { name: 'Peinture Pro', nameEn: 'Painting Pro', nameAr: 'صباغة برو', price: 99, currency: 'MAD' },
  ENTERPRISE: { name: 'Entreprise', nameEn: 'Enterprise', nameAr: 'مؤسسة', price: 299, currency: 'MAD' },
} as const;

export const MODULES = {
  PEINTURE: { slug: 'peinture', nameFr: 'Peinture', nameEn: 'Painting', nameAr: 'الصباغة', price: 99, isPublished: true },
  CARRELAGE: { slug: 'carrelage', nameFr: 'Carrelage', nameEn: 'Tiling', nameAr: 'التبليط', price: 119, isPublished: false },
} as const;

export const LANGUAGES: { code: string; label: string; dir: 'ltr' | 'rtl' }[] = [
  { code: 'fr', label: 'Français', dir: 'ltr' },
  { code: 'en', label: 'English', dir: 'ltr' },
  { code: 'ar', label: 'العربية', dir: 'rtl' },
];

export const SESSION_STATUS = {
  ACTIVE: 'active',
  EXPIRED: 'expired',
  FORCED_LOGOUT: 'forced_logout',
  ENDED: 'ended',
} as const;

export const SECURITY_EVENTS = {
  LOGIN_SUCCESS: 'login_success',
  LOGIN_FAILED: 'login_failed',
  ACCESS_DENIED: 'access_denied',
  ACCOUNT_BLOCKED: 'account_blocked',
  LOGOUT: 'logout',
  FORCED_LOGOUT: 'forced_logout',
} as const;

export const USER_STATUS = {
  ACTIVE: 'active',
  BLOCKED: 'blocked',
  PENDING: 'pending',
} as const;

export const USER_ROLE = {
  CLIENT: 'client',
  ADMIN: 'admin',
} as const;

export const MODULE_STATUS = {
  ACTIVE: 'active',
  PAUSED: 'paused',
  EXPIRED: 'expired',
  REVOKED: 'revoked',
  PENDING: 'pending',
} as const;

export const SUBSCRIPTION_STATUS = {
  PENDING: 'pending',
  ACTIVE: 'active',
  PAUSED: 'paused',
  CANCELLED: 'cancelled',
  EXPIRED: 'expired',
} as const;

export const PAYMENT_SOURCE = {
  MANUAL: 'manual',
  STRIPE: 'stripe',
} as const;

export const MODULE_SOURCE = {
  MANUAL: 'manual',
  STRIPE: 'stripe',
  ADMIN_GRANT: 'admin_grant',
} as const;

export const ONLINE_THRESHOLD_MINUTES = 2;
export const HEARTBEAT_INTERVAL_MS = 60 * 1000;
export const SECURITY_LOG_RETENTION_DAYS = 90;
