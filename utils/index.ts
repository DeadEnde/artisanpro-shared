// ArtisanPro Shared Utilities

import type { Language } from '../types';

/**
 * Format currency amount with Intl.NumberFormat
 */
export function formatCurrency(amount: number, locale: Language = 'fr', currency: string = 'MAD'): string {
  const localeMap: Record<Language, string> = { fr: 'fr-MA', en: 'en-MA', ar: 'ar-MA' };
  try {
    return new Intl.NumberFormat(localeMap[locale], {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${amount} ${currency}`;
  }
}

/**
 * Format date based on language
 */
export function formatDate(date: string | Date, lang: Language = 'fr', options?: Intl.DateTimeFormatOptions): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const localeMap: Record<Language, string> = { fr: 'fr-FR', en: 'en-US', ar: 'ar-MA' };
  const defaults: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options,
  };
  try {
    return d.toLocaleDateString(localeMap[lang], defaults);
  } catch {
    return d.toLocaleDateString();
  }
}

/**
 * Get relative time string
 */
export function relativeTime(date: string | Date, lang: Language = 'fr'): string {
  const now = Date.now();
  const then = typeof date === 'string' ? new Date(date).getTime() : date.getTime();
  const diff = now - then;

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (lang === 'fr') {
    if (minutes < 1) return "À l'instant";
    if (minutes < 60) return `Il y a ${minutes} min`;
    if (hours < 24) return `Il y a ${hours}h`;
    return `Il y a ${days}j`;
  }

  if (lang === 'ar') {
    if (minutes < 1) return 'الآن';
    if (minutes < 60) return `منذ ${minutes} دقيقة`;
    if (hours < 24) return `منذ ${hours} ساعة`;
    return `منذ ${days} يوم`;
  }

  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes} min ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

/**
 * Check if user has active access to a module
 */
export function hasModuleAccess(status: string, expiresAt: string | null): boolean {
  if (status !== 'active') return false;
  if (expiresAt && new Date(expiresAt) < new Date()) return false;
  return true;
}

/**
 * Generate initials from name
 */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Get text direction for a language
 */
export function getDirection(lang: Language): 'ltr' | 'rtl' {
  return lang === 'ar' ? 'rtl' : 'ltr';
}
