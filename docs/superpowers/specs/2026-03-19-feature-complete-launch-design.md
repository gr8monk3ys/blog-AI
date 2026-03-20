# Blog AI: Feature-Complete Launch Design

**Date**: 2026-03-19
**Status**: Approved (revised after spec review)
**Goal**: Wire all core backend capabilities to the frontend, fix storage/persistence gaps, flag unfinished features honestly, and ship a production-ready product.

## Context

Blog AI has significant backend depth (brand voice fingerprinting, tri-provider research, fact-checking, SEO scoring, RAG knowledge base, bulk job queue) but several critical disconnections prevent it from being market-ready:

1. **ContentGenerator is orphaned** — the primary generation UI is imported by zero page routes
2. **Ephemeral storage** — bulk jobs and webhooks silently fall back to in-memory when Redis is unavailable
3. **Demo data masks failures** — Next.js API routes silently return fake data when DB is missing
4. **Features with no frontend** — image generation, webhook management, social scheduling, plagiarism detection have backend APIs but no UI pages
5. **Knowledge Base off by default** — requires manual migration and feature flag
6. **E2E tests are smoke-only** — no test actually completes a generation, checkout, or bulk job

## Strategy

**Vertical slices**: Fix one feature end-to-end at a time. Each slice is independently deployable and testable. If we stop at slice 5, slices 1-4 still ship.

**Core features to wire**: Generation UI, brand voice, bulk generation, knowledge base, fact-checking, SEO scoring, export.

**Flagged for later**: AI images, webhooks/Zapier management, social scheduling, plagiarism detection — "Coming Soon" labels, not false advertising.

## Sections

### Section 1: Critical Infrastructure

Must complete before any feature work.

#### 1a. Require Redis in Production

Both bulk job state and webhook subscriptions use Redis as their primary store, with silent in-memory fallback when Redis is unavailable. The in-memory fallback means jobs and subscriptions are lost on restart.

**Fix**: Add a Redis availability check to `validate_production_config()` in `apps/api/src/config.py`. In production (`APP_ENV=production`), if `REDIS_URL` is unset or Redis is unreachable, log an error and refuse to start the batch and webhook systems. The existing `redis_client.py` defaults to `redis://localhost:6379/0` when `REDIS_URL` is unset — this must be changed to raise in production rather than silently connecting to a likely-nonexistent local Redis.

**Note**: `PostgresBrandVoiceStorage` already exists in `apps/api/src/brand/storage.py` (lines 158-367) and `get_brand_voice_storage()` already routes to Postgres when `DATABASE_URL` is configured. No new migration or storage class is needed for brand voice. The `001_create_webhook_tables.sql` migration already creates `webhook_subscriptions` and `webhook_deliveries` tables. No new webhook migration is needed either.

#### 1b. Disable Demo Data in Production

The `canServeDemoData()` / `getSqlOrNull()` pattern in Next.js API routes returns sample fixture data when the DB is absent. This masks real configuration failures.

**Fix**: Introduce a `DEMO_DATA_ENABLED` environment variable (default `true` in development, `false` in production). Do NOT use `NODE_ENV` because Vercel sets `NODE_ENV=production` even for preview deployments, where demo data is useful for QA without a database.

- When `DEMO_DATA_ENABLED=false` and DB is unavailable: return HTTP 503 with `{ error: "Database not configured" }`
- When `DEMO_DATA_ENABLED=true` (dev/preview): keep current behavior

**Note**: The `brand-profiles` route already partially implements this — it calls `databaseUnavailableResponse()` for writes and `canServeDemoData()` for reads. Extend this pattern consistently to `history`, `templates`, and `analytics` routes.

Affected Next.js API routes: `brand-profiles`, `history`, `templates`, `analytics`.

#### 1c. Migration Runner

Add a `--migrate` flag to `server.py` that applies pending SQL files from `migrations/` in order. This ensures `002_knowledge_base.sql` (and any future migrations) are applied before their features are enabled.

Existing migrations:
- `001_create_webhook_tables.sql` — webhook subscriptions and deliveries
- `002_knowledge_base.sql` — knowledge documents, chunks, embeddings (rollback exists: `002_rollback_knowledge_base.sql`)

**Ordering constraint**: Section 4 (enabling Knowledge Base by default) MUST NOT ship until migration 002 is reliably applied. The migration runner must be implemented and validated first.

### Section 2: Wire ContentGenerator Into a Page Route

**New files**: `apps/web/app/generate/page.tsx`, `apps/web/app/generate/GeneratePageClient.tsx`

This is the primary product surface — what a user sees after sign-in when they want to create content.

Page responsibilities:
- Generate a `conversationId` (UUID) on mount
- Render the refactored `ContentGenerator` component
- Display generated content below the form after submission (rendered blog post with sections)
- Show a loading overlay during generation
- After generation: show the content with export options, fact-check results (if enabled), and SEO score (if enabled)

