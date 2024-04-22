-- Blog-AI Neon/Postgres schema (Neon-only cloud SaaS)
--
-- Applies to: Neon (Postgres) used by:
-- - Next.js (Vercel) route handlers: templates, brand profiles, history, blog CMS
-- - Python backend (Railway): analytics, usage quotas, Stripe sync
--
-- Notes:
-- - We use `gen_random_uuid()` from the `pgcrypto` extension for UUID PKs.
-- - AuthZ is enforced at the application layer (Clerk user_id scoping).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =============================================================================
-- Marketing Blog CMS
-- =============================================================================

CREATE TABLE IF NOT EXISTS blog_posts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  slug text NOT NULL UNIQUE,
  excerpt text,
  body text NOT NULL,
  tags text[] NOT NULL DEFAULT '{}'::text[],
  status text NOT NULL DEFAULT 'draft',
  published_at timestamptz,
  cover_image text,
  seo_title text,
  seo_description text,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW(),
  CONSTRAINT blog_posts_status_check CHECK (status IN ('draft', 'published'))
);

CREATE INDEX IF NOT EXISTS idx_blog_posts_published_at
  ON blog_posts(published_at DESC NULLS LAST);

-- =============================================================================
-- Templates
-- =============================================================================

CREATE TABLE IF NOT EXISTS templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL,
  name text NOT NULL,
  description text,
  slug text NOT NULL,
  tool_id text NOT NULL,
  preset_inputs jsonb NOT NULL DEFAULT '{}'::jsonb,
  category text NOT NULL,
  tags text[] NOT NULL DEFAULT '{}'::text[],
  is_public boolean NOT NULL DEFAULT true,
  use_count integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW(),
  CONSTRAINT templates_user_slug_unique UNIQUE (user_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_templates_public_use_count
  ON templates(is_public, use_count DESC);
CREATE INDEX IF NOT EXISTS idx_templates_tool_id
  ON templates(tool_id);
CREATE INDEX IF NOT EXISTS idx_templates_category
  ON templates(category);

-- =============================================================================
-- Brand Profiles
-- =============================================================================

CREATE TABLE IF NOT EXISTS brand_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL,
  name text NOT NULL,
  slug text NOT NULL,
  tone_keywords text[] NOT NULL DEFAULT '{}'::text[],
  writing_style text NOT NULL DEFAULT 'balanced',
  example_content text,
  industry text,
  target_audience text,
  preferred_words text[] NOT NULL DEFAULT '{}'::text[],
  avoid_words text[] NOT NULL DEFAULT '{}'::text[],
  brand_values text[] NOT NULL DEFAULT '{}'::text[],
  content_themes text[] NOT NULL DEFAULT '{}'::text[],
  is_active boolean NOT NULL DEFAULT true,
  is_default boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW(),
  CONSTRAINT brand_profiles_user_slug_unique UNIQUE (user_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_brand_profiles_user_id
  ON brand_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_brand_profiles_user_default
  ON brand_profiles(user_id, is_default);

-- =============================================================================
-- Generation History (Next.js) + Analytics (Python)
-- =============================================================================

CREATE TABLE IF NOT EXISTS generated_content (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL,
  tool_id text NOT NULL,
  tool_name text,
  title text,
  inputs jsonb NOT NULL DEFAULT '{}'::jsonb,
  output text NOT NULL,
  provider text NOT NULL,
  execution_time_ms integer NOT NULL DEFAULT 0,
  is_favorite boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generated_content_user_created
  ON generated_content(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generated_content_user_tool
  ON generated_content(user_id, tool_id);

-- =============================================================================
-- Usage Quotas (Python backend)
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_quotas (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL UNIQUE,
  tier text NOT NULL DEFAULT 'free',
  period_start timestamptz NOT NULL,
  period_end timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW(),
  CONSTRAINT user_quotas_tier_check CHECK (tier IN ('free', 'starter', 'pro', 'business'))
);

CREATE TABLE IF NOT EXISTS usage_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL,
  operation_type text NOT NULL,
  tokens_used integer NOT NULL DEFAULT 0,
  timestamp timestamptz NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_records_user_time
  ON usage_records(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_usage_records_user_op
  ON usage_records(user_id, operation_type);

-- =============================================================================
-- Stripe Sync (Python backend)
-- =============================================================================

CREATE TABLE IF NOT EXISTS stripe_customers (
  user_id text PRIMARY KEY,
  customer_id text NOT NULL UNIQUE,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stripe_customers_customer_id
  ON stripe_customers(customer_id);

CREATE TABLE IF NOT EXISTS stripe_subscriptions (
  subscription_id text PRIMARY KEY,
  user_id text NOT NULL,
  customer_id text,
  tier text NOT NULL,
  status text NOT NULL DEFAULT 'active',
  cancelled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_user_id
  ON stripe_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_customer_id
  ON stripe_subscriptions(customer_id);

CREATE TABLE IF NOT EXISTS payments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL,
  subscription_id text,
  amount_cents integer NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'paid',
  paid_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payments_user_id
  ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_created_at
  ON payments(created_at DESC);

CREATE TABLE IF NOT EXISTS payment_failures (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL,
  subscription_id text,
  attempt_count integer NOT NULL DEFAULT 1,
  failed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payment_failures_user_id
  ON payment_failures(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_failures_created_at
  ON payment_failures(created_at DESC);

