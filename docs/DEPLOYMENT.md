# Deployment Overview

Blog AI deploys as a split system:

- `apps/web` on Vercel
- `apps/api` on Railway or another container host
- Neon/Postgres for persistence
- Clerk for authentication
- Stripe for billing

The web workspace is Bun-managed.

## Frontend Build Contract

```bash
bun install --frozen-lockfile
bun run build
bun run start -- --hostname 0.0.0.0 --port 3000
```

## Backend Runtime Contract

```bash
cd apps/api
python server.py
```

For containers, expose `/ready` for readiness and `/health` for deeper health checks.

## Minimum Production Dependencies

Backend:

- `ENVIRONMENT=production`
- `DATABASE_URL_DIRECT` or `DATABASE_URL`
- backend Clerk JWT verification settings
- at least one real LLM provider key

Frontend:

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_WS_URL`
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`
- `DATABASE_URL`

Billing:

- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID_STARTER_*`
- `STRIPE_PRICE_ID_PRO_*`

## What Breaks Without Infra

- no database: brand profiles, history, analytics, and other durable features degrade or fail
- no Clerk: protected routes redirect instead of behaving like a real SaaS
- no Stripe: checkout and portal flows are disabled
- no valid LLM key: generation reaches the backend and then fails at the provider

## Recommended Release Process

1. Deploy the backend.
2. Verify `/health` reports the database correctly.
3. Deploy the frontend with the production env vars.
4. Run `scripts/post_deploy_health_check.sh` (the `post-deploy-health-check` workflow does this hourly).

## Related Docs

- [Environment Variables](./ENVIRONMENT.md)
- [Vercel + Railway + Neon Guide](./DEPLOYMENT_VERCEL_RAILWAY_NEON.md)
- [Monitoring](./MONITORING.md)
- [Database](./DATABASE.md)
