# Blog AI

<p align="center">
  <img src="docs/assets/readme-cover.jpg" alt="Blog AI homepage" width="1200" />
</p>

<p align="center">
  Brand-safe AI content operations for drafting, SEO, analytics, and repeatable publishing workflows.
</p>

<p align="center">
  <a href="https://github.com/gr8monk3ys/blog-AI/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/gr8monk3ys/blog-AI/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Bun 1.3+" src="https://img.shields.io/badge/Bun-1.3%2B-black?logo=bun">
  <img alt="Next.js 16" src="https://img.shields.io/badge/Next.js-16-black?logo=next.js">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Python%203.12-009688?logo=fastapi">
  <a href="LICENSE"><img alt="License: AGPL-3.0" src="https://img.shields.io/badge/License-AGPL--3.0-blue.svg"></a>
</p>

## Overview

Blog AI is a monorepo with three product surfaces:

- `apps/web`: Next.js application for content teams
- `apps/api`: FastAPI backend for generation, quotas, and integrations
- `apps/extension`: browser extension

The product is positioned around repeatable publishing, not generic prompt-box output: brand voice controls, structured drafting, SEO workflows, history, analytics, and monetization hooks.

## Highlights

- Bun-first frontend workflow with a committed `bun.lock`
- Next.js 16 web app with React 18, Clerk, and Sentry
- FastAPI backend with Neon/Postgres, Stripe, and quota-based product logic
- Blocking CI: full backend pytest suite, frontend lint/type/unit/E2E, and a
  dependency-audit gate that fails on any high/critical advisory
- Coverage measured honestly (`all: true`) with ratchet floors that only move up

## Quick Start

### Prerequisites

- Bun `1.3+`
- Python `3.12+`
- Git
- At least one LLM API key

### 1. Install dependencies

```bash
git clone https://github.com/gr8monk3ys/blog-AI.git
cd blog-AI
bun install
```

### 2. Configure env files

```bash
cp .env.example .env
cp .env.local.example apps/web/.env.local
```

Minimum local values:

- `.env`
  - `OPENAI_API_KEY=...`
  - `ENVIRONMENT=development`
- `apps/web/.env.local`
  - `NEXT_PUBLIC_API_URL=http://localhost:8000`
  - `NEXT_PUBLIC_WS_URL=ws://localhost:8000`

### 3. Start the backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

### 4. Start the web app

```bash
cd /path/to/blog-AI
bun dev
```

Open `http://localhost:3000`.

## Bun Commands

| Command | Purpose |
| --- | --- |
| `bun dev` | Start the Next.js app in `apps/web` |
| `bun run build` | Build the web app |
| `bun run start` | Start the production web app |
| `bun run lint` | Run ESLint for `apps/web` |
| `bun run type-check` | Run TypeScript checks for `apps/web` |
| `bun run test:run` | Run Vitest once |
| `bun run test:coverage` | Run Vitest with coverage |
| `bun run test:e2e` | Run Playwright end-to-end tests |
| `bun run test:e2e:coverage` | Run the E2E coverage gate |
| `bun run audit:runtime` | Run the Bun-based runtime audit policy |
| `bun run db:migrate` | Apply SQL migrations from `db/migrations/` |

## Backend Commands

| Command | Purpose |
| --- | --- |
| `cd apps/api && python server.py` | Start the FastAPI app locally |
| `cd apps/api && pytest -q` | Run backend tests |
| `bun run test:api:smoke` | Run the blocking backend smoke suite from the repo root |
| `bun run test:api:full` | Run the full backend suite from the repo root |

## Deployment

- Web: Vercel
- API: Railway or another container host
- Database: Neon Postgres
- Auth: Clerk
- Billing: Stripe

Key references:

- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [docs/DEPLOYMENT_VERCEL_RAILWAY_NEON.md](docs/DEPLOYMENT_VERCEL_RAILWAY_NEON.md)
- [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)

## Repository Layout

```text
blog-AI/
├── apps/
│   ├── api/         FastAPI backend
│   ├── extension/   Browser extension
│   └── web/         Next.js app
├── db/              SQL migrations
├── docs/            Operational and technical docs
├── scripts/         Build, audit, and release helpers
└── package.json     Bun-first workspace shell
```

## Quality Bar

Enforced by CI on every PR (see `.github/workflows/ci.yml`):

- `bun run lint`, `bun run type-check`, and `bun run build` pass
- Vitest unit suite passes with coverage at or above the ratchet floor
- Playwright E2E suite passes
- Full backend pytest suite passes (blocking), plus per-route coverage gates
- `bun run audit:runtime` passes — zero unallowlisted high/critical advisories

## Notes

- The React homepage is rendered by `HomePageClient` at `/` (a previous
  static `home.html` rewrite was removed; see git history).
- Dependabot still uses the GitHub `npm` ecosystem for `apps/web`, but day-to-day development and CI now run through Bun.
