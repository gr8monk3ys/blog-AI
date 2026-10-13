# Deployment

What actually serves production today (verified 2026-10-13 against the live site's CSP,
the Vercel project list and `GET /health` on the API host):

| Piece | Where | Entry point / config | URL |
|-------|-------|----------------------|-----|
| `apps/web` (Next.js) | Vercel project `blog-ai`, root directory = repo root | root `vercel.json` (`bun run build`, output `apps/web/.next`) | https://blog-ai.vivancedata.com |
| `apps/api` (FastAPI) | **Vercel project `blog-ai-api`, Python runtime** | `apps/api/vercel.json` (one function, `server.py`, `maxDuration` 300) + `[tool.vercel] entrypoint = "server:app"` in `apps/api/pyproject.toml` | https://blog-ai-api-gr8monk3ys-projects.vercel.app |
| Postgres | Neon | `DATABASE_URL` (pooled) in both projects; `DATABASE_URL_DIRECT` for migrations | — |
| Auth | Clerk, custom domain | `NEXT_PUBLIC_CLERK_DOMAIN=clerk.vivancedata.com`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY` (web); `CLERK_JWKS_URL`, `CLERK_JWT_ISSUER` (API) | https://clerk.vivancedata.com |
| Billing | Stripe | `STRIPE_*` on the API | — |
| Errors | Sentry (`vivance` org, shared quota) | `NEXT_PUBLIC_SENTRY_DSN` (web), `SENTRY_DSN` (API) — see [MONITORING.md](./MONITORING.md) | — |

The API is **not** on Railway. `railway.json`, `Dockerfile.backend` and the GHCR image that
`.github/workflows/deploy.yml` publishes are an **alternative container path, not what
production runs**; they are kept so the API can be moved to a container host later without
re-deriving them. Nothing live pulls that image.

What the live API reported on 2026-10-13 (`GET /health`): status `healthy`, database
connected, Redis disconnected (not configured), OpenAI and Anthropic configured, Gemini
not, payments available, `web_research` **not** available (no `SERP_API_KEY` /
`TAVILY_API_KEY`). So research mode, fact-check sources and SERP analysis do not work in
production today, and anything that needs Redis (shared rate limits, bulk jobs across
workers) runs in-memory. `apps/web/lib/features.ts` is where the web app decides what it
may advertise given this.

## Owner to-do (Vercel dashboard — the repo cannot do these)

1. **`blog-ai-api` does not track `main`.** Its last production deploy (2026-08-23) came
   from the since-deleted branch `deploy/vercel-api`, whose SHA is not in `main`'s
   history. Set the project's **Production Branch to `main`** and its **Root Directory to
   `apps/api`** (Settings → Git / General), then trigger a redeploy. Until then every API
   change merged to `main` is invisible in production.
2. Audit the two projects' env vars against [ENVIRONMENT.md](./ENVIRONMENT.md) with
   `vercel env pull` (or `bun run env:check -- --check <pulled file>`).
3. If API errors should reach Sentry: the API's Sentry gate keys on Railway's
   `RAILWAY_ENVIRONMENT_NAME`, which Vercel never sets, so on Vercel the API reports
   nothing unless `SENTRY_FORCE_ENABLE=1` is set in the `blog-ai-api` project. Decide
   whether you want that against the shared quota before setting it.
4. On Vercel's Python runtime the filesystem is ephemeral: `API_KEY_STORAGE_PATH`,
   `USAGE_STORAGE_DIR` and `CONVERSATION_STORAGE_DIR` (defaults under `./data`) do not
   persist between invocations. API keys issued with `scripts/create_api_key.py` and
   file-based usage counters are lost on every cold start. Use `DATABASE_URL` for anything
   that must survive, or move the API to the container path below.

## How a deploy happens

- **Web.** Vercel's Git integration builds every push (previews for PRs, production for
  `main`). `deploy.yml` additionally runs `vercel --prod` through `amondnet/vercel-action`
  after `CI` succeeds on `main`, when `VERCEL_TOKEN` / `VERCEL_ORG_ID` /
  `VERCEL_PROJECT_ID` secrets are present; without them it logs a warning and skips.
  `next.config.mjs` refuses a `VERCEL_ENV=production` build without `NEXT_PUBLIC_API_URL`
  and valid Clerk keys.
- **API.** Vercel's Git integration on the `blog-ai-api` project (see owner to-do 1).
  There is no GitHub Action that deploys the API; `deploy.yml`'s backend job only builds
  and pushes the container image.
- **Database.** Migrations are not run by any deploy. Run them from a machine or CI with
  the direct URL:
  ```bash
  export DATABASE_URL_DIRECT="postgresql://..."   # Neon direct (non-pooled) string
  bun run db:migrate                               # db/migrations/*.sql -> schema_migrations
  cd apps/api && uv run python server.py --migrate # apps/api/migrations/*.sql -> _migrations
  ```
  See [DATABASE.md](./DATABASE.md) for which tables each set owns.

## After a deploy

- `scripts/post_deploy_health_check.sh` (run by `post-deploy-health-check.yml` after
  `Deploy` and hourly) checks the public routes, `GET /api/health` on the web app (fails
  on 503) and, when `VERCEL_TOKEN` is available, the deployment status and recent
  production logs. The workflow then probes the API's `GET /health` directly, resolving the
  API host from `vars.API_BASE_URL` or the live CSP `connect-src`.
- `deploy-watchdog.yml` fails daily if the newest `main` commit has no successful
  Production deployment attached (the silent-drop failure mode from 2026-09-14).
- Health endpoints:
  - Web `GET /api/health`: `status`, `version`, `commit`, and `checks.db` / `checks.api`
    / `checks.clerk`; 200 when every configured dependency is ok, 503 otherwise. No auth,
    no secrets.
  - API `GET /health`: status, version (from `pyproject.toml`), database/Redis latency,
    configured LLM providers, feature availability. `GET /ready`: 200 when an LLM key is
    present. Per-service `/health/*` routes require an API key.

## Minimum production environment

Web (Vercel `blog-ai`): `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`,
`CLERK_SECRET_KEY`, `NEXT_PUBLIC_CLERK_DOMAIN`, `DATABASE_URL`, `NEXT_PUBLIC_SITE_URL`.

API (Vercel `blog-ai-api`): `ENVIRONMENT=production`, `ALLOWED_ORIGINS` (the web origin;
localhost entries are stripped and the process exits if none remain), `DATABASE_URL`,
`CLERK_JWKS_URL`, `CLERK_JWT_ISSUER`, at least one of `OPENAI_API_KEY` /
`ANTHROPIC_API_KEY`, and the `STRIPE_*` set for billing.

The full list with required/optional per environment is in
[ENVIRONMENT.md](./ENVIRONMENT.md); `bun run env:check` prints the same table from the
code.

## Local production-like run

```bash
bun install --frozen-lockfile && bun run build && bun run start   # web :3000
cd apps/api && uv sync && uv run python server.py                 # API :8000 (reads PORT)
```

## Alternative: API as a container (not what production runs)

`Dockerfile.backend` builds the API with `uv sync --locked --no-dev` into
`python:3.12-slim`; `deploy.yml` pushes it to `ghcr.io/gr8monk3ys/blog-ai-backend` tagged
with the commit SHA and `latest`. `railway.json` describes how Railway would run that image
(`/health` as the health check). To use this path on any container host: run the image,
set the API environment above plus `PORT`, and point `NEXT_PUBLIC_API_URL` /
`ALLOWED_ORIGINS` at each other. The API's Sentry gate recognises Railway's environment
variables natively; other hosts need `SENTRY_FORCE_ENABLE=1`.

## Related

- [Environment variables](./ENVIRONMENT.md)
- [Monitoring](./MONITORING.md)
- [Database](./DATABASE.md)
