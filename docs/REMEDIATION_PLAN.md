# Remediation Plan

Living tracker for the codebase remediation effort. Status legend:
`TODO` · `IN PROGRESS` · `DONE` · `NEEDS-STAGING` (requires a live/staging DB to validate before cutover).

---

## Comprehensive Roadmap (v2)

Diagnosis: the repo has the apparatus of a production SaaS on top of an
ambitious, heavily-scaffolded prototype. The work is **finishing and making the
gauges tell the truth**, not rewriting. Phases are ordered by real-world risk.

### Phase 0 — Truth & safety (stop the bleeding)
| # | Item | Status |
|---|------|--------|
| 0.1 | Land PR #102 (makes `main` backend CI honestly green) | IN PROGRESS |
| 0.2 | **Critical Clerk auth-bypass CVE** (GHSA-vqx2-fgx2-5wq9) | DONE — bumped to @clerk/nextjs 6.39.5; 25→18 high/critical |
| 0.3 | Remaining dep CVEs | DONE — next 16.2.7, vitest 4.1.8, vite/undici/flatted overrides; picomatch (dev-only ReDoS) allowlisted. `audit:runtime` gate now passes; 0 blocking high/critical (down from 25) |
| 0.4 | Schema unification (see P0.1 / `docs/SCHEMA_AUDIT.md`) + CI schema-smoke guard | NEEDS-STAGING |
| 0.5 | Vercel preview: provide `VERCEL_TOKEN` secret or make check non-required | NEEDS-OWNER |

### Phase 1 — Decide the fate of half-features (kill the ghosts)
| # | Item | Status |
|---|------|--------|
| 1.1 | Knowledge base: finish the Supabase→Neon/pgvector migration **or** remove it (un-xfail/un-fixme when done) | TODO |
| 1.2 | Ghost-hunt sweep: orphaned pages, TDD tests for unwritten code, unreachable routes → finish/remove/keep list | TODO |

### Phase 2 — Make the gauges tell the truth
| # | Item | Status |
|---|------|--------|
| 2.1 | Ratchet coverage up toward 70/85 as tests land | ONGOING |
| 2.2 | Backfill money/security paths (payments, Stripe webhooks, SSO, quotas) | TODO |
| 2.3 | Accessibility sweep: header/footer as siblings of `<main>` repo-wide + landmark checks | IN PROGRESS (3 pages done in #102) |

### Phase 3 — Finish the structural refactors (with nets)
| # | Item | Status |
|---|------|--------|
| 3.1 | `BulkGenerationPageClient` — write bulk-flow component tests, then split the ~1,030-line hook/JSX | TODO |
| 3.2 | `batch.py` router split (lifecycle vs export) — route tests first | TODO |
| 3.3 | Remaining 1,000+ line modules — test-net first | TODO |

### Phase 4 — Keep it honest (durable hygiene)
| # | Item | Status |
|---|------|--------|
| 4.1 | Dependency automation (Dependabot grouping) so the CVE backlog can't silently rebuild | TODO |
| 4.2 | Docs-vs-reality reconciliation (`DATABASE.md`, drop unverified "100/100" claims) | TODO |
| 4.3 | Re-enable branch protection once `main` is genuinely green | NEEDS-OWNER |

---
## Original tracker (P0–P3) — completed-work record

## P0 — Correctness / single source of truth

| ID | Item | Status |
|----|------|--------|
| P0.1 | Unify schema management onto one migration system | IN PROGRESS — audit complete (`docs/SCHEMA_AUDIT.md`), consolidation NEEDS-STAGING |
| P0.2 | Make the backend full suite blocking (or explicitly quarantine) | DONE |

## P1 — Test integrity

| ID | Item | Status |
|----|------|--------|
| P1.1 | Frontend coverage `all: true` + ratchet to real baseline | DONE — floor ratcheted 9→10% after surfacing existing `lib/api.ts` coverage (was excluded; actually ~74%) + new csv tests |
| P1.2 | Backfill tests for highest-risk untested surfaces | IN PROGRESS — 19 rate-limiter tests + 6 batch-provider tests + 7 frontend csv tests (all 3 surfaces had 0); fixed a pre-existing stripe-mock test-isolation bug; more surfaces TODO |
| P1.3 | Expand backend coverage gate beyond 5 routes | DONE — added ratchet floor (50%) for organizations/sso/export/research; gate now covers 9 modules |

## P2 — Maintainability (god-file refactors)

| ID | File | Status |
|----|------|--------|
| P2.1 | `marketing_templates.py` (1944) → fields/categories/per-category modules | DONE — assembler is 42 lines; 7 category modules (≤369 lines); registry SHA verified identical |
| P2.2 | `rate_limit.py` (1288) → backends/models/shared base | DONE — backends → `rate_limit_backends.py`; `RateLimiter`/`GenerationRateLimiter` deduped onto shared `_BaseRateLimiter` (1288→880 lines). 19 rate-limiter tests; full suite green |
| P2.3 | `batch.py` (1312) → providers/item_processor/csv/lifecycle+export routers | PARTIAL — extracted `batch_providers.py` (6 tests), `batch_csv.py` (7 tests), and `batch_item_processor.py`; batch.py 1312→1076 lines. Remaining: lifecycle/export router split (needs route tests first) |
| P2.4 | `BulkGenerationPageClient.tsx` (1164) → constants/csv/hooks/components | PARTIAL — extracted `constants.ts` + pure `csv.ts` (1164→1074 lines) + 7 vitest tests for parseCSV/createDraftItem. Remaining: split the page-view hook and the 600-line render into components |
| P2.5 | `HomePageClient.tsx` (858) → data/animations/sections | DONE — extracted `_home/data.ts` + `_home/animations.ts` (858→622 lines) |

## P3 — Onboarding & hygiene

| ID | Item | Status |
|----|------|--------|
| P3.1 | Tier `.env.example` (required vs optional) | DONE — quick-start block added |
| P3.2 | Audit the 7 `eslint-disable`s | DONE — all intentional; justifications added |
| P3.3 | Document Next 16 / React 18 pin + React 19 follow-up | DONE |
| P3.4 | Consolidate rollback docs (after P0.1) | TODO (blocked on P0.1 cutover) |

## Sequencing

1. **Foundations (this wave):** P0.2, P3.3, schema audit for P0.1.
2. **Test honesty:** P1.1 (coverage `all: true`), then P1.2/P1.3 backfills.
3. **Refactors (test-covered first):** P2.5 → P2.1 → P2.4 → P2.3 → P2.2.
4. **Hygiene in parallel:** P3.1, P3.2, P3.4.
5. **P0.1 cutover:** only after validating the consolidated schema against a staging DB.
