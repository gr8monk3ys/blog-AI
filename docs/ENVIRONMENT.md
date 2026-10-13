# Environment Variables

Every variable the web app (`apps/web`) and the API (`apps/api`) read, with who reads it and
whether a production deployment needs it. The tables below are generated from the code and
from the table in `scripts/check-env.mjs`:

```bash
bun run env:check                      # same table in the terminal; fails if code and table disagree
bun run env:check -- --markdown        # regenerate the tables below
bun run env:check -- --check <file>    # e.g. a file from `vercel env pull`: lists missing required vars
bun run env:check -- --check .env --env api
```

Rules of thumb:

- `NEXT_PUBLIC_*` is inlined at **build** time into the client and server bundles. Set it for
  `bun run build` and in every Vercel environment, not only for `start`.
- The web app's server-only variables (`CLERK_SECRET_KEY`, `DATABASE_URL`, `BLOG_ADMIN_KEY`)
  live in `apps/web/.env.local` locally and in the Vercel `blog-ai` project in production.
- API variables live in the root `.env` locally (`apps/api/.env` is a symlink to it) and in the
  Vercel `blog-ai-api` project in production. See [DEPLOYMENT.md](./DEPLOYMENT.md) for what
  production actually runs.
- **Kind**: `required` = a production deployment does not work without it; `optional` = enables
  or tunes a feature; `dev only` = local or test use; `platform` = set by Vercel, CI or Node,
  never by hand.
- Feature flags (`NEXT_PUBLIC_FEATURE_*`, `NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE`,
  `NEXT_PUBLIC_LLM_GEMINI`) only control what the web app *says* (`apps/web/lib/features.ts`).
  The matching API key or `ENABLE_*` makes the feature *work*. Set both or neither.
- `NEXT_PUBLIC_API_KEY` is a local development fallback, never a production auth mechanism.

Start from:

```bash
cp .env.example .env
cp .env.local.example apps/web/.env.local
```

## Minimum to run locally

