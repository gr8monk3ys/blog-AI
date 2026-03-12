# Deployment

Blog AI deploys as two surfaces:

- Frontend: Next.js app from the repository root, typically on Vercel
- Backend: FastAPI container from `backend/`, typically on Railway, Fly.io, or a VM

## Frontend Build Contract

The frontend is Bun-managed.

```bash
bun install --frozen-lockfile
bun run build
```

Production runtime:

```bash
bun run start -- --hostname 0.0.0.0 --port 3000
```

## Backend Runtime Contract

The backend starts from `backend/server.py`:

```bash
cd backend
python server.py
```

Container deployments should expose `/ready` for readiness and `/health` for deeper health checks.

## Required Production Configuration

Backend:

- `ENVIRONMENT=production`
- One of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY`
- `DATABASE_URL` or `DATABASE_URL_DIRECT`
- `ALLOWED_ORIGINS` with the production frontend origin

Frontend:

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_WS_URL`
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`

Common add-ons:

- `SENTRY_DSN`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`

## GitHub Actions

Pushes to `main` trigger the repository deploy workflow in [deploy.yml](/Users/natalyscaturchio/code/blog-AI/.github/workflows/deploy.yml). The workflow:

1. Detects whether frontend, backend, or both changed.
2. Builds the frontend with Bun.
3. Builds and publishes the backend container image when backend files changed.

## Manual Release

```bash
gh workflow run deploy.yml --ref main
```

## Rollback

Frontend:

- Promote a previous Vercel deployment, or revert the commit and push `main`

Backend:

- Redeploy a previous container image tag, or revert the commit and push `main`

## More Specific Guides

- [README](README.md)
- [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md)
- [docs/DEPLOYMENT_VERCEL_RAILWAY_NEON.md](docs/DEPLOYMENT_VERCEL_RAILWAY_NEON.md)
