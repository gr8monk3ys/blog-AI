# Deployment Overview

This repo is deployed as a split system:

- `apps/web` on Vercel
- `apps/api` on Railway or another container host
- Neon/Postgres for persistence
- Clerk for authentication
- Stripe for billing

If you want the exact Vercel + Railway + Neon path, use [DEPLOYMENT_VERCEL_RAILWAY_NEON.md](./DEPLOYMENT_VERCEL_RAILWAY_NEON.md).

## Minimum Production Dependencies

Before production, configure all of the following:

- `DATABASE_URL` for the web app
- `DATABASE_URL_DIRECT` or `DATABASE_URL` for the backend
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`
- backend Clerk JWT verification settings
- at least one real LLM provider key

For monetization:

- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID_STARTER_*`
- `STRIPE_PRICE_ID_PRO_*`

## What Breaks Without Infra

The app can boot without the full stack, but important flows will not be production-ready:

- no database: brand profile writes, history, analytics, and other durable features are unavailable or degraded
- no Clerk: protected routes redirect to `/auth`
- no Stripe: checkout and portal flows are disabled
- no valid LLM key: generation requests reach the backend but fail at the provider

## Recommended Release Process

1. Deploy the backend.
2. Verify `/health` reports the database correctly.
3. Deploy the frontend with the production env vars.
4. Run the [staging checklist](./STAGING_CHECKLIST.md).
5. Only then treat the build as launch-capable.

## Related Docs

- [Environment Variables](./ENVIRONMENT.md)
- [Vercel + Railway + Neon Guide](./DEPLOYMENT_VERCEL_RAILWAY_NEON.md)
- [Monitoring](./MONITORING.md)
- [Repo Operations](./REPO_OPERATIONS.md)
