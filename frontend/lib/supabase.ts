/**
 * Supabase Client Configuration
 *
 * Provides a singleton Supabase client with lazy initialization.
 * Uses service role key for server-side operations (full database access).
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js'
import type { Database } from '../types/database'

// Singleton instance
let supabaseInstance: SupabaseClient<Database> | null = null

/**
 * Check if Supabase is properly configured
 */
export function isSupabaseConfigured(): boolean {
  return !!(
    process.env.NEXT_PUBLIC_SUPABASE_URL &&
    process.env.SUPABASE_SERVICE_KEY
  )
}

/**
 * Get the Supabase client instance (lazy initialization)
 *
 * Uses service role key for full database access.
 * Only call this from server-side code (API routes, server components).
 */
export function getSupabase(): SupabaseClient<Database> {
  if (supabaseInstance) {
    return supabaseInstance
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY

  if (!supabaseUrl || !supabaseKey) {
    throw new Error(
      'Supabase configuration missing. Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.'
    )
  }

  supabaseInstance = createClient<Database>(supabaseUrl, supabaseKey, {
    auth: {
      // Disable session persistence for server-side usage
      persistSession: false,
      autoRefreshToken: false,
    },
  })

  return supabaseInstance
}

/**
 * Get a Supabase client for browser-side usage (anon key)
 *
 * Uses anon key with RLS policies for restricted access.
 * Safe to use in client components.
 */
export function getSupabaseBrowser(): SupabaseClient<Database> | null {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseAnonKey) {
    return null
  }

  return createClient<Database>(supabaseUrl, supabaseAnonKey)
}

// Error code for "no rows found" from PostgREST
export const SUPABASE_NO_ROWS_ERROR = 'PGRST116'

/**
 * Check if an error is a "no rows found" error
 */
export function isNoRowsError(error: unknown): boolean {
  if (error && typeof error === 'object' && 'code' in error) {
    return (error as { code: string }).code === SUPABASE_NO_ROWS_ERROR
  }
  return false
}
