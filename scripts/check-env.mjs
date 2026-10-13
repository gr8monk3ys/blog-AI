#!/usr/bin/env node
/**
 * Environment variable inventory and audit. Plain Node, no dependencies.
 *
 *   bun run env:check                    table of every variable the code reads
 *   bun run env:check -- --markdown      the same table as Markdown (docs/ENVIRONMENT.md)
 *   bun run env:check -- --json          machine-readable
 *   bun run env:check -- --check <file>  read a dotenv file (e.g. from `vercel env pull`)
 *                                        and report required variables it is missing
 *                                        [--env web|api|all]  default: inferred from the
 *                                        file name (.env.local -> web, .env -> api)
 *
 * Two sources of truth are compared on every run:
 *
 *   1. The code. `process.env.X` under apps/web (app code, not tests), the
 *      pydantic-settings fields in apps/api/src/config.py and `os.environ`
 *      reads under apps/api. This is what the runtime actually consults.
 *   2. The ENV_VARS table below: scope (web-build / web-runtime / api),
 *      required-for-production or not, and one line of meaning.
 *
 * A variable the code reads that the table does not know is reported and
 * fails the run (exit 1): add it to the table and to docs/ENVIRONMENT.md.
 * A variable the table knows that nothing reads is reported too, so the table
 * cannot keep promising knobs the code has dropped. `.env.example` and
 * `.env.local.example` are checked the same way (entries nothing reads).
 *
 * Values are never printed. Only names.
 */

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const WEB_DIR = path.join(ROOT, 'apps', 'web')
const API_DIR = path.join(ROOT, 'apps', 'api')

// ---------------------------------------------------------------------------
// The table. scope: which process reads it. required: needed for a production
// deployment to work (not merely for a feature). platform: set by Vercel / CI /
// Node itself, never by hand.
// ---------------------------------------------------------------------------

/** @typedef {'web-build' | 'web-runtime' | 'api'} Scope */

/**
 * @type {Record<string, { scope: Scope[]; required?: boolean; platform?: boolean; dev?: boolean; note: string }>}
 */
