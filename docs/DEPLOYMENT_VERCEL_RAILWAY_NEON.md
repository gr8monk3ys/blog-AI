# Vercel + Railway + Neon (Cloud SaaS)

This guide assumes:
- Frontend: Next.js deployed on Vercel
- Backend: FastAPI deployed on Railway
- Database: Neon Postgres (shared by frontend route handlers + backend services)
- Auth: Clerk (frontend sessions; backend verifies Clerk JWTs via JWKS)

## 1. Create Neon Database

1. Create a Neon project and database.
2. Copy two connection strings:
   - `DATABASE_URL`: pooled/serverless connection string (good for Vercel)
   - `DATABASE_URL_DIRECT`: direct connection string (recommended for Railway and migrations)

## 2. Run Migrations

Run migrations from your machine (or CI) using the direct URL:

```bash
export DATABASE_URL_DIRECT="postgresql://user:password@host/db?sslmode=require"
bun run db:migrate
```

This applies `db/migrations/*.sql` and records applied files in `schema_migrations`.

## 3. Deploy Backend to Railway

1. Create a new Railway service from the `backend/` directory.
2. Set Railway environment variables:
   - `ENVIRONMENT=production`
   - `DATABASE_URL_DIRECT=...` (or `DATABASE_URL=...`)
   - `CLERK_JWKS_URL=...`
   - `CLERK_JWT_ISSUER=...`
   - `ALLOWED_ORIGINS=https://<your-vercel-domain>`
   - LLM keys: `OPENAI_API_KEY` (and optional `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`)
   - Stripe (if monetizing): `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_*`
3. Start command (Railway):
   - `python server.py`
   - The backend reads Railway's `PORT` env var automatically.

## 4. Deploy Frontend to Vercel

1. Import the repo in Vercel and deploy the Next.js app (project root).
2. Set Vercel environment variables:
   - `NEXT_PUBLIC_API_URL=https://<your-railway-domain>`
   - `NEXT_PUBLIC_WS_URL=wss://<your-railway-domain>` (optional; falls back from API URL)
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...`
   - `CLERK_SECRET_KEY=...`
   - `DATABASE_URL=...` (Neon pooled/serverless URL)
   - Stripe (optional): `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=...`
   - Admin blog (optional): `BLOG_ADMIN_KEY=...` (protects `/api/blog-posts/*`)

## 5. Clerk JWT Settings

The frontend attaches `Authorization: Bearer <token>` to backend requests.
Make sure the backend can validate tokens by setting:
- `CLERK_JWKS_URL`
- `CLERK_JWT_ISSUER`

## 6. Sanity Checks

1. Vercel: visit `/history` and generate a tool output; confirm it appears in history (DB write).
2. Vercel: visit `/analytics`; confirm charts load (backend reads from DB).
3. Railway: hit `/health` and confirm DB connectivity is reported healthy when configured.

