# Contributing

Blog AI uses a Bun-first frontend workspace and a Python backend. Keep changes focused, tested, and documented.

## Prerequisites

- Bun `1.3+`
- Python `3.12+`
- Git

## Local Setup

```bash
git clone https://github.com/gr8monk3ys/blog-AI.git
cd blog-AI
bun install
cp .env.example .env
cp .env.local.example apps/web/.env.local
```

Start the backend:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Start the web app from the repository root:

```bash
bun dev
```

## Common Checks

Run the relevant checks before opening a PR:

```bash
bun run lint
bun run type-check
bun run test:run
bun run build
bun run audit:runtime
```

For backend changes, also run:

```bash
bun run test:api:smoke
cd apps/api && pytest -q
```

For UI or user-flow changes, also run:

```bash
bun run test:e2e
```

## Pull Requests

1. Branch from `main`.
2. Keep commits focused and use conventional commit prefixes such as `feat:`, `fix:`, `docs:`, or `chore:`.
3. Update docs when setup, deployment, or user-facing behavior changes.
4. Add or update tests for material behavior changes.
5. Include screenshots for meaningful UI changes.

## Project Layout

```text
blog-AI/
├── apps/web      Next.js frontend
├── apps/api      FastAPI backend
├── apps/extension Browser extension
├── db            SQL migrations
├── docs          Operational and technical docs
└── scripts       Build, audit, and release helpers
```

## Security

- Never commit secrets or filled-in env files.
- Keep `.env` and `apps/web/.env.local` local-only.
- Report security issues privately rather than opening a public issue.
