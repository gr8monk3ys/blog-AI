# Competitive Parity Execution Plan (Q1-Q2 2026)

## Goal

Reach reliable, sellable parity with Jasper/Copy.ai on core workflows by fixing execution quality first, then closing product depth gaps.

## Current Snapshot (2026-02-21)

- Implemented: F1, F2, F3, F4, F11
- Partial: F5, F6, F8, F10, F12, F13, F15
- Missing: F7, F9, F14
- Critical blocker: deploy path previously not gated by successful CI outcomes.

## Progress Update (Completed 2026-02-21)

- `deploy.yml` now deploys from successful `CI` workflow runs on `main` (manual deploy still available).
- Frontend deploy now validates required Vercel secrets and skips with warning instead of hard-failing when credentials are not configured.
- Branch protection is now enabled on `main` with strict required checks and required review.
- Extension API no longer returns fabricated email/tier placeholders.
- PRD feature status table is now synchronized to verified implementation state.
- Security audit now uses `scripts/audit-runtime.mjs` to block high/critical runtime vulnerabilities while allowlisting one upstream-only minimatch advisory.

## 30-Day Plan (Reliability + Truth Alignment)

1. Enforce release gate:
- Deploy only after successful `CI` on `main`.
- Manual dispatch remains available for emergency overrides.

2. Make product claims truthful:
- Keep PRD status table synchronized to real implementation state.
- Remove fabricated user data from extension responses.

3. Stabilize check suite:
- Bring `Backend Tests`, `Frontend Checks`, dependency audit, and security scans to green on `main`.
- Define required checks in branch protection.

4. Reduce hidden technical risk:
- Replace in-memory workflow storage with persistent storage.
- Add regression tests for extension auth/user/usage responses.

## 60-Day Plan (Feature Depth)

1. F6 Fact-checking:
- Add explicit verification pipeline with citation validation and confidence scoring.

2. F8 Live SEO:
- Add continuous scoring in generation flow and final acceptance thresholds.

3. F10 Deep Research:
- Productize research as a first-class workflow with source quality controls.

4. F12 Team:
- Complete seat/invite/billing UX so Business tier can be sold.

## 90-Day Plan (Differentiation + Enterprise Readiness)

1. F7 Voice Input:
- Add speech-to-text ingestion path for prompt creation and editing.

2. F9 Ensemble Mode:
- Add real multi-model orchestration (plan, draft, critique/refine).

3. GTM packaging:
- Publish clear capability matrix by tier with evidence-backed claims.
- Add enterprise reliability SLOs and release policy.

## Success Metrics

- CI pass rate on `main`: >= 95% for trailing 30 days.
- Failed production deployments from mainline: 0.
- Feature claim accuracy: 100% of marketed features mapped to tested endpoints.
- Business tier conversion readiness: seats/invites/billing flows live and tested.
