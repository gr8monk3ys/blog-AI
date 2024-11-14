export function isProductionEnv(): boolean {
  return process.env.NODE_ENV === 'production'
}

export function canServeDemoData(): boolean {
  const explicit = process.env.DEMO_DATA_ENABLED
  if (explicit !== undefined) {
    return explicit === 'true'
  }
  // Default: allow in dev/test, disallow in production
  return !isProductionEnv()
}
