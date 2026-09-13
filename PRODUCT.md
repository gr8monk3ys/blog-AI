# Product

<!-- impeccable:product-schema 1 -->

This record was derived from repository evidence (README, docs/, apps/web copy, routes,
package manifests, tests) with no owner interview available. Every fact that is not stated
verbatim in the repo is marked **(inferred)** and needs owner confirmation. The web app
that Impeccable targets lives in `apps/web` (Next.js 16, App Router); `apps/api` is the
FastAPI backend and `apps/extension` the browser extension.

## Platform

web

## Users

- Founders, consultants, and lean marketing teams who publish on a schedule and cannot
  afford a full content team (home page: "Best fit for founders, consultants, and lean
  marketing teams"; pricing copy: "solo operators publishing on a real schedule", "lean
  marketing teams running brand-safe content ops").
- Situation **(inferred)**: they already use general-purpose AI writing, and its output
  sounds generic and drifts from their positioning. The job is to turn their own writing
  standards into repeatable, publish-ready long-form content without re-prompting each time.
- Secondary audience **(inferred)**: developers integrating the HTTP API or browser
  extension (`docs/API.md`, `apps/extension/README.md`).

## Product Purpose

Blog AI generates long-form blog posts and books in a trained brand voice, then publishes
them (README). The site promise is "Train your brand voice, run repeatable SEO content
workflows, and generate publish-ready drafts faster" (`apps/web/app/layout.tsx` metadata).

Success **(inferred)** is a user who saves a brand profile once, runs the generate or bulk
workflow repeatedly, and publishes with less rewriting than a prompt-by-prompt tool.

## Positioning

Generation is a pipeline of small, separately tested LLM calls rather than one prompt: a
post is researched (web search, up to 8 cited sources), outlined, written one section at a
time with the brand-voice summary and research context, then proofread and humanized. Two
opt-in stages follow: an SEO loop that rewrites until a score threshold is met, and a
claim-by-claim fact check. Each stage is a plain function in `apps/api/src/` with its own
tests, so a bad stage is diagnosable and swappable (README).

Providers (OpenAI, Anthropic, Gemini) sit behind one `generate_text()` with retries and
per-operation rate limits. Brand voice is trained from the user's own samples and scored
(`/brand/train`, `/brand/score`).

## Operating Context

- Web app at https://blog-ai.vivancedata.com on Vercel; FastAPI container on Railway/GHCR;
  Neon Postgres; Clerk auth; Stripe billing (README, `docs/DEPLOYMENT.md`).
- Surfaces in `apps/web/app`: home, pricing, blog, auth/sign-in/sign-up, onboarding,
  generate, bulk (CSV batch), brand (profiles, train, score), tools (directory, category,
  per-tool pages), templates, images, history, analytics, remix, plagiarism, social
  (accounts, campaigns, schedule), team, knowledge base (behind `ENABLE_KNOWLEDGE_BASE`,
  default off), settings/webhooks, admin/blog, privacy, terms.
- Long-running generation is streamed; the UI carries loading, empty, error and
  "still loading?" states (`app/loading.tsx`, `components/ErrorBoundary.tsx`).
- Browser extension sends selected page text into the API with a user API key.
- Development: Clerk optional (every route public without a publishable key); without
  `DATABASE_URL`, history, brand profiles and analytics fall back to in-memory storage.

## Capabilities and Constraints

- Content types: blog posts, books (chapter-by-chapter), 29+ specialised tools across 8
  categories (blog, email, social media, business, naming, video, SEO, rewriting), content
  remix into social formats, AI images (DALL-E 3, Stability), export (JSON, CSV, Markdown,
  ZIP), Zapier-compatible webhooks with HMAC signing (`app/_home/data.ts`, `types/tools.ts`,
  `docs/API.md`).
- Usage tiers in code: Free, Starter, Pro, Business (`types/usage.ts`). The Business tier
  is filtered out of the public pricing page ("We don't sell the Business/Agency tier yet",
  `app/pricing/PricingPageClient.tsx`). Live prices come from the API; the home page
  hard-codes $0 / $19 / $49 per month **(inferred to be current; verify against Stripe)**.
- Stack constraints: Next.js 16 with React 18.3 pinned; Node 22.x (Node 24 broke the Vercel
  build); Bun 1.3+; per-request CSP nonce in `apps/web/proxy.ts`; class-based dark mode
  with a FOUC-guard script in `app/layout.tsx`; Sentry on client, server and edge.
- Terminology used in the product: brand voice / brand profile, workflow, generation,
  bulk, tool, template, remix, fact-check, research mode, knowledge base.
- Undecided **(inferred)**: whether the Business tier ships; whether the knowledge base
  becomes default-on.

## Brand Commitments

- Name: "Blog AI". Title pattern "Blog AI — Brand-Consistent AI Content".
- Mark: a sparkles icon (`public/icon.svg`, Heroicons `SparklesIcon` in the header).
- Voice **(inferred from copy)**: direct, operational, anti-generic. Copy talks about
  workflows, standards and reuse ("Stop restarting from prompts and pasting between
  tools"), not about magic. Headlines are sentence-case statements.
- Existing visual system: amber primary, Inter body, Source Serif 4 display, light cream
  canvas with an optional dark theme. Recorded in DESIGN.md; not a product decision here.

## Evidence on Hand

- Product screenshot: `docs/screenshot.png`.
- Verifiable counts: 29+ tools and templates (`types/tools.ts`), 3 LLM providers (footer:
  "Powered by GPT-4, Claude & Gemini"), 8 tool categories.
- Documentation: `docs/API.md`, `docs/DATABASE.md`, `docs/DEPLOYMENT.md`,
  `docs/ENVIRONMENT.md`, `docs/MONITORING.md`, `docs/RATE-LIMITING.md`.
- Absent, and must not be fabricated: customer names, testimonials, case studies, press,
  usage numbers, benchmark results, and any claim about output quality beyond what the
  pipeline mechanically does. The home page "social proof" bar currently shows product
  facts (tool count, provider count), not customers.

## Product Principles

1. The workflow is the product: every surface should make saving a standard once and
   reusing it obvious, faster than starting from a blank prompt.
2. Show the pipeline, do not hide it: research sources, scores, fact-check confidence and
   stage progress are user-facing facts, not decoration.
3. Publish-ready means less cleanup: outputs carry structure, export formats and voice so
   the user edits, not rewrites.
4. Do not oversell **(inferred)**: no invented proof, no claims the pipeline cannot back.
5. Operate without third parties when they fail: the primary action never depends on
   Clerk, the API or the database being reachable (comment in `app/HomePageClient.tsx`).

## Accessibility & Inclusion

- Target **(inferred from tests and fixes)**: WCAG 2.1 AA. Playwright specs cover
  landmarks, dark mode, mobile responsiveness and keyboard-visible focus; text and
  interactive contrast was raised to at least 4.5:1 (text) and 3:1 (icons) in the
  Impeccable refinement pass.
- Reduced motion: entrance animations are opacity/translate only; loading indicators
  pulse rather than bounce.