const ENV_VARS = {
  // --- Web: public (NEXT_PUBLIC_*, inlined at build time into client + server) ---
  NEXT_PUBLIC_API_URL: {
    scope: ['web-build', 'web-runtime'],
    required: true,
    note: 'FastAPI base URL. Production: https://blog-ai-api-gr8monk3ys-projects.vercel.app. next.config.mjs refuses a production build without it.',
  },
  NEXT_PUBLIC_WS_URL: {
    scope: ['web-build', 'web-runtime'],
    note: 'WebSocket base; derived from NEXT_PUBLIC_API_URL (https->wss) when unset.',
  },
  NEXT_PUBLIC_API_VERSION: {
    scope: ['web-build', 'web-runtime'],
    note: 'API path version segment. Default v1.',
  },
  NEXT_PUBLIC_API_KEY: {
    scope: ['web-build', 'web-runtime'],
    dev: true,
    note: 'Local-only API key fallback (X-API-Key) when Clerk is absent. Never set in production.',
  },
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: {
    scope: ['web-build', 'web-runtime'],
    required: true,
    note: 'Clerk publishable key (pk_test_/pk_live_). Without it every route is public (dev) or redirects to /auth?reason=auth-not-configured (prod).',
  },
  NEXT_PUBLIC_CLERK_DOMAIN: {
    scope: ['web-build', 'web-runtime'],
    note: 'Clerk custom domain; production uses clerk.vivancedata.com. Added to the CSP connect-src.',
  },
  NEXT_PUBLIC_SITE_URL: {
    scope: ['web-build', 'web-runtime'],
    note: 'Public origin (sitemap, RSS, Sentry allowUrls, metadataBase). Production falls back to https://blog-ai.vivancedata.com; set it anyway.',
  },
  NEXT_PUBLIC_SUPPORT_EMAIL: {
    scope: ['web-build', 'web-runtime'],
    note: 'Support inbox shown on error/404/pricing pages. Default support@lscaturchio.xyz (lib/support.ts).',
  },
  NEXT_PUBLIC_APP_VERSION: {
    scope: ['web-build', 'web-runtime'],
    note: 'Overrides the version /api/health reports (default: apps/web/package.json).',
  },
  NEXT_PUBLIC_SIGNUP_MODE: {
    scope: ['web-build', 'web-runtime'],
    note: 'open | waitlist | invite (lib/signup-mode.ts). Default open. Must match the Clerk dashboard sign-up mode.',
  },
  NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE: {
    scope: ['web-build', 'web-runtime'],
    note: 'Feature flag: /knowledge + nav link. Pair with the API\'s ENABLE_KNOWLEDGE_BASE. Default off.',
  },
  NEXT_PUBLIC_LLM_GEMINI: {
    scope: ['web-build', 'web-runtime'],
    note: 'Feature flag: advertise Gemini. Pair with GEMINI_API_KEY on the API. Default off (not configured in production).',
  },
  NEXT_PUBLIC_FEATURE_WEB_RESEARCH: {
    scope: ['web-build', 'web-runtime'],
    note: 'Feature flag: research mode, fact-check sources, SERP analysis. Pair with SERP/Tavily/Metaphor keys on the API. Default off.',
  },
  NEXT_PUBLIC_FEATURE_IMAGE_GENERATION: {
    scope: ['web-build', 'web-runtime'],
    note: 'Feature flag: /images. Pair with IMAGE_PROVIDER + OpenAI/Stability key on the API. Default off.',
  },
  NEXT_PUBLIC_FEATURE_PLAGIARISM_CHECK: {
    scope: ['web-build', 'web-runtime'],
    note: 'Feature flag: /plagiarism. Pair with Copyscape or Originality credentials on the API. Default off.',
  },
  NEXT_PUBLIC_FEATURE_SOCIAL_POSTING: {
    scope: ['web-build', 'web-runtime'],
    note: 'Feature flag: /social. Pair with Twitter/LinkedIn OAuth or BUFFER_ACCESS_TOKEN on the API. Default off.',
  },
  NEXT_PUBLIC_FEATURE_TEAMS: {
    scope: ['web-build', 'web-runtime'],
    note: 'Feature flag: /team organisations and invites (no mailer delivers invites yet). Default off.',
  },
  NEXT_PUBLIC_FEATURE_BILLING: {
    scope: ['web-build', 'web-runtime'],
    note: 'Feature flag: pricing, checkout, billing portal. Default ON (Stripe is live); set false to hide.',
  },
  NEXT_PUBLIC_SENTRY_DSN: {
    scope: ['web-build', 'web-runtime'],
    note: 'Browser/server/edge Sentry DSN. Reports only on a Vercel deployment (lib/sentry-env.ts).',
  },
  NEXT_PUBLIC_SENTRY_FORCE_ENABLE: {
    scope: ['web-build'],
    dev: true,
    note: '=1 reports Sentry from a non-Vercel build (use a throwaway DSN).',
  },
  NEXT_PUBLIC_SENTRY_FORCE_DISABLE: {
    scope: ['web-build'],
    note: '=1 kill switch: a deployed build stops reporting to Sentry.',
  },
  NEXT_PUBLIC_VERCEL_ENV: {
    scope: ['web-build', 'web-runtime'],
    platform: true,
    note: 'Mirror of VERCEL_ENV that next.config.mjs inlines for the browser bundle. Do not set by hand.',
  },

  // --- Web: server-only runtime ---
  CLERK_SECRET_KEY: {
    scope: ['web-runtime'],
    required: true,
    note: 'Clerk secret (sk_test_/sk_live_) for proxy.ts and route handlers. Clerk is disabled unless both keys are present.',
  },
  DATABASE_URL: {
    scope: ['web-runtime', 'api'],
    required: true,
    note: 'Neon Postgres (pooled). Web route handlers: history, brand profiles, templates, blog CMS. API: analytics, quotas, Stripe sync. Without it those fall back to memory.',
  },
  BLOG_ADMIN_KEY: {
    scope: ['web-runtime'],
    note: 'Shared secret protecting /api/blog-posts/* (x-admin-key or Bearer). Unset: those routes are closed.',
  },
  HEALTH_DETAIL_TOKEN: {
    scope: ['web-runtime'],
    note: 'Bearer token that unlocks the `details` block of GET /api/health (which key is missing, error text, API services). Unset: the public aggregate view is all there is.',
  },
  DEMO_DATA_ENABLED: {
    scope: ['web-runtime'],
    dev: true,
    note: 'Seeds demo data outside production (lib/server-mode.ts).',
  },
  SUPPRESS_PROXY_AUTH_WARNING: {
    scope: ['web-runtime'],
    dev: true,
    note: '=1 silences the "Clerk not configured" warning from proxy.ts in local runs.',
  },
  PLAYWRIGHT_TEST: {
    scope: ['web-runtime'],
    dev: true,
    note: '=1 set by the Playwright config; proxy.ts suppresses its auth warning under e2e.',
  },

  // --- Web: build-only ---
  SENTRY_ORG: { scope: ['web-build'], note: 'Sentry org slug for source-map upload.' },
  SENTRY_PROJECT: { scope: ['web-build'], note: 'Sentry project slug for source-map upload.' },
  SENTRY_AUTH_TOKEN: {
    scope: ['web-build'],
    note: 'Sentry auth token; without it source maps are not uploaded (build still passes).',
  },
  ANALYZE: { scope: ['web-build'], dev: true, note: '=true runs the bundle analyzer (`bun run analyze`).' },

  // --- Platform-provided (Vercel, CI, Node) ---
  VERCEL: { scope: ['web-build'], platform: true, note: 'Set to 1 by Vercel builds.' },
  VERCEL_ENV: {
    scope: ['web-build', 'web-runtime'],
    platform: true,
    note: 'production | preview | development on Vercel. Gates Sentry and the production-build env checks.',
  },
  VERCEL_URL: {
    scope: ['web-build', 'web-runtime'],
    platform: true,
    note: 'Per-deployment *.vercel.app host; the preview fallback for getBaseUrl().',
  },
  VERCEL_GIT_COMMIT_SHA: {
    scope: ['web-runtime'],
    platform: true,
    note: 'Deployed commit, reported by /api/health as `commit`.',
  },
  CI: { scope: ['web-build'], platform: true, note: 'Set by GitHub Actions; enables the production-build env checks together with VERCEL.' },
  NODE_ENV: { scope: ['web-build', 'web-runtime'], platform: true, note: 'Set by Next.js.' },
  NEXT_RUNTIME: { scope: ['web-runtime'], platform: true, note: 'nodejs | edge, set by Next.js (instrumentation.ts).' },

  // --- API: LLM providers ---
  OPENAI_API_KEY: {
    scope: ['api'],
    required: true,
    note: 'At least one of OPENAI_API_KEY / ANTHROPIC_API_KEY is required; /ready returns 503 without one.',
  },
  ANTHROPIC_API_KEY: { scope: ['api'], note: 'Claude provider. Configured in production.' },
  GEMINI_API_KEY: {
    scope: ['api'],
    note: 'Gemini provider. Not configured in production; the google-genai package is not in uv.lock (requirements-gemini.txt).',
  },
  OPENAI_MODEL: { scope: ['api'], note: 'Default OpenAI model.' },
  ANTHROPIC_MODEL: { scope: ['api'], note: 'Default Anthropic model.' },
  GEMINI_MODEL: { scope: ['api'], note: 'Default Gemini model.' },
  LLM_API_TIMEOUT: { scope: ['api'], note: 'Seconds per provider call.' },
  LLM_STREAMING_TIMEOUT: { scope: ['api'], note: 'Seconds for a streaming generation.' },
  LLM_RATE_LIMIT_ENABLED: { scope: ['api'], note: 'Per-operation provider rate limiting.' },
  LLM_RATE_LIMIT_PER_MINUTE: { scope: ['api'], note: 'Provider calls per minute.' },
  LLM_RATE_LIMIT_MAX_QUEUE: { scope: ['api'], note: 'Queued provider calls before rejecting.' },
  LLM_RATE_LIMIT_MAX_WAIT: { scope: ['api'], note: 'Seconds a queued call waits.' },
  BOOK_SECTION_WORKERS: { scope: ['api'], note: 'Parallel section writers for book generation.' },
  RESEARCH_CACHE_TTL_SECONDS: { scope: ['api'], note: 'Research result cache TTL.' },
  RESEARCH_CACHE_MAX_ENTRIES: { scope: ['api'], note: 'Research result cache size.' },

  // --- API: runtime / security ---
  ENVIRONMENT: {
    scope: ['api'],
    required: true,
    note: 'development | staging | production. Production strips localhost origins and exits if none remain.',
  },
  ALLOWED_ORIGINS: {
    scope: ['api'],
    required: true,
    note: 'Comma-separated CORS origins; production: https://blog-ai.vivancedata.com.',
  },
  DEV_API_KEY: { scope: ['api'], dev: true, note: 'Static API key accepted in development only.' },
  DEV_MODE: { scope: ['api'], dev: true, note: 'scripts/smoke_test.py: skip auth locally. (pytest does not read it; conftest.py sets DEV_API_KEY itself.)' },
  BLOGAI_BASE_URL: { scope: ['api'], dev: true, note: 'scripts/smoke_test.py: API base URL to probe.' },
  BLOGAI_API_KEY: { scope: ['api'], dev: true, note: 'scripts/smoke_test.py: API key for authenticated probes.' },
  BLOGAI_ORG_ID: { scope: ['api'], dev: true, note: 'scripts/smoke_test.py: organisation to probe.' },
  BLOGAI_TIMEOUT_SECONDS: { scope: ['api'], dev: true, note: 'scripts/smoke_test.py: per-request timeout.' },
  ENABLE_PERFORMANCE_ANALYTICS: { scope: ['api'], note: 'Mounts the performance-analytics router (needs db/migrations/009). Default false.' },
  ENABLE_CONTENT_VERSIONING: { scope: ['api'], note: 'Mounts the content-versions router (needs db/migrations/007). Default false.' },
  TRACKING_BASE_URL: { scope: ['api'], note: 'Public base URL for performance tracking pixels.' },
  TRACKING_SECRET_KEY: { scope: ['api'], note: 'HMAC secret for tracking pixel tokens.' },
  PORT: { scope: ['api'], platform: true, note: 'Listen port for `python server.py` on container hosts. Not used on Vercel.' },
  BACKEND_PORT: { scope: ['api'], dev: true, note: 'Local listen port when PORT is unset (default 8000).' },
  UVICORN_RELOAD: { scope: ['api'], dev: true, note: '=true enables auto-reload for `python server.py`.' },
  HTTPS_REDIRECT_ENABLED: { scope: ['api'], note: 'Redirect http->https (behind a TLS-terminating host leave off).' },
  SECURITY_ENABLED: { scope: ['api'], note: 'Security headers middleware.' },
  SECURITY_HSTS_ENABLED: { scope: ['api'], note: 'HSTS header (defaults on in production).' },
  SECURITY_HSTS_MAX_AGE: { scope: ['api'], note: 'HSTS max-age seconds.' },
  SECURITY_MAX_BODY_SIZE: { scope: ['api'], note: 'Request body limit in bytes.' },
  SECURITY_TRUST_REQUEST_ID: { scope: ['api'], note: 'Trust an inbound X-Request-ID.' },
  SECURITY_REQUEST_ID_PREFIX: { scope: ['api'], note: 'Prefix for generated request ids.' },
  SECURITY_CSP_POLICY: { scope: ['api'], note: 'Content-Security-Policy for API HTML responses (/docs).' },
  RATE_LIMIT_ENABLED: { scope: ['api'], note: 'Per-client rate limiting (Redis-backed when REDIS_URL is set, else in-memory per worker).' },
  RATE_LIMIT_GENERAL: { scope: ['api'], note: 'General requests per minute.' },
  RATE_LIMIT_GENERATION: { scope: ['api'], note: 'Generation requests per minute.' },
  RATE_LIMIT_GEN_FREE_PER_MINUTE: { scope: ['api'], note: 'Tier limit.' },
  RATE_LIMIT_GEN_FREE_PER_HOUR: { scope: ['api'], note: 'Tier limit.' },
  RATE_LIMIT_GEN_STARTER_PER_MINUTE: { scope: ['api'], note: 'Tier limit.' },
  RATE_LIMIT_GEN_STARTER_PER_HOUR: { scope: ['api'], note: 'Tier limit.' },
  RATE_LIMIT_GEN_PRO_PER_MINUTE: { scope: ['api'], note: 'Tier limit.' },
  RATE_LIMIT_GEN_PRO_PER_HOUR: { scope: ['api'], note: 'Tier limit.' },
  RATE_LIMIT_GEN_BUSINESS_PER_MINUTE: { scope: ['api'], note: 'Tier limit.' },
  RATE_LIMIT_GEN_BUSINESS_PER_HOUR: { scope: ['api'], note: 'Tier limit.' },
  LOG_LEVEL: { scope: ['api'], note: 'DEBUG | INFO | WARNING | ERROR | CRITICAL.' },
  LOG_FORMAT_JSON: { scope: ['api'], note: 'Structured JSON logs.' },
  REQUEST_LOGGING_ENABLED: { scope: ['api'], note: 'Per-request access log.' },
  APP_ENV: { scope: ['api'], note: 'Legacy alias consulted by src/utils/logging; prefer ENVIRONMENT.' },
  PYTHON_ENV: { scope: ['api'], note: 'Legacy alias consulted by src/utils/logging; prefer ENVIRONMENT.' },

  // --- API: database / cache / storage ---
  DATABASE_URL_DIRECT: {
    scope: ['api'],
    note: 'Neon direct (non-pooled) string: migrations and long-lived container backends. On Vercel use DATABASE_URL.',
  },
  DATABASE_POOL_MIN_SIZE: { scope: ['api'], note: 'asyncpg pool minimum.' },
  DATABASE_POOL_MAX_SIZE: { scope: ['api'], note: 'asyncpg pool maximum.' },
  REDIS_URL: {
    scope: ['api'],
    note: 'Shared rate limits, bulk jobs, caches. Not configured in production (health reports redis disconnected).',
  },
  CONVERSATION_STORAGE_DIR: { scope: ['api'], note: 'File fallback for conversations. Ephemeral on Vercel.' },
  API_KEY_STORAGE_PATH: { scope: ['api'], note: 'JSON file of issued API keys (scripts/create_api_key.py). Ephemeral on Vercel.' },
  USAGE_STORAGE_DIR: { scope: ['api'], note: 'File-based usage counters without DATABASE_URL. Ephemeral on Vercel.' },
  SUPABASE_URL: { scope: ['api'], note: 'Deprecated supabase-py fallback; unused when DATABASE_URL is set.' },
  SUPABASE_KEY: { scope: ['api'], note: 'Deprecated supabase-py fallback.' },
  SUPABASE_SERVICE_ROLE_KEY: { scope: ['api'], note: 'Deprecated supabase-py fallback.' },
  SUPABASE_SERVICE_KEY: { scope: ['api'], note: 'Deprecated supabase-py fallback (content versioning).' },

  // --- API: auth ---
  CLERK_JWKS_URL: {
    scope: ['api'],
    required: true,
    note: 'Clerk JWKS endpoint used to verify the web app\'s Bearer tokens.',
  },
  CLERK_JWT_ISSUER: { scope: ['api'], required: true, note: 'Expected `iss` of Clerk session tokens.' },
  CLERK_JWT_AUDIENCE: { scope: ['api'], note: 'Expected `aud`, when the Clerk template sets one.' },

  // --- API: billing ---
  STRIPE_SECRET_KEY: { scope: ['api'], note: 'Enables payments (/health features.payments). Live in production.' },
  STRIPE_WEBHOOK_SECRET: { scope: ['api'], note: 'Verifies Stripe webhook signatures.' },
  STRIPE_PRICE_ID_STARTER_MONTHLY: { scope: ['api'], note: 'Stripe price id.' },
  STRIPE_PRICE_ID_STARTER_YEARLY: { scope: ['api'], note: 'Stripe price id.' },
  STRIPE_PRICE_ID_PRO_MONTHLY: { scope: ['api'], note: 'Stripe price id.' },
  STRIPE_PRICE_ID_PRO_YEARLY: { scope: ['api'], note: 'Stripe price id.' },
  STRIPE_PRICE_ID_BUSINESS_MONTHLY: { scope: ['api'], note: 'Stripe price id (Business tier, hidden unless ENABLE_BUSINESS_TIER).' },
  STRIPE_PRICE_ID_BUSINESS_YEARLY: { scope: ['api'], note: 'Stripe price id (Business tier).' },
  STRIPE_PRICE_ID_STARTER: { scope: ['api'], note: 'Legacy unsuffixed fallback for the monthly id; /health/stripe still checks these names.' },
  STRIPE_PRICE_ID_PRO: { scope: ['api'], note: 'Legacy unsuffixed fallback.' },
  STRIPE_PRICE_ID_BUSINESS: { scope: ['api'], note: 'Legacy unsuffixed fallback.' },
  ENABLE_BUSINESS_TIER: { scope: ['api'], note: 'Exposes the Business tier in /api/payments plans. Default false.' },
  RECONCILIATION_ENABLED: { scope: ['api'], note: 'Background Stripe subscription reconciliation.' },
  RECONCILIATION_INTERVAL_HOURS: { scope: ['api'], note: 'Stripe subscription reconciliation interval.' },

  // --- API: research / content features ---
  SERP_API_KEY: { scope: ['api'], note: 'Google SERP results (SerpAPI). Research mode needs SERP + Tavily + Metaphor; none set in production.' },
  SERP_PROVIDER: { scope: ['api'], note: 'serpapi | serpbase.' },
  SERPBASE_API_KEY: { scope: ['api'], note: 'SerpBase key when SERP_PROVIDER=serpbase.' },
  TAVILY_API_KEY: { scope: ['api'], note: 'Tavily web research.' },
  METAPHOR_API_KEY: { scope: ['api'], note: 'Metaphor/Exa neural search (legacy api.metaphor.systems host).' },
  SEC_API_API_KEY: { scope: ['api'], note: 'Declared in config.py; no code path reads it beyond has_any_research_api.' },
  IMAGE_PROVIDER: { scope: ['api'], note: 'openai | stability for /api/images.' },
  STABILITY_API_KEY: { scope: ['api'], note: 'Stability AI key when IMAGE_PROVIDER=stability.' },
  COPYSCAPE_USERNAME: { scope: ['api'], note: 'Plagiarism check (with COPYSCAPE_API_KEY).' },
  COPYSCAPE_API_KEY: { scope: ['api'], note: 'Plagiarism check.' },
  ORIGINALITY_API_KEY: { scope: ['api'], note: 'Plagiarism check alternative.' },
  PLAGIARISM_API_TIMEOUT: { scope: ['api'], note: 'Seconds per plagiarism provider call.' },
  WEBHOOK_SECRET: { scope: ['api'], note: 'HMAC secret for outbound webhooks (optional; per-subscription secrets otherwise).' },
  PUBLIC_API_URL: { scope: ['api'], note: 'Absolute API URL embedded in webhook/Zapier payloads.' },
  API_BASE_URL: { scope: ['api'], note: 'Legacy alias of PUBLIC_API_URL read by the extension route.' },
  APP_BASE_URL: { scope: ['api'], note: 'Public web origin used for SSO redirects and emails.' },

  // --- API: knowledge base ---
  ENABLE_KNOWLEDGE_BASE: { scope: ['api'], note: 'Mounts the knowledge-base router. Default false; pair with NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE.' },
  KB_VECTOR_STORE: { scope: ['api'], note: 'chromadb | pinecone | pgvector (pgvector is not implemented; chromadb/pinecone are not in uv.lock).' },
  KB_EMBEDDING_PROVIDER: { scope: ['api'], note: 'openai | voyage | cohere.' },
  KB_EMBEDDING_MODEL: { scope: ['api'], note: 'Embedding model id.' },
  KB_CHUNK_SIZE: { scope: ['api'], note: 'Chunk size in tokens.' },
  KB_CHUNK_OVERLAP: { scope: ['api'], note: 'Chunk overlap in tokens.' },
  KB_FREE_MAX_DOCS: { scope: ['api'], note: 'Tier quota.' },
  KB_FREE_MAX_STORAGE_MB: { scope: ['api'], note: 'Tier quota.' },
  KB_STARTER_MAX_DOCS: { scope: ['api'], note: 'Tier quota.' },
  KB_STARTER_MAX_STORAGE_MB: { scope: ['api'], note: 'Tier quota.' },
  PINECONE_API_KEY: { scope: ['api'], note: 'Pinecone vector store.' },
  PINECONE_ENVIRONMENT: { scope: ['api'], note: 'Pinecone environment/region.' },
  PINECONE_INDEX_NAME: { scope: ['api'], note: 'Pinecone index.' },
  CHROMA_PERSIST_PATH: { scope: ['api'], note: 'Chroma on-disk path.' },
  VOYAGE_API_KEY: { scope: ['api'], note: 'Voyage embeddings.' },
  COHERE_API_KEY: { scope: ['api'], note: 'Cohere embeddings.' },

  // --- API: SSO (routers are always mounted; SAML defaults are placeholders) ---
  SAML_SP_ENTITY_ID: { scope: ['api'], note: 'SAML SP entity id (default a placeholder https://api.example.com URL).' },
  SAML_SP_ACS_URL: { scope: ['api'], note: 'SAML assertion consumer URL.' },
  SAML_SP_CERT: { scope: ['api'], note: 'SAML SP certificate (PEM string).' },
  SAML_SP_CERT_PATH: { scope: ['api'], note: 'SAML SP certificate file.' },
  SAML_SP_PRIVATE_KEY: { scope: ['api'], note: 'SAML SP private key (PEM string).' },
  SAML_SP_KEY_PATH: { scope: ['api'], note: 'SAML SP private key file.' },

  // --- API: social publishing ---
  SOCIAL_SCHEDULER_ENABLED: { scope: ['api'], note: 'In-process scheduler (in-memory; src/social/worker.py is never launched).' },
  SOCIAL_WORKER_POLL_INTERVAL: { scope: ['api'], note: 'Scheduler poll seconds.' },
  SOCIAL_WORKER_BATCH_SIZE: { scope: ['api'], note: 'Posts per scheduler tick.' },
  SOCIAL_WORKER_MAX_CONCURRENT: { scope: ['api'], note: 'Concurrent publishes.' },
  SOCIAL_WEBHOOK_URL: { scope: ['api'], note: 'Callback for publish results.' },
  TWITTER_CLIENT_ID: { scope: ['api'], note: 'Twitter OAuth 2.' },
  TWITTER_CLIENT_SECRET: { scope: ['api'], note: 'Twitter OAuth 2.' },
  TWITTER_API_KEY: { scope: ['api'], note: 'Twitter OAuth 1.0a (media upload).' },
  TWITTER_API_SECRET: { scope: ['api'], note: 'Twitter OAuth 1.0a.' },
  LINKEDIN_CLIENT_ID: { scope: ['api'], note: 'LinkedIn OAuth.' },
  LINKEDIN_CLIENT_SECRET: { scope: ['api'], note: 'LinkedIn OAuth.' },
  BUFFER_ACCESS_TOKEN: { scope: ['api'], note: 'Buffer publishing (covers Facebook/Instagram, which have no direct OAuth here).' },

  // --- API: observability ---
  SENTRY_DSN: {
    scope: ['api'],
    note: 'API Sentry DSN. Initialises only with RAILWAY_ENVIRONMENT_NAME or SENTRY_FORCE_ENABLE=1 - on Vercel the latter is needed.',
  },
  SENTRY_ENVIRONMENT: { scope: ['api'], note: 'Tag only; does not enable Sentry.' },
  SENTRY_FORCE_ENABLE: { scope: ['api'], note: '=1 report from a host that is not Railway (Vercel included).' },
  SENTRY_FORCE_DISABLE: { scope: ['api'], note: '=1 kill switch.' },
  SENTRY_TRACES_SAMPLE_RATE: { scope: ['api'], note: '0.0-1.0.' },
  SENTRY_PROFILES_SAMPLE_RATE: { scope: ['api'], note: '0.0-1.0.' },
  SENTRY_RELEASE: { scope: ['api'], note: 'Release tag; default blog-ai@<pyproject version>.' },
  SERVER_NAME: { scope: ['api'], note: 'Sentry server_name tag.' },
  RAILWAY_ENVIRONMENT_NAME: { scope: ['api'], platform: true, note: 'Set by Railway only; the API\'s deployed-host signal for Sentry.' },
  RAILWAY_ENVIRONMENT: { scope: ['api'], platform: true, note: 'Older Railway alias of the above.' },
}

