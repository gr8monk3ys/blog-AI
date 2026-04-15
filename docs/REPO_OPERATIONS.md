# Repo Operations

This repo is now organized as a small monorepo:

- `apps/web`: Next.js frontend
- `apps/api`: FastAPI backend
- `apps/extension`: browser extension

The maintenance problem is no longer repo sprawl. It is backlog discipline.

## Baseline Checks

Run these before merging anything non-trivial:

```bash
bun run lint
bun run type-check
bun run test:run
bun run test:api:smoke
bun run audit:runtime
```

Use this when touching backend routing or startup behavior:

```bash
bun run test:api:blocking
```

Use this before release candidates or production deploy decisions:

```bash
bun run test:api:full
```

## Weekly Triage

1. Review open PRs and close stale automation PRs that no longer fit the current stack.
2. Review Dependabot PRs by ecosystem, not one-by-one.
3. Review security findings and clear anything already fixed by lockfile or transitive updates.
4. Review open issues and keep roadmap items separate from actionable bugs.

## Issue Hygiene

Current issue usage is roadmap-heavy. Keep it that way, but be explicit:

- Leave epics/sprints as planning issues.
- Open bugs only for concrete regressions, broken flows, or production risks.
- Close issues that are really notes, ideas, or already-covered sprint work.
- Do not mix implementation checklists into unrelated bug reports.

Recommended working labels:

- `bug`: confirmed defect
- `security`: vulnerability, secret leak, auth flaw, unsafe dependency
- `ops`: CI, deploy, infra, monitoring, alerting
- `parity`: roadmap execution work
- `p0` / `p1`: actual priority, not aspiration

## PR Hygiene

- Keep bot PRs small and isolated.
- Close grouped upgrade PRs that bundle framework migrations with routine maintenance.
- Merge workflow-only dependency bumps quickly if CI stays green.
- Treat deploy-policy PRs separately from code cleanup.

## Dependabot Notes

Dependabot must follow the monorepo layout:

- `pip`: `/apps/api`
- `npm`: `/apps/web`
- `github-actions`: `/`

GitHub still labels JavaScript dependency updates as `npm`, even though local development and CI now use Bun.

If alerts or update PRs look stale, check the manifest path first before assuming the repo is neglected.

## Security Notifications

Use this order:

1. `bun run audit:runtime`
2. `pip-audit` in `apps/api`
3. GitHub Dependabot alerts
4. workflow scanners (`security.yml`, org-level scanners, CodeQL if enabled at repo/org level)

If GitHub shows alerts that local audit no longer reproduces, clear them after verifying the lockfile on `main`.

## Current Reality

As of March 10, 2026:

- Open PRs: none
- Open issues: roadmap issues `#58` through `#64`
- Frontend checks: passing locally
- Backend smoke checks: passing locally
- Backend full test suite: passing locally once async test dependencies are installed

The next operational risk is not code organization. It is letting backlog noise accumulate again.
