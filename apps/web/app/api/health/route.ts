/**
 * GET /api/health -- the web app's own health report.
 *
 * Public, no auth. `post-deploy-health-check.yml` polls it after each deploy
 * and hourly, and fails on 503.
 *
 * The public body is aggregate only: one status word per dependency
 * (`ok | degraded | down`), a latency, and version strings. It never names an
 * environment variable, says which key is present or absent, lists providers,
 * or relays an error message -- an unauthenticated endpoint that enumerates
 * configuration is a map for an attacker and a leak of upstream error text.
 *
 *   db     -- `SELECT 1` through lib/db.ts. Unconfigured counts as degraded
 *             (the app runs on in-memory fallbacks), unreachable as down.
 *   api    -- `${NEXT_PUBLIC_API_URL}/health` with a 5 s timeout. `healthy`
 *             is ok, any other 2xx answer is degraded, non-2xx or no answer
 *             is down. Unconfigured is degraded.
 *   clerk  -- both keys present is ok, exactly one is down (proxy.ts disables
 *             Clerk entirely in that case), neither is degraded.
 *
 * HTTP 200 unless some dependency is down, then 503.
 *
 * Operators who need the detail (which Clerk key is missing, the database
 * error text, the API's services/features summary) send
 * `Authorization: Bearer ${HEALTH_DETAIL_TOKEN}`; the token is compared in
 * constant time and the extra fields appear under `details`. With no token
 * configured the detail view does not exist.
 */

import { timingSafeEqual } from 'node:crypto'

import { NextResponse } from 'next/server'

import pkg from '../../../package.json'
import { getSqlOrNull } from '../../../lib/db'

export const dynamic = 'force-dynamic'

const API_TIMEOUT_MS = 5_000

export type CheckStatus = 'ok' | 'degraded' | 'down'

interface PublicCheck {
  status: CheckStatus
  latencyMs?: number
  /** The dependency's own version string, when it reports one. */
  version?: string
}

interface HealthDetails {
  db: { configured: boolean; error?: string }
  api: {
    configured: boolean
    httpStatus?: number
    /** The API's own status word: healthy | degraded | unhealthy. */
    upstreamStatus?: string
    services?: { database?: string; redis?: string; llmProviders?: string[] }
    features?: Record<string, boolean>
    error?: string
  }
  clerk: { publishableKey: boolean; secretKey: boolean; customDomain: boolean }
}

export interface HealthReport {
  status: CheckStatus
  timestamp: string
  version: string
  commit: string | null
  environment: string | null
  checks: { db: PublicCheck; api: PublicCheck; clerk: PublicCheck }
  details?: HealthDetails
}

const elapsedMs = (start: number): number => Math.round((performance.now() - start) * 10) / 10

const errorMessage = (error: unknown): string =>
  error instanceof Error ? (error.name === 'TimeoutError' ? 'timeout' : error.message) : String(error)

async function checkDb(): Promise<{ check: PublicCheck; detail: HealthDetails['db'] }> {
  const sql = getSqlOrNull()
  if (!sql) return { check: { status: 'degraded' }, detail: { configured: false } }

  const start = performance.now()
  try {
    await sql.query('SELECT 1')
    return { check: { status: 'ok', latencyMs: elapsedMs(start) }, detail: { configured: true } }
  } catch (error) {
    return {
      check: { status: 'down', latencyMs: elapsedMs(start) },
      detail: { configured: true, error: errorMessage(error) },
    }
  }
}

type UpstreamHealth = {
  status?: unknown
  version?: unknown
  services?: {
    database?: { status?: unknown }
    redis?: { status?: unknown }
    llm_providers?: Record<string, { configured?: unknown }>
  }
  features?: Record<string, { available?: unknown }>
}

const asString = (value: unknown): string | undefined => (typeof value === 'string' ? value : undefined)

function summariseUpstream(body: UpstreamHealth): Pick<HealthDetails['api'], 'upstreamStatus' | 'services' | 'features'> {
  const features: Record<string, boolean> = {}
  for (const [name, value] of Object.entries(body.features ?? {})) {
    features[name] = value?.available === true
  }
  return {
    upstreamStatus: asString(body.status),
    services: {
      database: asString(body.services?.database?.status),
      redis: asString(body.services?.redis?.status),
      llmProviders: Object.entries(body.services?.llm_providers ?? {})
        .filter(([, value]) => value?.configured === true)
        .map(([name]) => name),
    },
    features,
  }
}

