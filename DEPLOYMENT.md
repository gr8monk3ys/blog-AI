# Deployment Guide

This document covers how Blog AI is deployed and how to operate it in production.

## Architecture

- **Frontend (Next.js)** -- deployed to Vercel automatically on push to `main`.
- **Backend (FastAPI)** -- built as a Docker image, pushed to GitHub Container Registry (`ghcr.io`), and pulled by whatever host runs the backend (self-hosted VM, Railway, Fly.io, etc.).

---

## Prerequisites

### GitHub Secrets

Configure these in **Settings > Secrets and variables > Actions**:

| Secret | Purpose |
|---|---|
| `VERCEL_TOKEN` | Vercel personal access token (Settings > Tokens) |
| `VERCEL_ORG_ID` | Vercel team/org ID (from `.vercel/project.json` or Vercel dashboard) |
| `VERCEL_PROJECT_ID` | Vercel project ID (same source as above) |

`GITHUB_TOKEN` is provided automatically and has `packages:write` permission for pushing to GHCR.

### GitHub Environment

Create a GitHub Environment named **production** under **Settings > Environments**. You can optionally add:
- Required reviewers (approval gate before deploy)
- Deployment branch rules (restrict to `main`)

### Vercel Setup

1. Import the repository in Vercel.
2. Set the root directory to `/` (the `next.config.mjs` and `package.json` are at the repo root).
3. Add all frontend environment variables in the Vercel project settings (e.g. `NEXT_PUBLIC_API_URL`, Clerk keys, Sentry DSN).
4. Note down the Org ID and Project ID for the GitHub secrets above. You can find them in `.vercel/project.json` after running `vercel link` locally, or in the Vercel dashboard under project settings.

---

## How Automatic Deployment Works

Every push to `main` triggers the **Deploy** workflow (`.github/workflows/deploy.yml`):

1. **Change detection** -- path filters determine whether frontend files, backend files, or both changed.
2. **Frontend** -- if frontend files changed, Vercel builds and deploys to production via `amondnet/vercel-action`.
3. **Backend** -- if backend files changed, the Docker image is built, tagged with the commit SHA and `latest`, and pushed to `ghcr.io/<owner>/blog-ai-backend`.

Both jobs require the `production` environment, so if you have configured approval reviewers, a human must approve before deployment proceeds.

---

## Manual Deployment

Use **workflow_dispatch** to deploy both frontend and backend regardless of file changes:

1. Go to **Actions > Deploy** in GitHub.
2. Click **Run workflow**.
3. Select the branch (defaults to `main`).
4. Click **Run workflow**.

You can also trigger it from the CLI:

```bash
gh workflow run deploy.yml --ref main
```

---

## Self-Hosted Backend Deployment

For running the backend on your own server:

```bash
# Pull the latest image
docker pull ghcr.io/<owner>/blog-ai-backend:latest

# Or use docker compose
# 1. Copy docker-compose.deploy.yml and .env to your server
# 2. Set GITHUB_REPOSITORY in your shell or .env
export GITHUB_REPOSITORY=your-org/blog-ai

# 3. Start services
docker compose -f docker-compose.deploy.yml up -d

# 4. Check health
curl http://localhost:8000/ready
curl http://localhost:8000/health
```

---

## Rollback

### Option A: Revert the commit

```bash
git revert <commit-sha>
git push origin main
```

This triggers a new deployment with the reverted code.

### Option B: Deploy a previous commit

```bash
# Run the deploy workflow on a specific ref
gh workflow run deploy.yml --ref <commit-sha>
```

### Option C: Pull a previous Docker image (backend only)

```bash
# Tag format is the short commit SHA
docker pull ghcr.io/<owner>/blog-ai-backend:<previous-sha>
docker compose -f docker-compose.deploy.yml up -d
```

### Option D: Vercel instant rollback (frontend only)

In the Vercel dashboard, go to **Deployments**, find the previous production deployment, and click **Promote to Production**.

---

## Required Production Environment Variables

These must be set in your `.env` file (backend) and/or Vercel project settings (frontend).

### Critical (backend)

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | At least one LLM provider key is required |
| `ENVIRONMENT` | Set to `production` |
| `DATABASE_URL` | Neon/Postgres connection string |
| `ALLOWED_ORIGINS` | Comma-separated list of frontend URLs (e.g. `https://yourdomain.com`) |
| `REDIS_URL` | Redis connection string (set automatically in docker-compose.deploy.yml) |

### Recommended (backend)

| Variable | Description |
|---|---|
| `SENTRY_DSN` | Error tracking |
| `STRIPE_SECRET_KEY` | Payment processing |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook verification |
| `CLERK_JWKS_URL` | JWT verification for Clerk auth |
| `CLERK_JWT_ISSUER` | Expected JWT issuer |

### Frontend (Vercel)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API URL (e.g. `https://api.yourdomain.com`) |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk frontend key |
| `CLERK_SECRET_KEY` | Clerk server key |
| `SENTRY_DSN` | Frontend error tracking |
| `DATABASE_URL` | For Next.js API routes / server actions |

---

## Health Check URLs

| Endpoint | Purpose | Auth |
|---|---|---|
| `GET /ready` | Lightweight readiness probe (returns 200 or 503) | None |
| `GET /health` | Comprehensive check (DB, Redis, LLM providers, Stripe) | None |
| `GET /health/db` | Database connectivity details | API key |
| `GET /health/redis` | Redis connectivity details | API key |
| `GET /health/stripe` | Stripe API status | API key |
| `GET /health/sentry` | Sentry configuration status | API key |

The Docker healthcheck and Kubernetes/ECS probes should use `/ready` for liveness and readiness checks.
