# Technical Architecture: Tier 1 Competitive Features

This document provides detailed technical architecture specifications for Blog AI's three Tier 1 competitive features: Batch Generation System, Content Remix Engine, and Enhanced Brand Voice Training.

---

## Table of Contents

1. [F1: Batch Generation System](#f1-batch-generation-system)
2. [F2: Content Remix Engine](#f2-content-remix-engine)
3. [F3: Enhanced Brand Voice Training](#f3-enhanced-brand-voice-training)

---

## F1: Batch Generation System

### Overview

The Batch Generation System enables users to process multiple content generation requests asynchronously with job tracking, cost estimation, and multi-LLM provider load balancing.

### Architecture Diagram

```
                                    +------------------+
                                    |   Frontend UI    |
                                    |  (Next.js 15)    |
                                    +--------+---------+
                                             |
                              WebSocket + REST API
                                             |
                                    +--------v---------+
                                    |   FastAPI        |
                                    |   /batch/*       |
                                    +--------+---------+
                                             |
                    +------------------------+------------------------+
                    |                        |                        |
           +--------v--------+      +--------v--------+      +--------v--------+
           |  Job Scheduler  |      |  Cost Estimator |      |  Quota Manager  |
           |  (Celery Beat)  |      |                 |      |                 |
           +-----------------+      +-----------------+      +-----------------+
                    |
           +--------v--------+
           |   Redis Queue   |
           |   (Job Broker)  |
           +--------+--------+
                    |
        +-----------+-----------+-----------+
        |           |           |           |
   +----v----+ +----v----+ +----v----+ +----v----+
   | Worker  | | Worker  | | Worker  | | Worker  |
   | (OpenAI)| |(Claude) | |(Gemini) | | (Mixed) |
   +---------+ +---------+ +---------+ +---------+
        |           |           |           |
        +-----------+-----------+-----------+
                    |
           +--------v--------+
           |   PostgreSQL    |
           |   (Supabase)    |
           +-----------------+
```

### Technology Selection: Celery + Redis

**Recommendation: Celery + Redis**

| Criteria | Celery + Redis | RQ (Redis Queue) | Dramatiq |
|----------|---------------|------------------|----------|
| Maturity | Excellent | Good | Good |
| Multi-provider support | Native | Limited | Good |
| Scheduling | Built-in (Beat) | Requires extra | Middleware |
| Monitoring | Flower UI | Basic | Custom |
| Retry/Error handling | Excellent | Basic | Good |
| Python ecosystem | Industry standard | Simpler | Modern |

**Rationale:**
- Celery provides battle-tested distributed task processing
- Native support for task prioritization and routing to specific workers
- Celery Beat enables scheduled/recurring batch jobs
- Flower provides real-time monitoring dashboard
- Redis serves dual purpose as message broker and result backend

### Data Models (Pydantic Schemas)

```python
# src/types/batch.py

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class JobStatus(str, Enum):
    """Batch job status states."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"  # Some items succeeded, some failed


class JobPriority(str, Enum):
    """Job priority levels for queue ordering."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ProviderStrategy(str, Enum):
    """Strategy for distributing work across LLM providers."""
    SINGLE = "single"           # Use one provider for all
    ROUND_ROBIN = "round_robin" # Rotate through available providers
    LOAD_BALANCED = "load_balanced"  # Route based on current load
    COST_OPTIMIZED = "cost_optimized"  # Route to cheapest available
    QUALITY_OPTIMIZED = "quality_optimized"  # Route to highest quality


class BatchItemInput(BaseModel):
    """Single item in a batch request."""
    topic: str = Field(..., min_length=3, max_length=500)
    keywords: List[str] = Field(default_factory=list, max_items=10)
    tone: str = Field(default="professional")
    content_type: str = Field(default="blog")  # blog, email, social, etc.
    custom_params: Dict[str, Any] = Field(default_factory=dict)

    @validator('keywords')
    def validate_keywords(cls, v):
        return [kw.strip().lower() for kw in v if kw.strip()]


class BatchRequest(BaseModel):
    """Request to create a new batch generation job."""
    items: List[BatchItemInput] = Field(..., min_items=1, max_items=100)

    # Processing options
    provider_strategy: ProviderStrategy = Field(default=ProviderStrategy.LOAD_BALANCED)
    preferred_provider: Optional[str] = Field(default=None)  # openai, anthropic, gemini
    parallel_limit: int = Field(default=3, ge=1, le=10)
    priority: JobPriority = Field(default=JobPriority.NORMAL)

    # Content options
    research_enabled: bool = Field(default=False)
    proofread_enabled: bool = Field(default=True)
    humanize_enabled: bool = Field(default=False)
    brand_profile_id: Optional[UUID] = Field(default=None)

    # Scheduling
    scheduled_at: Optional[datetime] = Field(default=None)

    # Metadata
    name: Optional[str] = Field(default=None, max_length=100)
    tags: List[str] = Field(default_factory=list, max_items=10)
    webhook_url: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"topic": "AI in Healthcare", "keywords": ["AI", "healthcare", "diagnosis"]},
                    {"topic": "Sustainable Technology", "keywords": ["green tech", "sustainability"]}
                ],
                "provider_strategy": "load_balanced",
                "parallel_limit": 5,
                "research_enabled": True
            }
        }


class BatchItemResult(BaseModel):
    """Result for a single batch item."""
    index: int
    item_id: UUID = Field(default_factory=uuid4)
    status: JobStatus
    topic: str

    # Results
    content: Optional[Dict[str, Any]] = Field(default=None)
    error: Optional[str] = Field(default=None)

    # Execution metadata
    provider_used: Optional[str] = Field(default=None)
    execution_time_ms: int = Field(default=0)
    token_count: int = Field(default=0)
    retry_count: int = Field(default=0)

    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)


class CostEstimate(BaseModel):
    """Cost estimation for a batch job."""
    estimated_tokens: int
    estimated_cost_usd: float
    cost_breakdown: Dict[str, float]  # Per provider if multi-provider
    confidence: float = Field(ge=0.0, le=1.0)  # Estimation confidence

    # Quota impact
    quota_available: int
    quota_after_job: int
    exceeds_quota: bool


class BatchJob(BaseModel):
    """Complete batch job with status and results."""
    id: UUID = Field(default_factory=uuid4)
    user_id: str

    # Request data
    request: BatchRequest

    # Status
    status: JobStatus = Field(default=JobStatus.PENDING)
    total_items: int
    completed_items: int = Field(default=0)
    failed_items: int = Field(default=0)
    progress_percentage: float = Field(default=0.0)

    # Results
    results: List[BatchItemResult] = Field(default_factory=list)

    # Cost tracking
    cost_estimate: Optional[CostEstimate] = Field(default=None)
    actual_cost_usd: float = Field(default=0.0)
    total_tokens_used: int = Field(default=0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    queued_at: Optional[datetime] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    # Control flags
    can_cancel: bool = Field(default=True)
    can_retry_failed: bool = Field(default=False)


class CSVImportSchema(BaseModel):
    """Schema for CSV batch import."""
    # Required columns
    topic: str

    # Optional columns
    keywords: Optional[str] = None  # Comma-separated
    tone: Optional[str] = "professional"
    content_type: Optional[str] = "blog"

    @validator('keywords', pre=True)
    def parse_keywords(cls, v):
        if isinstance(v, str):
            return [k.strip() for k in v.split(',') if k.strip()]
        return v


class CSVExportRow(BaseModel):
    """Schema for CSV batch export."""
    index: int
    topic: str
    status: str
    title: Optional[str]
    content_preview: Optional[str]  # First 500 chars
    full_content_url: Optional[str]  # Link to full content
    provider: Optional[str]
    execution_time_ms: int
    error: Optional[str]
```

### API Endpoints (OpenAPI-style)

```yaml
# Batch Generation API Endpoints

paths:
  /api/v1/batch/jobs:
    post:
      summary: Create a new batch generation job
      operationId: createBatchJob
      tags: [Batch]
      security:
        - ApiKeyAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BatchRequest'
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                  description: CSV file for batch import
                options:
                  $ref: '#/components/schemas/BatchOptions'
      responses:
        '202':
          description: Job accepted and queued
          content:
            application/json:
              schema:
                type: object
                properties:
                  success: { type: boolean }
                  job_id: { type: string, format: uuid }
                  status: { type: string }
                  estimated_completion: { type: string, format: date-time }
                  cost_estimate: { $ref: '#/components/schemas/CostEstimate' }
        '400':
          description: Invalid request (validation error)
        '402':
          description: Insufficient quota
        '429':
          description: Rate limited

    get:
      summary: List batch jobs for current user
      operationId: listBatchJobs
      tags: [Batch]
      security:
        - ApiKeyAuth: []
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [pending, queued, processing, completed, failed, cancelled]
        - name: limit
          in: query
          schema: { type: integer, default: 20, maximum: 100 }
        - name: offset
          in: query
          schema: { type: integer, default: 0 }
        - name: sort
          in: query
          schema: { type: string, enum: [created_at, -created_at, status] }
      responses:
        '200':
          description: List of batch jobs
          content:
            application/json:
              schema:
                type: object
                properties:
                  jobs:
                    type: array
                    items: { $ref: '#/components/schemas/BatchJobSummary' }
                  total: { type: integer }
                  has_more: { type: boolean }

  /api/v1/batch/jobs/{job_id}:
    get:
      summary: Get batch job details
      operationId: getBatchJob
      tags: [Batch]
      parameters:
        - name: job_id
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        '200':
          description: Batch job details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BatchJob'
        '404':
          description: Job not found

  /api/v1/batch/jobs/{job_id}/cancel:
    post:
      summary: Cancel a running batch job
      operationId: cancelBatchJob
      tags: [Batch]
      parameters:
        - name: job_id
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        '200':
          description: Job cancelled
        '400':
          description: Job cannot be cancelled (already completed)

  /api/v1/batch/jobs/{job_id}/retry:
    post:
      summary: Retry failed items in a batch job
      operationId: retryBatchJob
      tags: [Batch]
      parameters:
        - name: job_id
          in: path
          required: true
          schema: { type: string, format: uuid }
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                item_indices:
                  type: array
                  items: { type: integer }
                  description: Specific items to retry (empty = all failed)
      responses:
        '202':
          description: Retry job created

  /api/v1/batch/jobs/{job_id}/results:
    get:
      summary: Get batch job results
      operationId: getBatchResults
      tags: [Batch]
      parameters:
        - name: job_id
          in: path
          required: true
          schema: { type: string, format: uuid }
        - name: format
          in: query
          schema: { type: string, enum: [json, csv, zip], default: json }
        - name: include_content
          in: query
          schema: { type: boolean, default: true }
      responses:
        '200':
          description: Batch results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BatchJobResults'
            text/csv:
              schema:
                type: string
                format: binary
            application/zip:
              schema:
                type: string
                format: binary

  /api/v1/batch/estimate:
    post:
      summary: Estimate cost for a batch job
      operationId: estimateBatchCost
      tags: [Batch]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BatchRequest'
      responses:
        '200':
          description: Cost estimate
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CostEstimate'

  /api/v1/batch/templates:
    get:
      summary: Get CSV template for batch import
      operationId: getBatchTemplate
      tags: [Batch]
      responses:
        '200':
          description: CSV template
          content:
            text/csv:
              schema:
                type: string
```

### Database Schema

```sql
-- Migration: 006_create_batch_jobs.sql
-- Description: Tables for batch generation system

-- Batch jobs table
CREATE TABLE IF NOT EXISTS batch_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- User ownership
    user_hash TEXT NOT NULL,

    -- Job metadata
    name TEXT,
    tags TEXT[] DEFAULT '{}',

    -- Request configuration (stored as JSONB for flexibility)
    request_config JSONB NOT NULL,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'queued', 'processing', 'completed', 'failed', 'cancelled', 'partial')),

    -- Progress tracking
    total_items INTEGER NOT NULL,
    completed_items INTEGER NOT NULL DEFAULT 0,
    failed_items INTEGER NOT NULL DEFAULT 0,
    progress_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,

    -- Cost tracking
    estimated_cost_usd DECIMAL(10,4),
    actual_cost_usd DECIMAL(10,4) DEFAULT 0.0000,
    total_tokens_used INTEGER DEFAULT 0,

    -- Timing
    scheduled_at TIMESTAMPTZ,
    queued_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Control
    can_cancel BOOLEAN NOT NULL DEFAULT true,
    webhook_url TEXT,

    -- Celery task tracking
    celery_task_id TEXT
);

-- Batch job items table
CREATE TABLE IF NOT EXISTS batch_job_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Parent job
    job_id UUID NOT NULL REFERENCES batch_jobs(id) ON DELETE CASCADE,
    item_index INTEGER NOT NULL,

    -- Input
    topic TEXT NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    tone TEXT DEFAULT 'professional',
    content_type TEXT DEFAULT 'blog',
    custom_params JSONB DEFAULT '{}',

    -- Status
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),

    -- Result
    content JSONB,
    error TEXT,

    -- Execution metadata
    provider_used TEXT,
    execution_time_ms INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Celery task tracking
    celery_task_id TEXT,

    UNIQUE(job_id, item_index)
);

-- Indexes
CREATE INDEX idx_batch_jobs_user_hash ON batch_jobs(user_hash);
CREATE INDEX idx_batch_jobs_status ON batch_jobs(status);
CREATE INDEX idx_batch_jobs_created_at ON batch_jobs(created_at DESC);
CREATE INDEX idx_batch_jobs_scheduled_at ON batch_jobs(scheduled_at)
    WHERE scheduled_at IS NOT NULL AND status = 'pending';

CREATE INDEX idx_batch_job_items_job_id ON batch_job_items(job_id);
CREATE INDEX idx_batch_job_items_status ON batch_job_items(job_id, status);

-- Auto-update triggers
CREATE TRIGGER update_batch_jobs_updated_at
    BEFORE UPDATE ON batch_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_batch_job_items_updated_at
    BEFORE UPDATE ON batch_job_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security
ALTER TABLE batch_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch_job_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own batch_jobs"
    ON batch_jobs FOR ALL TO anon
    USING (user_hash IS NOT NULL)
    WITH CHECK (user_hash IS NOT NULL);

CREATE POLICY "Users can access items of own batch_jobs"
    ON batch_job_items FOR ALL TO anon
    USING (
        EXISTS (
            SELECT 1 FROM batch_jobs
            WHERE batch_jobs.id = batch_job_items.job_id
            AND batch_jobs.user_hash IS NOT NULL
        )
    );
```

### File/Module Structure

```
src/
  batch/
    __init__.py
    models.py              # Pydantic models (BatchRequest, BatchJob, etc.)
    service.py             # Business logic (create_job, cancel_job, etc.)
    cost_estimator.py      # Token/cost estimation
    quota_manager.py       # Quota checking and tracking
    csv_handler.py         # CSV import/export utilities

  celery_app/
    __init__.py
    celery.py              # Celery app configuration
    config.py              # Celery settings (broker, result backend)
    tasks/
      __init__.py
      batch_tasks.py       # Batch processing tasks
      content_tasks.py     # Individual content generation tasks
      notification_tasks.py # Webhook/email notifications

  workers/
    __init__.py
    provider_router.py     # Route tasks to appropriate provider
    load_balancer.py       # Track provider loads and route accordingly

app/
  routes/
    batch.py               # FastAPI endpoints for batch operations

frontend/
  components/
    batch/
      BatchJobMonitor.tsx    # Real-time job progress display
      BatchJobList.tsx       # List of user's batch jobs
      BatchItemTable.tsx     # Results table with pagination
      CSVUploader.tsx        # Drag-drop CSV upload
      CostEstimator.tsx      # Pre-submission cost display
      ProviderSelector.tsx   # Multi-provider strategy selection

  hooks/
    useBatchJob.ts           # WebSocket subscription for job updates
    useBatchJobList.ts       # Paginated job list fetching
```

### Dependencies to Add

```toml
# pyproject.toml additions

[tool.poetry.dependencies]
celery = "^5.3.0"
redis = "^5.0.0"
flower = "^2.0.0"          # Celery monitoring
kombu = "^5.3.0"           # Message queue abstraction
python-multipart = "^0.0.6" # File uploads

[tool.poetry.group.dev.dependencies]
pytest-celery = "^0.0.0"   # Celery testing utilities
fakeredis = "^2.20.0"      # Redis mocking
```

```json
// frontend/package.json additions
{
  "dependencies": {
    "react-dropzone": "^14.2.3",
    "papaparse": "^5.4.1",
    "file-saver": "^2.0.5"
  }
}
```

### Parallel Processing Strategy

```python
# src/workers/provider_router.py

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import redis
import time


@dataclass
class ProviderStatus:
    name: str
    available: bool
    current_load: int
    max_concurrent: int
    avg_latency_ms: float
    cost_per_1k_tokens: float
    error_rate_1h: float


class ProviderRouter:
    """Routes batch items to appropriate LLM providers based on strategy."""

    PROVIDER_COSTS = {
        "openai": {"gpt-4": 0.03, "gpt-4-turbo": 0.01, "gpt-3.5-turbo": 0.0015},
        "anthropic": {"claude-3-opus": 0.015, "claude-3-sonnet": 0.003},
        "gemini": {"gemini-1.5-pro": 0.00125, "gemini-1.5-flash": 0.000075}
    }

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self._load_key = "provider:load:{provider}"
        self._error_key = "provider:errors:{provider}"

    def get_provider_status(self) -> Dict[str, ProviderStatus]:
        """Get current status of all providers."""
        statuses = {}
        for provider in ["openai", "anthropic", "gemini"]:
            load = int(self.redis.get(self._load_key.format(provider=provider)) or 0)
            errors = int(self.redis.get(self._error_key.format(provider=provider)) or 0)

            statuses[provider] = ProviderStatus(
                name=provider,
                available=self._check_provider_available(provider),
                current_load=load,
                max_concurrent=self._get_max_concurrent(provider),
                avg_latency_ms=self._get_avg_latency(provider),
                cost_per_1k_tokens=self._get_cost(provider),
                error_rate_1h=errors / max(load, 1)
            )
        return statuses

    def select_provider(
        self,
        strategy: str,
        preferred: Optional[str] = None,
        item_complexity: str = "normal"
    ) -> str:
        """Select optimal provider based on strategy."""

        if strategy == "single" and preferred:
            return preferred

        statuses = self.get_provider_status()
        available = {k: v for k, v in statuses.items() if v.available}

        if not available:
            raise RuntimeError("No LLM providers available")

        if strategy == "round_robin":
            return self._round_robin_select(available)

        elif strategy == "load_balanced":
            # Select provider with lowest load ratio
            return min(
                available.items(),
                key=lambda x: x[1].current_load / x[1].max_concurrent
            )[0]

        elif strategy == "cost_optimized":
            return min(available.items(), key=lambda x: x[1].cost_per_1k_tokens)[0]

        elif strategy == "quality_optimized":
            # Prefer OpenAI GPT-4 > Claude Opus > Others
            priority = ["openai", "anthropic", "gemini"]
            for p in priority:
                if p in available:
                    return p

        return "openai"  # Default fallback

    def increment_load(self, provider: str):
        """Track that a task was sent to provider."""
        self.redis.incr(self._load_key.format(provider=provider))
        self.redis.expire(self._load_key.format(provider=provider), 3600)

    def decrement_load(self, provider: str):
        """Track that a task completed on provider."""
        self.redis.decr(self._load_key.format(provider=provider))

    def record_error(self, provider: str):
        """Record an error for provider health tracking."""
        self.redis.incr(self._error_key.format(provider=provider))
        self.redis.expire(self._error_key.format(provider=provider), 3600)
```

### Estimated Complexity

| Component | Effort | Risk | Dependencies |
|-----------|--------|------|--------------|
| Celery setup + Redis | 2 days | Low | Infrastructure |
| Data models + migrations | 1 day | Low | None |
| API endpoints | 2 days | Low | Models |
| Celery tasks | 3 days | Medium | Provider routing |
| Provider router/balancer | 2 days | Medium | Redis |
| Cost estimator | 1 day | Low | Provider data |
| CSV import/export | 1 day | Low | None |
| Frontend components | 3 days | Low | WebSocket |
| WebSocket integration | 1 day | Low | Existing WS |
| Testing + QA | 2 days | Medium | All above |
| **Total** | **18 days** | **Medium** | |

---

## F2: Content Remix Engine

### Overview

The Content Remix Engine transforms existing content between formats (blog to Twitter thread, blog to email newsletter, etc.) while preserving the core message and brand voice.

### Architecture Diagram

```
                         +-------------------+
                         |   Source Content  |
                         | (Blog/Article/Doc)|
                         +---------+---------+
                                   |
                         +---------v---------+
                         |  Content Analyzer |
                         |  - Extract topics |
                         |  - Identify key   |
                         |    points         |
                         |  - Detect tone    |
                         +---------+---------+
                                   |
                         +---------v---------+
                         |  Format Router    |
                         +---------+---------+
                                   |
        +-------------+------------+------------+-------------+
        |             |            |            |             |
   +----v----+   +----v----+  +----v----+  +----v----+  +----v----+
   | Twitter |   | LinkedIn|  | Email   |  | Video   |  | Podcast |
   | Thread  |   | Post    |  | Series  |  | Script  |  | Notes   |
   | Adapter |   | Adapter |  | Adapter |  | Adapter |  | Adapter |
   +---------+   +---------+  +---------+  +---------+  +---------+
        |             |            |            |             |
        +-------------+------------+------------+-------------+
                                   |
                         +---------v---------+
                         |  Quality Scorer   |
                         |  - Format fit     |
                         |  - Voice match    |
                         |  - Completeness   |
                         +---------+---------+
                                   |
                         +---------v---------+
                         |  Brand Voice      |
                         |  Harmonizer       |
                         +---------+---------+
                                   |
                         +---------v---------+
                         |   Remixed Output  |
                         +-------------------+
```

### Supported Format Mappings

```yaml
format_mappings:
  blog_post:
    targets:
      - twitter_thread:
          max_tweets: 15
          include_hook: true
          include_cta: true
      - linkedin_post:
          max_length: 3000
          professional_tone: true
      - email_newsletter:
          subject_variants: 3
          preview_text: true
      - instagram_carousel:
          max_slides: 10
          text_per_slide: 125
      - video_script:
          duration_options: [60, 180, 300]
          include_b_roll_notes: true
      - podcast_notes:
          include_timestamps: true
          include_quotes: true
      - executive_summary:
          max_length: 500
          bullet_points: true
      - seo_variations:
          count: 3
          keyword_focus: true

  long_form_article:
    targets:
      - blog_series:
          parts: 3-5
          interlinked: true
      - ebook_chapter:
          include_exercises: true
      - whitepaper:
          include_citations: true
          formal_tone: true

  video_transcript:
    targets:
      - blog_post:
          enhance_for_seo: true
      - key_quotes:
          max_quotes: 10
          include_timestamps: true
      - social_clips:
          duration_max: 60
          vertical_format: true
```

### Data Models (Pydantic Schemas)

```python
# src/types/remix.py

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class SourceFormat(str, Enum):
    """Supported source content formats."""
    BLOG_POST = "blog_post"
    LONG_ARTICLE = "long_article"
    VIDEO_TRANSCRIPT = "video_transcript"
    PODCAST_TRANSCRIPT = "podcast_transcript"
    WHITEPAPER = "whitepaper"
    PRESENTATION = "presentation"
    DOCUMENTATION = "documentation"


class TargetFormat(str, Enum):
    """Supported target output formats."""
    TWITTER_THREAD = "twitter_thread"
    LINKEDIN_POST = "linkedin_post"
    LINKEDIN_ARTICLE = "linkedin_article"
    EMAIL_NEWSLETTER = "email_newsletter"
    EMAIL_SEQUENCE = "email_sequence"
    INSTAGRAM_CAROUSEL = "instagram_carousel"
    INSTAGRAM_CAPTION = "instagram_caption"
    VIDEO_SCRIPT_SHORT = "video_script_short"
    VIDEO_SCRIPT_LONG = "video_script_long"
    PODCAST_NOTES = "podcast_notes"
    EXECUTIVE_SUMMARY = "executive_summary"
    BULLET_POINTS = "bullet_points"
    FAQ = "faq"
    INFOGRAPHIC_TEXT = "infographic_text"
    PRESS_RELEASE = "press_release"
    AD_COPY = "ad_copy"


class ContentChunk(BaseModel):
    """A chunk of content with metadata."""
    id: str
    text: str
    chunk_type: str  # heading, paragraph, list, quote, code
    importance_score: float = Field(ge=0.0, le=1.0)
    key_points: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    sentiment: Optional[str] = None


class ContentAnalysis(BaseModel):
    """Analysis of source content."""
    word_count: int
    reading_time_minutes: int

    # Structure
    chunks: List[ContentChunk]
    main_topics: List[str]
    key_points: List[str]

    # Style analysis
    detected_tone: str
    formality_score: float = Field(ge=0.0, le=1.0)
    complexity_score: float = Field(ge=0.0, le=1.0)

    # SEO elements
    keywords: List[str]
    entities: List[Dict[str, str]]  # {name, type, salience}

    # Quotable content
    notable_quotes: List[str]
    statistics: List[str]


class FormatAdapterConfig(BaseModel):
    """Configuration for a specific format adapter."""
    format: TargetFormat

    # Length constraints
    max_length: Optional[int] = None
    min_length: Optional[int] = None

    # Structure options
    max_parts: Optional[int] = None  # For threads, carousels, series
    include_hook: bool = True
    include_cta: bool = True

    # Style adjustments
    tone_override: Optional[str] = None
    emoji_usage: str = "moderate"  # none, minimal, moderate, heavy
    hashtag_count: int = 0

    # Platform-specific
    platform_optimized: bool = True


class RemixRequest(BaseModel):
    """Request to remix content to a new format."""
    # Source content
    source_content: str = Field(..., min_length=100)
    source_format: SourceFormat = Field(default=SourceFormat.BLOG_POST)
    source_url: Optional[str] = None  # For attribution

    # Target format(s)
    target_formats: List[TargetFormat] = Field(..., min_items=1)
    format_configs: Dict[TargetFormat, FormatAdapterConfig] = Field(default_factory=dict)

    # Brand voice
    brand_profile_id: Optional[UUID] = None
    voice_strength: float = Field(default=0.7, ge=0.0, le=1.0)

    # Quality settings
    preserve_key_points: bool = True
    preserve_statistics: bool = True
    preserve_quotes: bool = True

    # Output preferences
    variations_per_format: int = Field(default=1, ge=1, le=3)

    class Config:
        json_schema_extra = {
            "example": {
                "source_content": "Your blog post content here...",
                "source_format": "blog_post",
                "target_formats": ["twitter_thread", "linkedin_post"],
                "brand_profile_id": "uuid-here",
                "voice_strength": 0.8
            }
        }


class RemixedContent(BaseModel):
    """Single remixed content output."""
    id: UUID = Field(default_factory=uuid4)
    target_format: TargetFormat
    variation_index: int = 0

    # Content
    content: Union[str, List[str], Dict[str, Any]]  # Format-dependent

    # Metadata
    character_count: int
    word_count: int
    estimated_read_time: Optional[int] = None

    # Quality metrics
    quality_score: float = Field(ge=0.0, le=1.0)
    format_fit_score: float = Field(ge=0.0, le=1.0)
    voice_match_score: float = Field(ge=0.0, le=1.0)
    completeness_score: float = Field(ge=0.0, le=1.0)

    # Recommendations
    improvement_suggestions: List[str] = Field(default_factory=list)


class TwitterThread(BaseModel):
    """Twitter/X thread format."""
    tweets: List[str] = Field(..., max_items=25)
    total_characters: int
    hook_tweet: str
    cta_tweet: Optional[str] = None
    suggested_images: List[int] = Field(default_factory=list)  # Tweet indices


class LinkedInPost(BaseModel):
    """LinkedIn post format."""
    content: str = Field(..., max_length=3000)
    hook_line: str
    bullet_points: List[str] = Field(default_factory=list)
    call_to_action: Optional[str] = None
    suggested_hashtags: List[str] = Field(default_factory=list, max_items=5)


class EmailNewsletter(BaseModel):
    """Email newsletter format."""
    subject_lines: List[str] = Field(..., min_items=1, max_items=5)
    preview_text: str = Field(..., max_length=150)

    greeting: str
    intro_paragraph: str
    main_content: str
    bullet_highlights: List[str]
    call_to_action: str
    sign_off: str

    # Variants
    subject_a_b_variants: List[Dict[str, str]] = Field(default_factory=list)


class RemixResult(BaseModel):
    """Complete result of a remix operation."""
    id: UUID = Field(default_factory=uuid4)

    # Source info
    source_analysis: ContentAnalysis

    # Outputs
    outputs: List[RemixedContent]

    # Processing metadata
    processing_time_ms: int
    provider_used: str
    tokens_used: int

    created_at: datetime = Field(default_factory=datetime.utcnow)


class RemixHistory(BaseModel):
    """Historical record of a remix operation."""
    id: UUID
    user_hash: str

    source_preview: str  # First 500 chars
    source_format: SourceFormat
    target_formats: List[TargetFormat]

    brand_profile_id: Optional[UUID]
    brand_profile_name: Optional[str]

    quality_scores: Dict[TargetFormat, float]

    created_at: datetime
```

### Format Adapter Interface

```python
# src/remix/adapters/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ..types import ContentAnalysis, FormatAdapterConfig, RemixedContent, TargetFormat


class FormatAdapter(ABC):
    """Base class for content format adapters."""

    @property
    @abstractmethod
    def target_format(self) -> TargetFormat:
        """The target format this adapter produces."""
        pass

    @property
    @abstractmethod
    def constraints(self) -> Dict[str, Any]:
        """Format-specific constraints (max length, parts, etc.)."""
        pass

    @property
    @abstractmethod
    def prompt_template(self) -> str:
        """LLM prompt template for this format."""
        pass

    @abstractmethod
    def validate_config(self, config: FormatAdapterConfig) -> bool:
        """Validate adapter configuration."""
        pass

    @abstractmethod
    def pre_process(
        self,
        analysis: ContentAnalysis,
        config: FormatAdapterConfig
    ) -> Dict[str, Any]:
        """Prepare content for transformation."""
        pass

    @abstractmethod
    def post_process(
        self,
        raw_output: str,
        config: FormatAdapterConfig
    ) -> RemixedContent:
        """Process LLM output into structured format."""
        pass

    def calculate_quality_score(
        self,
        output: RemixedContent,
        analysis: ContentAnalysis,
        config: FormatAdapterConfig
    ) -> float:
        """Calculate overall quality score for the output."""
        scores = [
            self._format_fit_score(output),
            self._completeness_score(output, analysis),
            self._constraint_adherence_score(output, config)
        ]
        return sum(scores) / len(scores)

    @abstractmethod
    def _format_fit_score(self, output: RemixedContent) -> float:
        """How well does output fit the target format?"""
        pass

    @abstractmethod
    def _completeness_score(
        self,
        output: RemixedContent,
        analysis: ContentAnalysis
    ) -> float:
        """How complete is the content transformation?"""
        pass


# src/remix/adapters/twitter_thread.py

class TwitterThreadAdapter(FormatAdapter):
    """Adapter for converting content to Twitter/X threads."""

    MAX_TWEET_LENGTH = 280
    MAX_THREAD_LENGTH = 25

    @property
    def target_format(self) -> TargetFormat:
        return TargetFormat.TWITTER_THREAD

    @property
    def constraints(self) -> Dict[str, Any]:
        return {
            "max_tweet_length": self.MAX_TWEET_LENGTH,
            "max_thread_length": self.MAX_THREAD_LENGTH,
            "requires_hook": True,
            "supports_images": True
        }

    @property
    def prompt_template(self) -> str:
        return """Transform this content into an engaging Twitter/X thread.

SOURCE CONTENT:
{content}

KEY POINTS TO INCLUDE:
{key_points}

BRAND VOICE CONTEXT:
{brand_context}

REQUIREMENTS:
- Create {max_tweets} tweets maximum
- Each tweet must be under 280 characters
- Start with a compelling hook tweet that creates curiosity
- Use thread numbering (1/, 2/, etc.) or natural flow
- Include specific data/statistics where available
- End with a clear call-to-action
- {emoji_instruction}
- {hashtag_instruction}

OUTPUT FORMAT:
Return each tweet on a new line, separated by ---
Mark the hook tweet with [HOOK] and CTA tweet with [CTA]
"""

    def pre_process(
        self,
        analysis: ContentAnalysis,
        config: FormatAdapterConfig
    ) -> Dict[str, Any]:
        # Select most important chunks for thread
        key_chunks = sorted(
            analysis.chunks,
            key=lambda c: c.importance_score,
            reverse=True
        )[:config.max_parts or 10]

        return {
            "content": "\n".join([c.text for c in key_chunks]),
            "key_points": analysis.key_points[:5],
            "max_tweets": config.max_parts or 10,
            "emoji_instruction": self._get_emoji_instruction(config.emoji_usage),
            "hashtag_instruction": f"Include {config.hashtag_count} relevant hashtags"
                                  if config.hashtag_count else "No hashtags"
        }

    def post_process(
        self,
        raw_output: str,
        config: FormatAdapterConfig
    ) -> RemixedContent:
        # Parse tweets from output
        tweets = []
        hook_tweet = None
        cta_tweet = None

        for line in raw_output.split("---"):
            line = line.strip()
            if not line:
                continue

            if "[HOOK]" in line:
                hook_tweet = line.replace("[HOOK]", "").strip()
                tweets.append(hook_tweet)
            elif "[CTA]" in line:
                cta_tweet = line.replace("[CTA]", "").strip()
                tweets.append(cta_tweet)
            else:
                tweets.append(line)

        # Validate tweet lengths
        valid_tweets = []
        for tweet in tweets:
            if len(tweet) <= self.MAX_TWEET_LENGTH:
                valid_tweets.append(tweet)
            else:
                # Split long tweets
                valid_tweets.extend(self._split_tweet(tweet))

        thread_content = TwitterThread(
            tweets=valid_tweets[:self.MAX_THREAD_LENGTH],
            total_characters=sum(len(t) for t in valid_tweets),
            hook_tweet=hook_tweet or valid_tweets[0] if valid_tweets else "",
            cta_tweet=cta_tweet
        )

        return RemixedContent(
            target_format=self.target_format,
            content=thread_content.dict(),
            character_count=thread_content.total_characters,
            word_count=sum(len(t.split()) for t in valid_tweets),
            quality_score=0.0  # Calculated later
        )

    def _split_tweet(self, tweet: str) -> List[str]:
        """Split a long tweet into multiple valid tweets."""
        # Implementation: split on sentence boundaries
        pass
```

### Content Chunking/Expansion Algorithms

```python
# src/remix/processing/chunker.py

from typing import List, Tuple
from dataclasses import dataclass
import re
from sentence_transformers import SentenceTransformer
import numpy as np


@dataclass
class ChunkConfig:
    min_chunk_size: int = 100
    max_chunk_size: int = 1000
    overlap_size: int = 50
    preserve_paragraphs: bool = True
    preserve_headings: bool = True


class ContentChunker:
    """Intelligent content chunking with semantic awareness."""

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        self.embedder = SentenceTransformer(embedding_model)

    def chunk_content(
        self,
        content: str,
        config: ChunkConfig
    ) -> List[ContentChunk]:
        """Split content into semantically coherent chunks."""

        # Step 1: Structural parsing
        structural_chunks = self._parse_structure(content)

        # Step 2: Semantic coherence check
        coherent_chunks = self._ensure_semantic_coherence(
            structural_chunks,
            config
        )

        # Step 3: Importance scoring
        scored_chunks = self._score_importance(coherent_chunks, content)

        return scored_chunks

    def _parse_structure(self, content: str) -> List[dict]:
        """Parse content structure (headings, paragraphs, lists)."""
        chunks = []

        # Detect headings
        heading_pattern = r'^(#{1,6})\s+(.+)$|^(.+)\n[=-]+$'

        # Detect lists
        list_pattern = r'^[\s]*[-*\d.]+\s+.+$'

        # Detect code blocks
        code_pattern = r'```[\s\S]*?```'

        # Split by paragraphs first
        paragraphs = re.split(r'\n\s*\n', content)

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Determine chunk type
            if re.match(heading_pattern, para, re.MULTILINE):
                chunk_type = "heading"
            elif re.match(list_pattern, para, re.MULTILINE):
                chunk_type = "list"
            elif re.match(code_pattern, para):
                chunk_type = "code"
            elif para.startswith('>'):
                chunk_type = "quote"
            else:
                chunk_type = "paragraph"

            chunks.append({
                "text": para,
                "type": chunk_type
            })

        return chunks

    def _ensure_semantic_coherence(
        self,
        chunks: List[dict],
        config: ChunkConfig
    ) -> List[dict]:
        """Merge or split chunks based on semantic similarity."""

        # Get embeddings for all chunks
        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.encode(texts)

        coherent = []
        current_group = [chunks[0]]
        current_embedding = embeddings[0]

        for i in range(1, len(chunks)):
            chunk = chunks[i]
            embedding = embeddings[i]

            # Calculate similarity with current group
            similarity = np.dot(current_embedding, embedding) / (
                np.linalg.norm(current_embedding) * np.linalg.norm(embedding)
            )

            current_size = sum(len(c["text"]) for c in current_group)

            # Decide whether to merge or start new group
            if (similarity > 0.7 and
                current_size + len(chunk["text"]) <= config.max_chunk_size):
                current_group.append(chunk)
                # Update embedding as average
                current_embedding = (current_embedding + embedding) / 2
            else:
                # Finalize current group
                coherent.append(self._merge_group(current_group))
                current_group = [chunk]
                current_embedding = embedding

        # Don't forget last group
        if current_group:
            coherent.append(self._merge_group(current_group))

        return coherent

    def _score_importance(
        self,
        chunks: List[dict],
        full_content: str
    ) -> List[ContentChunk]:
        """Score chunk importance using multiple signals."""

        scored = []

        # Get full content embedding for relevance comparison
        full_embedding = self.embedder.encode([full_content])[0]
        chunk_embeddings = self.embedder.encode([c["text"] for c in chunks])

        for i, chunk in enumerate(chunks):
            text = chunk["text"]
            chunk_type = chunk["type"]

            # Calculate relevance score
            relevance = np.dot(full_embedding, chunk_embeddings[i]) / (
                np.linalg.norm(full_embedding) * np.linalg.norm(chunk_embeddings[i])
            )

            # Position score (earlier = more important for intros)
            position_score = 1.0 - (i / len(chunks)) * 0.3

            # Type score
            type_scores = {
                "heading": 0.9,
                "quote": 0.8,
                "list": 0.7,
                "paragraph": 0.6,
                "code": 0.5
            }
            type_score = type_scores.get(chunk_type, 0.5)

            # Information density (entities, numbers, proper nouns)
            density_score = self._calculate_density(text)

            # Combined importance
            importance = (
                relevance * 0.4 +
                position_score * 0.2 +
                type_score * 0.2 +
                density_score * 0.2
            )

            # Extract key points from chunk
            key_points = self._extract_key_points(text)

            scored.append(ContentChunk(
                id=f"chunk_{i}",
                text=text,
                chunk_type=chunk_type,
                importance_score=min(1.0, importance),
                key_points=key_points,
                entities=self._extract_entities(text)
            ))

        return scored
```

### Brand Voice Preservation Strategy

```python
# src/remix/processing/voice_harmonizer.py

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class VoiceProfile:
    tone_keywords: List[str]
    writing_style: str
    preferred_words: List[str]
    avoid_words: List[str]
    example_content: Optional[str]
    formality_level: float  # 0.0 (casual) to 1.0 (formal)


class BrandVoiceHarmonizer:
    """Applies brand voice consistently across remixed content."""

    def __init__(self, llm_provider):
        self.llm = llm_provider

    def apply_voice(
        self,
        content: str,
        voice_profile: VoiceProfile,
        strength: float = 0.7,
        preserve_structure: bool = True
    ) -> str:
        """Apply brand voice to content with specified strength."""

        # Step 1: Analyze current voice
        current_voice = self._analyze_voice(content)

        # Step 2: Calculate voice delta
        voice_delta = self._calculate_voice_delta(
            current_voice,
            voice_profile,
            strength
        )

        # Step 3: Generate transformation prompt
        prompt = self._build_voice_prompt(
            content,
            voice_profile,
            voice_delta,
            preserve_structure
        )

        # Step 4: Apply transformation
        transformed = self.llm.generate(prompt)

        # Step 5: Validate transformation
        if self._validate_voice_match(transformed, voice_profile) < 0.6:
            # Retry with stronger instructions
            return self._retry_with_examples(
                content,
                voice_profile,
                preserve_structure
            )

        return transformed

    def _build_voice_prompt(
        self,
        content: str,
        profile: VoiceProfile,
        delta: Dict[str, float],
        preserve_structure: bool
    ) -> str:
        """Build prompt for voice transformation."""

        word_instructions = []
        if profile.preferred_words:
            word_instructions.append(
                f"USE these words where natural: {', '.join(profile.preferred_words)}"
            )
        if profile.avoid_words:
            word_instructions.append(
                f"AVOID these words: {', '.join(profile.avoid_words)}"
            )

        example_section = ""
        if profile.example_content:
            example_section = f"""
EXAMPLE OF DESIRED VOICE:
\"\"\"{profile.example_content}\"\"\"

Match this example's tone and style."""

        return f"""Transform the following content to match a specific brand voice.

CONTENT TO TRANSFORM:
\"\"\"{content}\"\"\"

BRAND VOICE REQUIREMENTS:
- Writing style: {profile.writing_style}
- Tone: {', '.join(profile.tone_keywords)}
- Formality level: {'formal' if profile.formality_level > 0.6 else 'casual' if profile.formality_level < 0.4 else 'balanced'}

{chr(10).join(word_instructions)}

{example_section}

TRANSFORMATION RULES:
1. {"Preserve the exact structure and formatting" if preserve_structure else "Restructure as needed for better flow"}
2. Keep all factual information intact
3. Maintain the same approximate length
4. Apply the brand voice naturally - don't force it

Transform the content now:"""

    def _validate_voice_match(
        self,
        content: str,
        profile: VoiceProfile
    ) -> float:
        """Score how well content matches the voice profile."""

        scores = []

        # Check preferred word usage
        preferred_count = sum(
            1 for word in profile.preferred_words
            if word.lower() in content.lower()
        )
        if profile.preferred_words:
            scores.append(min(1.0, preferred_count / len(profile.preferred_words)))

        # Check avoided word absence
        avoided_count = sum(
            1 for word in profile.avoid_words
            if word.lower() in content.lower()
        )
        if profile.avoid_words:
            scores.append(1.0 - min(1.0, avoided_count / len(profile.avoid_words)))

        # Formality check (simple heuristic)
        formal_indicators = ['therefore', 'furthermore', 'consequently', 'regarding']
        casual_indicators = ["you'll", "we're", "it's", "don't", "!"]

        formal_count = sum(1 for w in formal_indicators if w in content.lower())
        casual_count = sum(1 for w in casual_indicators if w in content.lower())

        actual_formality = formal_count / max(1, formal_count + casual_count)
        formality_match = 1.0 - abs(profile.formality_level - actual_formality)
        scores.append(formality_match)

        return sum(scores) / len(scores) if scores else 0.5
```

### Quality Scoring Metrics

```python
# src/remix/scoring/quality.py

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class QualityDimension(str, Enum):
    FORMAT_FIT = "format_fit"
    VOICE_MATCH = "voice_match"
    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    ENGAGEMENT = "engagement"
    PLATFORM_OPTIMIZATION = "platform_optimization"


@dataclass
class QualityReport:
    overall_score: float
    dimension_scores: Dict[QualityDimension, float]
    issues: List[str]
    suggestions: List[str]
    confidence: float


class RemixQualityScorer:
    """Comprehensive quality scoring for remixed content."""

    def score(
        self,
        original_content: str,
        remixed_content: any,
        target_format: str,
        voice_profile: Optional[dict] = None
    ) -> QualityReport:
        """Calculate comprehensive quality score."""

        scores = {}
        issues = []
        suggestions = []

        # 1. Format Fit Score
        format_score, format_issues = self._score_format_fit(
            remixed_content,
            target_format
        )
        scores[QualityDimension.FORMAT_FIT] = format_score
        issues.extend(format_issues)

        # 2. Voice Match Score
        if voice_profile:
            voice_score, voice_issues = self._score_voice_match(
                remixed_content,
                voice_profile
            )
            scores[QualityDimension.VOICE_MATCH] = voice_score
            issues.extend(voice_issues)
        else:
            scores[QualityDimension.VOICE_MATCH] = 1.0

        # 3. Completeness Score
        completeness_score, completeness_issues = self._score_completeness(
            original_content,
            remixed_content
        )
        scores[QualityDimension.COMPLETENESS] = completeness_score
        issues.extend(completeness_issues)

        # 4. Coherence Score
        coherence_score = self._score_coherence(remixed_content)
        scores[QualityDimension.COHERENCE] = coherence_score

        # 5. Engagement Score
        engagement_score = self._score_engagement(
            remixed_content,
            target_format
        )
        scores[QualityDimension.ENGAGEMENT] = engagement_score

        # 6. Platform Optimization Score
        platform_score, platform_suggestions = self._score_platform_optimization(
            remixed_content,
            target_format
        )
        scores[QualityDimension.PLATFORM_OPTIMIZATION] = platform_score
        suggestions.extend(platform_suggestions)

        # Calculate weighted overall score
        weights = {
            QualityDimension.FORMAT_FIT: 0.25,
            QualityDimension.VOICE_MATCH: 0.20,
            QualityDimension.COMPLETENESS: 0.20,
            QualityDimension.COHERENCE: 0.15,
            QualityDimension.ENGAGEMENT: 0.10,
            QualityDimension.PLATFORM_OPTIMIZATION: 0.10
        }

        overall = sum(
            scores[dim] * weights[dim]
            for dim in QualityDimension
        )

        return QualityReport(
            overall_score=overall,
            dimension_scores=scores,
            issues=issues,
            suggestions=self._generate_suggestions(scores, suggestions),
            confidence=self._calculate_confidence(scores)
        )

    def _score_format_fit(
        self,
        content: any,
        target_format: str
    ) -> tuple[float, List[str]]:
        """Score how well content fits the target format."""
        issues = []
        score = 1.0

        if target_format == "twitter_thread":
            tweets = content.get("tweets", [])

            # Check tweet count
            if len(tweets) > 15:
                score -= 0.1
                issues.append("Thread exceeds optimal length (>15 tweets)")

            # Check individual tweet lengths
            long_tweets = [t for t in tweets if len(t) > 280]
            if long_tweets:
                score -= 0.3
                issues.append(f"{len(long_tweets)} tweets exceed character limit")

            # Check for hook
            if not content.get("hook_tweet"):
                score -= 0.1
                issues.append("Missing strong hook tweet")

            # Check thread flow
            if not self._check_thread_flow(tweets):
                score -= 0.1
                issues.append("Thread lacks natural flow/transitions")

        elif target_format == "linkedin_post":
            text = content.get("content", "")

            if len(text) > 3000:
                score -= 0.3
                issues.append("Exceeds LinkedIn character limit")

            if len(text) < 150:
                score -= 0.2
                issues.append("Post too short for engagement")

            # Check for hook
            first_line = text.split('\n')[0] if text else ""
            if len(first_line) > 150 or not self._is_engaging_hook(first_line):
                score -= 0.1
                issues.append("First line should be a compelling hook")

        return max(0.0, score), issues

    def _score_completeness(
        self,
        original: str,
        remixed: any
    ) -> tuple[float, List[str]]:
        """Score how well the remix captures original key points."""
        issues = []

        # Extract key points from original
        original_points = self._extract_key_points(original)

        # Check coverage in remixed content
        remixed_text = self._flatten_content(remixed)
        covered = 0

        for point in original_points:
            if self._point_covered(point, remixed_text):
                covered += 1
            else:
                issues.append(f"Missing key point: {point[:50]}...")

        score = covered / max(len(original_points), 1)

        return score, issues[:5]  # Limit issues reported
```

### Database Schema

```sql
-- Migration: 007_create_remix_tables.sql
-- Description: Tables for content remix engine

-- Remix requests/results
CREATE TABLE IF NOT EXISTS remix_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- User
    user_hash TEXT NOT NULL,

    -- Source content
    source_content TEXT NOT NULL,
    source_format TEXT NOT NULL,
    source_url TEXT,
    source_analysis JSONB,  -- ContentAnalysis

    -- Configuration
    target_formats TEXT[] NOT NULL,
    format_configs JSONB DEFAULT '{}',
    brand_profile_id UUID REFERENCES brand_profiles(id),
    voice_strength DECIMAL(3,2) DEFAULT 0.70,

    -- Status
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),

    -- Processing metadata
    processing_time_ms INTEGER,
    provider_used TEXT,
    tokens_used INTEGER DEFAULT 0,

    -- Error tracking
    error TEXT
);

-- Individual remix outputs
CREATE TABLE IF NOT EXISTS remix_outputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Parent job
    remix_job_id UUID NOT NULL REFERENCES remix_jobs(id) ON DELETE CASCADE,

    -- Output details
    target_format TEXT NOT NULL,
    variation_index INTEGER NOT NULL DEFAULT 0,
    content JSONB NOT NULL,

    -- Metrics
    character_count INTEGER NOT NULL,
    word_count INTEGER NOT NULL,

    -- Quality scores
    quality_score DECIMAL(4,3),
    format_fit_score DECIMAL(4,3),
    voice_match_score DECIMAL(4,3),
    completeness_score DECIMAL(4,3),

    -- Improvement suggestions
    suggestions TEXT[],

    UNIQUE(remix_job_id, target_format, variation_index)
);

-- Format mappings configuration (admin-editable)
CREATE TABLE IF NOT EXISTS format_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_format TEXT NOT NULL,
    target_format TEXT NOT NULL,

    -- Configuration
    default_config JSONB NOT NULL DEFAULT '{}',
    constraints JSONB NOT NULL DEFAULT '{}',
    prompt_template TEXT NOT NULL,

    -- Metadata
    is_active BOOLEAN NOT NULL DEFAULT true,
    quality_threshold DECIMAL(3,2) DEFAULT 0.70,

    UNIQUE(source_format, target_format)
);

-- Indexes
CREATE INDEX idx_remix_jobs_user_hash ON remix_jobs(user_hash);
CREATE INDEX idx_remix_jobs_status ON remix_jobs(status);
CREATE INDEX idx_remix_jobs_created_at ON remix_jobs(created_at DESC);
CREATE INDEX idx_remix_jobs_source_format ON remix_jobs(source_format);

CREATE INDEX idx_remix_outputs_job_id ON remix_outputs(remix_job_id);
CREATE INDEX idx_remix_outputs_target_format ON remix_outputs(target_format);
CREATE INDEX idx_remix_outputs_quality ON remix_outputs(quality_score DESC);

-- RLS
ALTER TABLE remix_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE remix_outputs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can access own remix_jobs"
    ON remix_jobs FOR ALL TO anon
    USING (user_hash IS NOT NULL);

CREATE POLICY "Users can access outputs of own jobs"
    ON remix_outputs FOR ALL TO anon
    USING (
        EXISTS (
            SELECT 1 FROM remix_jobs
            WHERE remix_jobs.id = remix_outputs.remix_job_id
            AND remix_jobs.user_hash IS NOT NULL
        )
    );
```

### File/Module Structure

```
src/
  remix/
    __init__.py
    models.py              # Pydantic schemas
    service.py             # Main remix orchestration
    analyzer.py            # Content analysis
    router.py              # Format routing logic

    adapters/
      __init__.py
      base.py              # FormatAdapter ABC
      twitter_thread.py
      linkedin_post.py
      email_newsletter.py
      video_script.py
      instagram_carousel.py
      executive_summary.py

    processing/
      __init__.py
      chunker.py           # Content chunking
      expander.py          # Content expansion
      compressor.py        # Content compression
      voice_harmonizer.py  # Brand voice application

    scoring/
      __init__.py
      quality.py           # Quality scoring
      metrics.py           # Individual metrics

app/
  routes/
    remix.py               # FastAPI endpoints

frontend/
  components/
    remix/
      RemixStudio.tsx        # Main remix interface
      SourceContentInput.tsx # Content input with format detection
      FormatSelector.tsx     # Target format selection
      FormatPreview.tsx      # Preview remixed content
      QualityIndicator.tsx   # Quality score display
      RemixHistory.tsx       # Past remix operations

  hooks/
    useRemix.ts              # Remix API hooks
    useFormatDetection.ts    # Auto-detect source format
```

### Dependencies to Add

```toml
# pyproject.toml additions

[tool.poetry.dependencies]
sentence-transformers = "^2.2.0"  # Semantic similarity
spacy = "^3.7.0"                  # NLP/entity extraction
tiktoken = "^0.5.0"               # Token counting
beautifulsoup4 = "^4.12.0"        # HTML parsing for imports
```

### Estimated Complexity

| Component | Effort | Risk | Dependencies |
|-----------|--------|------|--------------|
| Content analyzer | 3 days | Medium | NLP models |
| Format adapters (6 formats) | 4 days | Medium | LLM prompts |
| Chunker/expander algorithms | 3 days | High | Embeddings |
| Voice harmonizer | 2 days | Medium | Brand profiles |
| Quality scorer | 2 days | Medium | NLP metrics |
| API endpoints | 1 day | Low | Models |
| Database schema | 1 day | Low | None |
| Frontend components | 4 days | Medium | API |
| Testing + QA | 3 days | Medium | All above |
| **Total** | **23 days** | **Medium-High** | |

---

## F3: Enhanced Brand Voice Training

### Overview

Enhanced Brand Voice Training enables sophisticated brand voice capture through content ingestion, style extraction using embeddings, and application with configurable strength during content generation.

### Architecture Diagram

```
                        +----------------------+
                        |   Content Ingestion  |
                        |   (URLs, Files, Text)|
                        +-----------+----------+
                                    |
                        +-----------v----------+
                        |   Content Processor  |
                        |   - Clean/normalize  |
                        |   - Chunk for embed  |
                        +-----------+----------+
                                    |
              +---------------------+---------------------+
              |                     |                     |
    +---------v--------+  +--------v--------+  +---------v--------+
    |  Style Analyzer  |  | Voice Embedder  |  |  Pattern Extractor|
    |  - Tone detect   |  | - Sentence emb  |  |  - Phrase patterns|
    |  - Formality     |  | - Style vectors |  |  - Word frequency |
    +------------------+  +-----------------+  +------------------+
              |                     |                     |
              +---------------------+---------------------+
                                    |
                        +-----------v----------+
                        |   Vector Database    |
                        |   (ChromaDB/Pinecone)|
                        +-----------+----------+
                                    |
           +------------------------+------------------------+
           |                                                 |
  +--------v--------+                               +--------v--------+
  |  Voice Profile  |                               |  Voice Retrieval|
  |  - Embeddings   |                               |  - Similarity   |
  |  - Statistics   |                               |  - RAG for voice|
  |  - Examples     |                               +--------+--------+
  +-----------------+                                        |
                                                   +---------v---------+
                                                   | Generation Prompt |
                                                   | Augmentation      |
                                                   +---------+---------+
                                                             |
                                                   +---------v---------+
                                                   | Voice-Enhanced    |
                                                   | Content Output    |
                                                   +-------------------+
```

### Vector Database Selection

**Recommendation: ChromaDB for MVP, Pinecone for Scale**

| Criteria | ChromaDB | Pinecone | Weaviate |
|----------|----------|----------|----------|
| Deployment | Self-hosted/Local | Managed cloud | Self-hosted/Cloud |
| Cost | Free (OSS) | Pay-per-use | Free tier available |
| Setup complexity | Low | Very Low | Medium |
| Scalability | Limited (<1M) | Excellent | Good |
| Python integration | Excellent | Excellent | Good |
| Metadata filtering | Good | Excellent | Excellent |
| Persistence | SQLite backend | Cloud native | Multiple backends |

**Phased Approach:**
1. **Phase 1 (MVP):** ChromaDB with local persistence - zero infrastructure cost
2. **Phase 2 (Growth):** Migrate to Pinecone when user base exceeds 1000 profiles
3. **Phase 3 (Enterprise):** Consider Weaviate for on-premise deployments

### Data Models (Pydantic Schemas)

```python
# src/types/brand_voice.py

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4
import numpy as np


class ContentSource(str, Enum):
    """Sources for brand voice training content."""
    URL = "url"
    FILE = "file"
    TEXT = "text"
    EXISTING_CONTENT = "existing_content"


class IngestionStatus(str, Enum):
    """Status of content ingestion."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VoiceStrength(str, Enum):
    """Preset voice strength levels."""
    SUBTLE = "subtle"      # 0.3 - Light touch
    MODERATE = "moderate"  # 0.5 - Balanced
    STRONG = "strong"      # 0.7 - Clear voice
    DOMINANT = "dominant"  # 0.9 - Strong override


class ContentIngestionRequest(BaseModel):
    """Request to ingest content for voice training."""
    brand_profile_id: UUID

    # Source specification
    source_type: ContentSource

    # Source data (one of these based on source_type)
    urls: List[str] = Field(default_factory=list, max_items=20)
    text_content: Optional[str] = Field(default=None, max_length=50000)
    file_ids: List[str] = Field(default_factory=list, max_items=10)
    existing_content_ids: List[UUID] = Field(default_factory=list)

    # Processing options
    min_content_length: int = Field(default=100, ge=50)
    max_chunks_per_source: int = Field(default=50, ge=1, le=200)

    @validator('urls')
    def validate_urls(cls, v):
        import re
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        for url in v:
            if not url_pattern.match(url):
                raise ValueError(f"Invalid URL: {url}")
        return v


class VoiceEmbedding(BaseModel):
    """A single voice embedding from training content."""
    id: str
    chunk_text: str
    embedding: List[float]  # Vector

    # Metadata
    source_url: Optional[str] = None
    source_type: ContentSource
    chunk_index: int

    # Style attributes detected in this chunk
    tone: str
    formality_score: float
    complexity_score: float

    created_at: datetime = Field(default_factory=datetime.utcnow)


class VoiceStatistics(BaseModel):
    """Statistical analysis of brand voice from training data."""
    # Vocabulary analysis
    vocabulary_size: int
    avg_word_length: float
    avg_sentence_length: float

    # Readability metrics
    flesch_reading_ease: float
    flesch_kincaid_grade: float

    # Style distribution
    tone_distribution: Dict[str, float]  # {tone: frequency}
    formality_distribution: Dict[str, float]

    # Phrase patterns
    common_phrases: List[Dict[str, Any]]  # [{phrase, frequency, contexts}]
    sentence_starters: List[str]
    transition_phrases: List[str]

    # Word preferences (from training, not just manual input)
    learned_preferred_words: List[str]
    learned_avoid_patterns: List[str]


class EnhancedBrandProfile(BaseModel):
    """Extended brand profile with voice training data."""
    # Base profile fields
    id: UUID
    name: str
    slug: str

    # Manual configuration (from existing BrandProfile)
    tone_keywords: List[str]
    writing_style: str
    example_content: Optional[str]
    industry: Optional[str]
    target_audience: Optional[str]
    preferred_words: List[str]
    avoid_words: List[str]
    brand_values: List[str]
    content_themes: List[str]

    # Training data
    training_status: str = "untrained"  # untrained, training, trained
    training_sources: List[Dict[str, Any]] = Field(default_factory=list)
    total_training_chunks: int = 0
    last_trained_at: Optional[datetime] = None

    # Voice embeddings reference
    embedding_collection_id: Optional[str] = None

    # Learned voice statistics
    voice_statistics: Optional[VoiceStatistics] = None

    # Quality metrics
    voice_consistency_score: float = 0.0
    training_coverage_score: float = 0.0


class VoiceApplicationRequest(BaseModel):
    """Request to apply brand voice to content."""
    content: str = Field(..., min_length=10)
    brand_profile_id: UUID

    # Voice strength
    strength: Union[VoiceStrength, float] = Field(default=VoiceStrength.MODERATE)

    # Application options
    preserve_structure: bool = True
    preserve_technical_terms: bool = True
    use_example_retrieval: bool = True  # RAG for voice examples
    max_examples: int = Field(default=3, ge=1, le=10)

    @validator('strength')
    def convert_strength(cls, v):
        if isinstance(v, VoiceStrength):
            mapping = {
                VoiceStrength.SUBTLE: 0.3,
                VoiceStrength.MODERATE: 0.5,
                VoiceStrength.STRONG: 0.7,
                VoiceStrength.DOMINANT: 0.9
            }
            return mapping[v]
        return v


class VoiceApplicationResult(BaseModel):
    """Result of applying brand voice."""
    original_content: str
    transformed_content: str

    # Application details
    strength_applied: float
    examples_used: List[str]  # Example chunks used for voice matching

    # Quality assessment
    voice_match_score: float
    naturalness_score: float

    # Comparison
    changes_summary: Dict[str, Any]  # {words_changed, tone_shift, etc.}


class ABTestVariant(BaseModel):
    """A variant in an A/B test for brand voice."""
    id: UUID = Field(default_factory=uuid4)
    name: str

    # Voice configuration
    brand_profile_id: UUID
    strength: float

    # Content
    content: str

    # Metrics (populated after testing)
    impressions: int = 0
    engagement_score: Optional[float] = None
    conversion_rate: Optional[float] = None


class ABTest(BaseModel):
    """A/B test configuration for brand voice."""
    id: UUID = Field(default_factory=uuid4)
    name: str

    # Test configuration
    original_content: str
    variants: List[ABTestVariant]

    # Status
    status: str = "draft"  # draft, active, completed
    winner_variant_id: Optional[UUID] = None

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
```

### Content Ingestion Pipeline

```python
# src/brand_voice/ingestion/pipeline.py

from typing import AsyncIterator, List, Optional
from dataclasses import dataclass
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re


@dataclass
class IngestedChunk:
    text: str
    source_url: Optional[str]
    source_type: str
    chunk_index: int
    metadata: dict


class ContentIngestionPipeline:
    """Pipeline for ingesting and processing brand voice training content."""

    def __init__(
        self,
        embedding_service,
        vector_store,
        style_analyzer
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.style_analyzer = style_analyzer

    async def ingest(
        self,
        request: ContentIngestionRequest
    ) -> AsyncIterator[dict]:
        """Stream ingestion progress updates."""

        total_sources = (
            len(request.urls) +
            len(request.file_ids) +
            (1 if request.text_content else 0) +
            len(request.existing_content_ids)
        )

        processed = 0
        total_chunks = 0

        # Process URLs
        for url in request.urls:
            try:
                async for chunk in self._process_url(url, request):
                    await self._store_chunk(chunk, request.brand_profile_id)
                    total_chunks += 1

                processed += 1
                yield {
                    "status": "processing",
                    "progress": processed / total_sources,
                    "message": f"Processed {url}",
                    "chunks_created": total_chunks
                }
            except Exception as e:
                yield {
                    "status": "error",
                    "source": url,
                    "error": str(e)
                }

        # Process text content
        if request.text_content:
            async for chunk in self._process_text(
                request.text_content,
                request
            ):
                await self._store_chunk(chunk, request.brand_profile_id)
                total_chunks += 1

            processed += 1
            yield {
                "status": "processing",
                "progress": processed / total_sources,
                "message": "Processed text content",
                "chunks_created": total_chunks
            }

        # Calculate voice statistics after all ingestion
        stats = await self._calculate_voice_statistics(request.brand_profile_id)

        yield {
            "status": "completed",
            "total_chunks": total_chunks,
            "voice_statistics": stats.dict()
        }

    async def _process_url(
        self,
        url: str,
        request: ContentIngestionRequest
    ) -> AsyncIterator[IngestedChunk]:
        """Fetch and process content from URL."""

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch URL: {response.status}")

                html = await response.text()

        # Parse and extract main content
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script, style, nav, footer elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()

        # Try to find main content area
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find(class_=re.compile(r'content|post|article', re.I)) or
            soup.find('body')
        )

        if not main_content:
            return

        # Extract text and split into chunks
        text = main_content.get_text(separator='\n', strip=True)

        if len(text) < request.min_content_length:
            return

        # Chunk the content
        chunks = self._chunk_text(text, request.max_chunks_per_source)

        for i, chunk_text in enumerate(chunks):
            yield IngestedChunk(
                text=chunk_text,
                source_url=url,
                source_type="url",
                chunk_index=i,
                metadata={
                    "title": soup.title.string if soup.title else None,
                    "word_count": len(chunk_text.split())
                }
            )

    def _chunk_text(
        self,
        text: str,
        max_chunks: int,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """Split text into overlapping chunks."""

        # Split into sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence.split())

            if current_length + sentence_length > chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))

                    # Keep overlap
                    overlap_words = ' '.join(current_chunk).split()[-overlap:]
                    current_chunk = overlap_words + [sentence]
                    current_length = len(overlap_words) + sentence_length
                else:
                    current_chunk = [sentence]
                    current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks[:max_chunks]

    async def _store_chunk(
        self,
        chunk: IngestedChunk,
        profile_id: UUID
    ):
        """Generate embedding and store in vector database."""

        # Analyze style
        style = await self.style_analyzer.analyze(chunk.text)

        # Generate embedding
        embedding = await self.embedding_service.embed(chunk.text)

        # Store in vector database
        await self.vector_store.add(
            collection_name=f"voice_{profile_id}",
            documents=[chunk.text],
            embeddings=[embedding],
            metadatas=[{
                "source_url": chunk.source_url,
                "source_type": chunk.source_type,
                "chunk_index": chunk.chunk_index,
                "tone": style.tone,
                "formality": style.formality_score,
                "complexity": style.complexity_score,
                **chunk.metadata
            }],
            ids=[f"{profile_id}_{chunk.source_type}_{chunk.chunk_index}"]
        )
```

### Style Extraction Approach

```python
# src/brand_voice/analysis/style_extractor.py

from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer
from collections import Counter
import spacy
import textstat


@dataclass
class StyleAnalysis:
    tone: str
    formality_score: float
    complexity_score: float
    sentiment: str
    key_phrases: List[str]


class StyleExtractor:
    """Extract style characteristics from text using embeddings and NLP."""

    # Pre-computed embeddings for tone reference texts
    TONE_REFERENCES = {
        "professional": [
            "We are committed to delivering exceptional results.",
            "Our analysis indicates a strong correlation.",
            "Please find attached the quarterly report."
        ],
        "casual": [
            "Hey, check this out - it's pretty cool!",
            "So here's the thing about that...",
            "You're gonna love what we've got."
        ],
        "friendly": [
            "We're so excited to share this with you!",
            "Thanks for being part of our community.",
            "We appreciate your support and feedback."
        ],
        "authoritative": [
            "Research conclusively demonstrates that...",
            "The evidence overwhelmingly supports...",
            "Industry standards require compliance with..."
        ],
        "enthusiastic": [
            "This is absolutely incredible!",
            "We can't wait for you to experience this!",
            "The results have exceeded all expectations!"
        ]
    }

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        spacy_model: str = "en_core_web_sm"
    ):
        self.embedder = SentenceTransformer(embedding_model)
        self.nlp = spacy.load(spacy_model)

        # Pre-compute tone reference embeddings
        self.tone_embeddings = {}
        for tone, texts in self.TONE_REFERENCES.items():
            embeddings = self.embedder.encode(texts)
            self.tone_embeddings[tone] = np.mean(embeddings, axis=0)

    async def analyze(self, text: str) -> StyleAnalysis:
        """Perform comprehensive style analysis on text."""

        # Get text embedding
        text_embedding = self.embedder.encode([text])[0]

        # Detect tone
        tone = self._detect_tone(text_embedding)

        # Calculate formality
        formality = self._calculate_formality(text)

        # Calculate complexity
        complexity = self._calculate_complexity(text)

        # Detect sentiment
        sentiment = self._detect_sentiment(text)

        # Extract key phrases
        key_phrases = self._extract_key_phrases(text)

        return StyleAnalysis(
            tone=tone,
            formality_score=formality,
            complexity_score=complexity,
            sentiment=sentiment,
            key_phrases=key_phrases
        )

    def _detect_tone(self, embedding: np.ndarray) -> str:
        """Detect tone using embedding similarity."""

        similarities = {}
        for tone, ref_embedding in self.tone_embeddings.items():
            similarity = np.dot(embedding, ref_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(ref_embedding)
            )
            similarities[tone] = similarity

        return max(similarities, key=similarities.get)

    def _calculate_formality(self, text: str) -> float:
        """Calculate formality score (0=casual, 1=formal)."""

        doc = self.nlp(text)

        # Indicators of formality
        formal_indicators = 0
        casual_indicators = 0

        # Check for contractions (casual)
        contractions = ["'s", "'re", "'ve", "'ll", "'d", "n't", "'m"]
        for contraction in contractions:
            casual_indicators += text.lower().count(contraction)

        # Check for personal pronouns (casual)
        personal_pronouns = ['i', 'you', 'we', 'us']
        for token in doc:
            if token.text.lower() in personal_pronouns:
                casual_indicators += 1

        # Check for passive voice (formal)
        for token in doc:
            if token.dep_ == "nsubjpass":
                formal_indicators += 1

        # Check for complex sentences (formal)
        if len(list(doc.sents)) > 0:
            avg_sent_length = len(doc) / len(list(doc.sents))
            if avg_sent_length > 20:
                formal_indicators += 2

        # Check for hedging language (formal)
        hedges = ['perhaps', 'possibly', 'might', 'may', 'could', 'appears']
        for hedge in hedges:
            if hedge in text.lower():
                formal_indicators += 1

        # Check for exclamation marks (casual)
        casual_indicators += text.count('!')

        total = formal_indicators + casual_indicators
        if total == 0:
            return 0.5

        return formal_indicators / total

    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity score (0=simple, 1=complex)."""

        # Use Flesch-Kincaid Grade Level
        fk_grade = textstat.flesch_kincaid_grade(text)

        # Normalize to 0-1 (assuming grade 0-16 range)
        normalized = min(1.0, max(0.0, fk_grade / 16))

        return normalized

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases using spaCy."""

        doc = self.nlp(text)

        # Get noun phrases
        phrases = []
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2:
                phrases.append(chunk.text)

        # Get named entities
        for ent in doc.ents:
            phrases.append(ent.text)

        # Deduplicate and limit
        return list(set(phrases))[:10]


class VoiceStatisticsCalculator:
    """Calculate comprehensive voice statistics from training data."""

    def __init__(self, vector_store, nlp_model: str = "en_core_web_sm"):
        self.vector_store = vector_store
        self.nlp = spacy.load(nlp_model)

    async def calculate(self, profile_id: str) -> VoiceStatistics:
        """Calculate voice statistics for a brand profile."""

        # Retrieve all chunks from vector store
        collection = f"voice_{profile_id}"
        results = await self.vector_store.get_all(collection)

        all_text = ' '.join([r['document'] for r in results])
        doc = self.nlp(all_text)

        # Vocabulary analysis
        words = [token.text.lower() for token in doc if token.is_alpha]
        word_freq = Counter(words)

        # Sentence analysis
        sentences = list(doc.sents)

        # Calculate statistics
        return VoiceStatistics(
            vocabulary_size=len(word_freq),
            avg_word_length=np.mean([len(w) for w in words]) if words else 0,
            avg_sentence_length=np.mean([len(s) for s in sentences]) if sentences else 0,

            flesch_reading_ease=textstat.flesch_reading_ease(all_text),
            flesch_kincaid_grade=textstat.flesch_kincaid_grade(all_text),

            tone_distribution=self._calculate_tone_distribution(results),
            formality_distribution=self._calculate_formality_distribution(results),

            common_phrases=self._extract_common_phrases(doc),
            sentence_starters=self._extract_sentence_starters(sentences),
            transition_phrases=self._extract_transitions(doc),

            learned_preferred_words=self._identify_preferred_words(word_freq),
            learned_avoid_patterns=[]  # Could be enhanced with more analysis
        )

    def _calculate_tone_distribution(
        self,
        results: List[dict]
    ) -> Dict[str, float]:
        """Calculate distribution of tones across training data."""
        tones = [r['metadata'].get('tone', 'unknown') for r in results]
        total = len(tones)
        if total == 0:
            return {}

        counter = Counter(tones)
        return {tone: count / total for tone, count in counter.items()}

    def _extract_common_phrases(self, doc) -> List[Dict[str, Any]]:
        """Extract frequently used phrases."""

        # Get noun phrase frequencies
        phrase_counter = Counter()
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2:
                phrase_counter[chunk.text.lower()] += 1

        return [
            {"phrase": phrase, "frequency": count}
            for phrase, count in phrase_counter.most_common(20)
        ]

    def _extract_sentence_starters(
        self,
        sentences: List
    ) -> List[str]:
        """Identify common sentence starters."""

        starters = []
        for sent in sentences:
            words = sent.text.split()[:3]
            if words:
                starters.append(' '.join(words))

        counter = Counter(starters)
        return [s for s, _ in counter.most_common(10)]
```

### Voice Application Algorithm

```python
# src/brand_voice/application/applicator.py

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class VoiceApplicationConfig:
    strength: float
    preserve_structure: bool
    use_rag: bool
    max_examples: int


class BrandVoiceApplicator:
    """Apply trained brand voice to content with configurable strength."""

    def __init__(
        self,
        llm_provider,
        vector_store,
        embedding_service,
        style_extractor
    ):
        self.llm = llm_provider
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.style_extractor = style_extractor

    async def apply(
        self,
        content: str,
        profile: EnhancedBrandProfile,
        config: VoiceApplicationConfig
    ) -> VoiceApplicationResult:
        """Apply brand voice to content."""

        # Step 1: Analyze input content
        input_style = await self.style_extractor.analyze(content)

        # Step 2: Retrieve relevant voice examples (RAG)
        examples = []
        if config.use_rag and profile.embedding_collection_id:
            examples = await self._retrieve_voice_examples(
                content,
                profile.embedding_collection_id,
                config.max_examples
            )

        # Step 3: Build voice-aware prompt
        prompt = self._build_application_prompt(
            content=content,
            profile=profile,
            examples=examples,
            config=config
        )

        # Step 4: Generate transformed content
        transformed = await self.llm.generate(prompt)

        # Step 5: Assess transformation quality
        output_style = await self.style_extractor.analyze(transformed)
        quality = self._assess_quality(
            input_style,
            output_style,
            profile,
            config.strength
        )

        return VoiceApplicationResult(
            original_content=content,
            transformed_content=transformed,
            strength_applied=config.strength,
            examples_used=[e['text'] for e in examples],
            voice_match_score=quality['voice_match'],
            naturalness_score=quality['naturalness'],
            changes_summary=self._summarize_changes(content, transformed)
        )

    async def _retrieve_voice_examples(
        self,
        content: str,
        collection_id: str,
        max_examples: int
    ) -> List[dict]:
        """Retrieve relevant voice examples using semantic search."""

        # Embed the input content
        query_embedding = await self.embedding_service.embed(content)

        # Search for similar voice samples
        results = await self.vector_store.query(
            collection_name=collection_id,
            query_embedding=query_embedding,
            n_results=max_examples,
            where={
                # Optionally filter by quality metrics
                "formality": {"$gte": 0.0}  # Example filter
            }
        )

        return results

    def _build_application_prompt(
        self,
        content: str,
        profile: EnhancedBrandProfile,
        examples: List[dict],
        config: VoiceApplicationConfig
    ) -> str:
        """Build the LLM prompt for voice application."""

        # Strength-based instructions
        strength_instructions = self._get_strength_instructions(config.strength)

        # Voice characteristics
        voice_description = self._describe_voice(profile)

        # Examples section
        examples_section = ""
        if examples:
            examples_text = "\n\n".join([
                f'Example {i+1}:\n"""{e["text"]}"""'
                for i, e in enumerate(examples)
            ])
            examples_section = f"""
VOICE EXAMPLES (match this style):
{examples_text}
"""

        # Word guidance
        word_guidance = ""
        if profile.preferred_words:
            word_guidance += f"\nUSE these words/phrases where natural: {', '.join(profile.preferred_words)}"
        if profile.avoid_words:
            word_guidance += f"\nAVOID these words/phrases: {', '.join(profile.avoid_words)}"

        # Voice statistics guidance
        stats_guidance = ""
        if profile.voice_statistics:
            stats = profile.voice_statistics
            stats_guidance = f"""
STYLE METRICS TO MATCH:
- Average sentence length: ~{stats.avg_sentence_length:.0f} words
- Reading level: Grade {stats.flesch_kincaid_grade:.1f}
- Common sentence starters: {', '.join(stats.sentence_starters[:5])}
"""

        return f"""Transform the following content to match a specific brand voice.

CONTENT TO TRANSFORM:
\"\"\"{content}\"\"\"

{voice_description}
{examples_section}
{word_guidance}
{stats_guidance}

TRANSFORMATION INSTRUCTIONS:
{strength_instructions}

{"Preserve the exact structure and formatting of the original." if config.preserve_structure else ""}

Transform the content now, maintaining all factual information while applying the brand voice:"""

    def _get_strength_instructions(self, strength: float) -> str:
        """Get strength-specific transformation instructions."""

        if strength <= 0.3:
            return """Apply the brand voice SUBTLY:
- Make minimal changes to the original text
- Focus on key word substitutions
- Preserve most of the original phrasing
- Only adjust the most obvious mismatches"""

        elif strength <= 0.5:
            return """Apply the brand voice MODERATELY:
- Balance original style with brand voice
- Adjust tone throughout the text
- Replace key phrases with brand-appropriate alternatives
- Maintain the original structure"""

        elif strength <= 0.7:
            return """Apply the brand voice STRONGLY:
- Significantly transform the writing style
- Comprehensively apply tone and word choices
- Restructure sentences to match brand patterns
- Keep core message but rewrite extensively"""

        else:
            return """Apply the brand voice DOMINANTLY:
- Completely rewrite in the brand voice
- Prioritize brand consistency over original phrasing
- Transform structure, tone, and vocabulary
- Only preserve factual content, not style"""

    def _describe_voice(self, profile: EnhancedBrandProfile) -> str:
        """Generate voice description from profile."""

        parts = [
            f"BRAND VOICE: {profile.name}",
            f"Writing Style: {profile.writing_style}",
            f"Tone: {', '.join(profile.tone_keywords)}"
        ]

        if profile.target_audience:
            parts.append(f"Target Audience: {profile.target_audience}")

        if profile.brand_values:
            parts.append(f"Brand Values: {', '.join(profile.brand_values)}")

        if profile.example_content:
            parts.append(f'Example of desired voice:\n"{profile.example_content}"')

        return '\n'.join(parts)
```

### API Design

```yaml
# Brand Voice API Endpoints

paths:
  /api/v1/brand-voice/profiles/{profile_id}/train:
    post:
      summary: Start voice training from content sources
      operationId: trainBrandVoice
      tags: [Brand Voice]
      parameters:
        - name: profile_id
          in: path
          required: true
          schema: { type: string, format: uuid }
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ContentIngestionRequest'
      responses:
        '202':
          description: Training started (streaming progress)
          content:
            text/event-stream:
              schema:
                type: object
                properties:
                  status: { type: string }
                  progress: { type: number }
                  message: { type: string }

  /api/v1/brand-voice/profiles/{profile_id}/status:
    get:
      summary: Get training status and voice statistics
      operationId: getVoiceTrainingStatus
      tags: [Brand Voice]
      parameters:
        - name: profile_id
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        '200':
          description: Training status
          content:
            application/json:
              schema:
                type: object
                properties:
                  training_status: { type: string }
                  total_chunks: { type: integer }
                  voice_statistics: { $ref: '#/components/schemas/VoiceStatistics' }
                  training_sources: { type: array }

  /api/v1/brand-voice/apply:
    post:
      summary: Apply brand voice to content
      operationId: applyBrandVoice
      tags: [Brand Voice]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/VoiceApplicationRequest'
      responses:
        '200':
          description: Voice-transformed content
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VoiceApplicationResult'

  /api/v1/brand-voice/profiles/{profile_id}/examples:
    get:
      summary: Get stored voice examples
      operationId: getVoiceExamples
      tags: [Brand Voice]
      parameters:
        - name: profile_id
          in: path
          required: true
          schema: { type: string, format: uuid }
        - name: limit
          in: query
          schema: { type: integer, default: 10 }
        - name: tone_filter
          in: query
          schema: { type: string }
      responses:
        '200':
          description: Voice examples
          content:
            application/json:
              schema:
                type: object
                properties:
                  examples: { type: array }
                  total: { type: integer }

  /api/v1/brand-voice/ab-tests:
    post:
      summary: Create A/B test for brand voice
      operationId: createABTest
      tags: [Brand Voice]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name, original_content, variant_configs]
              properties:
                name: { type: string }
                original_content: { type: string }
                variant_configs:
                  type: array
                  items:
                    type: object
                    properties:
                      brand_profile_id: { type: string, format: uuid }
                      strength: { type: number }
      responses:
        '201':
          description: A/B test created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ABTest'

  /api/v1/brand-voice/profiles/{profile_id}/clear:
    delete:
      summary: Clear training data (GDPR compliance)
      operationId: clearVoiceTraining
      tags: [Brand Voice]
      parameters:
        - name: profile_id
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        '204':
          description: Training data cleared
```

### Database Schema

```sql
-- Migration: 008_enhance_brand_profiles.sql
-- Description: Add voice training support to brand profiles

-- Add training columns to brand_profiles
ALTER TABLE brand_profiles
ADD COLUMN IF NOT EXISTS training_status TEXT DEFAULT 'untrained'
    CHECK (training_status IN ('untrained', 'training', 'trained', 'failed')),
ADD COLUMN IF NOT EXISTS total_training_chunks INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_trained_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS embedding_collection_id TEXT,
ADD COLUMN IF NOT EXISTS voice_statistics JSONB;

-- Voice training sources
CREATE TABLE IF NOT EXISTS voice_training_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Parent profile
    brand_profile_id UUID NOT NULL REFERENCES brand_profiles(id) ON DELETE CASCADE,

    -- Source details
    source_type TEXT NOT NULL,  -- url, file, text, existing_content
    source_identifier TEXT NOT NULL,  -- URL, file path, or content ID
    source_title TEXT,

    -- Processing status
    status TEXT NOT NULL DEFAULT 'pending',
    chunks_created INTEGER DEFAULT 0,
    error TEXT,

    -- Metadata
    processed_at TIMESTAMPTZ
);

-- Voice application history
CREATE TABLE IF NOT EXISTS voice_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- User
    user_hash TEXT,

    -- Application details
    brand_profile_id UUID REFERENCES brand_profiles(id),
    original_content TEXT NOT NULL,
    transformed_content TEXT NOT NULL,

    -- Configuration
    strength_applied DECIMAL(3,2) NOT NULL,

    -- Quality metrics
    voice_match_score DECIMAL(4,3),
    naturalness_score DECIMAL(4,3),

    -- Examples used (store IDs for privacy)
    example_ids TEXT[]
);

-- A/B tests
CREATE TABLE IF NOT EXISTS voice_ab_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- User
    user_hash TEXT NOT NULL,

    -- Test configuration
    name TEXT NOT NULL,
    original_content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'active', 'completed', 'cancelled')),

    -- Timing
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,

    -- Results
    winner_variant_id UUID
);

-- A/B test variants
CREATE TABLE IF NOT EXISTS voice_ab_test_variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Parent test
    ab_test_id UUID NOT NULL REFERENCES voice_ab_tests(id) ON DELETE CASCADE,

    -- Variant configuration
    name TEXT NOT NULL,
    brand_profile_id UUID REFERENCES brand_profiles(id),
    strength DECIMAL(3,2) NOT NULL,
    content TEXT NOT NULL,

    -- Metrics
    impressions INTEGER DEFAULT 0,
    engagement_score DECIMAL(5,3),
    conversion_rate DECIMAL(5,4)
);

-- Indexes
CREATE INDEX idx_voice_training_sources_profile
    ON voice_training_sources(brand_profile_id);
CREATE INDEX idx_voice_applications_profile
    ON voice_applications(brand_profile_id);
CREATE INDEX idx_voice_applications_user
    ON voice_applications(user_hash);
CREATE INDEX idx_voice_ab_tests_user
    ON voice_ab_tests(user_hash);
CREATE INDEX idx_voice_ab_tests_status
    ON voice_ab_tests(status);

-- Triggers
CREATE TRIGGER update_voice_ab_tests_updated_at
    BEFORE UPDATE ON voice_ab_tests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS
ALTER TABLE voice_training_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_ab_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_ab_test_variants ENABLE ROW LEVEL SECURITY;

-- Policies (simplified - expand based on auth model)
CREATE POLICY "Users can access own voice data"
    ON voice_applications FOR ALL TO anon
    USING (user_hash IS NOT NULL);

CREATE POLICY "Users can access own ab tests"
    ON voice_ab_tests FOR ALL TO anon
    USING (user_hash IS NOT NULL);
```

### File/Module Structure

```
src/
  brand_voice/
    __init__.py
    models.py                    # Enhanced Pydantic models
    service.py                   # Main orchestration service

    ingestion/
      __init__.py
      pipeline.py                # Content ingestion pipeline
      url_fetcher.py             # URL content extraction
      file_processor.py          # File upload processing
      chunker.py                 # Text chunking

    analysis/
      __init__.py
      style_extractor.py         # Style/tone analysis
      statistics.py              # Voice statistics calculator
      embeddings.py              # Embedding generation

    storage/
      __init__.py
      chroma_store.py            # ChromaDB implementation
      pinecone_store.py          # Pinecone implementation (future)
      base.py                    # Abstract vector store interface

    application/
      __init__.py
      applicator.py              # Voice application logic
      prompt_builder.py          # LLM prompt construction
      quality_assessor.py        # Output quality scoring

    testing/
      __init__.py
      ab_test.py                 # A/B testing implementation

app/
  routes/
    brand_voice.py               # API endpoints

frontend/
  components/
    brand/
      VoiceTrainingPanel.tsx       # Training UI
      ContentIngestionForm.tsx     # URL/file input
      VoiceStatisticsDisplay.tsx   # Statistics visualization
      VoiceStrengthSlider.tsx      # Strength control
      VoicePreview.tsx             # Before/after comparison
      ABTestCreator.tsx            # A/B test setup
      ABTestResults.tsx            # Test results display

  hooks/
    useVoiceTraining.ts            # Training status hooks
    useVoiceApplication.ts         # Voice application hooks
```

### Privacy Considerations

```python
# src/brand_voice/privacy.py

from typing import Optional
from datetime import datetime, timedelta


class VoicePrivacyManager:
    """Manage privacy and data retention for voice training."""

    # Default retention periods
    TRAINING_DATA_RETENTION_DAYS = 365
    APPLICATION_LOG_RETENTION_DAYS = 90

    def __init__(self, vector_store, database):
        self.vector_store = vector_store
        self.db = database

    async def anonymize_training_data(self, profile_id: str):
        """Remove PII from training data while keeping embeddings."""

        # Update metadata to remove source URLs
        await self.vector_store.update_metadata(
            collection_name=f"voice_{profile_id}",
            updates={"source_url": "[REDACTED]"}
        )

        # Update database records
        await self.db.execute(
            """
            UPDATE voice_training_sources
            SET source_identifier = '[REDACTED]',
                source_title = '[REDACTED]'
            WHERE brand_profile_id = $1
            """,
            profile_id
        )

    async def delete_training_data(self, profile_id: str):
        """Complete deletion of all training data (GDPR right to erasure)."""

        # Delete vector embeddings
        await self.vector_store.delete_collection(f"voice_{profile_id}")

        # Delete database records
        await self.db.execute(
            "DELETE FROM voice_training_sources WHERE brand_profile_id = $1",
            profile_id
        )

        # Reset profile training status
        await self.db.execute(
            """
            UPDATE brand_profiles
            SET training_status = 'untrained',
                total_training_chunks = 0,
                last_trained_at = NULL,
                embedding_collection_id = NULL,
                voice_statistics = NULL
            WHERE id = $1
            """,
            profile_id
        )

    async def export_user_data(self, user_hash: str) -> dict:
        """Export all user's voice data (GDPR data portability)."""

        # Get all profiles
        profiles = await self.db.fetch_all(
            "SELECT * FROM brand_profiles WHERE user_hash = $1",
            user_hash
        )

        export = {
            "exported_at": datetime.utcnow().isoformat(),
            "profiles": []
        }

        for profile in profiles:
            profile_data = dict(profile)

            # Get training sources
            sources = await self.db.fetch_all(
                "SELECT * FROM voice_training_sources WHERE brand_profile_id = $1",
                profile['id']
            )
            profile_data['training_sources'] = [dict(s) for s in sources]

            # Get application history
            applications = await self.db.fetch_all(
                "SELECT * FROM voice_applications WHERE brand_profile_id = $1",
                profile['id']
            )
            profile_data['applications'] = [dict(a) for a in applications]

            export['profiles'].append(profile_data)

        return export

    async def cleanup_expired_data(self):
        """Scheduled job to clean up expired data."""

        training_cutoff = datetime.utcnow() - timedelta(
            days=self.TRAINING_DATA_RETENTION_DAYS
        )
        application_cutoff = datetime.utcnow() - timedelta(
            days=self.APPLICATION_LOG_RETENTION_DAYS
        )

        # Delete old application logs
        await self.db.execute(
            "DELETE FROM voice_applications WHERE created_at < $1",
            application_cutoff
        )

        # Notify about profiles with old training data
        # (Don't auto-delete without user consent)
        old_profiles = await self.db.fetch_all(
            """
            SELECT id, user_hash FROM brand_profiles
            WHERE last_trained_at < $1
            AND training_status = 'trained'
            """,
            training_cutoff
        )

        return {
            "applications_deleted": True,
            "profiles_with_old_training": len(old_profiles)
        }
```

### Dependencies to Add

```toml
# pyproject.toml additions

[tool.poetry.dependencies]
chromadb = "^0.4.0"           # Vector database
sentence-transformers = "^2.2.0"  # Embeddings
spacy = "^3.7.0"              # NLP
textstat = "^0.7.3"           # Readability metrics
aiohttp = "^3.9.0"            # Async HTTP for URL fetching
beautifulsoup4 = "^4.12.0"    # HTML parsing
python-magic = "^0.4.27"      # File type detection

# Optional (for Pinecone migration)
pinecone-client = { version = "^3.0.0", optional = true }
```

```json
// frontend/package.json additions
{
  "dependencies": {
    "react-diff-viewer-continued": "^3.3.0",
    "recharts": "^2.10.0"
  }
}
```

### Estimated Complexity

| Component | Effort | Risk | Dependencies |
|-----------|--------|------|--------------|
| Content ingestion pipeline | 3 days | Medium | URL fetching |
| Style extractor | 3 days | High | NLP models |
| ChromaDB integration | 2 days | Low | Infrastructure |
| Statistics calculator | 2 days | Medium | NLP |
| Voice applicator | 3 days | High | LLM prompts |
| Quality assessor | 2 days | Medium | Style extractor |
| A/B testing system | 2 days | Low | Database |
| API endpoints | 1 day | Low | Models |
| Database migrations | 1 day | Low | None |
| Frontend training UI | 3 days | Medium | API |
| Frontend application UI | 2 days | Medium | API |
| Privacy/GDPR compliance | 2 days | High | Legal review |
| Testing + QA | 3 days | Medium | All above |
| **Total** | **29 days** | **Medium-High** | |

---

## Summary: Implementation Priorities

### Phase 1: Foundation (Weeks 1-3)
- F1: Batch Generation core (Celery + Redis setup, basic API)
- F3: Enhanced Brand Voice (ChromaDB setup, basic ingestion)

### Phase 2: Core Features (Weeks 4-6)
- F1: Multi-provider load balancing, CSV import/export
- F2: Content Remix Engine (3 format adapters)
- F3: Voice application with strength control

### Phase 3: Advanced Features (Weeks 7-8)
- F1: Cost estimation, quota management
- F2: Quality scoring, remaining format adapters
- F3: A/B testing, voice statistics

### Phase 4: Polish (Weeks 9-10)
- Frontend components for all features
- Integration testing
- Performance optimization
- Documentation

### Total Estimated Effort
| Feature | Backend | Frontend | Total |
|---------|---------|----------|-------|
| F1: Batch Generation | 12 days | 6 days | 18 days |
| F2: Content Remix | 17 days | 6 days | 23 days |
| F3: Brand Voice | 21 days | 8 days | 29 days |
| **Combined** | **50 days** | **20 days** | **70 days** |

With parallel development across features, estimated calendar time: **10-12 weeks** with a team of 2-3 engineers.