async function checkApi(): Promise<{ check: PublicCheck; detail: HealthDetails['api'] }> {
  const base = process.env.NEXT_PUBLIC_API_URL?.trim().replace(/\/$/, '')
  if (!base) return { check: { status: 'degraded' }, detail: { configured: false } }

  const start = performance.now()
  try {
    const response = await fetch(`${base}/health`, {
      cache: 'no-store',
      headers: { Accept: 'application/json' },
      signal: AbortSignal.timeout(API_TIMEOUT_MS),
    })
    const latencyMs = elapsedMs(start)
    let body: UpstreamHealth = {}
    try {
      body = (await response.json()) as UpstreamHealth
    } catch {
      // Not JSON: the status code still tells the story.
    }
    const summary = summariseUpstream(body)
    const status: CheckStatus = !response.ok ? 'down' : summary.upstreamStatus === 'healthy' ? 'ok' : 'degraded'
    const check: PublicCheck = { status, latencyMs }
    const version = asString(body.version)
    if (version) check.version = version
    return {
      check,
      detail: {
        configured: true,
        httpStatus: response.status,
        ...summary,
        ...(status === 'ok' ? {} : { error: response.ok ? `upstream reports ${summary.upstreamStatus ?? 'unknown'}` : `HTTP ${response.status}` }),
      },
    }
  } catch (error) {
    return {
      check: { status: 'down', latencyMs: elapsedMs(start) },
      detail: { configured: true, error: errorMessage(error) },
    }
  }
}

function checkClerk(): { check: PublicCheck; detail: HealthDetails['clerk'] } {
  const publishableKey = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.trim())
  const secretKey = Boolean(process.env.CLERK_SECRET_KEY?.trim())
  const status: CheckStatus = publishableKey && secretKey ? 'ok' : publishableKey || secretKey ? 'down' : 'degraded'
  return {
    check: { status },
    detail: { publishableKey, secretKey, customDomain: Boolean(process.env.NEXT_PUBLIC_CLERK_DOMAIN?.trim()) },
  }
}

/**
 * True when the request carries `Authorization: Bearer <HEALTH_DETAIL_TOKEN>`.
 * Constant-time comparison; a missing token on either side is simply false,
 * so an unconfigured deployment has no detail view at all.
 */
export function isDetailAuthorised(authorization: string | null, configuredToken = process.env.HEALTH_DETAIL_TOKEN): boolean {
  const expected = configuredToken?.trim()
  if (!expected || !authorization) return false
  const match = authorization.match(/^Bearer\s+(.+)$/i)
  if (!match) return false
  const presented = Buffer.from(match[1]!.trim(), 'utf8')
  const wanted = Buffer.from(expected, 'utf8')
  if (presented.length !== wanted.length) return false
  return timingSafeEqual(presented, wanted)
}

const WORST: CheckStatus[] = ['ok', 'degraded', 'down']
const worstOf = (statuses: CheckStatus[]): CheckStatus =>
  statuses.reduce((worst, status) => (WORST.indexOf(status) > WORST.indexOf(worst) ? status : worst), 'ok')

export async function GET(request: Request): Promise<NextResponse<HealthReport>> {
  const [db, api] = await Promise.all([checkDb(), checkApi()])
  const clerk = checkClerk()

  const checks = { db: db.check, api: api.check, clerk: clerk.check }
  const status = worstOf(Object.values(checks).map((check) => check.status))

  const report: HealthReport = {
    status,
    timestamp: new Date().toISOString(),
    version: process.env.NEXT_PUBLIC_APP_VERSION?.trim() || pkg.version,
    commit: process.env.VERCEL_GIT_COMMIT_SHA?.trim() || null,
    environment: process.env.VERCEL_ENV?.trim() || null,
    checks,
  }

  if (isDetailAuthorised(request.headers.get('authorization'))) {
    report.details = { db: db.detail, api: api.detail, clerk: clerk.detail }
  }

  return NextResponse.json(report, {
    status: status === 'down' ? 503 : 200,
    headers: { 'Cache-Control': 'no-store' },
  })
}
