// ArtisanPro Shared Supabase Types
// Database schema types for Supabase

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          email: string;
          full_name: string | null;
          company: string | null;
          phone: string | null;
          role: 'admin' | 'user' | 'artisan';
          status: 'active' | 'blocked' | 'pending';
          created_at: string;
          updated_at: string;
        };
        Insert: Omit<Database['public']['Tables']['profiles']['Row'], 'created_at' | 'updated_at'>;
        Update: Partial<Database['public']['Tables']['profiles']['Insert']>;
      };
      modules: {
        Row: {
          id: string;
          slug: string;
          name: string;
          description: string | null;
          price: number;
          currency: string;
          created_at: string;
        };
        Insert: Omit<Database['public']['Tables']['modules']['Row'], 'id' | 'created_at'>;
        Update: Partial<Database['public']['Tables']['modules']['Insert']>;
      };
      module_entitlements: {
        Row: {
          id: string;
          user_id: string;
          module_slug: string;
          status: 'active' | 'paused' | 'revoked' | 'locked';
          expires_at: string | null;
          created_at: string;
        };
        Insert: Omit<Database['public']['Tables']['module_entitlements']['Row'], 'id' | 'created_at'>;
        Update: Partial<Database['public']['Tables']['module_entitlements']['Insert']>;
      };
      subscriptions: {
        Row: {
          id: string;
          user_id: string;
          plan_name: string;
          status: 'active' | 'paused' | 'cancelled' | 'expired';
          amount: number;
          currency: string;
          expires_at: string | null;
          created_at: string;
        };
        Insert: Omit<Database['public']['Tables']['subscriptions']['Row'], 'id' | 'created_at'>;
        Update: Partial<Database['public']['Tables']['subscriptions']['Insert']>;
      };
    };
    Functions: {
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
    };
  };
}