// ---------------------------------------------------------------------------
// Discovery: what the code reads.
// ---------------------------------------------------------------------------

const SKIP_DIRS = new Set(['node_modules', '.next', '.venv', 'venv', '__pycache__', 'coverage', 'playwright-report', 'test-results', 'dist', 'build', '.turbo'])

function* walk(dir, { skipDirs = SKIP_DIRS, skipPaths = [] } = {}) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (skipPaths.some((skip) => full === skip || full.startsWith(skip + path.sep))) continue
    if (entry.isDirectory()) {
      if (skipDirs.has(entry.name)) continue
      yield* walk(full, { skipDirs, skipPaths })
    } else if (entry.isFile()) {
      yield full
    }
  }
}

function collect(regex, text, group = 1) {
  const names = new Set()
  for (const match of text.matchAll(regex)) names.add(match[group])
  return names
}

/** `process.env.X` in web app code (tests, e2e and the Playwright config excluded). */
function discoverWeb() {
  const found = new Map() // name -> Set(relative files)
  const skipPaths = ['tests', 'e2e', 'playwright.config.ts', 'vitest.config.ts'].map((p) => path.join(WEB_DIR, p))
  for (const file of walk(WEB_DIR, { skipPaths })) {
    if (!/\.(ts|tsx|mjs|cjs|js)$/.test(file)) continue
    const text = fs.readFileSync(file, 'utf8')
    for (const name of collect(/process\.env\.([A-Z][A-Z0-9_]*)/g, text)) {
      if (!found.has(name)) found.set(name, new Set())
      found.get(name).add(path.relative(ROOT, file).replaceAll(path.sep, '/'))
    }
  }
  return found
}

