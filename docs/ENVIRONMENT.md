# Environment Configuration Guide

This document provides comprehensive documentation for all environment variables used by Blog AI.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Overview](#configuration-overview)
- [Backend Environment Variables](#backend-environment-variables)
  - [LLM Provider API Keys](#llm-provider-api-keys)
  - [Model Configuration](#model-configuration)
  - [LLM Rate Limiting](#llm-rate-limiting)
  - [Server Configuration](#server-configuration)
  - [CORS Configuration](#cors-configuration)
  - [API Rate Limiting](#api-rate-limiting)
  - [Security Configuration](#security-configuration)
  - [Database (Supabase)](#database-supabase)
  - [Payment Processing (Stripe)](#payment-processing-stripe)
  - [Redis (Optional)](#redis-optional)
  - [Research APIs](#research-apis)
  - [Image Generation](#image-generation)
  - [Logging Configuration](#logging-configuration)
  - [Error Tracking (Sentry)](#error-tracking-sentry)
  - [Local Storage](#local-storage)
- [Frontend Environment Variables](#frontend-environment-variables)
  - [API Configuration](#api-configuration)
  - [Supabase (Frontend)](#supabase-frontend)
  - [Stripe (Frontend)](#stripe-frontend)
  - [Sentry (Frontend)](#sentry-frontend)
  - [Analytics](#analytics)
  - [Feature Flags](#feature-flags)
- [Security Considerations](#security-considerations)
- [Configuration Validation](#configuration-validation)
- [Environment-Specific Settings](#environment-specific-settings)

---

## Quick Start

### Minimal Development Setup

1. Copy `.env.example` to `.env` in the project root
2. Set at least one LLM provider API key:
   ```bash
   OPENAI_API_KEY=sk-your-openai-api-key
   ```
3. Run the server: `python server.py`

### Recommended Production Setup

1. Configure all required environment variables
2. Set `ENVIRONMENT=production`
3. Enable HTTPS redirect: `HTTPS_REDIRECT_ENABLED=true`
4. Configure Supabase for persistent storage
5. Configure Stripe for billing (if monetizing)
6. Configure Sentry for error tracking
7. Set specific CORS origins (no wildcards)

---

## Configuration Overview

| Category | Required | Purpose |
|----------|----------|---------|
| LLM Providers | At least one | Content generation |
| Database (Supabase) | Recommended | Persistent storage |
| Payments (Stripe) | Optional | Subscription billing |
| Monitoring (Sentry) | Recommended | Error tracking |
| Security | Defaults provided | Request validation, rate limiting |
| Redis | Optional | Caching, job queues |

---

## Backend Environment Variables

All backend variables are configured in the root `.env` file.

### LLM Provider API Keys

At least **one** LLM provider API key is **required** for the application to start.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes* | - | OpenAI API key for GPT models (primary provider) |
| `ANTHROPIC_API_KEY` | No | - | Anthropic API key for Claude models |
| `GEMINI_API_KEY` | No | - | Google Gemini API key |

*At least one provider key is required.

**Where to get API keys:**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/
- Google Gemini: https://makersuite.google.com/app/apikey

**Example:**
```bash
OPENAI_API_KEY=sk-proj-REPLACE_WITH_YOUR_OPENAI_KEY
# ANTHROPIC_API_KEY=sk-ant-REPLACE_WITH_YOUR_ANTHROPIC_KEY
# GEMINI_API_KEY=REPLACE_WITH_YOUR_GEMINI_KEY
```

---

### Model Configuration

Override default models for each provider.

| Variable | Required | Default | Options |
|----------|----------|---------|---------|
| `OPENAI_MODEL` | No | `gpt-4` | `gpt-4`, `gpt-4-turbo`, `gpt-4o`, `gpt-3.5-turbo` |
| `ANTHROPIC_MODEL` | No | `claude-3-opus-20240229` | `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, `claude-3-haiku-20240307` |
| `GEMINI_MODEL` | No | `gemini-1.5-flash-latest` | `gemini-1.5-pro`, `gemini-1.5-flash`, `gemini-1.5-flash-latest` |
| `LLM_API_TIMEOUT` | No | `60` | Timeout in seconds (1-600) |

**Example:**
```bash
OPENAI_MODEL=gpt-4-turbo
LLM_API_TIMEOUT=120
```

---

### LLM Rate Limiting

Prevent excessive API calls and manage costs.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_RATE_LIMIT_ENABLED` | No | `true` | Enable rate limiting for LLM API calls |
| `LLM_RATE_LIMIT_PER_MINUTE` | No | `60` | Maximum LLM API calls per minute |
| `LLM_RATE_LIMIT_MAX_QUEUE` | No | `100` | Maximum requests to queue when rate limited |
| `LLM_RATE_LIMIT_MAX_WAIT` | No | `60.0` | Maximum seconds to wait for rate limit |

**Example:**
```bash
LLM_RATE_LIMIT_ENABLED=true
LLM_RATE_LIMIT_PER_MINUTE=30
```

---

### Server Configuration

| Variable | Required | Default | Options |
|----------|----------|---------|---------|
| `ENVIRONMENT` | No | `development` | `development`, `staging`, `production` |
| `DEV_MODE` | No | `false` | `true`, `false` |

**Security Warning:** Never set `DEV_MODE=true` in production. This may bypass API key authentication.

**Example:**
```bash
ENVIRONMENT=production
DEV_MODE=false
```

---

### CORS Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ALLOWED_ORIGINS` | No | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated list of allowed CORS origins |

**Security Warning:** Never use wildcards (`*`) in production. Always specify exact domains.

**Example:**
```bash
# Development
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Production
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

### API Rate Limiting

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RATE_LIMIT_ENABLED` | No | `true` | Enable rate limiting middleware |
| `RATE_LIMIT_GENERAL` | No | `60` | General endpoints: requests per minute per IP |
| `RATE_LIMIT_GENERATION` | No | `10` | Generation endpoints: requests per minute per IP |

**Example:**
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GENERAL=60
RATE_LIMIT_GENERATION=5
```

---

### Security Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HTTPS_REDIRECT_ENABLED` | No | `false` | Redirect HTTP to HTTPS |
| `SECURITY_ENABLED` | No | `true` | Enable security middleware stack |
| `SECURITY_HSTS_ENABLED` | No | Auto (production) | Enable HSTS header |
| `SECURITY_HSTS_MAX_AGE` | No | `31536000` | HSTS max-age in seconds (1 year) |
| `SECURITY_MAX_BODY_SIZE` | No | `10485760` | Maximum request body size (10MB) |
| `SECURITY_TRUST_REQUEST_ID` | No | `false` | Trust incoming X-Request-ID headers |
| `SECURITY_REQUEST_ID_PREFIX` | No | `blog-ai` | Prefix for generated request IDs |
| `SECURITY_CSP_POLICY` | No | Restrictive default | Custom Content-Security-Policy |

**Example:**
```bash
HTTPS_REDIRECT_ENABLED=true
SECURITY_ENABLED=true
SECURITY_HSTS_ENABLED=true
SECURITY_MAX_BODY_SIZE=5242880  # 5MB
```

---

### Database (Supabase)

Required for persistent storage of user data, brand voice profiles, and conversation history.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | Recommended | - | Supabase project URL |
| `SUPABASE_KEY` | Recommended | - | Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Recommended | - | Supabase service role key (admin operations) |

**Where to get credentials:**
- Supabase Dashboard: https://supabase.com/dashboard/project/_/settings/api

**Security Warning:** The service role key bypasses Row Level Security. Never expose it to clients.

**Example:**
```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxx.anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxx.service-role-key
```

---

### Payment Processing (Stripe)

Required for subscription billing features.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STRIPE_SECRET_KEY` | For payments | - | Stripe secret API key |
| `STRIPE_WEBHOOK_SECRET` | For webhooks | - | Stripe webhook signing secret |
| `STRIPE_PRICE_ID_STARTER` | For subscriptions | - | Price ID for Starter tier |
| `STRIPE_PRICE_ID_PRO` | For subscriptions | - | Price ID for Pro tier |
| `STRIPE_PRICE_ID_BUSINESS` | For subscriptions | - | Price ID for Business tier |

**Where to get credentials:**
- Stripe API Keys: https://dashboard.stripe.com/apikeys
- Stripe Webhooks: https://dashboard.stripe.com/webhooks
- Stripe Products/Prices: https://dashboard.stripe.com/products

**Security Warning:** Never expose the secret key in client-side code.

**Example:**
```bash
STRIPE_SECRET_KEY=sk_test_REPLACE_WITH_YOUR_STRIPE_KEY
STRIPE_WEBHOOK_SECRET=whsec_REPLACE_WITH_YOUR_WEBHOOK_SECRET
STRIPE_PRICE_ID_STARTER=price_REPLACE_WITH_STARTER_PRICE_ID
STRIPE_PRICE_ID_PRO=price_REPLACE_WITH_PRO_PRICE_ID
STRIPE_PRICE_ID_BUSINESS=price_REPLACE_WITH_BUSINESS_PRICE_ID
```

---

### Redis (Optional)

Optional caching and job queue support.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | No | - | Redis connection URL |

**Format:** `redis://[[username:]password@]host[:port][/database]`

**Example:**
```bash
REDIS_URL=redis://localhost:6379/0
# With authentication
REDIS_URL=redis://:password@redis-host:6379/0
```

---

### Research APIs

Enable web research features for enhanced content generation.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERP_API_KEY` | No | - | SERP API for Google search results |
| `TAVILY_API_KEY` | No | - | Tavily API for web research |
| `METAPHOR_API_KEY` | No | - | Metaphor API for neural search |
| `SEC_API_API_KEY` | No | - | SEC API for financial filings |

**Where to get API keys:**
- SERP API: https://serpapi.com/
- Tavily: https://tavily.com/
- Metaphor: https://metaphor.systems/
- SEC API: https://sec-api.io/

**Example:**
```bash
SERP_API_KEY=your_serp_api_key
TAVILY_API_KEY=your_tavily_api_key
```

---

### Image Generation

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `IMAGE_PROVIDER` | No | `openai` | Image generation provider (`openai` or `stability`) |
| `STABILITY_API_KEY` | If using Stability | - | Stability AI API key |

**Where to get credentials:**
- Stability AI: https://platform.stability.ai/

**Example:**
```bash
IMAGE_PROVIDER=openai  # Uses DALL-E 3 via OPENAI_API_KEY

# Or use Stability AI
IMAGE_PROVIDER=stability
STABILITY_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### Logging Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_FORMAT_JSON` | No | `false` | Force JSON log format in development |
| `REQUEST_LOGGING_ENABLED` | No | `true` | Enable HTTP request logging |

**Note:** JSON format is automatically used in production regardless of `LOG_FORMAT_JSON`.

**Example:**
```bash
LOG_LEVEL=DEBUG
LOG_FORMAT_JSON=true
REQUEST_LOGGING_ENABLED=true
```

---

### Error Tracking (Sentry)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENTRY_DSN` | Recommended | - | Sentry DSN for error tracking |
| `SENTRY_ENVIRONMENT` | No | `development` | Environment name in Sentry |
| `SENTRY_TRACES_SAMPLE_RATE` | No | `0.1` | Transaction sample rate (0.0-1.0) |
| `SENTRY_PROFILES_SAMPLE_RATE` | No | `0.1` | Profile sample rate (0.0-1.0) |
| `SENTRY_RELEASE` | No | `blog-ai@1.0.0` | Release version |
| `SERVER_NAME` | No | `blog-ai-api` | Server identifier |

**Where to get credentials:**
- Sentry: https://sentry.io

**Example:**
```bash
SENTRY_DSN=https://xxxx@xxx.ingest.sentry.io/xxxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
SENTRY_RELEASE=blog-ai@1.2.0
```

---

### Local Storage

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CONVERSATION_STORAGE_DIR` | No | `./data/conversations` | Directory for conversation persistence |
| `API_KEY_STORAGE_PATH` | No | `./data/api_keys.json` | Path for API key storage |
| `USAGE_STORAGE_DIR` | No | `./data/usage` | Directory for usage tracking |

**Security Note:** Ensure `API_KEY_STORAGE_PATH` has restricted file permissions (`chmod 600`).

**Example:**
```bash
CONVERSATION_STORAGE_DIR=/var/data/blog-ai/conversations
API_KEY_STORAGE_PATH=/var/data/blog-ai/api_keys.json
USAGE_STORAGE_DIR=/var/data/blog-ai/usage
```

---

## Frontend Environment Variables

Frontend variables are configured in `frontend/.env.local` (development) or `frontend/.env.production.local` (production).

**Important:** All `NEXT_PUBLIC_*` variables are exposed to the browser. Never put secrets in these variables.

### API Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000` | Backend API URL |
| `NEXT_PUBLIC_WS_URL` | No | Derived from API URL | WebSocket URL |
| `NEXT_PUBLIC_API_VERSION` | No | `v1` | API version prefix |
| `NEXT_PUBLIC_API_KEY` | Production | - | API key for authentication |

**Example:**
```bash
# Development
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
NEXT_PUBLIC_API_KEY=your_production_api_key
```

---

### Supabase (Frontend)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Recommended | - | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Recommended | - | Supabase anon key (client-safe, uses RLS) |
| `SUPABASE_SERVICE_KEY` | Server-side | - | Service role key (server-side only) |

**Example:**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxx
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxx
```

---

### Stripe (Frontend)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | For payments | - | Stripe publishable key (client-safe) |
| `STRIPE_SECRET_KEY` | Server-side | - | Stripe secret key (server-side only) |
| `STRIPE_WEBHOOK_SECRET` | Server-side | - | Webhook signing secret |

**Where to get credentials:**
- Stripe Dashboard: https://dashboard.stripe.com/apikeys

**Example:**
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_REPLACE_WITH_PUBLISHABLE_KEY
STRIPE_SECRET_KEY=sk_test_REPLACE_WITH_SECRET_KEY
STRIPE_WEBHOOK_SECRET=whsec_REPLACE_WITH_WEBHOOK_SECRET
```

---

### Sentry (Frontend)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_SENTRY_DSN` | Recommended | - | Sentry DSN for client-side errors |
| `SENTRY_ORG` | For source maps | - | Sentry organization slug |
| `SENTRY_PROJECT` | For source maps | - | Sentry project slug |
| `SENTRY_AUTH_TOKEN` | For source maps | - | Sentry auth token for CI/CD |

**Where to get credentials:**
- Sentry Auth Tokens: https://sentry.io/settings/auth-tokens/

**Example:**
```bash
NEXT_PUBLIC_SENTRY_DSN=https://xxxx@xxx.ingest.sentry.io/xxxx
SENTRY_ORG=your-org
SENTRY_PROJECT=blog-ai-frontend
SENTRY_AUTH_TOKEN=sntrys_eyJxxxxxxxxxxxxxxxxxx
```

---

### Analytics

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_GA_MEASUREMENT_ID` | No | - | Google Analytics measurement ID |
| `NEXT_PUBLIC_POSTHOG_KEY` | No | - | PostHog analytics key |
| `NEXT_PUBLIC_POSTHOG_HOST` | No | `https://app.posthog.com` | PostHog host URL |

**Example:**
```bash
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
NEXT_PUBLIC_POSTHOG_KEY=phc_xxxxxxxxxxxxxxxxxxxx
```

---

### Feature Flags

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_MAINTENANCE_MODE` | No | `false` | Enable maintenance mode |
| `NEXT_PUBLIC_DEBUG` | No | `false` | Enable debug logging |
| `ANALYZE` | No | - | Enable bundle analyzer during build |

**Example:**
```bash
NEXT_PUBLIC_MAINTENANCE_MODE=false
NEXT_PUBLIC_DEBUG=false
```

---

## Security Considerations

### Secrets That Should NEVER Be Exposed to Clients

These variables must only be used server-side:

- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_SERVICE_KEY`
- `SENTRY_AUTH_TOKEN`
- Any `*_API_KEY` or `*_SECRET*` variable

### Client-Safe Variables

These are safe to expose (prefixed with `NEXT_PUBLIC_`):

- `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`
- `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- `NEXT_PUBLIC_SENTRY_DSN`

### File Permissions

Ensure sensitive files have proper permissions:

```bash
chmod 600 .env
chmod 600 frontend/.env.local
chmod 600 ./data/api_keys.json
```

### Git Ignore

Ensure these patterns are in `.gitignore`:

```
.env
.env.local
.env.production.local
*.local
```

---

## Configuration Validation

The application validates configuration at startup in `server.py`. The validation system:

1. **Fails fast** on critical errors (missing LLM provider)
2. **Logs warnings** for recommended but missing config
3. **Never logs secrets** - only configuration status

### Validation Rules

| Check | Severity | Description |
|-------|----------|-------------|
| No LLM provider | Error | At least one of OPENAI/ANTHROPIC/GEMINI API key required |
| DEV_MODE in production | Error | DEV_MODE=true not allowed when ENVIRONMENT=production |
| Wildcard CORS origin | Error | `*` not allowed in production |
| No Supabase | Warning | Database features will use in-memory fallback |
| No Stripe webhook | Warning | Webhook signature verification will fail |
| No Sentry in production | Warning | Error tracking recommended for production |
| Rate limiting disabled | Warning | Rate limiting recommended in production |
| HTTPS redirect disabled | Warning | HTTPS recommended in production |

### Startup Output

On successful startup, you will see a configuration summary:

```
============================================================
Blog AI Configuration Summary
============================================================
Environment: production
Dev Mode: False
Log Level: INFO
------------------------------------------------------------
Features:
  LLM Providers: openai
  Default Provider: openai
  Supabase: Enabled
  Stripe Payments: Enabled
  Stripe Webhooks: Enabled
  Sentry Monitoring: Enabled
  Redis Cache: Disabled
  Research APIs: Disabled
------------------------------------------------------------
Security:
  Rate Limiting: Enabled
  Security Middleware: Enabled
  HTTPS Redirect: Enabled
  HSTS: Enabled
  Allowed Origins: 2 configured
============================================================
```

---

## Environment-Specific Settings

### Development

```bash
# .env (backend)
ENVIRONMENT=development
DEV_MODE=true
OPENAI_API_KEY=sk-your-key
ALLOWED_ORIGINS=http://localhost:3000
LOG_LEVEL=DEBUG

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Staging

```bash
# .env (backend)
ENVIRONMENT=staging
DEV_MODE=false
OPENAI_API_KEY=sk-your-key
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key
ALLOWED_ORIGINS=https://staging.yourdomain.com
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=staging

# frontend/.env.local
NEXT_PUBLIC_API_URL=https://api-staging.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api-staging.yourdomain.com
```

### Production

```bash
# .env (backend)
ENVIRONMENT=production
DEV_MODE=false
OPENAI_API_KEY=sk-your-production-key
SUPABASE_URL=https://production-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key
STRIPE_SECRET_KEY=sk_test_YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_REPLACE_WITH_PRODUCTION_SECRET
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
HTTPS_REDIRECT_ENABLED=true
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
LOG_LEVEL=INFO

# frontend/.env.production.local
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
NEXT_PUBLIC_API_KEY=your-api-key
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxx
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
```

---

## Troubleshooting

### Application Won't Start

1. Check that at least one LLM API key is set
2. Verify the API key format is correct
3. Check the logs for configuration validation errors

### Missing Features

- **No database persistence:** Configure `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- **No payments:** Configure `STRIPE_SECRET_KEY`
- **No error tracking:** Configure `SENTRY_DSN`

### CORS Errors

- Ensure `ALLOWED_ORIGINS` includes your frontend URL
- Check that the protocol matches (http vs https)
- Verify no trailing slashes in origins

### Rate Limiting Issues

- Check `RATE_LIMIT_GENERAL` and `RATE_LIMIT_GENERATION` values
- Consider increasing limits for development
- Check Redis connection if using distributed rate limiting
