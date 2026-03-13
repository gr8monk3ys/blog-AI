# Environment Variables

This is the short, current environment reference for the active monorepo layout.

## Files

- root `.env`: backend configuration
- `apps/web/.env.local`: local frontend configuration
- `.env.production.local`: production frontend configuration

## Backend Essentials

Required for meaningful local or staging use:

```bash
OPENAI_API_KEY=...
ENVIRONMENT=development|staging|production
ALLOWED_ORIGINS=http://localhost:3000,https://your-web-domain
```

Required for persistent product behavior:

```bash
DATABASE_URL=...
# or
DATABASE_URL_DIRECT=...
```

Required for production auth:

```bash
CLERK_JWKS_URL=...
CLERK_JWT_ISSUER=...
```

Required for billing:

```bash
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
STRIPE_PRICE_ID_STARTER_MONTHLY=...
STRIPE_PRICE_ID_STARTER_YEARLY=...
STRIPE_PRICE_ID_PRO_MONTHLY=...
STRIPE_PRICE_ID_PRO_YEARLY=...
ENABLE_BUSINESS_TIER=false
```

Optional but important:

```bash
REDIS_URL=...
SENTRY_DSN=...
SERP_API_KEY=...
TAVILY_API_KEY=...
```

## Frontend Essentials

Local:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

Production:

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
CLERK_SECRET_KEY=...
DATABASE_URL=...
```

Billing on the frontend:

```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=...
```

## Important Notes

- Without Clerk, public pages still render, but protected product routes do not behave like a real SaaS.
- Without a database, the app can demo some reads but cannot prove durable user workflows.
- Without a real LLM key, generation requests make it through the stack and then fail at the provider.
- `NEXT_PUBLIC_API_KEY` should only be used as a local development fallback, not as a production auth mechanism.

## Recommended Reading

- [Deployment Overview](./DEPLOYMENT.md)
- [Vercel + Railway + Neon Guide](./DEPLOYMENT_VERCEL_RAILWAY_NEON.md)
- [Staging Checklist](./STAGING_CHECKLIST.md)
