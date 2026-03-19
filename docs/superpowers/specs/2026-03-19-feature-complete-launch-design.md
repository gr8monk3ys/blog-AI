# Blog AI: Feature-Complete Launch Design

**Date**: 2026-03-19
**Status**: Approved
**Goal**: Wire all core backend capabilities to the frontend, fix storage/persistence gaps, flag unfinished features honestly, and ship a production-ready product.

## Context

Blog AI has significant backend depth (brand voice fingerprinting, tri-provider research, fact-checking, SEO scoring, RAG knowledge base, bulk job queue) but several critical disconnections prevent it from being market-ready:

1. **ContentGenerator is orphaned** — the primary generation UI is imported by zero page routes
2. **Ephemeral storage** — brand voice training, bulk jobs, and webhooks use file/memory storage that won't survive deploys
3. **Demo data masks failures** — routes silently return fake data when DB is missing instead of showing errors
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

#### 1a. Persistent Storage

| Current | Target | Migration |
|---------|--------|-----------|
| Brand voice fingerprints → file system (`./data/brand_voice/`) | Postgres `voice_fingerprints` table | New SQL migration `003_voice_fingerprints.sql` |
| Bulk job state → in-memory dict (no Redis) | Require `REDIS_URL` in production, fail loudly without it | Config validation in `server.py` startup |
| Webhook subscriptions → in-memory dict (`webhook_storage`) | Postgres `webhook_subscriptions` table | New SQL migration `004_webhook_subscriptions.sql` |

The brand voice storage interface (`get_brand_voice_storage()`) already returns a storage backend — implement a Postgres-backed class that conforms to the same interface.

For bulk jobs, the Redis support already exists in the codebase. The fix is config validation: in production, if `REDIS_URL` is unset, log an error and refuse to start the batch system rather than silently falling back to in-memory.

#### 1b. Kill Demo Data in Production

The `canServeDemoData()` / `getSqlOrNull()` pattern returns sample data when the DB is absent. Change behavior by environment:

- `NODE_ENV=production`: Return HTTP 503 with `{ error: "Database not configured" }`. Never return demo data.
- `NODE_ENV=development`: Keep current behavior (demo data for local dev without DB).

Affected Next.js API routes: `brand-profiles`, `history`, `templates`, `analytics`.

#### 1c. Migration Runner

Options (pick one during implementation):
- Add a `--migrate` flag to `server.py` that applies pending SQL files from `migrations/` in order
- Or document the required `psql` commands in a deployment checklist

The Knowledge Base migration (`002_knowledge_base.sql`) and new migrations from 1a must be applied before their features work.

### Section 2: Wire ContentGenerator Into a Page Route

**New file**: `apps/web/app/generate/page.tsx`

This is the primary product surface — what a user sees after sign-in when they want to create content.

Page responsibilities:
- Generate a `conversationId` (UUID) on mount
- Render the refactored `ContentGenerator` component
- Display generated content below the form after submission (rendered blog post with sections)
- Show a loading overlay during generation
- After generation: show the content with export options, fact-check results (if enabled), and SEO score (if enabled)

Navigation:
- Add `/generate` to the nav as the primary authenticated CTA ("Generate" link already exists as `/tools` — evaluate whether `/generate` is the quick-start and `/tools` is the directory, or if they merge)
- Post-sign-in redirect should land on `/generate`, not `/`

### Section 3: Brand Voice — Complete the Loop

#### 3a. Voice Scoring Page

**New file**: `apps/web/app/brand/score/page.tsx`

A page where users paste or select generated content and score it against their trained brand voice fingerprint. The `ScoreResult.tsx` component already exists with animated score reveal and per-dimension breakdowns.

Flow:
1. User selects a trained brand profile from a dropdown
2. Pastes content (or selects from generation history)
3. Clicks "Score" → `POST /brand-voice/score` with content + fingerprint ID
4. Results render in `ScoreResult.tsx`: letter grade, dimension breakdown, LLM-generated improvement suggestions with example rewrites

#### 3b. Post-Generation Score

After the generation flow (Section 2), if a brand profile was active:
- Automatically score the output against the active profile
- Show the grade inline below the generated content
- Link to the full scoring page for detailed breakdown

#### 3c. Storage Fix

Covered by Section 1a — voice fingerprints persist in Postgres instead of file system.

### Section 4: Knowledge Base — Enable by Default

- Flip `ENABLE_KNOWLEDGE_BASE` default to `true` in `src/config.py`
- The migration from Section 1c ensures the tables exist
- Add a frontend check: if the KB API returns 404 or 500, show an informative message ("Knowledge Base requires database setup") instead of silently failing
- Add the KB toggle to the generation page (Section 2) — it's already in ContentGenerator's AdvancedOptions

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

**New component**: `apps/web/components/content-generator/SEOScorePanel.tsx` (an SEO score panel component already exists at `components/seo/SEOScorePanel.tsx` — evaluate reuse vs. new)

