# Contributing

Blog AI uses a Bun-first frontend and a Python backend. Keep changes small, tested, and documented.

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
cp .env.local.example .env.local
```

Start the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Start the frontend from the repository root:

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
```

For UI or flow changes, also run:

```bash
bun run test:e2e
```

For backend changes, run:

```bash
cd backend
pytest -q
```

## Pull Requests

1. Branch from `main`.
2. Keep commits focused and use conventional commit prefixes such as `feat:`, `fix:`, `docs:`, or `chore:`.
3. Update docs when behavior, setup, or deployment changes.
4. Add or update tests for user-facing behavior.
5. Include screenshots for meaningful UI changes.

## Project Layout

```text
blog-AI/
├── app/          Next.js routes and pages
├── backend/      FastAPI app, tests, and Python services
├── components/   Shared React components
├── docs/         Reference docs
├── e2e/          Playwright tests
├── lib/          Shared frontend utilities
├── public/       Static assets and marketing page
└── scripts/      Build, audit, and operational helpers
```

## Security

- Never commit secrets or filled-in env files.
- Treat `.env` and `.env.local` as local-only.
- Report security issues privately instead of opening a public issue.
