# Remediation Plan

Single living tracker for the codebase remediation effort. Status legend:
`TODO` · `IN PROGRESS` · `DONE` · `NEEDS-STAGING` (requires a live/staging DB to
validate before cutover) · `NEEDS-OWNER` (requires a repo secret or admin action).

Diagnosis: the repo has the apparatus of a production SaaS on top of an
ambitious, heavily-scaffolded prototype. The remaining work is **finishing the
last mile so a brand-new user can run the product end to end**, and keeping the
gauges honest — not rewriting.

---

## Active focus — End-to-end usability

These are the gaps that block a fresh install / new user. Ordered by how hard
they break the first-run experience.

| # | Item | Status |
|---|------|--------|
| E1 | Fresh-install schema completion — `db:migrate` must produce a working DB (see `docs/SCHEMA_AUDIT.md`) | NEEDS-STAGING |
| E2 | CSV bulk import round-trip (quoted-comma parsing + consistent comma delimiter across template/parser/editor) | DONE |
| E3 | Gate the `/knowledge` nav link behind `NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE` so the UI never links to a flagged-off backend | DONE |
| E4 | `/auth` no longer dead-ends when Clerk is unconfigured — routes new users straight into the workspace | DONE |
| E5 | Stripe pre-flight: surface missing price IDs clearly before checkout instead of warn-only | TODO |

---

## Phase 0 — Truth & safety (stop the bleeding)

| # | Item | Status |
|---|------|--------|
| 0.1 | Backend CI honestly green on `main` (PR #102) | DONE |
| 0.2 | **Critical Clerk auth-bypass CVE** (GHSA-vqx2-fgx2-5wq9) | DONE — bumped to @clerk/nextjs 6.39.5 |
| 0.3 | Remaining dep CVEs | DONE — `audit:runtime` gate passes; 0 blocking high/critical (down from 25) |
| 0.4 | Schema unification + CI schema-smoke guard (= E1) | NEEDS-STAGING |
| 0.5 | Vercel preview: provide `VERCEL_TOKEN` secret or make check non-required | NEEDS-OWNER |
| 0.6 | Re-enable branch protection once `main` is genuinely green | NEEDS-OWNER |

## Phase 1 — Decide the fate of half-features

| # | Item | Status |
|---|------|--------|
| 1.1 | Knowledge base: finish or remove | DONE (decision: **leave flagged off**) — it's integrated RAG (chat), defaults `ENABLE_KNOWLEDGE_BASE=false`, no CVEs. Finishing the pgvector storage layer is a future *product* decision. UI link now gated (E3). |
| 1.2 | Ghost-hunt sweep | DONE — KB was the only true ghost; other not-in-nav pages (settings/history/admin/privacy/terms) are intentional (footer/user-menu access). |

## Phase 2 — Make the gauges tell the truth

| # | Item | Status |
|---|------|--------|
| 2.1 | Ratchet frontend coverage up toward 70/85 as tests land | ONGOING — floor at 10/11/11/11 (branches/functions/lines/statements); never lowered to pass a build. |
| 2.2 | Backfill money/security paths (payments, Stripe webhooks, SSO, quotas) | DONE — subscription routes 33%→89% + webhook HMAC; SSO mappers 19%→~37%; webhook delivery/storage service 28%→55%, storage 14%→40%. |
| 2.3 | Accessibility: header/footer as siblings of `<main>` repo-wide + landmark checks | DONE — 16/16 pages restructured; `e2e/landmarks.spec.ts` regression guard. |
| 2.4 | Backend coverage gate beyond 5 routes | DONE — ratchet floor (50%) for organizations/sso/export/research; gate covers 9 modules. |

## Phase 3 — Finish the structural refactors (with test nets)

| # | Item | Status |
|---|------|--------|
| 3.1 | `BulkGenerationPageClient.tsx` (1164) — characterization tests, then split hook/JSX | IN PROGRESS — 5-test RTL net + 13-test csv unit suite; Hero/ActivationHint/WorkflowBanner extracted to `app/bulk/components/PageBanners.tsx`. Remaining: CSV panel, topics list, job panel. |
| 3.2 | `batch.py` (1312) router split (lifecycle vs export) | DONE — 15 route tests first, then export endpoint → `batch_export.py`; batch.py 1312→834. |
| 3.3 | `marketing_templates.py` (1944) → fields/categories modules | DONE — assembler 42 lines; 7 category modules; registry SHA verified identical. |
| 3.4 | `rate_limit.py` (1288) → backends/models/shared base | DONE — deduped onto `_BaseRateLimiter` (1288→880); 19 tests. |
| 3.5 | `HomePageClient.tsx` (858) → data/animations/sections | DONE — extracted `_home/data.ts` + `_home/animations.ts` (858→622). |
| 3.6 | Remaining 1,000+ line modules — test-net first | TODO |

## Phase 4 — Keep it honest (durable hygiene)

| # | Item | Status |
|---|------|--------|
| 4.1 | Dependency automation (Dependabot grouping) | DONE — security updates grouped into one batched PR for pip + npm. |
| 4.2 | Docs-vs-reality reconciliation (drop unverified "100/100" claims) | DONE — README claims replaced with CI-enforced quality bar; `DATABASE.md` carries an accuracy warning pointing to `SCHEMA_AUDIT.md` until E1 lands. |
| 4.3 | `.env.example` tiered (required vs optional) + Next 16/React 18 pin documented | DONE. |
| 4.4 | Audit the 7 `eslint-disable`s | DONE — all intentional; justifications added. |
| 4.5 | Consolidate rollback docs | TODO (blocked on E1 cutover). |

---

## Completed-work record (refactor sizing, for reference)

- `marketing_templates.py` 1944 → 42-line assembler + 7 modules (≤369 lines each).
- `rate_limit.py` 1288 → 880 (shared base; 19 tests).
- `batch.py` 1312 → 834 (export router split; 15 route tests).
- `BulkGenerationPageClient.tsx` 1164 → ~1012 (constants + pure `csv.ts` + banners; 18 tests).
- `HomePageClient.tsx` 858 → 622 (data + animations extracted).
