# Database Schema Documentation

This document provides comprehensive documentation of the Blog AI database schema, including all tables, relationships, indexes, and Row Level Security (RLS) policies.

## Table of Contents

- [Migration Status](#migration-status)
- [Schema Overview](#schema-overview)
- [Entity Relationship Diagram](#entity-relationship-diagram)
- [Tables](#tables)
- [Functions](#functions)
- [Indexes](#indexes)
- [Row Level Security Policies](#row-level-security-policies)
- [Known Issues](#known-issues)
- [Missing Migrations](#missing-migrations)

---

## Migration Status

### Migration Inventory

| Number | File | Status | Description |
|--------|------|--------|-------------|
| 001 | `001_create_generated_content.sql` | OK | Core generated content table |
| 002 | `002_create_tool_usage.sql` | OK | Tool usage statistics |
| 003 | `003_create_conversations.sql` | OK | Conversation history storage |
| 004 | `004_add_favorites.sql` | **DUPLICATE** | Favorites functionality |
| 004 | `004_create_templates.sql` | **DUPLICATE** | Reusable templates |
| 005 | `005_create_brand_profiles.sql` | OK | Brand voice profiles |
| 006 | `006_enhance_brand_voice_training.sql` | OK | Voice samples and fingerprints |
| 007 | `007_usage_quotas.sql` | OK | Subscription quotas and usage tracking |
| 008 | `008_stripe_integration.sql` | OK | Stripe payment integration |

### Issues Found

#### 1. Duplicate Migration Number (004)
**Severity: HIGH**

Two migrations share the same number `004`:
- `004_add_favorites.sql` - Adds favorites functionality to `generated_content`
- `004_create_templates.sql` - Creates the `templates` table

**Resolution Required:**
One of these should be renumbered. Recommended fix:
```bash
# Rename templates migration to 004a or rename to 004b_create_templates.sql
mv 004_create_templates.sql 004b_create_templates.sql
```

#### 2. No Rollback Support
**Severity: MEDIUM**

None of the migrations include DOWN/rollback statements. This makes it difficult to:
- Roll back failed deployments
- Develop iteratively with schema changes
- Perform blue-green deployments safely

**Recommendation:** Add rollback scripts for each migration, e.g.:
```sql
-- DOWN Migration for 001_create_generated_content.sql
DROP TRIGGER IF EXISTS update_generated_content_updated_at ON generated_content;
DROP TABLE IF EXISTS generated_content;
DROP FUNCTION IF EXISTS update_updated_at_column();
```

#### 3. Circular Dependency Potential
**Severity: LOW**

Migration `006_enhance_brand_voice_training.sql` adds a foreign key from `brand_profiles` to `voice_fingerprints`, but `voice_fingerprints` also references `brand_profiles`. This is handled correctly (FK added via ALTER TABLE), but requires careful ordering.

---

## Schema Overview

The database consists of the following logical domains:

### Content Generation Domain
- `generated_content` - Stores all AI-generated content
- `conversations` - Chat/conversation history
- `templates` - Reusable content templates

### Tool & Analytics Domain
- `tool_usage` - Tool usage statistics

### Brand Voice Domain
- `brand_profiles` - Brand voice configuration
- `voice_samples` - Training samples for voice
- `voice_fingerprints` - Aggregated voice characteristics
- `voice_scores` - Content consistency scores

### Billing & Subscriptions Domain
- `user_quotas` - User subscription tier and limits
- `usage_records` - Individual usage events
- `tier_limits` - Configurable tier limits and pricing
- `stripe_customers` - Stripe customer mappings
- `stripe_subscriptions` - Subscription details
- `payments` - Successful payment records
- `payment_failures` - Failed payment tracking
- `users` - Core user accounts

---

## Entity Relationship Diagram

```mermaid
erDiagram
    %% Content Generation Domain
    generated_content {
        uuid id PK
        timestamptz created_at
        timestamptz updated_at
        text tool_id
        jsonb inputs
        text output
        text provider
        int execution_time_ms
        text user_hash
        boolean is_favorite
        text tool_name
        text title
    }

    conversations {
        text id PK
        timestamptz created_at
        timestamptz updated_at
        jsonb messages
        jsonb metadata
    }

    templates {
        uuid id PK
        timestamptz created_at
        timestamptz updated_at
        text name
        text description
        text slug UK
        text tool_id
        jsonb preset_inputs
        text category
        text[] tags
        boolean is_public
        text user_hash
        int use_count
    }

    %% Tool Analytics Domain
    tool_usage {
        uuid id PK
        text tool_id UK
        int count
        timestamptz last_used_at
        timestamptz created_at
    }

    %% Brand Voice Domain
    brand_profiles {
        uuid id PK
        timestamptz created_at
        timestamptz updated_at
        text name
        text slug UK
        text[] tone_keywords
        text writing_style
        text example_content
        text industry
        text target_audience
        text[] preferred_words
        text[] avoid_words
        text[] brand_values
        text[] content_themes
        text user_hash
        boolean is_active
        boolean is_default
        uuid voice_fingerprint_id FK
        text training_status
        float training_quality
        int sample_count
    }

    voice_samples {
        uuid id PK
        uuid profile_id FK
        timestamptz created_at
        text title
        text content
        text content_type
        int word_count
        text source_url
        text source_platform
        boolean is_analyzed
        jsonb analysis_result
        float quality_score
        boolean is_primary_example
    }

    voice_fingerprints {
        uuid id PK
        uuid profile_id FK UK
        timestamptz created_at
        timestamptz updated_at
        jsonb vocabulary_profile
        jsonb sentence_patterns
        jsonb tone_distribution
        jsonb style_metrics
        text voice_summary
        float[] embedding_vector
        text embedding_model
        int sample_count
        timestamptz last_trained_at
        float training_quality
    }

    voice_scores {
        uuid id PK
        uuid profile_id FK
        text content_id
        timestamptz created_at
        float overall_score
        float tone_match
        float vocabulary_match
        float style_match
        jsonb feedback
        jsonb deviations
    }

    %% Billing Domain
    users {
        uuid id PK
        text user_id UK
        text email
        text name
        text stripe_customer_id
        text tier
        boolean is_active
        timestamptz last_login_at
        timestamptz created_at
        timestamptz updated_at
    }

    user_quotas {
        uuid id PK
        text user_id UK
        text tier
        timestamptz period_start
        timestamptz period_end
        timestamptz created_at
        timestamptz updated_at
    }

    usage_records {
        uuid id PK
        text user_id
        text operation_type
        int tokens_used
        timestamptz timestamp
        jsonb metadata
        timestamptz created_at
    }

    tier_limits {
        text tier PK
        int monthly_limit
        int daily_limit
        text[] features
        decimal price_monthly
        decimal price_yearly
        text description
        timestamptz updated_at
    }

    stripe_customers {
        uuid id PK
        text user_id UK
        text customer_id UK
        text email
        timestamptz created_at
        timestamptz updated_at
    }

    stripe_subscriptions {
        uuid id PK
        text subscription_id UK
        text user_id
        text customer_id
        text tier
        text status
        timestamptz current_period_start
        timestamptz current_period_end
        boolean cancel_at_period_end
        timestamptz cancelled_at
        timestamptz created_at
        timestamptz updated_at
    }

    payments {
        uuid id PK
        text user_id
        text subscription_id
        text invoice_id
        int amount_cents
        text currency
        text status
        timestamptz paid_at
        timestamptz created_at
    }

    payment_failures {
        uuid id PK
        text user_id
        text subscription_id
        text invoice_id
        int attempt_count
        text failure_reason
        timestamptz failed_at
        timestamptz resolved_at
        timestamptz created_at
    }

    %% Relationships
    brand_profiles ||--o{ voice_samples : "has many"
    brand_profiles ||--o| voice_fingerprints : "has one"
    brand_profiles ||--o{ voice_scores : "has many"
    voice_fingerprints ||--|| brand_profiles : "belongs to"

    users ||--o| user_quotas : "has one"
    users ||--o| stripe_customers : "has one"
    users ||--o{ stripe_subscriptions : "has many"
    users ||--o{ usage_records : "has many"
    users ||--o{ payments : "has many"
    users ||--o{ payment_failures : "has many"

    user_quotas }o--|| tier_limits : "references"
    stripe_subscriptions }o--|| tier_limits : "references tier"
```

---

## Tables

### generated_content

**Purpose:** Stores all AI-generated content for history and analytics.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |
| tool_id | TEXT | NO | - | Tool used for generation |
| inputs | JSONB | NO | - | Input parameters |
| output | TEXT | NO | - | Generated content |
| provider | TEXT | NO | 'openai' | LLM provider used |
| execution_time_ms | INTEGER | NO | 0 | Generation time |
| user_hash | TEXT | YES | - | Hashed user identifier |
| is_favorite | BOOLEAN | NO | false | Bookmarked status |
| tool_name | TEXT | YES | - | Display name of tool |
| title | TEXT | YES | - | Content title |

### conversations

**Purpose:** Stores conversation history (replacing file-based storage).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | TEXT | NO | - | Primary key (UUID from frontend) |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |
| messages | JSONB | NO | '[]' | Array of messages |
| metadata | JSONB | YES | - | Optional metadata |

### templates

**Purpose:** Stores reusable content templates with preset inputs.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |
| name | TEXT | NO | - | Template name |
| description | TEXT | YES | - | Template description |
| slug | TEXT | NO | - | URL-friendly identifier (UNIQUE) |
| tool_id | TEXT | NO | - | Associated tool |
| preset_inputs | JSONB | NO | '{}' | Preset input values |
| category | TEXT | NO | - | Category for filtering |
| tags | TEXT[] | YES | '{}' | Tags for search |
| is_public | BOOLEAN | NO | true | Public visibility |
| user_hash | TEXT | YES | - | Owner identifier |
| use_count | INTEGER | NO | 0 | Usage counter |

### tool_usage

**Purpose:** Tracks tool usage statistics for analytics.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| tool_id | TEXT | NO | - | Tool identifier (UNIQUE) |
| count | INTEGER | NO | 0 | Usage count |
| last_used_at | TIMESTAMPTZ | NO | NOW() | Last usage timestamp |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |

### brand_profiles

**Purpose:** Stores brand voice profiles for consistent content generation.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |
| name | TEXT | NO | - | Profile name |
| slug | TEXT | NO | - | URL-friendly identifier (UNIQUE) |
| tone_keywords | TEXT[] | NO | '{}' | Tone descriptors |
| writing_style | TEXT | NO | 'balanced' | Writing style |
| example_content | TEXT | YES | - | Sample content |
| industry | TEXT | YES | - | Industry/niche |
| target_audience | TEXT | YES | - | Target audience |
| preferred_words | TEXT[] | YES | '{}' | Words to prefer |
| avoid_words | TEXT[] | YES | '{}' | Words to avoid |
| brand_values | TEXT[] | YES | '{}' | Core values |
| content_themes | TEXT[] | YES | '{}' | Common themes |
| user_hash | TEXT | YES | - | Owner identifier |
| is_active | BOOLEAN | NO | true | Active status |
| is_default | BOOLEAN | NO | false | Default profile flag |
| voice_fingerprint_id | UUID | YES | - | FK to voice_fingerprints |
| training_status | TEXT | YES | 'untrained' | Training state |
| training_quality | FLOAT | YES | 0.0 | Training quality score |
| sample_count | INTEGER | YES | 0 | Number of samples |

### voice_samples

**Purpose:** Content samples used to train brand voice profiles.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| profile_id | UUID | NO | - | FK to brand_profiles |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| title | TEXT | YES | - | Sample title |
| content | TEXT | NO | - | Sample content |
| content_type | TEXT | NO | 'text' | Type (text/blog/email/social) |
| word_count | INTEGER | NO | 0 | Word count |
| source_url | TEXT | YES | - | Source URL |
| source_platform | TEXT | YES | - | Platform source |
| is_analyzed | BOOLEAN | NO | false | Analysis status |
| analysis_result | JSONB | YES | '{}' | Analysis results |
| quality_score | FLOAT | YES | 0.0 | Quality score |
| is_primary_example | BOOLEAN | YES | false | Primary example flag |

### voice_fingerprints

**Purpose:** Aggregated voice characteristics extracted from samples.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| profile_id | UUID | NO | - | FK to brand_profiles (UNIQUE) |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |
| vocabulary_profile | JSONB | YES | '{}' | Word patterns |
| sentence_patterns | JSONB | YES | '{}' | Sentence structure |
| tone_distribution | JSONB | YES | '{}' | Tone scores |
| style_metrics | JSONB | YES | '{}' | Style metrics |
| voice_summary | TEXT | YES | - | Natural language description |
| embedding_vector | FLOAT[] | YES | '{}' | Vector embedding |
| embedding_model | TEXT | YES | - | Embedding model used |
| sample_count | INTEGER | YES | 0 | Number of samples |
| last_trained_at | TIMESTAMPTZ | YES | - | Last training timestamp |
| training_quality | FLOAT | YES | 0.0 | Training quality |

### voice_scores

**Purpose:** Consistency scores for generated content against brand voice.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| profile_id | UUID | NO | - | FK to brand_profiles |
| content_id | TEXT | NO | - | Reference to generated content |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| overall_score | FLOAT | NO | - | Overall consistency score |
| tone_match | FLOAT | NO | - | Tone matching score |
| vocabulary_match | FLOAT | NO | - | Vocabulary matching score |
| style_match | FLOAT | NO | - | Style matching score |
| feedback | JSONB | YES | '{}' | Detailed feedback |
| deviations | JSONB | YES | '{}' | Deviation details |

### user_quotas

**Purpose:** Stores user subscription tier and billing period information.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| user_id | TEXT | NO | - | User identifier (UNIQUE) |
| tier | TEXT | NO | 'free' | Subscription tier |
| period_start | TIMESTAMPTZ | NO | date_trunc('month', NOW()) | Period start |
| period_end | TIMESTAMPTZ | NO | period_start + 1 month | Period end |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |

**Check Constraint:** `tier IN ('free', 'starter', 'pro', 'business')`

### usage_records

**Purpose:** Records individual content generation usage events.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| user_id | TEXT | NO | - | User identifier |
| operation_type | TEXT | NO | - | Type of operation |
| tokens_used | INTEGER | NO | 0 | Tokens consumed |
| timestamp | TIMESTAMPTZ | NO | NOW() | Event timestamp |
| metadata | JSONB | YES | - | Additional metadata |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |

**Check Constraint:** `operation_type IN ('blog', 'book', 'batch', 'remix', 'tool', 'other')`

### tier_limits

**Purpose:** Configurable tier limits and pricing (source of truth for quota enforcement).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| tier | TEXT | NO | - | Tier name (PRIMARY KEY) |
| monthly_limit | INTEGER | NO | - | Monthly generation limit |
| daily_limit | INTEGER | NO | -1 | Daily limit (-1 = unlimited) |
| features | TEXT[] | NO | '{}' | Available features |
| price_monthly | DECIMAL(10,2) | NO | 0 | Monthly price |
| price_yearly | DECIMAL(10,2) | NO | 0 | Yearly price |
| description | TEXT | YES | - | Tier description |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |

**Default Tier Configuration:**

| Tier | Monthly Limit | Daily Limit | Price/Month | Price/Year |
|------|---------------|-------------|-------------|------------|
| free | 5 | 2 | $0 | $0 |
| starter | 50 | 10 | $19 | $190 |
| pro | 200 | 50 | $49 | $490 |
| business | 1000 | unlimited | $149 | $1,490 |

### stripe_customers

**Purpose:** Maps internal user IDs to Stripe customer IDs.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| user_id | TEXT | NO | - | Internal user ID (UNIQUE) |
| customer_id | TEXT | NO | - | Stripe customer ID (UNIQUE) |
| email | TEXT | YES | - | Customer email |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |

### stripe_subscriptions

**Purpose:** Tracks Stripe subscription details.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| subscription_id | TEXT | NO | - | Stripe subscription ID (UNIQUE) |
| user_id | TEXT | NO | - | User identifier |
| customer_id | TEXT | YES | - | Stripe customer ID |
| tier | TEXT | NO | - | Subscription tier |
| status | TEXT | NO | 'active' | Subscription status |
| current_period_start | TIMESTAMPTZ | YES | - | Period start |
| current_period_end | TIMESTAMPTZ | YES | - | Period end |
| cancel_at_period_end | BOOLEAN | YES | false | Cancellation flag |
| cancelled_at | TIMESTAMPTZ | YES | - | Cancellation timestamp |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |

**Check Constraints:**
- `tier IN ('free', 'starter', 'pro', 'business')`
- `status IN ('active', 'trialing', 'past_due', 'cancelled', 'incomplete')`

### payments

**Purpose:** Records successful payment events from Stripe.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| user_id | TEXT | NO | - | User identifier |
| subscription_id | TEXT | YES | - | Related subscription |
| invoice_id | TEXT | YES | - | Stripe invoice ID |
| amount_cents | INTEGER | NO | - | Amount in cents |
| currency | TEXT | YES | 'usd' | Currency code |
| status | TEXT | NO | 'paid' | Payment status |
| paid_at | TIMESTAMPTZ | NO | NOW() | Payment timestamp |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |

**Check Constraint:** `status IN ('paid', 'refunded', 'partially_refunded')`

### payment_failures

**Purpose:** Tracks failed payment attempts for monitoring and user notification.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| user_id | TEXT | NO | - | User identifier |
| subscription_id | TEXT | YES | - | Related subscription |
| invoice_id | TEXT | YES | - | Stripe invoice ID |
| attempt_count | INTEGER | NO | 1 | Number of attempts |
| failure_reason | TEXT | YES | - | Failure reason |
| failed_at | TIMESTAMPTZ | NO | NOW() | Failure timestamp |
| resolved_at | TIMESTAMPTZ | YES | - | Resolution timestamp |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |

### users

**Purpose:** Core user accounts with subscription status.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | uuid_generate_v4() | Primary key |
| user_id | TEXT | NO | - | User identifier (UNIQUE) |
| email | TEXT | YES | - | User email |
| name | TEXT | YES | - | User name |
| stripe_customer_id | TEXT | YES | - | Stripe customer ID |
| tier | TEXT | YES | 'free' | Current tier |
| is_active | BOOLEAN | YES | true | Active status |
| last_login_at | TIMESTAMPTZ | YES | - | Last login |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |

**Check Constraint:** `tier IN ('free', 'starter', 'pro', 'business')`

---

## Functions

### Content Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `update_updated_at_column()` | - | TRIGGER | Auto-updates updated_at timestamp |
| `toggle_favorite(UUID)` | content_id | BOOLEAN | Toggles favorite status |
| `set_favorite(UUID, BOOLEAN)` | content_id, status | BOOLEAN | Sets favorite status explicitly |

### Tool Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `increment_tool_usage(TEXT)` | tool_id | VOID | Atomically increments tool usage |
| `get_tool_stats()` | - | TABLE | Returns tool usage sorted by popularity |

### Conversation Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `upsert_conversation(TEXT, JSONB, JSONB)` | id, messages, metadata | conversations | Create or update conversation |
| `add_conversation_message(TEXT, JSONB)` | id, message | conversations | Append message to conversation |

### Template Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `increment_template_use_count(UUID)` | template_id | VOID | Increments template usage |

### Brand Voice Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `set_default_brand_profile(UUID, TEXT)` | profile_id, user_hash | VOID | Sets default profile for user |

### Quota Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `get_current_month_usage(TEXT)` | user_id | TABLE | Returns current period usage |
| `get_daily_usage(TEXT)` | user_id | BIGINT | Returns today's usage count |
| `check_quota_available(TEXT)` | user_id | TABLE | Checks if user has remaining quota |
| `increment_user_usage(TEXT, TEXT, INT, JSONB)` | user_id, op_type, tokens, metadata | TABLE | Records usage atomically |
| `reset_expired_quotas()` | - | INTEGER | Resets expired billing periods |
| `get_usage_breakdown(TEXT, TIMESTAMPTZ, TIMESTAMPTZ)` | user_id, start, end | TABLE | Returns usage by operation type |

### Subscription Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `sync_user_tier_from_subscription()` | - | TRIGGER | Syncs tier when subscription changes |
| `get_subscription_status(TEXT)` | user_id | TABLE | Returns complete subscription status |

---

## Indexes

### Primary Indexes (Performance Critical)

| Table | Index Name | Columns | Type | Purpose |
|-------|------------|---------|------|---------|
| generated_content | idx_generated_content_tool_id | tool_id | BTREE | Filter by tool |
| generated_content | idx_generated_content_created_at | created_at DESC | BTREE | Sort by date |
| generated_content | idx_generated_content_user_hash | user_hash | BTREE (partial) | User content lookup |
| generated_content | idx_generated_content_is_favorite | is_favorite | BTREE (partial) | Filter favorites |
| generated_content | idx_generated_content_user_favorites | user_hash, is_favorite, created_at DESC | BTREE (partial) | User favorites |
| generated_content | idx_generated_content_title | title | GIN (tsvector) | Full-text search |
| usage_records | idx_usage_records_user_time | user_id, timestamp DESC | BTREE | User usage queries |
| usage_records | idx_usage_records_recent | user_id, timestamp | BTREE (partial) | Recent records optimization |

### Secondary Indexes

| Table | Index Name | Columns | Type |
|-------|------------|---------|------|
| conversations | idx_conversations_created_at | created_at DESC | BTREE |
| conversations | idx_conversations_updated_at | updated_at DESC | BTREE |
| templates | idx_templates_tool_id | tool_id | BTREE |
| templates | idx_templates_category | category | BTREE |
| templates | idx_templates_slug | slug | BTREE |
| templates | idx_templates_tags | tags | GIN |
| templates | idx_templates_use_count | use_count DESC | BTREE |
| brand_profiles | idx_brand_profiles_slug | slug | BTREE |
| brand_profiles | idx_brand_profiles_user_hash | user_hash | BTREE (partial) |
| brand_profiles | idx_brand_profiles_tone_keywords | tone_keywords | GIN |
| voice_samples | idx_voice_samples_profile | profile_id | BTREE |
| voice_samples | idx_voice_samples_analyzed | is_analyzed | BTREE (partial) |
| voice_fingerprints | idx_voice_fingerprints_profile | profile_id | BTREE (unique) |
| voice_scores | idx_voice_scores_profile | profile_id | BTREE |
| voice_scores | idx_voice_scores_content | content_id | BTREE |

---

## Row Level Security Policies

### generated_content

| Policy Name | Operation | Role | Condition |
|-------------|-----------|------|-----------|
| Service role has full access | ALL | service_role | true |
| Anonymous can insert | INSERT | anon | true |
| Users can read own content | SELECT | anon | user_hash IS NOT NULL |

### conversations

| Policy Name | Operation | Role | Condition |
|-------------|-----------|------|-----------|
| Service role has full access | ALL | service_role | true |
| Anonymous can manage | ALL | anon | true |

### templates

| Policy Name | Operation | Role | Condition |
|-------------|-----------|------|-----------|
| Service role has full access | ALL | service_role | true |
| Anonymous can read public | SELECT | anon | is_public = true |
| Anonymous can create | INSERT | anon | true |
| Users can update own | UPDATE | anon | user_hash IS NOT NULL |
| Users can delete own | DELETE | anon | user_hash IS NOT NULL |

### tool_usage

| Policy Name | Operation | Role | Condition |
|-------------|-----------|------|-----------|
| Anyone can read | SELECT | anon, authenticated | true |
| Service role can write | ALL | service_role | true |

### brand_profiles

| Policy Name | Operation | Role | Condition |
|-------------|-----------|------|-----------|
| Service role has full access | ALL | service_role | true |
| Anonymous can read own | SELECT | anon | user_hash IS NOT NULL |
| Anonymous can create | INSERT | anon | true |
| Anonymous can update own | UPDATE | anon | user_hash IS NOT NULL |
| Anonymous can delete own | DELETE | anon | user_hash IS NOT NULL |

### voice_samples, voice_fingerprints, voice_scores

| Policy Name | Operation | Role | Condition |
|-------------|-----------|------|-----------|
| Service role has full access | ALL | service_role | true |
| Users can manage via profile | ALL/SELECT | anon | EXISTS (SELECT 1 FROM brand_profiles WHERE user_hash IS NOT NULL) |

### user_quotas, usage_records

| Policy Name | Operation | Role | Condition |
|-------------|-----------|------|-----------|
| Users can view own | SELECT | authenticated | user_id = auth.uid() |
| Service role can manage | ALL | service_role | true |

### tier_limits

| Policy Name | Operation | Role | Condition |
|-------------|-----------|------|-----------|
| Anyone can read | SELECT | anon, authenticated, service_role | true |
| Service role can manage | ALL | service_role | true |

### stripe_customers, stripe_subscriptions, payments, payment_failures

| Policy Name | Operation | Role | Condition |
|-------------|-----------|------|-----------|
| Users can view own | SELECT | authenticated | user_id = auth.uid() |
| Service role can manage | ALL | service_role | true |

### users

| Policy Name | Operation | Role | Condition |
|-------------|-----------|------|-----------|
| Users can view own | SELECT | authenticated | user_id = auth.uid() |
| Users can update own | UPDATE | authenticated | user_id = auth.uid() |
| Service role can manage | ALL | service_role | true |

---

## Known Issues

### 1. Duplicate Migration Number (004) - HIGH PRIORITY

**Problem:** Two migrations share number 004, which can cause:
- Unpredictable execution order
- Migration tools may skip one file
- Deployment failures in some environments

**Fix:** Rename `004_create_templates.sql` to `004b_create_templates.sql` or renumber it to `009`.

### 2. Missing Rollback Scripts - MEDIUM PRIORITY

**Problem:** No DOWN migrations exist, making rollbacks impossible.

**Recommendation:** Create a `rollback/` directory with corresponding rollback scripts.

### 3. Potential RLS Gaps - LOW PRIORITY

**Observations:**
- `generated_content` SELECT policy allows any anon user to read content if user_hash IS NOT NULL (not checking if it matches)
- `templates` UPDATE/DELETE policies check if user_hash IS NOT NULL but don't verify ownership

**Recommendation:** Review and strengthen RLS policies to check actual ownership.

---

## Missing Migrations

Based on the codebase analysis (type definitions in `src/types/`), the following features may require additional database tables:

### 1. Batch Job Processing (src/types/batch.py)

**Current State:** No dedicated batch job table exists.

**Recommended Migration:**
```sql
CREATE TABLE IF NOT EXISTS batch_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    name TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    provider_strategy TEXT NOT NULL DEFAULT 'single',
    total_items INTEGER NOT NULL,
    completed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    estimated_cost_usd DECIMAL(10,4),
    actual_cost_usd DECIMAL(10,4),
    items JSONB NOT NULL DEFAULT '[]',
    results JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
```

### 2. Remix History (src/types/remix.py)

**Current State:** Remix operations are not persisted.

**Recommended Migration:**
```sql
CREATE TABLE IF NOT EXISTS remix_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT,
    source_content_id TEXT,
    target_format TEXT NOT NULL,
    remixed_content JSONB NOT NULL,
    quality_score FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3. Image Generation (src/types/images.py)

**Current State:** Generated images are not tracked.

**Recommended Migration:**
```sql
CREATE TABLE IF NOT EXISTS generated_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT,
    content_id TEXT,
    prompt TEXT NOT NULL,
    revised_prompt TEXT,
    url TEXT NOT NULL,
    provider TEXT NOT NULL,
    image_type TEXT NOT NULL,
    size TEXT NOT NULL,
    style TEXT,
    quality TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Maintenance Recommendations

### Regular Tasks

1. **Reset Expired Quotas** - Run daily via cron:
   ```sql
   SELECT reset_expired_quotas();
   ```

2. **Cleanup Old Usage Records** - Archive records older than 1 year:
   ```sql
   DELETE FROM usage_records WHERE timestamp < NOW() - INTERVAL '1 year';
   ```

3. **Vacuum Analyze** - Run weekly on high-write tables:
   ```sql
   VACUUM ANALYZE generated_content;
   VACUUM ANALYZE usage_records;
   ```

### Monitoring Queries

```sql
-- Check quota status for all users
SELECT * FROM check_quota_available(user_id) FROM users;

-- Find users approaching quota
SELECT user_id, tier, current_usage, monthly_limit
FROM check_quota_available(user_id)
WHERE remaining <= 5 AND remaining > 0;

-- Revenue by tier
SELECT tier, COUNT(*) as users, SUM(amount_cents)/100.0 as revenue
FROM stripe_subscriptions s
JOIN payments p ON p.subscription_id = s.subscription_id
WHERE s.status = 'active'
GROUP BY tier;
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-24 | 1.0 | Initial documentation |
