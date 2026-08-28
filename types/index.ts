// ArtisanPro Shared Types
// Matches the Supabase schema defined in artisanpro-supabase-setup.sql
// Used across Admin, Client, and API projects

export interface Profile {
  id: string;
  email: string | null;
  full_name: string;
  company: string | null;
  phone: string | null;
  avatar_url: string | null;
  role: 'client' | 'admin';
  status: 'active' | 'blocked' | 'pending';
  created_at: string;
  updated_at: string;
}

export interface Module {
  id: string;
  slug: string;
  name_fr: string;
  name_en: string;
  name_ar: string;
  monthly_price: number;
  is_published: boolean;
  created_at: string;
}

export interface UserModule {
  id: string;
  user_id: string;
  module_id: string;
  status: 'active' | 'paused' | 'expired' | 'revoked' | 'pending';
  starts_at: string;
  expires_at: string | null;
  source: 'manual' | 'stripe' | 'admin_grant';
  granted_by: string | null;
  created_at: string;
}

export interface ModuleEntitlement {
  user_id: string;
  module_slug: string;
  status: string;
  starts_at: string;
  expires_at: string | null;
  is_unlocked: boolean;
}

export interface Subscription {
  id: string;
  user_id: string;
  plan_name: string;
  amount: number;
  currency: string;
  status: 'pending' | 'active' | 'paused' | 'cancelled' | 'expired';
  payment_source: 'manual' | 'stripe';
  starts_at: string;
  expires_at: string | null;
  created_by: string | null;
  created_at: string;
}

export interface AppSession {
  id: string;
  user_id: string;
  device_name: string;
  is_active: boolean;
  started_at: string;
  last_seen_at: string;
  ended_at: string | null;
  browser: string | null;
  os: string | null;
  device_type: string | null;
  user_agent: string | null;
  status: 'active' | 'expired' | 'forced_logout' | 'ended';
}

export interface SecurityLog {
  id: string;
  occurred_at: string;
  app: 'client' | 'admin';
  event: 'login_success' | 'login_failed' | 'access_denied' | 'account_blocked' | 'logout' | 'forced_logout';
  email: string | null;
  user_id: string | null;
  provider: 'google' | 'email' | null;
  device_type: string | null;
  browser: string | null;
  os: string | null;
  ip_hash: string | null;
  reason: string | null;
  metadata: Record<string, unknown>;
}

export interface AdminActivityLog {
  id: string;
  admin_id: string | null;
  action: string;
  target_user_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export type Language = 'fr' | 'en' | 'ar';

export type AdminView = 'overview' | 'users' | 'modules' | 'plans' | 'security' | 'content' | 'settings';
export * from './content';
