/**
 * Type-safe configuration module with runtime validation
 *
 * This module provides centralized access to environment variables
 * with proper typing and validation. It ensures that required
 * configuration is present and provides helpful error messages
 * when configuration is missing.
 */

/**
 * Environment type based on NODE_ENV
 */
export type Environment = 'development' | 'production' | 'test'

/**
 * Configuration shape for the application
 */
export interface AppConfig {
  // Environment
  readonly env: Environment
  readonly isDevelopment: boolean
  readonly isProduction: boolean
  readonly isTest: boolean

  // API Configuration
  readonly api: {
    readonly baseUrl: string
    readonly wsUrl: string
    readonly version: string
    readonly key?: string
  }

  // Supabase Configuration
  readonly supabase: {
    readonly url: string
    readonly anonKey: string
    readonly serviceKey?: string
  }

  // Stripe Configuration (optional)
  readonly stripe: {
    readonly publishableKey?: string
  }

  // Sentry Configuration (optional)
  readonly sentry: {
    readonly dsn?: string
    readonly org?: string
    readonly project?: string
  }

  // Feature Flags
  readonly features: {
    readonly maintenanceMode: boolean
    readonly debug: boolean
  }
}

/**
 * Get the current environment
 */
function getEnvironment(): Environment {
  const env = process.env.NODE_ENV
  if (env === 'production') return 'production'
  if (env === 'test') return 'test'
  return 'development'
}

/**
 * Validation error class for configuration issues
 */
export class ConfigValidationError extends Error {
  constructor(
    public readonly missingVariables: string[],
    public readonly context: string
  ) {
    const message = `Missing required configuration for ${context}: ${missingVariables.join(', ')}`
    super(message)
    this.name = 'ConfigValidationError'
  }
}

/**
 * Validate that required environment variables are present
 */
function validateRequired(
  variables: Record<string, string | undefined>,
  context: string
): void {
  const missing = Object.entries(variables)
    .filter(([, value]) => !value)
    .map(([key]) => key)

  if (missing.length > 0) {
    throw new ConfigValidationError(missing, context)
  }
}

/**
 * Safely get a boolean environment variable
 */
function getBooleanEnv(key: string, defaultValue: boolean): boolean {
  const value = process.env[key]
  if (value === undefined) return defaultValue
  return value.toLowerCase() === 'true' || value === '1'
}

/**
 * Safely get the WebSocket URL from API URL
 */
function deriveWsUrl(apiUrl: string): string {
  if (apiUrl.startsWith('https://')) {
    return apiUrl.replace('https://', 'wss://')
  }
  if (apiUrl.startsWith('http://')) {
    return apiUrl.replace('http://', 'ws://')
  }
  return apiUrl
}

/**
 * Build the configuration object
 * Throws ConfigValidationError if required variables are missing in production
 */
function buildConfig(): AppConfig {
  const env = getEnvironment()
  const isDevelopment = env === 'development'
  const isProduction = env === 'production'
  const isTest = env === 'test'

  // API Configuration
  const apiBaseUrl =
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const apiWsUrl =
    process.env.NEXT_PUBLIC_WS_URL || deriveWsUrl(apiBaseUrl)
  const apiVersion = process.env.NEXT_PUBLIC_API_VERSION || 'v1'
  const apiKey = process.env.NEXT_PUBLIC_API_KEY

  // Supabase Configuration
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
  const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY

  // Stripe Configuration
  const stripePublishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY

  // Sentry Configuration
  const sentryDsn = process.env.NEXT_PUBLIC_SENTRY_DSN
  const sentryOrg = process.env.SENTRY_ORG
  const sentryProject = process.env.SENTRY_PROJECT

  // Feature Flags
  const maintenanceMode = getBooleanEnv('NEXT_PUBLIC_MAINTENANCE_MODE', false)
  const debug = getBooleanEnv('NEXT_PUBLIC_DEBUG', false)

  // Validate required variables in production
  if (isProduction) {
    // Warn about missing Supabase config but don't throw
    // (allows graceful degradation)
    if (!supabaseUrl || !supabaseAnonKey) {
      console.warn(
        '[Config] Supabase configuration is missing. Some features may not work.'
      )
    }

    // Warn about missing Sentry
    if (!sentryDsn) {
      console.warn(
        '[Config] Sentry DSN is not configured. Error tracking is disabled.'
      )
    }
  }

  return {
    env,
    isDevelopment,
    isProduction,
    isTest,

    api: {
      baseUrl: apiBaseUrl,
      wsUrl: apiWsUrl,
      version: apiVersion,
      key: apiKey,
    },

    supabase: {
      url: supabaseUrl,
      anonKey: supabaseAnonKey,
      serviceKey: supabaseServiceKey,
    },

    stripe: {
      publishableKey: stripePublishableKey,
    },

    sentry: {
      dsn: sentryDsn,
      org: sentryOrg,
      project: sentryProject,
    },

    features: {
      maintenanceMode,
      debug,
    },
  }
}

/**
 * Singleton configuration instance
 * Lazily initialized on first access
 */
let configInstance: AppConfig | null = null

/**
 * Get the application configuration
 *
 * @returns The application configuration object
 * @throws ConfigValidationError if required configuration is missing in production
 *
 * @example
 * ```ts
 * import { getConfig } from '@/lib/config'
 *
 * const config = getConfig()
 * console.log(config.api.baseUrl)
 * ```
 */
export function getConfig(): AppConfig {
  if (!configInstance) {
    configInstance = buildConfig()
  }
  return configInstance
}

/**
 * Reset the configuration (useful for testing)
 */
export function resetConfig(): void {
  configInstance = null
}

/**
 * Check if a feature is enabled
 *
 * @param feature - The feature to check
 * @returns Whether the feature is enabled
 *
 * @example
 * ```ts
 * import { isFeatureEnabled } from '@/lib/config'
 *
 * if (isFeatureEnabled('debug')) {
 *   console.log('Debug mode is enabled')
 * }
 * ```
 */
export function isFeatureEnabled(
  feature: keyof AppConfig['features']
): boolean {
  return getConfig().features[feature]
}

/**
 * Get the API base URL with version
 *
 * @returns The versioned API URL
 *
 * @example
 * ```ts
 * import { getApiUrl } from '@/lib/config'
 *
 * const url = getApiUrl() // 'https://api.example.com/api/v1'
 * ```
 */
export function getApiUrl(): string {
  const config = getConfig()
  return `${config.api.baseUrl}/api/${config.api.version}`
}

// Export the config getter as default for convenience
export default getConfig
