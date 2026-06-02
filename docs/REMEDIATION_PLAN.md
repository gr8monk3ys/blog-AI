# Remediation Plan

Living tracker for the codebase remediation effort. Status legend:
`TODO` · `IN PROGRESS` · `DONE` · `NEEDS-STAGING` (requires a live/staging DB to validate before cutover).

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
| P2.3 | `batch.py` (1312) → providers/item_processor/csv/lifecycle+export routers | PARTIAL — extracted `batch_providers.py` (6 tests) and `batch_csv.py` (7 tests); batch.py 1312→1265 lines. Remaining: item_processor extraction, lifecycle/export router split (needs route tests first) |
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