**Navigation decision**: The current nav has `{ href: '/tools', label: 'Generate', authRequired: true }`. Change this to point to `/generate` instead. `/tools` becomes the tool directory (browsing all 29 tools by category). The nav entry becomes:
- `{ href: '/generate', label: 'Generate', authRequired: true }` — primary generation page
- `/tools` stays in the nav as-is but with label "Tools" (currently not shown as a separate nav item since "Generate" points there)

Also update `HomePageClient.tsx` signed-in CTA from `/bulk` to `/generate`.

Post-sign-in redirect should land on `/generate`, not `/`.

### Section 3: Brand Voice — Complete the Loop

#### 3a. Voice Scoring Page

**New file**: `apps/web/app/brand/score/page.tsx`

A page where users paste or select generated content and score it against their trained brand voice fingerprint. The `ScoreResult.tsx` component already exists with animated score reveal and per-dimension breakdowns.

Flow:
1. User selects a trained brand profile from a dropdown
2. Pastes content (or selects from generation history)
3. Clicks "Score" → `POST /brand-voice/score` with content + fingerprint ID
4. Results render in `ScoreResult.tsx`: letter grade, dimension breakdown, LLM-generated improvement suggestions with example rewrites

**Pre-implementation check**: Verify `POST /brand-voice/score` endpoint exists in `apps/api/app/routes/brand_voice.py` and confirm its request/response schema before building the page.

#### 3b. Post-Generation Score

After the generation flow (Section 2), if a brand profile was active:
- Automatically score the output against the active profile
- Show the grade inline below the generated content
- Link to the full scoring page for detailed breakdown

**Implementation detail**: The generation response from `POST /generate-blog` must include the `brand_profile_id` that was used so the frontend can pass it to the scoring endpoint. Verify whether `BlogGenerationResponse` already includes this field; if not, add it to both the backend response and the `ContentGenerationResponse` TypeScript type.

#### 3c. Storage

Already handled — `PostgresBrandVoiceStorage` exists and `get_brand_voice_storage()` routes to Postgres when `DATABASE_URL` is configured. No additional work needed.

### Section 4: Knowledge Base — Enable by Default

**Ordering dependency**: This section ships ONLY after Section 1c (migration runner) is complete and verified.

- Flip `ENABLE_KNOWLEDGE_BASE` default to `true` in `src/config.py`
- Add a frontend check in `KnowledgePage.tsx`: if the KB API returns 404 or 500, show an informative message ("Knowledge Base requires database setup — contact your administrator") instead of silently failing
- Add the KB toggle to the generation page (Section 2) — it's already in ContentGenerator's AdvancedOptions
- Document in deployment guide that migration `002_knowledge_base.sql` must be applied (the migration runner from 1c should handle this, but document the manual fallback)

**Rollback**: If the migration fails, `002_rollback_knowledge_base.sql` exists in the repo and can be applied manually.

### Section 5: Fact-Checking & SEO — Surface in Generation Flow

These are Pro-tier features with complete backend implementations. They become accessible once ContentGenerator is wired into a page (Section 2).

#### 5a. Fact-Check Results Display

After generation completes with `factCheck: true`:
- Call `POST /fact-check` with the generated content
- Display results inline: each extracted claim with verification status (verified/unverified/contradicted), confidence score, and source links
- Use a collapsible panel below the generated content

**New component**: `apps/web/components/content-generator/FactCheckResults.tsx`

#### 5b. SEO Score Panel

After generation completes with `seoOptimize: true`:
- Call `POST /seo/analyze-content` with the generated content and target keyword
- Display the Surfer-style score (0-100) with breakdowns: topic coverage, NLP term usage, structure, word count, readability
- Show missing topics and optimization suggestions

**Decision**: Reuse the existing `components/seo/SEOScorePanel.tsx` component. It already has 6 passing tests. Import it into the generation results view and pass it the analysis data. Do NOT create a duplicate component.

### Section 6: Export — Surface All Formats

The generation results view (Section 2) should offer all 6 export formats:

1. Markdown (`.md`)
2. HTML (standalone)
3. Plain Text (`.txt`)
4. PDF (via weasyprint, with HTML fallback — surface the fallback status to users: "PDF generated as print-ready HTML")
5. WordPress Gutenberg blocks
6. Medium-compatible HTML

The `ExportMenu` component already exists with 16 passing tests. Wire it into the post-generation view with the content ID/data needed to call `POST /export/{format}`.

### Section 7: "Coming Soon" Flags

#### Frontend Changes

Add "Coming Soon" badges to features with backend APIs but no frontend pages:

- **Tools page** (`/tools`): AI Image Generation, Social Media Scheduling, Plagiarism Detection — show cards with a subtle "Coming Soon" pill badge, disabled click
- **Settings** (future `/settings/integrations`): Webhooks/Zapier — for now, don't advertise. No settings page needed yet.

