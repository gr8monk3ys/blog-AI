/**
 * GET /api/health -- the web app's own health report.
 *
 * Public, no auth, no secrets: every value is a status word, a latency, a
 * version string or a boolean. `post-deploy-health-check.yml` polls it after
 * each deploy and hourly, and fails on 503.
 *
 * It reports each dependency the web app depends on at request time:
 *   db     -- `SELECT 1` through lib/db.ts when DATABASE_URL is set, else skipped.
 *   api    -- `${NEXT_PUBLIC_API_URL}/health` with a 5 s timeout, plus the
 *             services/features summary the API returns, so one request shows
 *             what the backend can actually do (LLM providers, research keys...).
 *   clerk  -- configured or not (both keys present). Booleans only.
 *
 * HTTP 200 when every configured dependency is ok (skipped counts as ok: an
 * unconfigured dependency is a deployment choice, not an outage), 503 otherwise.
 */

import { NextResponse } from 'next/server'

import pkg from '../../../package.json'
import { getSqlOrNull } from '../../../lib/db'

export const dynamic = 'force-dynamic'

const API_TIMEOUT_MS = 5_000

type CheckStatus = 'ok' | 'error' | 'skipped'

interface DbCheck {
  status: CheckStatus
  latencyMs?: number
  error?: string
}

interface ApiCheck {
  status: CheckStatus
  latencyMs?: number
  httpStatus?: number
  /** The API's own status word: healthy | degraded | unhealthy. */
  upstreamStatus?: string
  version?: string
  services?: {
    database?: string
    redis?: string
    llmProviders?: string[]
  }
  features?: Record<string, boolean>
  error?: string
}

interface ClerkCheck {
  status: CheckStatus
  configured: boolean
  publishableKey: boolean
  secretKey: boolean
  customDomain: boolean
}

export interface HealthReport {
  status: 'ok' | 'error'
  timestamp: string
  version: string
  commit: string | null
  environment: string | null
  checks: {
    db: DbCheck
    api: ApiCheck
    clerk: ClerkCheck
  }
}

const elapsedMs = (start: number): number => Math.round((performance.now() - start) * 10) / 10

const errorMessage = (error: unknown): string =>
  error instanceof Error ? error.name === 'TimeoutError' ? 'timeout' : error.message : String(error)

async function checkDb(): Promise<DbCheck> {
  const sql = getSqlOrNull()
  if (!sql) return { status: 'skipped' }

  const start = performance.now()
  try {
    await sql.query('SELECT 1')
    return { status: 'ok', latencyMs: elapsedMs(start) }
  } catch (error) {
    return { status: 'error', latencyMs: elapsedMs(start), error: errorMessage(error) }
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

function summariseUpstream(body: UpstreamHealth): Pick<ApiCheck, 'upstreamStatus' | 'version' | 'services' | 'features'> {
  const providers = body.services?.llm_providers ?? {}
  const features: Record<string, boolean> = {}
  for (const [name, value] of Object.entries(body.features ?? {})) {
    features[name] = value?.available === true
  }
  return {
    upstreamStatus: typeof body.status === 'string' ? body.status : undefined,
    version: typeof body.version === 'string' ? body.version : undefined,
    services: {
      database: typeof body.services?.database?.status === 'string' ? body.services.database.status : undefined,
      redis: typeof body.services?.redis?.status === 'string' ? body.services.redis.status : undefined,
      llmProviders: Object.entries(providers)
        .filter(([, value]) => value?.configured === true)
        .map(([name]) => name),
    },
    features,
  }
}

async function checkApi(): Promise<ApiCheck> {
  const base = process.env.NEXT_PUBLIC_API_URL?.trim().replace(/\/$/, '')
  if (!base) return { status: 'skipped' }

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
    const healthy = response.ok && summary.upstreamStatus === 'healthy'
    return {
      status: healthy ? 'ok' : 'error',
      latencyMs,
      httpStatus: response.status,
      ...summary,
      ...(healthy ? {} : { error: response.ok ? `upstream reports ${summary.upstreamStatus ?? 'unknown'}` : `HTTP ${response.status}` }),
    }
  } catch (error) {
    return { status: 'error', latencyMs: elapsedMs(start), error: errorMessage(error) }
  }
}

function checkClerk(): ClerkCheck {
  const publishableKey = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.trim())
  const secretKey = Boolean(process.env.CLERK_SECRET_KEY?.trim())
  const configured = publishableKey && secretKey
  // Exactly one key present is a misconfiguration (proxy.ts disables Clerk
  // entirely in that case), not an unconfigured dependency.
  const status: CheckStatus = configured ? 'ok' : publishableKey || secretKey ? 'error' : 'skipped'
  return {
    status,
    configured,
    publishableKey,
    secretKey,
    customDomain: Boolean(process.env.NEXT_PUBLIC_CLERK_DOMAIN?.trim()),
  }
}

export async function GET(): Promise<NextResponse<HealthReport>> {
  const [db, api] = await Promise.all([checkDb(), checkApi()])
  const clerk = checkClerk()

  const checks = { db, api, clerk }
  const failing = Object.values(checks).some((check) => check.status === 'error')

  const report: HealthReport = {
    status: failing ? 'error' : 'ok',
    timestamp: new Date().toISOString(),
    version: process.env.NEXT_PUBLIC_APP_VERSION?.trim() || pkg.version,
    commit: process.env.VERCEL_GIT_COMMIT_SHA?.trim() || null,
    environment: process.env.VERCEL_ENV?.trim() || null,
    checks,
  }

  return NextResponse.json(report, {
    status: failing ? 503 : 200,
    headers: { 'Cache-Control': 'no-store' },
  })
}