/** pydantic-settings fields in src/config.py (env var = upper-cased field name) plus os.environ reads. */
function discoverApi() {
  const found = new Map()
  const add = (name, file) => {
    if (!found.has(name)) found.set(name, new Set())
    found.get(name).add(path.relative(ROOT, file).replaceAll(path.sep, '/'))
  }

  const configPath = path.join(API_DIR, 'src', 'config.py')
  const config = fs.readFileSync(configPath, 'utf8')
  let currentClass = null
  for (const line of config.split(/\r?\n/)) {
    const cls = line.match(/^class\s+(\w+)\(BaseSettings\)/)
    if (cls) {
      currentClass = cls[1]
      continue
    }
    if (/^class\s/.test(line)) currentClass = null
    if (!currentClass || currentClass === 'Settings') continue
    const field = line.match(/^ {4}([a-z][a-z0-9_]*)\s*:\s*([^=]+)=/)
    if (!field) continue
    if (/Settings\b/.test(field[2])) continue // nested groups on the aggregator
    add(field[1].toUpperCase(), configPath)
  }

  // `os.environ.get("X")`, `os.getenv("X")`, `os.environ["X"]` and the small
  // local helpers server.py wraps them in (`_env_true("X")`). Root scripts/*.py
  // are API tooling (smoke test, API-key issuing) and count as API reads.
  const READ = /(?:os\.)?(?:environ\.get|getenv|environ\[|_env_true|_env_int|_env_bool|_env_float)\(?\s*["']([A-Z][A-Z0-9_]*)["']/g
  const roots = [path.join(API_DIR, 'server.py'), path.join(API_DIR, 'app'), path.join(API_DIR, 'src'), path.join(ROOT, 'scripts')]
  for (const root of roots) {
    if (!fs.existsSync(root)) continue
    const files = fs.statSync(root).isDirectory() ? [...walk(root)] : [root]
    for (const file of files) {
      if (!file.endsWith('.py')) continue
      const text = fs.readFileSync(file, 'utf8')
      for (const name of collect(READ, text)) add(name, file)
    }
  }
  return found
}

/** Variable names declared (set or commented out) in an example dotenv file. */
function exampleNames(file) {
  if (!fs.existsSync(file)) return new Set()
  return collect(/^#?\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=/gm, fs.readFileSync(file, 'utf8'))
}

/** Names assigned in a real dotenv file. Values are read and discarded. */
function dotenvNames(file) {
  const names = new Set()
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const line = raw.trim()
    if (!line || line.startsWith('#')) continue
    const match = line.match(/^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=/)
    if (match) names.add(match[1])
  }
  return names
}

// ---------------------------------------------------------------------------
// Reporting
// ---------------------------------------------------------------------------

const SCOPE_LABEL = { 'web-build': 'web build', 'web-runtime': 'web runtime', api: 'API' }

function kind(meta) {
  if (meta.platform) return 'platform'
  if (meta.required) return 'required'
  if (meta.dev) return 'dev only'
  return 'optional'
}

function rows() {
  return Object.entries(ENV_VARS)
    .map(([name, meta]) => ({ name, scope: meta.scope, kind: kind(meta), note: meta.note }))
    .sort((a, b) => a.name.localeCompare(b.name))
}

function printTable(list) {
  const width = Math.max(...list.map((r) => r.name.length))
  const scopeWidth = Math.max(...list.map((r) => r.scope.map((s) => SCOPE_LABEL[s]).join(', ').length))
  for (const row of list) {
    const scope = row.scope.map((s) => SCOPE_LABEL[s]).join(', ')
    console.log(`${row.name.padEnd(width)}  ${row.kind.padEnd(9)}  ${scope.padEnd(scopeWidth)}  ${row.note}`)
  }
}

function printMarkdown(list) {
  const sections = [
    ['Web app, public (`NEXT_PUBLIC_*`, inlined at build time)', (r) => r.name.startsWith('NEXT_PUBLIC_')],
    ['Web app, server and build only', (r) => !r.name.startsWith('NEXT_PUBLIC_') && !r.scope.includes('api')],
    ['API (FastAPI)', (r) => r.scope.includes('api') && !r.scope.some((s) => s.startsWith('web'))],
    ['Shared by web and API', (r) => r.scope.includes('api') && r.scope.some((s) => s.startsWith('web')) && !r.name.startsWith('NEXT_PUBLIC_')],
  ]
  for (const [title, filter] of sections) {
    const subset = list.filter(filter)
    if (subset.length === 0) continue
    console.log(`### ${title}\n`)
    console.log('| Variable | Kind | Read by | Meaning |')
    console.log('|----------|------|---------|---------|')
    for (const row of subset) {
      const scope = row.scope.map((s) => SCOPE_LABEL[s]).join(', ')
      console.log(`| \`${row.name}\` | ${row.kind} | ${scope} | ${row.note.replaceAll('|', '\\|')} |`)
    }
    console.log('')
  }
}

function audit({ quiet = false } = {}) {
  const web = discoverWeb()
  const api = discoverApi()
  const read = new Map([...web, ...api].map(([name, files]) => [name, files]))
  for (const [name, files] of api) {
    if (web.has(name)) for (const f of files) read.get(name).add(f)
  }

  const undocumented = [...read.keys()].filter((name) => !ENV_VARS[name]).sort()
  const unread = Object.keys(ENV_VARS).filter((name) => !read.has(name)).sort()

  const exampleOnly = []
  for (const [label, file] of [['.env.example', path.join(ROOT, '.env.example')], ['.env.local.example', path.join(ROOT, '.env.local.example')]]) {
    for (const name of exampleNames(file)) {
      if (!read.has(name)) exampleOnly.push(`${name} (${label})`)
    }
  }
  exampleOnly.sort()

  let failed = false
  if (undocumented.length > 0) {
    failed = true
    console.error(`\nRead by code but missing from scripts/check-env.mjs ENV_VARS (${undocumented.length}):`)
    for (const name of undocumented) console.error(`  ${name}  <- ${[...read.get(name)].join(', ')}`)
  }
  if (unread.length > 0 && !quiet) {
    console.error(`\nIn ENV_VARS but nothing in the code reads them (${unread.length}); remove or fix the table:`)
    for (const name of unread) console.error(`  ${name}`)
    failed = true
  }
  if (exampleOnly.length > 0 && !quiet) {
    console.error(`\nIn an example file but not read by any code (${exampleOnly.length}); stale or a typo:`)
    for (const entry of exampleOnly) console.error(`  ${entry}`)
  }
  return { read, undocumented, unread, exampleOnly, failed }
}

function inferScopes(file, explicit) {
  if (explicit === 'web') return ['web-build', 'web-runtime']
  if (explicit === 'api') return ['api']
  if (explicit === 'all') return ['web-build', 'web-runtime', 'api']
  const base = path.basename(file)
  if (/\.env\.local/.test(base) || /web/.test(file)) return ['web-build', 'web-runtime']
  if (base === '.env' || /api/.test(file)) return ['api']
  return ['web-build', 'web-runtime', 'api']
}

function check(file, explicitEnv) {
  if (!fs.existsSync(file)) {
    console.error(`No such file: ${file}`)
    return 2
  }
  const scopes = inferScopes(file, explicitEnv)
  const present = dotenvNames(file)
  const inScope = Object.entries(ENV_VARS).filter(([, meta]) => meta.scope.some((s) => scopes.includes(s)) && !meta.platform)
  const missingRequired = inScope.filter(([name, meta]) => meta.required && !present.has(name)).map(([name]) => name)
  const missingOptional = inScope.filter(([name, meta]) => !meta.required && !meta.dev && !present.has(name)).map(([name]) => name)
  const unknown = [...present].filter((name) => !ENV_VARS[name]).sort()
  const outOfScope = [...present].filter((name) => ENV_VARS[name] && !ENV_VARS[name].scope.some((s) => scopes.includes(s))).sort()

  console.log(`Checking ${path.relative(ROOT, file) || file} against: ${scopes.map((s) => SCOPE_LABEL[s]).join(', ')}`)
  console.log(`  ${present.size} variable(s) set (values not shown)`)
  if (missingRequired.length > 0) {
    console.log(`\nMISSING required (${missingRequired.length}):`)
    for (const name of missingRequired) console.log(`  ${name}  - ${ENV_VARS[name].note}`)
  } else {
    console.log('\nAll required variables for this scope are set.')
  }
  if (missingOptional.length > 0) {
    console.log(`\nNot set, optional (${missingOptional.length}): ${missingOptional.join(', ')}`)
  }
  if (outOfScope.length > 0) {
    console.log(`\nSet here but read by a different process (${outOfScope.length}): ${outOfScope.join(', ')}`)
  }
  if (unknown.length > 0) {
    console.log(`\nSet here but unknown to the code (${unknown.length}; typo or stale?): ${unknown.join(', ')}`)
  }
  return missingRequired.length > 0 ? 1 : 0
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function main(argv) {
  const args = [...argv]
  const flag = (name) => {
    const i = args.indexOf(name)
    if (i === -1) return undefined
    const value = args[i + 1]
    args.splice(i, 2)
    return value ?? true
  }
  const has = (name) => {
    const i = args.indexOf(name)
    if (i === -1) return false
    args.splice(i, 1)
    return true
  }

  if (has('--help') || has('-h')) {
    console.log(fs.readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n').slice(1, 30).map((l) => l.replace(/^ \*\s?/, '')).join('\n'))
    return 0
  }

  const checkFile = flag('--check')
  const env = flag('--env')
  const json = has('--json')
  const markdown = has('--markdown')

  if (typeof checkFile === 'string') {
    const result = audit({ quiet: true })
    const code = check(path.resolve(checkFile), env)
    return result.failed ? Math.max(code, 1) : code
  }

  const list = rows()
  if (json) {
    const result = audit({ quiet: true })
    console.log(JSON.stringify({ variables: list, undocumented: result.undocumented, unread: result.unread, exampleOnly: result.exampleOnly }, null, 2))
    return result.failed ? 1 : 0
  }
  if (markdown) {
    printMarkdown(list)
    const result = audit({ quiet: true })
    return result.failed ? 1 : 0
  }

  printTable(list)
  const result = audit()
  console.log(`\n${list.length} documented variable(s); ${result.read.size} read by code.`)
  if (result.failed) {
    console.error('\nFAILED: the inventory and the code disagree (see above).')
    return 1
  }
  console.log('OK: every variable the code reads is documented, and every documented variable is read.')
  return 0
}

process.exitCode = main(process.argv.slice(2))
