# CLAUDE.md

This repository is Bun-first at the root and Python-based in `backend/`.

## Core Commands

Frontend and repo-level checks:

```bash
bun install
bun dev
bun run build
bun run lint
bun run type-check
bun run test:run
bun run test:e2e
bun run audit:runtime
bun run db:migrate
```

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
pytest -q
```

## Repository Shape

- `app/` contains the Next.js App Router.
- `components/`, `hooks/`, `lib/`, and `types/` support the frontend at the repo root.
- `public/home.html` is the ultra-fast marketing landing page, served from `/` via a rewrite in [next.config.mjs](/Users/natalyscaturchio/code/blog-AI/next.config.mjs).
- `backend/` contains the FastAPI app, migrations, and tests.

## Environment Files

- `.env` is for backend and shared server-side configuration.
- `.env.local` is for frontend local development.
- See [docs/ENVIRONMENT.md](/Users/natalyscaturchio/code/blog-AI/docs/ENVIRONMENT.md) for the active reference.

## Current Conventions

- Use Bun commands in docs, scripts, and CI for frontend work.
- Do not reintroduce a separate web-app subdirectory in new docs or examples; the frontend lives at the repository root.
- Keep the landing page fast. Changes to `/` should preserve the static rewrite and the current Lighthouse target.
