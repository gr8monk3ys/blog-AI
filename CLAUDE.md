# CLAUDE.md

Blog AI: Next.js web app + FastAPI API + browser extension for generating and publishing
blog posts and books with a configurable brand voice. Live at https://blog-ai.vivancedata.com.

## Layout
- `apps/web` — Next.js 16 (App Router, React 18.3 pinned, Clerk, Sentry). `proxy.ts` is the middleware.
- `apps/api` — FastAPI. `server.py` wires routes from `app/routes/`; logic in `src/`; config in `src/config.py`.
- `apps/extension` — browser extension (see its README).
- `db/migrations/` — SQL applied by `bun run db:migrate`. `apps/api/migrations/` — applied by `python server.py --migrate`. See `docs/DATABASE.md`.
- `scripts/` — migrate, seed, runtime audit, post-deploy health check.

## Run
```bash
bun install && cp .env.example .env && cp .env.local.example apps/web/.env.local
cd apps/api && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python server.py   # :8000
bun dev                                                                                                                  # :3000
```
Minimum env: `OPENAI_API_KEY` in `.env`; `NEXT_PUBLIC_API_URL=http://localhost:8000` in `apps/web/.env.local`.
Clerk is optional in dev: with no publishable key every route is public.

## Test
```bash
bun run lint && bun run type-check && bun run test:run && bun run build
bun run test:e2e                                   # Playwright, starts its own dev server
cd apps/api && DEV_MODE=true OPENAI_API_KEY=test pytest -q
```
CI (`.github/workflows/ci.yml`) also runs per-route coverage floors and DB-backed tests
against Postgres. Required checks: Backend Tests (FastAPI), Backend DB Tests (Postgres),
Frontend Checks (Next.js).

## Gotchas
- `apps/api/.env` is a symlink to the root `.env`; a populated `.env` makes `/health` report
  `degraded` and fails `test_api.py::TestHealthEndpoint` — run pytest without it.
- Node is pinned to `22.x` in `package.json` engines; Node 24 broke the Vercel build.
- Coverage thresholds are ratchets: raise them, never lower them to pass a build.
- Python style: black 88 / isort (black profile) / ruff, enforced by pre-commit.
