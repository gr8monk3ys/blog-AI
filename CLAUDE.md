# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Blog AI is a monorepo for brand-safe AI content operations: drafting, SEO, analytics, and publishing workflows. It has three product surfaces: a Next.js web app, a FastAPI backend, and a browser extension.

## Commands

### Frontend (from repo root, uses Bun)

```bash
bun install              # Install dependencies
bun dev                  # Start Next.js dev server (apps/web)
bun run build            # Build the web app
bun run lint             # ESLint
bun run lint:fix         # ESLint with autofix
bun run type-check       # TypeScript check (tsc --noEmit)
bun run test:run         # Vitest once
bun run test:coverage    # Vitest with coverage
bun run test:e2e         # Playwright E2E (Chromium, starts its own dev server)
bun run audit:runtime    # Runtime audit policy
```

### Backend (from apps/api)

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python server.py                    # Start FastAPI on :8000
pytest -q                           # Run all backend tests
pytest tests/test_ci_smoke.py -q    # Quick smoke tests only
```

From repo root:
```bash
bun run test:api:smoke    # Smoke suite (pytest)
bun run test:api:full     # Full backend suite (pytest)
```

### Running a single test

```bash
# Frontend (Vitest) — single file
cd apps/web && bunx vitest run tests/lib/config.test.ts

# Frontend (Playwright) — single spec
cd apps/web && bunx playwright test e2e/navigation.spec.ts

# Backend (pytest) — single file
cd apps/api && pytest tests/test_blog.py -q

# Backend — single test function
cd apps/api && pytest tests/test_blog.py::test_function_name -q
```

### Pre-PR checks

```bash
bun run lint && bun run type-check && bun run test:run && bun run build && bun run audit:runtime
# For backend changes: bun run test:api:smoke
# For UI changes: bun run test:e2e
```

## Architecture

### Monorepo Layout

- **`apps/web`** — Next.js 16 frontend (Bun workspace, React 18, Tailwind, Clerk auth, Sentry)
- **`apps/api`** — FastAPI backend (Python 3.12, Neon/Postgres, Stripe, multi-provider LLM)
- **`apps/extension`** — Browser extension
- **`db/migrations/`** — SQL migration files
- **`scripts/`** — Build, audit, deploy, and seed helpers

### Frontend (`apps/web`)

The web app uses Next.js 16 App Router with `proxy.ts` (not `middleware.ts`) for request interception. The proxy handles Clerk auth protection and injects per-request CSP nonces.

Key structure:
- **`app/`** — App Router pages and API routes. Route handlers under `app/api/` proxy to the FastAPI backend.
- **`components/`** — React components organized by feature domain (brand, analytics, seo, tools, etc.) plus shared `ui/` components.
- **`lib/`** — Shared utilities: API client (`api.ts`), Clerk wrappers (`clerk-auth.ts`, `clerk-ui.tsx`), Neon DB client (`db.ts`), config.
- **`hooks/`** — Custom hooks: `useTheme`, `useToast`, `useConfirmModal`, `useLlmConfig`.
- **`types/`** — TypeScript type definitions per domain.
- **`e2e/`** — Playwright E2E tests.
- **`tests/`** — Vitest unit tests mirroring app structure.

Provider wrapping chain: `ClerkProvider` (conditional on key) → `ThemeProvider` → `ErrorBoundary` + `ConnectionStatus`.

Path alias: `@` resolves to `apps/web/` root (configured in vitest and tsconfig).

### Backend (`apps/api`)

FastAPI app assembled in `server.py` with routes registered from `app/routes/`. Business logic lives in `src/` organized by domain.

Key structure:
- **`server.py`** — Main entry point. Loads `.env`, configures Sentry, validates config, registers all route modules.
- **`src/config.py`** — Pydantic Settings-based configuration (`get_settings()` singleton). Groups: LLM, database, Stripe, auth, feature flags.
- **`src/text_generation/core.py`** — Multi-provider LLM client (OpenAI, Anthropic, Gemini) with retry/rate-limiting.
- **`src/types/`** — Pydantic models and provider configs.
- **`app/routes/`** — ~35 FastAPI route modules (blog, book, brand, payments, SEO, social, workflows, etc.).
- **`tests/`** — pytest suite. `test_ci_smoke.py` and `test_feature_smoke.py` are the fast CI gates.

### How Frontend Talks to Backend

The frontend uses `NEXT_PUBLIC_API_URL` (default `http://localhost:8000` in dev) to reach the FastAPI backend. `lib/api.ts` exports `API_BASE_URL` and WebSocket URL derivation. Some Next.js API routes in `app/api/` act as thin proxies to the backend.

### Deployment

- **Web**: Vercel (vercel.json at repo root, `outputDirectory: apps/web/.next`)
- **API**: Railway or container host (Dockerfile.backend)
- **Database**: Neon Postgres
- **Auth**: Clerk
- **Billing**: Stripe
- **Monitoring**: Sentry (both frontend and backend)

### Environment Files

- **`.env`** — Backend config (LLM keys, database, Stripe). Symlinked into `apps/api/.env`.
- **`apps/web/.env.local`** — Frontend-specific (API URL, Clerk keys, Sentry DSN).
- Minimum local dev: `OPENAI_API_KEY` in `.env`, `NEXT_PUBLIC_API_URL=http://localhost:8000` in `apps/web/.env.local`.

## Conventions

- **Package manager**: Bun for the frontend workspace. Python pip/poetry for the backend.
- **Commit messages**: Conventional prefixes (`feat:`, `fix:`, `docs:`, `chore:`).
- **Python formatting**: Black (line-length 88) + isort (black profile) + Ruff. Pre-commit hooks enforce this.
- **TypeScript linting**: ESLint flat config (`eslint.config.mjs`) with `@typescript-eslint`, Next.js core-web-vitals, and react-hooks rules. `no-explicit-any` is warn-level.
- **Testing**: Vitest (jsdom) for frontend unit tests, Playwright for E2E, pytest for backend. Coverage thresholds: branches 70%, functions/lines/statements 85%.
- **Turbopack**: Default bundler in dev. E2E tests use `--webpack` flag for stability.
- **Clerk auth is optional in dev**: When `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is unset, all routes are publicly accessible. Protected routes are enforced only when Clerk is configured.
