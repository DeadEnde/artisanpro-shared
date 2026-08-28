// ArtisanPro Shared Supabase Types
// Synced with real Supabase schema: artisanpro-supabase-setup.sql + upgrades
// Generated 2026-08-25 - Source of truth

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          full_name: string;
          email: string | null;
          role: 'client' | 'admin';
          status: 'active' | 'blocked' | 'pending';
          company: string | null;
          phone: string | null;
          avatar_url: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          full_name?: string;
          email?: string | null;
          role?: 'client' | 'admin';
          status?: 'active' | 'blocked' | 'pending';
          company?: string | null;
          phone?: string | null;
          avatar_url?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: Partial<Database['public']['Tables']['profiles']['Insert']>;
          Relationships: [];
      };
      modules: {
        Row: {
          id: string;
          slug: string;
          name_fr: string;
          name_en: string;
          name_ar: string;
          monthly_price: number;
          is_published: boolean;
          created_at: string;
        };
        Insert: Omit<Database['public']['Tables']['modules']['Row'], 'id' | 'created_at'>;
        Update: Partial<Database['public']['Tables']['modules']['Insert']>;
          Relationships: [];
      };
      app_sessions: {
        Row: {
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
        };
        Insert: {
          id?: string;
          user_id: string;
          device_name?: string;
          is_active?: boolean;
          started_at?: string;
          last_seen_at?: string;
          ended_at?: string | null;
          browser?: string | null;
          os?: string | null;
          device_type?: string | null;
          user_agent?: string | null;
          status?: 'active' | 'expired' | 'forced_logout' | 'ended';
        };
        Update: Partial<Database['public']['Tables']['app_sessions']['Insert']>;
          Relationships: [];
      };
      user_modules: {
        Row: {
          id: string;
          user_id: string;
          module_id: string;
          status: 'active' | 'paused' | 'expired' | 'revoked' | 'pending';
          starts_at: string;
          expires_at: string | null;
          source: 'manual' | 'stripe' | 'admin_grant';
          granted_by: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          module_id: string;
          status?: 'active' | 'paused' | 'expired' | 'revoked' | 'pending';
          starts_at?: string;
          expires_at?: string | null;
          source?: 'manual' | 'stripe' | 'admin_grant';
          granted_by?: string | null;
          created_at?: string;
        };
        Update: Partial<Database['public']['Tables']['user_modules']['Insert']>;
          Relationships: [];
      };
      subscriptions: {
        Row: {
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
        };
        Insert: {
          id?: string;
          user_id: string;
          plan_name: string;
          amount?: number;
          currency?: string;
          status?: 'pending' | 'active' | 'paused' | 'cancelled' | 'expired';
          payment_source?: 'manual' | 'stripe';
          starts_at?: string;
          expires_at?: string | null;
          created_by?: string | null;
          created_at?: string;
        };
        Update: Partial<Database['public']['Tables']['subscriptions']['Insert']>;
          Relationships: [];
      };
      admin_activity_logs: {
        Row: {
          id: string;
          admin_id: string | null;
          action: string;
          target_user_id: string | null;
          metadata: Record<string, unknown>;
          created_at: string;
        };
        Insert: {
          id?: string;
          admin_id?: string | null;
          action: string;
          target_user_id?: string | null;
          metadata?: Record<string, unknown>;
          created_at?: string;
        };
        Update: Partial<Database['public']['Tables']['admin_activity_logs']['Insert']>;
          Relationships: [];
      };
      security_logs: {
        Row: {
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
        };
        Insert: {
          id?: string;
          occurred_at?: string;
          app: 'client' | 'admin';
          event: 'login_success' | 'login_failed' | 'access_denied' | 'account_blocked' | 'logout' | 'forced_logout';
          email?: string | null;
          user_id?: string | null;
          provider?: 'google' | 'email' | null;
          device_type?: string | null;
          browser?: string | null;
          os?: string | null;
          ip_hash?: string | null;
          reason?: string | null;
          metadata?: Record<string, unknown>;
        };
        Update: Partial<Database['public']['Tables']['security_logs']['Insert']>;
          Relationships: [];
      };

      clients: {
        Row: {
          id: string;
          user_id: string;
          name: string;
          phone: string | null;
          city: string | null;
          email: string | null;
          address: string | null;
          notes: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          name: string;
          phone?: string | null;
          city?: string | null;
          email?: string | null;
          address?: string | null;
          notes?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: Partial<Database['public']['Tables']['clients']['Insert']>;
          Relationships: [];
      };
      projects: {
        Row: {
          id: string;
          user_id: string;
          client_id: string | null;
          name: string;
          module: string;
          status: string;
          city: string | null;
          address: string | null;
          notes: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          client_id?: string | null;
          name: string;
          module?: string;
          status?: string;
          city?: string | null;
          address?: string | null;
          notes?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: Partial<Database['public']['Tables']['projects']['Insert']>;
          Relationships: [];
      };
      quotes: {
        Row: {
          id: string;
          user_id: string;
          project_id: string | null;
          client_id: string | null;
          number: string;
          title: string;
          area: number | null;
          liters: number | null;
          total: number | null;
          status: string;
          validity_date: string | null;
          payment_terms: string | null;
          notes: string | null;
          terms: string | null;
          metadata: Record<string, unknown>;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          project_id?: string | null;
          client_id?: string | null;
          number: string;
          title?: string;
          area?: number | null;
          liters?: number | null;
          total?: number | null;
          status?: string;
          validity_date?: string | null;
          payment_terms?: string | null;
          notes?: string | null;
          terms?: string | null;
          metadata?: Record<string, unknown>;
          created_at?: string;
          updated_at?: string;
        };
        Update: Partial<Database['public']['Tables']['quotes']['Insert']>;
          Relationships: [];
      };
      paint_calculations: {
        Row: {
          id: string;
          user_id: string;
          name: string;
          area: number;
          coats: number;
          yield_rate: number;
          waste_percent: number;
          paint_price: number;
          liters: number | null;
          total: number | null;
          room_type: string | null;
          ceiling: boolean | null;
          doors_trims: boolean | null;
          interior_exterior: string | null;
          wall_condition: string | null;
          metadata: Record<string, unknown>;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          name?: string;
          area: number;
          coats?: number;
          yield_rate?: number;
          waste_percent?: number;
          paint_price?: number;
          liters?: number | null;
          total?: number | null;
          room_type?: string | null;
          ceiling?: boolean | null;
          doors_trims?: boolean | null;
          interior_exterior?: string | null;
          wall_condition?: string | null;
          metadata?: Record<string, unknown>;
          created_at?: string;
          updated_at?: string;
        };
        Update: Partial<Database['public']['Tables']['paint_calculations']['Insert']>;
          Relationships: [];
      };

      content_sections: {
        Row: {
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
        };
        Insert: Omit<Database['public']['Tables']['content_sections']['Row'], 'id' | 'created_at' | 'updated_at'> & { id?: string; created_at?: string; updated_at?: string };
        Update: Partial<Database['public']['Tables']['content_sections']['Insert']>;
          Relationships: [];
      };
      seo_metadata: {
        Row: {
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
        };
        Insert: Omit<Database['public']['Tables']['seo_metadata']['Row'], 'id' | 'created_at' | 'updated_at'> & { id?: string; created_at?: string; updated_at?: string };
        Update: Partial<Database['public']['Tables']['seo_metadata']['Insert']>;
          Relationships: [];
      };
    };
    Views: {
      module_entitlements: {
        Row: {
          user_id: string;
          module_slug: string;
          status: string;
          starts_at: string;
          expires_at: string | null;
          is_unlocked: boolean;
        };
          Relationships: [];
      };
    };
    Functions: {
      is_admin: {
        Args: Record<string, never>;
        Returns: boolean;
      };
      claim_single_session: {
        Args: { p_device_name?: string };
        Returns: string;
      };
      is_session_active: {
        Args: { p_session_id: string };
        Returns: boolean;
      };
      heartbeat_session: {
        Args: { p_session_id: string };
        Returns: boolean;
      };
      end_own_session: {
        Args: { p_session_id: string };
        Returns: void;
      };
      admin_force_logout_session: {
        Args: { p_session_id: string };
        Returns: void;
      };
      admin_set_user_status: {
        Args: { p_user_id: string; p_status: string };
        Returns: void;
      };
      admin_set_module_access: {
        Args: {
          p_user_id: string;
          p_module_slug: string;
          p_status: string;
          p_expires_at: string | null;
        };
        Returns: void;
      };
      admin_set_subscription_status: {
        Args: {
          p_user_id: string;
          p_plan_name: string;
          p_status: string;
          p_expires_at: string | null;
          p_amount: number;
        };
        Returns: void;
      };
      cleanup_security_logs: {
        Args: Record<string, never>;
        Returns: void;
      };
    };
  };
}