### Section 6: Export — Surface All Formats

The generation results view (Section 2) should offer all 6 export formats:

1. Markdown (`.md`)
2. HTML (standalone)
3. Plain Text (`.txt`)
4. PDF (via weasyprint, with HTML fallback)
5. WordPress Gutenberg blocks
6. Medium-compatible HTML

The `ExportMenu` component already exists with 16 passing tests. Wire it into the post-generation view with the content ID/data needed to call `POST /export/{format}`.

### Section 7: "Coming Soon" Flags

#### Frontend Changes

Add "Coming Soon" badges to features with backend APIs but no frontend pages:

- **Tools page** (`/tools`): AI Image Generation, Social Media Scheduling, Plagiarism Detection — show cards with a subtle "Coming Soon" pill badge, disabled click
- **Settings** (future `/settings/integrations`): Webhooks/Zapier — for now, just don't advertise. No settings page needed yet.

#### Homepage Copy Updates

In `HomePageClient.tsx` capabilities showcase:
- "AI Image Generation" → keep, add "Coming Soon" badge
- "Webhooks & Integrations" → keep, add "Coming Soon" badge
- All other advertised features (brand voice, research, fact-checking, book generation, export) must be fully wired by launch

### Section 8: Production Hardening

#### 8a. Real E2E Tests

Add 3 end-to-end Playwright tests that exercise actual flows (with a test backend or mocked API):

1. **Generate a blog post**: Fill topic → submit → wait for content → verify sections render
2. **Brand profile lifecycle**: Create profile → verify it appears in list → delete → verify removal
3. **Bulk generation**: Add 2 topics → start job → wait for completion → verify results

These supplement (not replace) the existing 59 smoke tests.

#### 8b. Honest Empty States

Replace demo data fallbacks with proper empty states in production:

- Analytics: "No content generated yet. Create your first blog post to see analytics here."
- History: "No generation history. Your content will appear here after you generate something."
- Templates: "No templates yet. Templates you create will appear here."

#### 8c. Feature Flag Error States

When a feature-flagged feature is enabled but its dependencies are missing:
- Knowledge Base enabled but migration not run → show specific error, not generic 500
- Stripe not configured → pricing page shows plans but "Contact us" instead of checkout buttons
- Research API keys missing → research toggle disabled with tooltip "Requires API key configuration"

## Files to Create

| File | Purpose |
|------|---------|
| `apps/web/app/generate/page.tsx` | Primary generation page |
| `apps/web/app/generate/GeneratePageClient.tsx` | Client component for generation page |
| `apps/web/app/brand/score/page.tsx` | Brand voice scoring page |
| `apps/web/components/content-generator/FactCheckResults.tsx` | Fact-check results display |
| `apps/web/components/content-generator/SEOScorePanel.tsx` | Post-generation SEO score (or reuse existing) |
| `apps/api/migrations/003_voice_fingerprints.sql` | Voice fingerprint storage migration |
| `apps/api/migrations/004_webhook_subscriptions.sql` | Webhook subscription storage migration |
| `apps/web/e2e/generate-blog.spec.ts` | Real generation E2E test |
| `apps/web/e2e/brand-lifecycle.spec.ts` | Brand profile E2E test |
| `apps/web/e2e/bulk-generation.spec.ts` | Bulk job E2E test |

## Files to Modify

| File | Change |
|------|--------|
| `apps/api/src/config.py` | KB default to `true`, production Redis validation |
| `apps/api/server.py` | Startup validation for production dependencies |
| `apps/web/app/api/brand-profiles/route.ts` | Return 503 in production when DB missing |
| `apps/web/app/api/history/route.ts` | Same |
| `apps/web/app/api/templates/route.ts` | Same |
| `apps/web/components/SiteHeader.tsx` | Add `/generate` nav link |
| `apps/web/app/HomePageClient.tsx` | "Coming Soon" badges on unfinished features |
| `apps/web/app/knowledge/KnowledgePage.tsx` | Error state for missing backend |
| `apps/api/src/brand/` | Postgres-backed storage implementation |
| `apps/api/app/routes/webhooks.py` | Postgres-backed subscription storage |

## What's NOT in Scope

- Social media scheduling frontend page
- Plagiarism detection frontend page
- Webhook/Zapier management settings page
- AI image generation frontend page
- SSO/SAML configuration page
- New backend features not already implemented
- Mobile app
- i18n/localization

## Success Criteria

1. A new user can sign up, generate a blog post, and see the output — without hitting dead ends or fake data
2. Brand voice training persists across deploys and the score is shown after generation
3. Knowledge base documents can be uploaded and used in generation
4. Bulk generation jobs persist across server restarts (Redis)
5. Fact-check and SEO results display inline after generation
6. All 6 export formats are accessible from the generation results view
7. The homepage only advertises features that work or are clearly marked "Coming Soon"
8. At least 3 E2E tests exercise real end-to-end flows
9. No route returns demo data in production