#### Homepage Copy Updates

In `HomePageClient.tsx` capabilities showcase:
- "AI Image Generation" → keep, add "Coming Soon" badge
- "Webhooks & Integrations" → keep, add "Coming Soon" badge
- All other advertised features (brand voice, research, fact-checking, book generation, export) must be fully wired by launch

### Section 8: Production Hardening

#### 8a. Honest Empty States

Replace demo data fallbacks with proper empty states in production:

- Analytics: "No content generated yet. Create your first blog post to see analytics here."
- History: "No generation history. Your content will appear here after you generate something."
- Templates: "No templates yet. Templates you create will appear here."

#### 8b. Feature Flag Error States

When a feature-flagged feature is enabled but its dependencies are missing:
- Knowledge Base enabled but migration not run → show specific error, not generic 500
- Stripe not configured → pricing page shows plans but "Contact us" instead of checkout buttons
- Research API keys missing → research toggle disabled with tooltip "Requires API key configuration"

#### 8c. E2E Tests (deferred to post-launch)

Real end-to-end Playwright tests that exercise actual flows require test infrastructure: a running FastAPI server, test API keys, and a seeded database. This is a meaningful infrastructure investment that should not block the launch.

**Post-launch**: Add 3 real E2E tests:
1. Generate a blog post via the UI with mocked API responses
2. Brand profile CRUD lifecycle
3. Bulk generation with 2 topics to completion

The existing 59 smoke tests remain the launch gate. Real-flow E2E tests are prioritized immediately after launch.

## Files to Create

| File | Purpose |
|------|---------|
| `apps/web/app/generate/page.tsx` | Primary generation page (server component shell) |
| `apps/web/app/generate/GeneratePageClient.tsx` | Client component for generation page |
| `apps/web/app/brand/score/page.tsx` | Brand voice scoring page |
| `apps/web/components/content-generator/FactCheckResults.tsx` | Fact-check results display |

## Files to Modify

| File | Change |
|------|--------|
| `apps/api/src/config.py` | KB default to `true`, production Redis validation in `validate_production_config()` |
| `apps/api/src/storage/redis_client.py` | Raise in production when `REDIS_URL` is unset instead of defaulting to localhost |
| `apps/api/server.py` | Add `--migrate` flag for applying pending SQL migrations |
| `apps/web/lib/server-mode.ts` | Add `DEMO_DATA_ENABLED` env var check to `canServeDemoData()` |
| `apps/web/app/api/brand-profiles/route.ts` | Use `DEMO_DATA_ENABLED` for demo data gating |
| `apps/web/app/api/history/route.ts` | Same |
| `apps/web/app/api/templates/route.ts` | Same |
| `apps/web/components/SiteHeader.tsx` | Change `/tools` to `/generate` for primary nav CTA |
| `apps/web/app/HomePageClient.tsx` | "Coming Soon" badges, signed-in CTA → `/generate` |
| `apps/web/app/knowledge/KnowledgePage.tsx` | Error state for missing backend |
| `apps/web/components/seo/SEOScorePanel.tsx` | Adapt for use in generation results view (if interface changes needed) |

## What's NOT in Scope

- Social media scheduling frontend page
- Plagiarism detection frontend page
- Webhook/Zapier management settings page
- AI image generation frontend page
- SSO/SAML configuration page
- New backend features not already implemented
- Mobile app
- i18n/localization
- New SQL migrations for brand voice or webhooks (already exist)
- Real-flow E2E test infrastructure (deferred to post-launch)

## Success Criteria

1. A new user can sign up, generate a blog post at `/generate`, and see the output — without hitting dead ends or fake data
2. Brand voice training persists across deploys (Postgres) and the score is shown after generation
3. Knowledge base documents can be uploaded and used in generation with KB enabled by default
4. Bulk generation jobs persist across server restarts (Redis required in production)
5. Fact-check and SEO results display inline after generation for Pro-tier users
6. All 6 export formats are accessible from the generation results view
7. The homepage only advertises features that work or are clearly marked "Coming Soon"
8. No route returns demo data when `DEMO_DATA_ENABLED=false`
9. Feature-flagged features show helpful error states when dependencies are missing

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Flipping KB default to `true` before migration 002 is applied | Section 4 blocked on Section 1c completion; migration runner must be verified first |
| `DEMO_DATA_ENABLED` defaults confuse Vercel preview deployments | Default to `true` in `.env.example`, document that production deployments must set `false` |
| `POST /brand-voice/score` endpoint may not match spec assumptions | Pre-implementation check in Section 3a — verify endpoint path and schema before building page |
| Generation response may not include `brand_profile_id` | Verify and add to `BlogGenerationResponse` if missing (Section 3b) |
| PDF export falls back to HTML without user awareness | Surface fallback status in export UI: "PDF generated as print-ready HTML" (Section 6) |
