# Environment Reference

Blog AI uses two local env files:

- `.env` for backend and shared server-side configuration
- `.env.local` for the Next.js frontend

Start from the checked-in examples:

```bash
cp .env.example .env
cp .env.local.example .env.local
```

## Minimum Local Development

In `.env`:

```bash
OPENAI_API_KEY=sk-...
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

In `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Backend Variables

Required for a real backend:

- `OPENAI_API_KEY` or another provider key (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`)
- `ENVIRONMENT`
- `ALLOWED_ORIGINS`

Recommended for persistent production use:

- `DATABASE_URL`
- `DATABASE_URL_DIRECT`
- `CLERK_JWKS_URL`
- `CLERK_JWT_ISSUER`
- `SENTRY_DSN`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`

Notes:

- Use `DATABASE_URL` for serverless/frontend contexts.
- Prefer `DATABASE_URL_DIRECT` for migrations and long-lived backend processes.
- `DEV_MODE=true` should not be used in production.

## Frontend Variables

Common `.env.local` values:

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_WS_URL`
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`
- `DATABASE_URL`

Optional:

- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- `NEXT_PUBLIC_SENTRY_DSN`
- `SENTRY_ORG`
- `SENTRY_PROJECT`
- `SENTRY_AUTH_TOKEN`
- `BLOG_ADMIN_KEY`

Rules:

- Only variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.
- Keep secrets such as `CLERK_SECRET_KEY`, `DATABASE_URL`, and Stripe secret keys server-only.

## Local Permissions

Protect local env files:

```bash
chmod 600 .env
chmod 600 .env.local
```

## Production Checklist

Backend:

- `ENVIRONMENT=production`
- Production `ALLOWED_ORIGINS`
- Database configured
- At least one LLM provider configured

Frontend:

- `NEXT_PUBLIC_API_URL` points at the production API
- `NEXT_PUBLIC_WS_URL` points at the production WebSocket endpoint
- Clerk keys set

## Related Files

- [.env.example](/Users/natalyscaturchio/code/blog-AI/.env.example)
- [.env.local.example](/Users/natalyscaturchio/code/blog-AI/.env.local.example)
- [DEPLOYMENT.md](/Users/natalyscaturchio/code/blog-AI/DEPLOYMENT.md)
- [docs/DEPLOYMENT_VERCEL_RAILWAY_NEON.md](/Users/natalyscaturchio/code/blog-AI/docs/DEPLOYMENT_VERCEL_RAILWAY_NEON.md)
