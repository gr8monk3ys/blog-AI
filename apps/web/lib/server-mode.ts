export function isProductionEnv(): boolean {
  return process.env.NODE_ENV === 'production'
}

export function canServeDemoData(): boolean {
  return !isProductionEnv()
}