```bash
# .env
OPENAI_API_KEY=...                     # or ANTHROPIC_API_KEY
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000
# apps/web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Clerk is optional in development (every route is public without a publishable key). Without
`DATABASE_URL`, history, brand profiles, templates and analytics fall back to in-memory storage.

## Minimum for production

Web (Vercel `blog-ai`): `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`,
`CLERK_SECRET_KEY`, `DATABASE_URL`; strongly recommended `NEXT_PUBLIC_SITE_URL`,
`NEXT_PUBLIC_CLERK_DOMAIN`, `NEXT_PUBLIC_SUPPORT_EMAIL`, `NEXT_PUBLIC_SENTRY_DSN`.

API (Vercel `blog-ai-api`): `ENVIRONMENT=production`, `ALLOWED_ORIGINS`, `DATABASE_URL`,
`CLERK_JWKS_URL`, `CLERK_JWT_ISSUER`, one of `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`;
`STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` + `STRIPE_PRICE_ID_{STARTER,PRO}_{MONTHLY,YEARLY}`
for billing. `next.config.mjs` refuses a production web build without the first three web
variables; the API exits at start-up in production if `ALLOWED_ORIGINS` has no non-localhost
entry.

## Known stale entries

`.env.example` still lists variables nothing reads: `SSO_ENABLED`, `SSO_*`, `OIDC_*`,
`SAML_SP_SLO_URL`, `SAML_CLOCK_SKEW_SECONDS`, `SAML_DEBUG_MODE`, `SAML_DIGEST_ALGORITHM`,
`SAML_SIGNATURE_ALGORITHM`, `UVICORN_WORKERS`, `WEBHOOK_TIMEOUT_SECONDS`, `WEBHOOK_MAX_RETRIES`,
`PERFORMANCE_TRACKING_ENABLED`, `PERFORMANCE_EVENT_RETENTION_DAYS`. `bun run env:check` lists
them under "in an example file but not read by any code"; they are kept there only until the
SSO/webhook code either reads them or is removed. `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` was
dropped: the web app has no Stripe.js and never read it.

## Reference (generated)

### Web app, public (`NEXT_PUBLIC_*`, inlined at build time)

| Variable | Kind | Read by | Meaning |
|----------|------|---------|---------|
| `NEXT_PUBLIC_API_KEY` | dev only | web build, web runtime | Local-only API key fallback (X-API-Key) when Clerk is absent. Never set in production. |
| `NEXT_PUBLIC_API_URL` | required | web build, web runtime | FastAPI base URL. Production: https://blog-ai-api-gr8monk3ys-projects.vercel.app. next.config.mjs refuses a production build without it. |
| `NEXT_PUBLIC_API_VERSION` | optional | web build, web runtime | API path version segment. Default v1. |
| `NEXT_PUBLIC_APP_VERSION` | optional | web build, web runtime | Overrides the version /api/health reports (default: apps/web/package.json). |
| `NEXT_PUBLIC_CLERK_DOMAIN` | optional | web build, web runtime | Clerk custom domain; production uses clerk.vivancedata.com. Added to the CSP connect-src. |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | required | web build, web runtime | Clerk publishable key (pk_test_/pk_live_). Without it every route is public (dev) or redirects to /auth?reason=auth-not-configured (prod). |
| `NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE` | optional | web build, web runtime | Feature flag: /knowledge + nav link. Pair with the API's ENABLE_KNOWLEDGE_BASE. Default off. |
| `NEXT_PUBLIC_FEATURE_BILLING` | optional | web build, web runtime | Feature flag: pricing, checkout, billing portal. Default ON (Stripe is live); set false to hide. |
| `NEXT_PUBLIC_FEATURE_IMAGE_GENERATION` | optional | web build, web runtime | Feature flag: /images. Pair with IMAGE_PROVIDER + OpenAI/Stability key on the API. Default off. |
| `NEXT_PUBLIC_FEATURE_PLAGIARISM_CHECK` | optional | web build, web runtime | Feature flag: /plagiarism. Pair with Copyscape or Originality credentials on the API. Default off. |
| `NEXT_PUBLIC_FEATURE_SOCIAL_POSTING` | optional | web build, web runtime | Feature flag: /social. Pair with Twitter/LinkedIn OAuth or BUFFER_ACCESS_TOKEN on the API. Default off. |
| `NEXT_PUBLIC_FEATURE_TEAMS` | optional | web build, web runtime | Feature flag: /team organisations and invites (no mailer delivers invites yet). Default off. |
| `NEXT_PUBLIC_FEATURE_WEB_RESEARCH` | optional | web build, web runtime | Feature flag: research mode, fact-check sources, SERP analysis. Pair with SERP/Tavily/Metaphor keys on the API. Default off. |
| `NEXT_PUBLIC_LLM_GEMINI` | optional | web build, web runtime | Feature flag: advertise Gemini. Pair with GEMINI_API_KEY on the API. Default off (not configured in production). |
| `NEXT_PUBLIC_SENTRY_DSN` | optional | web build, web runtime | Browser/server/edge Sentry DSN. Reports only on a Vercel deployment (lib/sentry-env.ts). |
| `NEXT_PUBLIC_SENTRY_FORCE_DISABLE` | optional | web build | =1 kill switch: a deployed build stops reporting to Sentry. |
| `NEXT_PUBLIC_SENTRY_FORCE_ENABLE` | dev only | web build | =1 reports Sentry from a non-Vercel build (use a throwaway DSN). |
| `NEXT_PUBLIC_SIGNUP_MODE` | optional | web build, web runtime | open \| waitlist \| invite (lib/signup-mode.ts). Default open. Must match the Clerk dashboard sign-up mode. |
| `NEXT_PUBLIC_SITE_URL` | optional | web build, web runtime | Public origin (sitemap, RSS, Sentry allowUrls, metadataBase). Production falls back to https://blog-ai.vivancedata.com; set it anyway. |
| `NEXT_PUBLIC_SUPPORT_EMAIL` | optional | web build, web runtime | Support inbox shown on error/404/pricing pages. Default support@lscaturchio.xyz (lib/support.ts). |
| `NEXT_PUBLIC_VERCEL_ENV` | platform | web build, web runtime | Mirror of VERCEL_ENV that next.config.mjs inlines for the browser bundle. Do not set by hand. |
| `NEXT_PUBLIC_WS_URL` | optional | web build, web runtime | WebSocket base; derived from NEXT_PUBLIC_API_URL (https->wss) when unset. |

### Web app, server and build only

| Variable | Kind | Read by | Meaning |
|----------|------|---------|---------|
| `ANALYZE` | dev only | web build | =true runs the bundle analyzer (`bun run analyze`). |
| `BLOG_ADMIN_KEY` | optional | web runtime | Shared secret protecting /api/blog-posts/* (x-admin-key or Bearer). Unset: those routes are closed. |
| `CI` | platform | web build | Set by GitHub Actions; enables the production-build env checks together with VERCEL. |
| `CLERK_SECRET_KEY` | required | web runtime | Clerk secret (sk_test_/sk_live_) for proxy.ts and route handlers. Clerk is disabled unless both keys are present. |
| `DEMO_DATA_ENABLED` | dev only | web runtime | Seeds demo data outside production (lib/server-mode.ts). |
| `NEXT_RUNTIME` | platform | web runtime | nodejs \| edge, set by Next.js (instrumentation.ts). |
| `NODE_ENV` | platform | web build, web runtime | Set by Next.js. |
| `PLAYWRIGHT_TEST` | dev only | web runtime | =1 set by the Playwright config; proxy.ts suppresses its auth warning under e2e. |
| `SENTRY_AUTH_TOKEN` | optional | web build | Sentry auth token; without it source maps are not uploaded (build still passes). |
| `SENTRY_ORG` | optional | web build | Sentry org slug for source-map upload. |
| `SENTRY_PROJECT` | optional | web build | Sentry project slug for source-map upload. |
| `SUPPRESS_PROXY_AUTH_WARNING` | dev only | web runtime | =1 silences the "Clerk not configured" warning from proxy.ts in local runs. |
| `VERCEL` | platform | web build | Set to 1 by Vercel builds. |
| `VERCEL_ENV` | platform | web build, web runtime | production \| preview \| development on Vercel. Gates Sentry and the production-build env checks. |
| `VERCEL_GIT_COMMIT_SHA` | platform | web runtime | Deployed commit, reported by /api/health as `commit`. |
| `VERCEL_URL` | platform | web build, web runtime | Per-deployment *.vercel.app host; the preview fallback for getBaseUrl(). |

### API (FastAPI)

| Variable | Kind | Read by | Meaning |
|----------|------|---------|---------|
| `ALLOWED_ORIGINS` | required | API | Comma-separated CORS origins; production: https://blog-ai.vivancedata.com. |
| `ANTHROPIC_API_KEY` | optional | API | Claude provider. Configured in production. |
| `ANTHROPIC_MODEL` | optional | API | Default Anthropic model. |
| `API_BASE_URL` | optional | API | Legacy alias of PUBLIC_API_URL read by the extension route. |
| `API_KEY_STORAGE_PATH` | optional | API | JSON file of issued API keys (scripts/create_api_key.py). Ephemeral on Vercel. |
| `APP_BASE_URL` | optional | API | Public web origin used for SSO redirects and emails. |
| `APP_ENV` | optional | API | Legacy alias consulted by src/utils/logging; prefer ENVIRONMENT. |
| `BACKEND_PORT` | dev only | API | Local listen port when PORT is unset (default 8000). |
| `BLOGAI_API_KEY` | dev only | API | scripts/smoke_test.py: API key for authenticated probes. |
| `BLOGAI_BASE_URL` | dev only | API | scripts/smoke_test.py: API base URL to probe. |
| `BLOGAI_ORG_ID` | dev only | API | scripts/smoke_test.py: organisation to probe. |
| `BLOGAI_TIMEOUT_SECONDS` | dev only | API | scripts/smoke_test.py: per-request timeout. |
| `BOOK_SECTION_WORKERS` | optional | API | Parallel section writers for book generation. |
| `BUFFER_ACCESS_TOKEN` | optional | API | Buffer publishing (covers Facebook/Instagram, which have no direct OAuth here). |
| `CHROMA_PERSIST_PATH` | optional | API | Chroma on-disk path. |
| `CLERK_JWKS_URL` | required | API | Clerk JWKS endpoint used to verify the web app's Bearer tokens. |
| `CLERK_JWT_AUDIENCE` | optional | API | Expected `aud`, when the Clerk template sets one. |
| `CLERK_JWT_ISSUER` | required | API | Expected `iss` of Clerk session tokens. |
| `COHERE_API_KEY` | optional | API | Cohere embeddings. |
| `CONVERSATION_STORAGE_DIR` | optional | API | File fallback for conversations. Ephemeral on Vercel. |
| `COPYSCAPE_API_KEY` | optional | API | Plagiarism check. |
| `COPYSCAPE_USERNAME` | optional | API | Plagiarism check (with COPYSCAPE_API_KEY). |
| `DATABASE_POOL_MAX_SIZE` | optional | API | asyncpg pool maximum. |
| `DATABASE_POOL_MIN_SIZE` | optional | API | asyncpg pool minimum. |
| `DATABASE_URL_DIRECT` | optional | API | Neon direct (non-pooled) string: migrations and long-lived container backends. On Vercel use DATABASE_URL. |
| `DEV_API_KEY` | dev only | API | Static API key accepted in development only. |
| `DEV_MODE` | dev only | API | scripts/smoke_test.py: skip auth locally. (pytest does not read it; conftest.py sets DEV_API_KEY itself.) |
| `ENABLE_BUSINESS_TIER` | optional | API | Exposes the Business tier in /api/payments plans. Default false. |
| `ENABLE_CONTENT_VERSIONING` | optional | API | Mounts the content-versions router (needs db/migrations/007). Default false. |
| `ENABLE_KNOWLEDGE_BASE` | optional | API | Mounts the knowledge-base router. Default false; pair with NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE. |
| `ENABLE_PERFORMANCE_ANALYTICS` | optional | API | Mounts the performance-analytics router (needs db/migrations/009). Default false. |
| `ENVIRONMENT` | required | API | development \| staging \| production. Production strips localhost origins and exits if none remain. |
| `GEMINI_API_KEY` | optional | API | Gemini provider. Not configured in production; the google-genai package is not in uv.lock (requirements-gemini.txt). |
| `GEMINI_MODEL` | optional | API | Default Gemini model. |
| `HTTPS_REDIRECT_ENABLED` | optional | API | Redirect http->https (behind a TLS-terminating host leave off). |
| `IMAGE_PROVIDER` | optional | API | openai \| stability for /api/images. |
| `KB_CHUNK_OVERLAP` | optional | API | Chunk overlap in tokens. |
| `KB_CHUNK_SIZE` | optional | API | Chunk size in tokens. |
| `KB_EMBEDDING_MODEL` | optional | API | Embedding model id. |
| `KB_EMBEDDING_PROVIDER` | optional | API | openai \| voyage \| cohere. |
| `KB_FREE_MAX_DOCS` | optional | API | Tier quota. |
| `KB_FREE_MAX_STORAGE_MB` | optional | API | Tier quota. |
| `KB_STARTER_MAX_DOCS` | optional | API | Tier quota. |
| `KB_STARTER_MAX_STORAGE_MB` | optional | API | Tier quota. |
| `KB_VECTOR_STORE` | optional | API | chromadb \| pinecone \| pgvector (pgvector is not implemented; chromadb/pinecone are not in uv.lock). |
| `LINKEDIN_CLIENT_ID` | optional | API | LinkedIn OAuth. |
| `LINKEDIN_CLIENT_SECRET` | optional | API | LinkedIn OAuth. |
| `LLM_API_TIMEOUT` | optional | API | Seconds per provider call. |
| `LLM_RATE_LIMIT_ENABLED` | optional | API | Per-operation provider rate limiting. |
| `LLM_RATE_LIMIT_MAX_QUEUE` | optional | API | Queued provider calls before rejecting. |
| `LLM_RATE_LIMIT_MAX_WAIT` | optional | API | Seconds a queued call waits. |
| `LLM_RATE_LIMIT_PER_MINUTE` | optional | API | Provider calls per minute. |
| `LLM_STREAMING_TIMEOUT` | optional | API | Seconds for a streaming generation. |
| `LOG_FORMAT_JSON` | optional | API | Structured JSON logs. |
| `LOG_LEVEL` | optional | API | DEBUG \| INFO \| WARNING \| ERROR \| CRITICAL. |
| `METAPHOR_API_KEY` | optional | API | Metaphor/Exa neural search (legacy api.metaphor.systems host). |
| `OPENAI_API_KEY` | required | API | At least one of OPENAI_API_KEY / ANTHROPIC_API_KEY is required; /ready returns 503 without one. |
| `OPENAI_MODEL` | optional | API | Default OpenAI model. |
| `ORIGINALITY_API_KEY` | optional | API | Plagiarism check alternative. |
| `PINECONE_API_KEY` | optional | API | Pinecone vector store. |
| `PINECONE_ENVIRONMENT` | optional | API | Pinecone environment/region. |
| `PINECONE_INDEX_NAME` | optional | API | Pinecone index. |
| `PLAGIARISM_API_TIMEOUT` | optional | API | Seconds per plagiarism provider call. |
| `PORT` | platform | API | Listen port for `python server.py` on container hosts. Not used on Vercel. |
| `PUBLIC_API_URL` | optional | API | Absolute API URL embedded in webhook/Zapier payloads. |
| `PYTHON_ENV` | optional | API | Legacy alias consulted by src/utils/logging; prefer ENVIRONMENT. |
| `RAILWAY_ENVIRONMENT` | platform | API | Older Railway alias of the above. |
| `RAILWAY_ENVIRONMENT_NAME` | platform | API | Set by Railway only; the API's deployed-host signal for Sentry. |
| `RATE_LIMIT_ENABLED` | optional | API | Per-client rate limiting (Redis-backed when REDIS_URL is set, else in-memory per worker). |
| `RATE_LIMIT_GEN_BUSINESS_PER_HOUR` | optional | API | Tier limit. |
| `RATE_LIMIT_GEN_BUSINESS_PER_MINUTE` | optional | API | Tier limit. |
| `RATE_LIMIT_GEN_FREE_PER_HOUR` | optional | API | Tier limit. |
| `RATE_LIMIT_GEN_FREE_PER_MINUTE` | optional | API | Tier limit. |
| `RATE_LIMIT_GEN_PRO_PER_HOUR` | optional | API | Tier limit. |
| `RATE_LIMIT_GEN_PRO_PER_MINUTE` | optional | API | Tier limit. |
| `RATE_LIMIT_GEN_STARTER_PER_HOUR` | optional | API | Tier limit. |
| `RATE_LIMIT_GEN_STARTER_PER_MINUTE` | optional | API | Tier limit. |
| `RATE_LIMIT_GENERAL` | optional | API | General requests per minute. |
| `RATE_LIMIT_GENERATION` | optional | API | Generation requests per minute. |
| `RECONCILIATION_ENABLED` | optional | API | Background Stripe subscription reconciliation. |
| `RECONCILIATION_INTERVAL_HOURS` | optional | API | Stripe subscription reconciliation interval. |
| `REDIS_URL` | optional | API | Shared rate limits, bulk jobs, caches. Not configured in production (health reports redis disconnected). |
| `REQUEST_LOGGING_ENABLED` | optional | API | Per-request access log. |
| `RESEARCH_CACHE_MAX_ENTRIES` | optional | API | Research result cache size. |
| `RESEARCH_CACHE_TTL_SECONDS` | optional | API | Research result cache TTL. |
| `SAML_SP_ACS_URL` | optional | API | SAML assertion consumer URL. |
| `SAML_SP_CERT` | optional | API | SAML SP certificate (PEM string). |
| `SAML_SP_CERT_PATH` | optional | API | SAML SP certificate file. |
| `SAML_SP_ENTITY_ID` | optional | API | SAML SP entity id (default a placeholder https://api.example.com URL). |
| `SAML_SP_KEY_PATH` | optional | API | SAML SP private key file. |
| `SAML_SP_PRIVATE_KEY` | optional | API | SAML SP private key (PEM string). |
| `SEC_API_API_KEY` | optional | API | Declared in config.py; no code path reads it beyond has_any_research_api. |
| `SECURITY_CSP_POLICY` | optional | API | Content-Security-Policy for API HTML responses (/docs). |
| `SECURITY_ENABLED` | optional | API | Security headers middleware. |
| `SECURITY_HSTS_ENABLED` | optional | API | HSTS header (defaults on in production). |
| `SECURITY_HSTS_MAX_AGE` | optional | API | HSTS max-age seconds. |
| `SECURITY_MAX_BODY_SIZE` | optional | API | Request body limit in bytes. |
| `SECURITY_REQUEST_ID_PREFIX` | optional | API | Prefix for generated request ids. |
| `SECURITY_TRUST_REQUEST_ID` | optional | API | Trust an inbound X-Request-ID. |
| `SENTRY_DSN` | optional | API | API Sentry DSN. Initialises only with RAILWAY_ENVIRONMENT_NAME or SENTRY_FORCE_ENABLE=1 - on Vercel the latter is needed. |
| `SENTRY_ENVIRONMENT` | optional | API | Tag only; does not enable Sentry. |
| `SENTRY_FORCE_DISABLE` | optional | API | =1 kill switch. |
| `SENTRY_FORCE_ENABLE` | optional | API | =1 report from a host that is not Railway (Vercel included). |
| `SENTRY_PROFILES_SAMPLE_RATE` | optional | API | 0.0-1.0. |
| `SENTRY_RELEASE` | optional | API | Release tag; default blog-ai@<pyproject version>. |
| `SENTRY_TRACES_SAMPLE_RATE` | optional | API | 0.0-1.0. |
| `SERP_API_KEY` | optional | API | Google SERP results (SerpAPI). Research mode needs SERP + Tavily + Metaphor; none set in production. |
| `SERP_PROVIDER` | optional | API | serpapi \| serpbase. |
| `SERPBASE_API_KEY` | optional | API | SerpBase key when SERP_PROVIDER=serpbase. |
| `SERVER_NAME` | optional | API | Sentry server_name tag. |
| `SOCIAL_SCHEDULER_ENABLED` | optional | API | In-process scheduler (in-memory; src/social/worker.py is never launched). |
| `SOCIAL_WEBHOOK_URL` | optional | API | Callback for publish results. |
| `SOCIAL_WORKER_BATCH_SIZE` | optional | API | Posts per scheduler tick. |
| `SOCIAL_WORKER_MAX_CONCURRENT` | optional | API | Concurrent publishes. |
| `SOCIAL_WORKER_POLL_INTERVAL` | optional | API | Scheduler poll seconds. |
| `STABILITY_API_KEY` | optional | API | Stability AI key when IMAGE_PROVIDER=stability. |
| `STRIPE_PRICE_ID_BUSINESS` | optional | API | Legacy unsuffixed fallback. |
| `STRIPE_PRICE_ID_BUSINESS_MONTHLY` | optional | API | Stripe price id (Business tier, hidden unless ENABLE_BUSINESS_TIER). |
| `STRIPE_PRICE_ID_BUSINESS_YEARLY` | optional | API | Stripe price id (Business tier). |
| `STRIPE_PRICE_ID_PRO` | optional | API | Legacy unsuffixed fallback. |
| `STRIPE_PRICE_ID_PRO_MONTHLY` | optional | API | Stripe price id. |
| `STRIPE_PRICE_ID_PRO_YEARLY` | optional | API | Stripe price id. |
| `STRIPE_PRICE_ID_STARTER` | optional | API | Legacy unsuffixed fallback for the monthly id; /health/stripe still checks these names. |
| `STRIPE_PRICE_ID_STARTER_MONTHLY` | optional | API | Stripe price id. |
| `STRIPE_PRICE_ID_STARTER_YEARLY` | optional | API | Stripe price id. |
| `STRIPE_SECRET_KEY` | optional | API | Enables payments (/health features.payments). Live in production. |
| `STRIPE_WEBHOOK_SECRET` | optional | API | Verifies Stripe webhook signatures. |
| `SUPABASE_KEY` | optional | API | Deprecated supabase-py fallback. |
| `SUPABASE_SERVICE_KEY` | optional | API | Deprecated supabase-py fallback (content versioning). |
| `SUPABASE_SERVICE_ROLE_KEY` | optional | API | Deprecated supabase-py fallback. |
| `SUPABASE_URL` | optional | API | Deprecated supabase-py fallback; unused when DATABASE_URL is set. |
| `TAVILY_API_KEY` | optional | API | Tavily web research. |
| `TRACKING_BASE_URL` | optional | API | Public base URL for performance tracking pixels. |
| `TRACKING_SECRET_KEY` | optional | API | HMAC secret for tracking pixel tokens. |
| `TWITTER_API_KEY` | optional | API | Twitter OAuth 1.0a (media upload). |
| `TWITTER_API_SECRET` | optional | API | Twitter OAuth 1.0a. |
| `TWITTER_CLIENT_ID` | optional | API | Twitter OAuth 2. |
| `TWITTER_CLIENT_SECRET` | optional | API | Twitter OAuth 2. |
| `USAGE_STORAGE_DIR` | optional | API | File-based usage counters without DATABASE_URL. Ephemeral on Vercel. |
| `UVICORN_RELOAD` | dev only | API | =true enables auto-reload for `python server.py`. |
| `VOYAGE_API_KEY` | optional | API | Voyage embeddings. |
| `WEBHOOK_SECRET` | optional | API | HMAC secret for outbound webhooks (optional; per-subscription secrets otherwise). |

### Shared by web and API

| Variable | Kind | Read by | Meaning |
|----------|------|---------|---------|
| `DATABASE_URL` | required | web runtime, API | Neon Postgres (pooled). Web route handlers: history, brand profiles, templates, blog CMS. API: analytics, quotas, Stripe sync. Without it those fall back to memory. |

## Related

- [Deployment](./DEPLOYMENT.md)
- [Monitoring](./MONITORING.md)
- [Database](./DATABASE.md)
