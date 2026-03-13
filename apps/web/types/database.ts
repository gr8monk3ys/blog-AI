/**
 * Supabase Database Types
 *
 * Auto-generated types for the database schema.
 * Regenerate with: npx supabase gen types typescript --project-id <project-id> > types/database.ts
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      // Generated content storage
      generated_content: {
        Row: {
          id: string
          created_at: string
          updated_at: string
          tool_id: string
          tool_name: string | null
          title: string | null
          inputs: Json
          output: string
          provider: string
          execution_time_ms: number
          user_hash: string | null
          is_favorite: boolean
        }
        Insert: {
          id?: string
          created_at?: string
          updated_at?: string
          tool_id: string
          tool_name?: string | null
          title?: string | null
          inputs: Json
          output: string
          provider: string
          execution_time_ms: number
          user_hash?: string | null
          is_favorite?: boolean
        }
        Update: {
          id?: string
          created_at?: string
          updated_at?: string
          tool_id?: string
          tool_name?: string | null
          title?: string | null
          inputs?: Json
          output?: string
          provider?: string
          execution_time_ms?: number
          user_hash?: string | null
          is_favorite?: boolean
        }
      }
      // Tool usage analytics
      tool_usage: {
        Row: {
          id: string
          tool_id: string
          count: number
          last_used_at: string
          created_at: string
        }
        Insert: {
          id?: string
          tool_id: string
          count?: number
          last_used_at?: string
          created_at?: string
        }
        Update: {
          id?: string
          tool_id?: string
          count?: number
          last_used_at?: string
          created_at?: string
        }
      }
      // Conversations (replacing file-based storage)
      conversations: {
        Row: {
          id: string
          created_at: string
          updated_at: string
          messages: Json
          metadata: Json | null
        }
        Insert: {
          id: string
          created_at?: string
          updated_at?: string
          messages: Json
          metadata?: Json | null
        }
        Update: {
          id?: string
          created_at?: string
          updated_at?: string
          messages?: Json
          metadata?: Json | null
        }
      }
      // Templates for reusable content presets
      templates: {
        Row: {
          id: string
          created_at: string
          updated_at: string
          name: string
          description: string | null
          slug: string
          tool_id: string
          preset_inputs: Json
          category: string
          tags: string[]
          is_public: boolean
          user_hash: string | null
          use_count: number
        }
        Insert: {
          id?: string
          created_at?: string
          updated_at?: string
          name: string
          description?: string | null
          slug: string
          tool_id: string
          preset_inputs?: Json
          category: string
          tags?: string[]
          is_public?: boolean
          user_hash?: string | null
          use_count?: number
        }
        Update: {
          id?: string
          created_at?: string
          updated_at?: string
          name?: string
          description?: string | null
          slug?: string
          tool_id?: string
          preset_inputs?: Json
          category?: string
          tags?: string[]
          is_public?: boolean
          user_hash?: string | null
          use_count?: number
        }
      }
      // Brand voice profiles for consistent content
      brand_profiles: {
        Row: {
          id: string
          created_at: string
          updated_at: string
          name: string
          slug: string
          tone_keywords: string[]
          writing_style: string
          example_content: string | null
          industry: string | null
          target_audience: string | null
          preferred_words: string[]
          avoid_words: string[]
          brand_values: string[]
          content_themes: string[]
          user_hash: string | null
          is_active: boolean
          is_default: boolean
        }
        Insert: {
          id?: string
          created_at?: string
          updated_at?: string
          name: string
          slug: string
          tone_keywords?: string[]
          writing_style?: string
          example_content?: string | null
          industry?: string | null
          target_audience?: string | null
          preferred_words?: string[]
          avoid_words?: string[]
          brand_values?: string[]
          content_themes?: string[]
          user_hash?: string | null
          is_active?: boolean
          is_default?: boolean
        }
        Update: {
          id?: string
          created_at?: string
          updated_at?: string
          name?: string
          slug?: string
          tone_keywords?: string[]
          writing_style?: string
          example_content?: string | null
          industry?: string | null
          target_audience?: string | null
          preferred_words?: string[]
          avoid_words?: string[]
          brand_values?: string[]
          content_themes?: string[]
          user_hash?: string | null
          is_active?: boolean
          is_default?: boolean
        }
      }
      // Blog posts for CMS-backed publishing
      blog_posts: {
        Row: {
          id: string
          created_at: string
          updated_at: string
          title: string
          slug: string
          excerpt: string | null
          body: string
          tags: string[]
          status: string
          published_at: string | null
          cover_image: string | null
          seo_title: string | null
          seo_description: string | null
        }
        Insert: {
          id?: string
          created_at?: string
          updated_at?: string
          title: string
          slug: string
          excerpt?: string | null
          body: string
          tags?: string[]
          status?: string
          published_at?: string | null
          cover_image?: string | null
          seo_title?: string | null
          seo_description?: string | null
        }
        Update: {
          id?: string
          created_at?: string
          updated_at?: string
          title?: string
          slug?: string
          excerpt?: string | null
          body?: string
          tags?: string[]
          status?: string
          published_at?: string | null
          cover_image?: string | null
          seo_title?: string | null
          seo_description?: string | null
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      // Increment tool usage count
      increment_tool_usage: {
        Args: { p_tool_id: string }
        Returns: void
      }
      // Get tool usage stats
      get_tool_stats: {
        Args: Record<PropertyKey, never>
        Returns: {
          tool_id: string
          count: number
          last_used_at: string
        }[]
      }
      // Toggle favorite status
      toggle_favorite: {
        Args: { content_id: string }
        Returns: boolean
      }
      // Set favorite status explicitly
      set_favorite: {
        Args: { content_id: string; favorite_status: boolean }
        Returns: boolean
      }
      // Increment template use count
      increment_template_use_count: {
        Args: { p_template_id: string }
        Returns: void
      }
      // Set default brand profile
      set_default_brand_profile: {
        Args: { p_profile_id: string; p_user_hash: string }
        Returns: void
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}
