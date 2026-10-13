# CLAUDE.md

Blog AI: Next.js web app + FastAPI API + browser extension for generating and publishing
blog posts and books with a configurable brand voice. Bun workspace (`apps/web`) plus a
uv-managed Python app (`apps/api`). Live at https://blog-ai.vivancedata.com. The repo is
public: nothing committed here is private.

## Layout
- `apps/web` — Next.js 16 (App Router, React 19, TypeScript 6, Tailwind 3, Clerk, Sentry).
  `proxy.ts` is the middleware (per-request CSP nonce). Unit tests in `tests/` (Vitest + jsdom),
  Playwright journeys in `e2e/`.
- `apps/api` — FastAPI. `server.py` wires routes from `app/routes/`; logic in `src/`; config in
  `src/config.py`; tests in `tests/`. `pyproject.toml` + `uv.lock` are the source of truth;
  `requirements.txt` mirrors the dependency table for pip users and must be kept in sync.
- `apps/extension` — browser extension (see its README).
- `db/migrations/` — SQL applied by `bun run db:migrate`. `apps/api/migrations/` — applied by
  `python server.py --migrate`. See `docs/DATABASE.md`.
- `scripts/` — migrate, seed, runtime audit, Lighthouse/a11y gates, post-deploy health check.
- `Dockerfile.backend` — the API image published to GHCR by `deploy.yml`; it installs with
  `uv sync --locked`, so `uv.lock` must match `pyproject.toml` exactly.

## Run
```bash
bun install && cp .env.example .env && cp .env.local.example apps/web/.env.local
cd apps/api && uv sync && uv run python server.py     # :8000 (or: python -m venv .venv && pip install -r requirements.txt)
bun dev                                                # :3000
```
Minimum env: `OPENAI_API_KEY` in `.env`; `NEXT_PUBLIC_API_URL=http://localhost:8000` in
`apps/web/.env.local`. Clerk is optional in dev: with no publishable key every route is public.
Without `DATABASE_URL`, history, brand profiles and analytics fall back to in-memory storage.

## Test
```bash
bun install --frozen-lockfile                       # what CI runs; fails if bun.lock drifted
bun run lint && bun run type-check && bun run test:run && bun run build
bun run test:e2e                                    # Playwright, starts its own dev server
cd apps/api && DEV_MODE=true OPENAI_API_KEY=test pytest -q
```

CI (`.github/workflows/ci.yml`) runs seven jobs on every PR and on every push to main:
`Backend Tests (FastAPI)` (smoke suite + per-route coverage floors), `Backend Regression
(blocking)` (full pytest), `Frontend Checks (Next.js)` (frozen install → lint → type-check →
`test:coverage` → build), `Lighthouse (score floors)` (production build, score + byte budget on
`/`, `/pricing`, `/blog`, `/tools`, then a dark-mode axe pass), `Frontend E2E (Playwright)`
(e2e with coverage gate), `Schema Smoke (fresh-install migration)` (applies `db/migrations`
to a fresh Postgres 16 and asserts the tables the code references exist) and `Backend DB Tests
(Postgres)` (asyncpg-backed tests against a real database). Main requires three of them:
`Backend DB Tests (Postgres)`, `Backend Tests (FastAPI)` and `Frontend Checks (Next.js)`; the
other four still have to be green before a PR is considered done. After CI passes on main,
`deploy.yml` deploys the web app to Vercel and publishes the backend image to GHCR;
`post-deploy-health-check.yml` probes production afterwards and hourly, `deploy-watchdog.yml`
checks daily that the newest main commit has a live production deploy, and `preview.yml`
deploys a Vercel preview per PR.

## Working in this repo
- Work in a git worktree under `.worktrees/<slug>` (the folder is ignored via
  `.git/info/exclude`), one branch per PR, created from `origin/main`. Never edit the main
  checkout except to fast-forward `main`; never touch another session's worktree.
- Commits follow Conventional Commits (`feat:`, `fix:`, `perf:`, `build:`, `ci:`, `docs:`,
  `chore:` …) because that is what cuts releases (below). Squash-merge PRs so the squash title is
  the conventional message.
