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
| P1.1 | Frontend coverage `all: true` + ratchet to real baseline | DONE |
| P1.2 | Backfill tests for highest-risk untested surfaces | TODO (ongoing) |
| P1.3 | Expand backend coverage gate beyond 5 routes | TODO |

## P2 — Maintainability (god-file refactors)

| ID | File | Status |
|----|------|--------|
| P2.1 | `marketing_templates.py` (1944) → fields/categories/per-category modules | TODO |
| P2.2 | `rate_limit.py` (1288) → backends/models/shared base | TODO |
| P2.3 | `batch.py` (1312) → providers/item_processor/csv/lifecycle+export routers | TODO |
| P2.4 | `BulkGenerationPageClient.tsx` (1164) → constants/csv/hooks/components | TODO |
| P2.5 | `HomePageClient.tsx` (858) → data/animations/sections | TODO |

## P3 — Onboarding & hygiene

| ID | Item | Status |
|----|------|--------|
| P3.1 | Tier `.env.example` (required vs optional) | TODO |
| P3.2 | Audit the 7 `eslint-disable`s | TODO |
| P3.3 | Document Next 16 / React 18 pin + React 19 follow-up | TODO |
| P3.4 | Consolidate rollback docs (after P0.1) | TODO |

## Sequencing

1. **Foundations (this wave):** P0.2, P3.3, schema audit for P0.1.
2. **Test honesty:** P1.1 (coverage `all: true`), then P1.2/P1.3 backfills.
3. **Refactors (test-covered first):** P2.5 → P2.1 → P2.4 → P2.3 → P2.2.
4. **Hygiene in parallel:** P3.1, P3.2, P3.4.
5. **P0.1 cutover:** only after validating the consolidated schema against a staging DB.
