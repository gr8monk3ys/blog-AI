# Blog AI

A web app, API and browser extension that generate and publish blog posts and books in a configurable brand voice. Terms below are the ones the code uses (`apps/web/types/`, `db/migrations/`, `apps/api/src/`).

## Language

### Content

**Blog post**:
A single generated article made of titled sections, each carrying source citations. Stored in `blog_posts` when published to the site, and in `generated_content` when saved to History.
_Avoid_: article, entry

**Book**:
A generated long-form work made of Chapters, each holding Topics. Not a Blog post with more sections.
_Avoid_: ebook, manuscript

**Chapter**:
A numbered, titled part of a Book that contains Topics.
_Avoid_: section (a Section belongs to a Blog post)

**Topic**:
A titled unit of content inside a Chapter.
_Avoid_: subsection

**Template**:
A saved preset (a Tool plus its preset inputs) that a user can re-run. Stored in `templates`.
_Avoid_: preset, recipe

**Tool**:
A single-purpose generator in the tool directory, belonging to a Tool category.
_Avoid_: widget, utility

**History**:
The user's saved generated content (`generated_content`), filterable and favouritable.
_Avoid_: library, archive

**Content version**:
A saved revision of a piece of content (`content_versions`).
_Avoid_: draft, snapshot

### Brand voice

**Brand profile**:
A named set of writing style, tone keywords and industry that steers generation. Stored in `brand_profiles`.
_Avoid_: persona, style guide

**Voice sample**:
A piece of the user's existing writing added to train a Voice fingerprint (`voice_samples`).
_Avoid_: training data, example

**Voice fingerprint**:
The vocabulary, sentence-pattern, tone and style metrics learned from Voice samples (`voice_fingerprints`).
_Avoid_: voice model

**Voice score**:
How closely a piece of content matches a Voice fingerprint.
_Avoid_: brand score

### Transforming and checking content

**Remix**:
Turning source content into other Content formats (Twitter thread, LinkedIn post, email newsletter, YouTube script, Instagram carousel, podcast notes).
_Avoid_: repurpose, convert

**Fact check**:
Verifying a piece of content's claims; each claim is `verified`, `unverified` or `contradicted`.
_Avoid_: validation

**SEO score**:
A rating of content across SEO dimensions against thresholds.
_Avoid_: ranking

**Deep research**:
LLM-assisted research that records Research queries and their Research sources (`research_queries`, `research_sources`).
_Avoid_: web search

**Knowledge base**:
A user's uploaded documents (`kb_documents`) that are chunked and searched to ground generation.
_Avoid_: library, corpus

### Volume and delivery

**Bulk generation**:
Generating many Blog posts from a CSV or list of items as one Batch job, with a Provider strategy and per-item results and retries.
_Avoid_: batch import, mass generation

**Provider strategy**:
How a Batch job spreads items across LLM providers: `single`, `round_robin`, `load_balanced`, `cost_optimized`, `quality_optimized`.
_Avoid_: routing mode

**LLM provider**:
The model vendor behind generation: `openai`, `anthropic` or `gemini`.
_Avoid_: model backend

**Social post**:
Content scheduled to a Social platform (twitter, linkedin, facebook, instagram) through a connected Social account, optionally grouped into a Campaign.
_Avoid_: tweet, update

**Campaign**:
A group of Social posts with its own platform config and analytics.
_Avoid_: series

**Webhook subscription**:
A registered endpoint that receives Webhook event types; deliveries are logged (`webhook_subscriptions`, `webhook_deliveries`). Zapier-compatible.
_Avoid_: callback, hook

**Workflow**:
A user-defined automation with recorded executions (`app_workflows`, `app_workflow_executions`).
_Avoid_: pipeline

### Accounts and billing

**Organization**:
A team that owns shared resources; members hold an Organization role (`owner`, `admin`, `member`, `viewer`) and join by Invite.
_Avoid_: workspace, team account

**Tier**:
A subscription level: `free`, `starter`, `pro` or `business`. Frontend ids must match the backend `SubscriptionTier`.
_Avoid_: plan (Stripe plans map onto a Tier)

**Quota**:
A user's per-Tier allowance of generations, tracked in `user_quotas` and `usage_records`.
_Avoid_: limit, credits

**API key**:
A credential for programmatic access to the API (`api_keys`), created by `scripts/create_api_key.py`.
_Avoid_: token

**Onboarding**:
The first-run wizard that collects a profile and produces a First content item (blog post, marketing copy or book chapter).
_Avoid_: setup, welcome flow