- Bun is pinned to 1.4.3 (`packageManager` and `engines.bun` in `package.json`,
  `packageManager` in `apps/web/package.json`, `BUN_VERSION` in `ci.yml` and `preview.yml`,
  `bun-version` in `post-deploy-health-check.yml`). Run that version locally (`bun upgrade`) and
  bump all six places together.

## Releases

Releases are cut by `release-please` (`.github/workflows/release-please.yml`,
`release-please-config.json`, `.release-please-manifest.json`) from the conventional commits on
main. Every push to main refreshes one release PR that bumps the version in four files — root
`package.json`, `apps/web/package.json`, `apps/api/pyproject.toml` (`[project] version`) and
`apps/api/uv.lock` (the `blog-ai-api` package entry) — and writes `CHANGELOG.md`. Merging it
tags `vX.Y.Z`, publishes a GitHub Release, and deploys like any main push. A `feat` bumps
minor, a `fix` bumps patch, a `!`/`BREAKING CHANGE` bumps major; `Release-As: x.y.z` in a
commit footer forces a version. `docs`, `chore`, `build`, `ci`, `test`, `refactor` and `style`
commits are hidden from the changelog and do not trigger a release on their own.

The release PR is opened with `GITHUB_TOKEN`, so no CI runs on it and the required checks never
report; merge it with `gh pr merge <N> --squash --admin`, and only after `gh pr diff <N>` shows
exactly `CHANGELOG.md` plus the version line in those four files. Anything else in that diff
means something is wrong (most likely a dependency landed in `pyproject.toml` without
`uv lock`), not that the bypass should widen. The `uv.lock` entry in the config filters on
`@.name.value`, not `@.name`: release-please's TOML parser wraps scalars in a
`{start, end, value}` record to replace them in place, and a filter on the bare key matches
nothing (verified against release-please 17.x).

## Gotchas
- `bun.lock` is `lockfileVersion` 1 and Bun 1.4.3 keeps it that way (it re-saves the same
  format). A lockfile regenerated from scratch by Bun 1.4 comes out as `lockfileVersion` 2 /
  `configVersion` 1, which Bun < 1.4 cannot read under `--frozen-lockfile` — so do not delete
  and regenerate it casually. `bunfig.toml` forces the text lockfile; a stray old Bun writes a
  binary `bun.lockb` instead of touching `bun.lock` — delete it if it appears.
- Changing `apps/api/pyproject.toml` (even only its version) without running `uv lock` makes
  `uv sync --locked` fail, which is how `Dockerfile.backend` installs. Run `uv lock` and commit
  `uv.lock` with the change.
- `apps/api/.env` is a symlink to the root `.env`; a populated `.env` makes `/health` report
  `degraded` and fails `test_api.py::TestHealthEndpoint` — run pytest without it.
- Node is pinned to `22.x` in `package.json` engines; Node 24 broke the Vercel build.
- Coverage thresholds (Vitest `thresholds`, pytest `--cov-fail-under`, the e2e coverage gate)
  are ratchets: raise them, never lower them to pass a build.
- Lighthouse builds with `NEXT_PUBLIC_API_URL=http://127.0.0.1:3000` on purpose: the home page
  pings the API root on load and the localhost:8000 fallback is blocked by the CSP, which sinks
  the best-practices score for reasons unrelated to the change under test.
- Python style: ruff + ruff-format (line length 88, `py312`), enforced by `.pre-commit-config.yaml`.
  The old black/isort config is gone; do not reintroduce it.
- Dependabot ignores TypeScript ≥ 7 (no JS compiler API for typescript-eslint) and Tailwind ≥ 4
  (a deliberate migration, not a bump); see `.github/dependabot.yml` before "fixing" that.

## Agent skills

### Issue tracker

GitHub Issues on `gr8monk3ys/blog-AI`, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical roles, label string equal to role name. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: `CONTEXT.md` + `docs/adr/` at the repo root, created lazily — neither
exists yet, and that is fine. See `docs/agents/domain.md`.
