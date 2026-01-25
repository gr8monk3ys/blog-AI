# Tier 2 Competitive Features - Technical Architecture

This document provides detailed technical architecture specifications for Blog AI's Tier 2 competitive features. These features build upon the existing modular pipeline architecture and extend the platform's capabilities for AI image generation, visual content workflows, and fact-checking.

---

## Table of Contents

1. [F4: AI Image Generation Integration](#f4-ai-image-generation-integration)
2. [F5: Visual Content Workflows](#f5-visual-content-workflows)
3. [F6: Fact-Checking & Citation Layer](#f6-fact-checking--citation-layer)
4. [Cross-Feature Dependencies](#cross-feature-dependencies)
5. [Infrastructure Requirements](#infrastructure-requirements)

---

## F4: AI Image Generation Integration

### Overview

Multi-provider image generation abstraction layer following the same patterns as `src/text_generation/core.py`, enabling seamless switching between DALL-E 3, Stability AI, and Midjourney APIs.

### Architecture Diagram

```
                                    +------------------+
                                    |   Frontend UI    |
                                    | (ImageGenerator) |
                                    +--------+---------+
                                             |
                                             v
+----------------------------------------------------------------------------------------------------------+
|                                      API Layer (FastAPI)                                                 |
|  POST /api/v1/images/generate    POST /api/v1/images/batch    GET /api/v1/images/{id}                   |
+----------------------------------------------------------------------------------------------------------+
                                             |
                                             v
                              +------------------------------+
                              |    Image Generation Core     |
                              | src/image_generation/core.py |
                              +------------------------------+
                                             |
            +--------------------------------+--------------------------------+
            |                                |                                |
            v                                v                                v
+-------------------+           +------------------------+        +---------------------+
|   DALL-E 3        |           |    Stability AI        |        |     Midjourney      |
|   Provider        |           |    Provider            |        |     Provider        |
| (OpenAI Images)   |           | (stability.ai API)     |        | (via Discord/API)   |
+-------------------+           +------------------------+        +---------------------+
            |                                |                                |
            +--------------------------------+--------------------------------+
                                             |
                                             v
                              +------------------------------+
                              |    Content Moderation        |
                              |    Pipeline                  |
                              +------------------------------+
                                             |
                                             v
                              +------------------------------+
                              |    Image Storage Layer       |
                              | (S3/CloudFlare R2 + CDN)     |
                              +------------------------------+
                                             |
                                             v
                              +------------------------------+
                              |    Cache Layer (Redis)       |
                              |    - Prompt hash caching     |
                              |    - Resolution variants     |
                              +------------------------------+
```

### Data Models

```python
# src/types/image_generation.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union


class ImageProviderType(str, Enum):
    """Supported image generation providers."""
    DALLE3 = "dalle3"
    STABILITY = "stability"
    MIDJOURNEY = "midjourney"


class ImageSize(str, Enum):
    """Standard image sizes for different use cases."""
    # Blog images
    BLOG_HERO = "1792x1024"      # 16:9 landscape
    BLOG_INLINE = "1024x1024"    # Square
    BLOG_THUMBNAIL = "512x512"   # Thumbnail

    # Social media
    INSTAGRAM_POST = "1080x1080"
    INSTAGRAM_STORY = "1080x1920"
    TWITTER_POST = "1200x675"
    FACEBOOK_POST = "1200x630"
    LINKEDIN_POST = "1200x627"
    PINTEREST_PIN = "1000x1500"

    # Custom
    CUSTOM = "custom"


class ImageStyle(str, Enum):
    """Image style presets."""
    PHOTOREALISTIC = "photorealistic"
    ILLUSTRATION = "illustration"
    DIGITAL_ART = "digital_art"
    WATERCOLOR = "watercolor"
    MINIMALIST = "minimalist"
    CORPORATE = "corporate"
    VINTAGE = "vintage"
    MODERN = "modern"


@dataclass
class ImageProviderConfig:
    """Base configuration for image providers."""
    api_key: str
    timeout: int = 120
    max_retries: int = 3


@dataclass
class DallE3Config(ImageProviderConfig):
    """DALL-E 3 specific configuration."""
    model: str = "dall-e-3"
    quality: Literal["standard", "hd"] = "hd"
    style: Literal["vivid", "natural"] = "natural"


@dataclass
class StabilityConfig(ImageProviderConfig):
    """Stability AI specific configuration."""
    engine: str = "stable-diffusion-xl-1024-v1-0"
    cfg_scale: float = 7.0
    steps: int = 30
    sampler: str = "K_DPM_2_ANCESTRAL"


@dataclass
class MidjourneyConfig(ImageProviderConfig):
    """Midjourney specific configuration."""
    version: str = "6.0"
    stylize: int = 100
    chaos: int = 0


@dataclass
class ImageProvider:
    """Image generation provider."""
    type: ImageProviderType
    config: Union[DallE3Config, StabilityConfig, MidjourneyConfig]


@dataclass
class ImageGenerationOptions:
    """Options for image generation."""
    size: ImageSize = ImageSize.BLOG_HERO
    custom_width: Optional[int] = None
    custom_height: Optional[int] = None
    style: ImageStyle = ImageStyle.PHOTOREALISTIC
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    num_images: int = 1


@dataclass
class ImageTemplate:
    """Template for social media image generation."""
    id: str
    name: str
    platform: str
    size: ImageSize
    style_preset: ImageStyle
    prompt_template: str
    overlay_config: Optional[Dict[str, Any]] = None

    # Brand customization
    brand_colors: List[str] = field(default_factory=list)
    font_family: Optional[str] = None
    logo_position: Optional[str] = None


@dataclass
class ContentImageRequest:
    """Request for generating images from content context."""
    content_id: str
    content_type: Literal["blog", "book", "social"]
    content_title: str
    content_summary: str
    keywords: List[str]
    target_platforms: List[str] = field(default_factory=lambda: ["blog"])
    style_preference: Optional[ImageStyle] = None
    brand_profile_id: Optional[str] = None


@dataclass
class GeneratedImage:
    """A generated image."""
    id: str
    provider: ImageProviderType
    prompt: str
    revised_prompt: Optional[str]  # Provider's modified prompt
    url: str
    cdn_url: Optional[str]
    size: ImageSize
    width: int
    height: int
    style: ImageStyle
    content_id: Optional[str]
    created_at: datetime = field(default_factory=datetime.now)

    # Metadata
    generation_time_ms: int = 0
    cost_cents: int = 0
    moderation_passed: bool = True
    moderation_flags: List[str] = field(default_factory=list)

    # Cache info
    cache_key: Optional[str] = None
    cache_hit: bool = False


@dataclass
class ModerationResult:
    """Content moderation result."""
    passed: bool
    flags: List[str] = field(default_factory=list)
    confidence: float = 1.0
    provider: str = "openai"
    reviewed_at: datetime = field(default_factory=datetime.now)


@dataclass
class ImageCacheEntry:
    """Cache entry for generated images."""
    prompt_hash: str
    provider: ImageProviderType
    size: ImageSize
    style: ImageStyle
    image_id: str
    cdn_url: str
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
```

### API Endpoints

```python
# app/routes/images.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

router = APIRouter(prefix="/images", tags=["images"])


class ImageProviderEnum(str, Enum):
    dalle3 = "dalle3"
    stability = "stability"
    midjourney = "midjourney"


class ImageSizeEnum(str, Enum):
    blog_hero = "1792x1024"
    blog_inline = "1024x1024"
    instagram_post = "1080x1080"
    twitter_post = "1200x675"
    custom = "custom"


class ImageStyleEnum(str, Enum):
    photorealistic = "photorealistic"
    illustration = "illustration"
    digital_art = "digital_art"
    minimalist = "minimalist"
    corporate = "corporate"


class ImageGenerateRequest(BaseModel):
    """Request to generate an image."""
    prompt: str = Field(..., min_length=10, max_length=4000)
    provider: ImageProviderEnum = ImageProviderEnum.dalle3
    size: ImageSizeEnum = ImageSizeEnum.blog_hero
    custom_width: Optional[int] = Field(None, ge=256, le=4096)
    custom_height: Optional[int] = Field(None, ge=256, le=4096)
    style: ImageStyleEnum = ImageStyleEnum.photorealistic
    negative_prompt: Optional[str] = None
    num_images: int = Field(1, ge=1, le=4)
    use_cache: bool = True


class ContentImageRequest(BaseModel):
    """Request to generate images from content."""
    content_id: str
    content_type: str = "blog"
    content_title: str
    content_summary: str = Field(..., max_length=2000)
    keywords: List[str] = Field(default_factory=list, max_items=10)
    target_platforms: List[str] = Field(default=["blog"])
    style_preference: Optional[ImageStyleEnum] = None
    brand_profile_id: Optional[str] = None
    num_variations: int = Field(1, ge=1, le=4)


class BatchImageRequest(BaseModel):
    """Request to generate multiple images."""
    requests: List[ImageGenerateRequest] = Field(..., max_items=10)
    parallel: bool = True


class ImageResponse(BaseModel):
    """Response containing generated image."""
    success: bool
    image_id: str
    url: str
    cdn_url: Optional[str]
    provider: str
    prompt: str
    revised_prompt: Optional[str]
    size: str
    width: int
    height: int
    style: str
    generation_time_ms: int
    cost_cents: int
    cache_hit: bool
    moderation_passed: bool


class BatchImageResponse(BaseModel):
    """Response containing multiple generated images."""
    success: bool
    images: List[ImageResponse]
    total_cost_cents: int
    total_generation_time_ms: int
    failed_count: int


# Endpoints

@router.post("/generate", response_model=ImageResponse)
async def generate_image(request: ImageGenerateRequest):
    """Generate a single image from a prompt."""
    pass


@router.post("/generate-from-content", response_model=List[ImageResponse])
async def generate_from_content(request: ContentImageRequest):
    """Generate images based on content context (blog, book, etc.)."""
    pass


@router.post("/batch", response_model=BatchImageResponse)
async def generate_batch(
    request: BatchImageRequest,
    background_tasks: BackgroundTasks
):
    """Generate multiple images in batch."""
    pass


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: str):
    """Get image details by ID."""
    pass


@router.delete("/{image_id}")
async def delete_image(image_id: str):
    """Delete an image."""
    pass


@router.get("/templates", response_model=List[dict])
async def list_templates(platform: Optional[str] = None):
    """List available image templates."""
    pass


@router.post("/templates/{template_id}/generate", response_model=ImageResponse)
async def generate_from_template(
    template_id: str,
    content_title: str,
    content_keywords: List[str]
):
    """Generate image using a template."""
    pass


@router.post("/{image_id}/resize", response_model=ImageResponse)
async def resize_image(image_id: str, target_size: ImageSizeEnum):
    """Resize an existing image to a new size."""
    pass


@router.get("/{image_id}/variations", response_model=List[ImageResponse])
async def get_image_variations(image_id: str, count: int = 3):
    """Generate variations of an existing image."""
    pass
```

### Database Schema Changes

```sql
-- migrations/004_image_generation.sql

-- Generated images table
CREATE TABLE generated_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content_id UUID REFERENCES content(id) ON DELETE SET NULL,

    -- Generation details
    provider VARCHAR(50) NOT NULL,
    prompt TEXT NOT NULL,
    revised_prompt TEXT,
    negative_prompt TEXT,

    -- Image details
    original_url TEXT NOT NULL,
    cdn_url TEXT,
    storage_key TEXT,  -- S3/R2 key
    size VARCHAR(20) NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    style VARCHAR(50),
    format VARCHAR(10) DEFAULT 'png',
    file_size_bytes INTEGER,

    -- Generation metadata
    seed INTEGER,
    generation_time_ms INTEGER,
    cost_cents INTEGER DEFAULT 0,
    cache_hit BOOLEAN DEFAULT FALSE,
    cache_key VARCHAR(64),

    -- Moderation
    moderation_passed BOOLEAN DEFAULT TRUE,
    moderation_flags JSONB DEFAULT '[]',
    moderation_provider VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Image templates table
CREATE TABLE image_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    platform VARCHAR(50) NOT NULL,
    size VARCHAR(20) NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    style_preset VARCHAR(50),
    prompt_template TEXT NOT NULL,
    overlay_config JSONB,
    brand_colors JSONB DEFAULT '[]',
    font_family VARCHAR(100),
    logo_position VARCHAR(50),
    is_system BOOLEAN DEFAULT FALSE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Image cache table
CREATE TABLE image_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_hash VARCHAR(64) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    size VARCHAR(20) NOT NULL,
    style VARCHAR(50),
    image_id UUID REFERENCES generated_images(id) ON DELETE CASCADE,
    cdn_url TEXT NOT NULL,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    UNIQUE(prompt_hash, provider, size, style)
);

-- Image usage tracking
CREATE TABLE image_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    image_id UUID REFERENCES generated_images(id) ON DELETE SET NULL,
    provider VARCHAR(50) NOT NULL,
    cost_cents INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_images_user ON generated_images(user_id);
CREATE INDEX idx_images_content ON generated_images(content_id);
CREATE INDEX idx_images_created ON generated_images(created_at DESC);
CREATE INDEX idx_image_cache_lookup ON image_cache(prompt_hash, provider, size, style);
CREATE INDEX idx_image_cache_expires ON image_cache(expires_at);
CREATE INDEX idx_templates_platform ON image_templates(platform);
CREATE INDEX idx_templates_user ON image_templates(user_id);
```

### File/Module Structure

```
src/
  image_generation/
    __init__.py
    core.py                    # Main abstraction layer (like text_generation/core.py)
    providers/
      __init__.py
      dalle3.py                # DALL-E 3 implementation
      stability.py             # Stability AI implementation
      midjourney.py            # Midjourney implementation
      base.py                  # Base provider interface
    prompt/
      __init__.py
      generator.py             # Prompt generation from content
      enhancer.py              # Prompt enhancement/optimization
      templates.py             # Template-based prompt building
    moderation/
      __init__.py
      pipeline.py              # Content moderation pipeline
      openai_moderation.py     # OpenAI moderation API
      custom_filters.py        # Custom content filters
    storage/
      __init__.py
      manager.py               # Storage abstraction
      s3.py                    # AWS S3 implementation
      r2.py                    # Cloudflare R2 implementation
      cdn.py                   # CDN URL generation
    cache/
      __init__.py
      manager.py               # Cache management
      redis_cache.py           # Redis cache implementation
    cost/
      __init__.py
      calculator.py            # Cost calculation per provider
      optimizer.py             # Cost optimization strategies

  types/
    image_generation.py        # All image-related type definitions

app/
  routes/
    images.py                  # Image generation API routes

frontend/
  components/
    images/
      ImageGenerator.tsx       # Main image generation UI
      ImagePromptBuilder.tsx   # Prompt construction interface
      ImageTemplateSelector.tsx
      ImageGallery.tsx         # Generated images gallery
      ImageEditor.tsx          # Basic image editing
      PlatformPreview.tsx      # Preview for different platforms
```

### Third-Party Dependencies

```
# requirements.txt additions

# Image generation providers
openai>=1.0.0                  # DALL-E 3 API
stability-sdk>=0.8.0           # Stability AI SDK
httpx>=0.25.0                  # Async HTTP for Midjourney

# Image processing
Pillow>=10.0.0                 # Image manipulation
python-magic>=0.4.27           # File type detection

# Storage
boto3>=1.28.0                  # AWS S3
cloudflare>=2.0.0              # Cloudflare R2 (S3-compatible)

# Caching
redis>=5.0.0                   # Redis for caching
hiredis>=2.2.0                 # Redis performance

# Content moderation
azure-ai-contentsafety>=1.0.0  # Alternative moderation (optional)
```

### Estimated Complexity and Risks

| Component | Complexity | Risk Level | Notes |
|-----------|------------|------------|-------|
| Provider Abstraction | Medium | Low | Follows existing pattern from text_generation |
| DALL-E 3 Integration | Low | Low | Well-documented API |
| Stability AI Integration | Medium | Medium | Rate limits and response format variations |
| Midjourney Integration | High | High | No official API; requires Discord bot or third-party |
| Content Moderation | Medium | Medium | False positives can block legitimate content |
| Storage/CDN | Medium | Low | Standard cloud infrastructure |
| Prompt Generation | High | Medium | Quality depends on context extraction |
| Caching | Low | Low | Standard Redis patterns |

**Total Estimated Development Time:** 4-6 weeks

**Key Risks:**
1. Midjourney has no official API - requires third-party solutions or Discord automation
2. Content moderation false positives may frustrate users
3. Cost management is critical - image generation is expensive
4. Image storage costs can grow rapidly without proper cleanup

---

## F5: Visual Content Workflows

### Overview

A visual workflow builder enabling users to create, save, and execute automated content generation pipelines using a drag-and-drop canvas interface.

### Architecture Diagram

```
+----------------------------------------------------------------------------------------------------------+
|                                        Frontend (React Flow)                                             |
|  +------------------+  +------------------+  +------------------+  +------------------+                   |
|  | Workflow Canvas  |  | Node Palette     |  | Properties Panel |  | Execution View   |                  |
|  | (Drag & Drop)    |  | (Node Types)     |  | (Node Config)    |  | (Live Status)    |                  |
|  +------------------+  +------------------+  +------------------+  +------------------+                   |
+----------------------------------------------------------------------------------------------------------+
                                             |
                                             v
+----------------------------------------------------------------------------------------------------------+
|                                      API Layer (FastAPI)                                                 |
|  POST /workflows         GET /workflows/{id}        POST /workflows/{id}/execute                         |
|  PUT /workflows/{id}     DELETE /workflows/{id}     GET /workflows/{id}/executions                       |
+----------------------------------------------------------------------------------------------------------+
                                             |
                                             v
                              +------------------------------+
                              |    Workflow Engine           |
                              | src/workflows/engine.py      |
                              +------------------------------+
                                             |
         +-----------------------------------+-----------------------------------+
         |                                   |                                   |
         v                                   v                                   v
+------------------+              +--------------------+              +------------------+
| Graph Validator  |              | Execution Planner  |              | State Manager    |
| - Cycle detection|              | - Dependency order |              | - Redis state    |
| - Type checking  |              | - Parallelization  |              | - Checkpoints    |
+------------------+              +--------------------+              +------------------+
                                             |
                                             v
                              +------------------------------+
                              |    Node Executor             |
                              +------------------------------+
                                             |
    +--------+--------+--------+--------+--------+--------+--------+
    |        |        |        |        |        |        |        |
    v        v        v        v        v        v        v        v
+------+ +------+ +------+ +------+ +------+ +------+ +------+ +------+
|Resrch| |Genrte| |Trans | | SEO  | |Publish| |Cond  | |Sched | |Image |
| Node | | Node | | Node | | Node | | Node  | | Node | | Node | | Node |
+------+ +------+ +------+ +------+ +------+ +------+ +------+ +------+
                                             |
                                             v
                              +------------------------------+
                              |    Scheduler (APScheduler)   |
                              | - Cron execution             |
                              | - One-time scheduling        |
                              +------------------------------+
                                             |
                                             v
                              +------------------------------+
                              |    Notification Service      |
                              | - WebSocket updates          |
                              | - Email notifications        |
                              +------------------------------+
```

### Workflow Graph Data Model

```python
# src/types/workflows.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4


class NodeType(str, Enum):
    """Types of nodes in a workflow."""
    # Input nodes
    TRIGGER = "trigger"              # Manual, scheduled, or webhook trigger
    INPUT = "input"                  # User input/configuration

    # Research nodes
    WEB_RESEARCH = "web_research"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    TREND_ANALYSIS = "trend_analysis"

    # Generation nodes
    BLOG_GENERATE = "blog_generate"
    BOOK_GENERATE = "book_generate"
    SOCIAL_GENERATE = "social_generate"
    IMAGE_GENERATE = "image_generate"
    OUTLINE_GENERATE = "outline_generate"

    # Transform nodes
    SUMMARIZE = "summarize"
    EXPAND = "expand"
    TRANSLATE = "translate"
    REWRITE = "rewrite"
    FORMAT_CONVERT = "format_convert"

    # SEO nodes
    META_GENERATE = "meta_generate"
    KEYWORD_OPTIMIZE = "keyword_optimize"
    ALT_TEXT_GENERATE = "alt_text_generate"
    STRUCTURED_DATA = "structured_data"

    # Post-processing nodes
    PROOFREAD = "proofread"
    HUMANIZE = "humanize"
    FACT_CHECK = "fact_check"

    # Publishing nodes
    PUBLISH_WORDPRESS = "publish_wordpress"
    PUBLISH_MEDIUM = "publish_medium"
    PUBLISH_GITHUB = "publish_github"
    PUBLISH_SOCIAL = "publish_social"

    # Control flow nodes
    CONDITION = "condition"          # If/else branching
    SWITCH = "switch"                # Multi-way branching
    LOOP = "loop"                    # Iterate over items
    PARALLEL = "parallel"            # Execute branches in parallel
    MERGE = "merge"                  # Merge parallel branches
    DELAY = "delay"                  # Wait for duration

    # Utility nodes
    WEBHOOK = "webhook"              # HTTP request
    EMAIL = "email"                  # Send email
    NOTIFICATION = "notification"    # Push notification
    VARIABLE = "variable"            # Set/get variables
    SCRIPT = "script"                # Custom Python/JS


class NodeCategory(str, Enum):
    """Categories for organizing nodes in the palette."""
    TRIGGERS = "triggers"
    RESEARCH = "research"
    GENERATION = "generation"
    TRANSFORM = "transform"
    SEO = "seo"
    POST_PROCESSING = "post_processing"
    PUBLISHING = "publishing"
    CONTROL_FLOW = "control_flow"
    UTILITIES = "utilities"


class PortType(str, Enum):
    """Data types for node ports."""
    ANY = "any"
    TEXT = "text"
    BLOG = "blog"
    BOOK = "book"
    IMAGE = "image"
    LIST = "list"
    BOOLEAN = "boolean"
    NUMBER = "number"
    OBJECT = "object"


class ExecutionStatus(str, Enum):
    """Status of workflow/node execution."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class Port:
    """Input or output port on a node."""
    id: str
    name: str
    type: PortType
    required: bool = True
    multiple: bool = False  # Can accept multiple connections
    default_value: Optional[Any] = None


@dataclass
class NodeDefinition:
    """Definition of a node type."""
    type: NodeType
    category: NodeCategory
    name: str
    description: str
    icon: str
    color: str
    inputs: List[Port] = field(default_factory=list)
    outputs: List[Port] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)  # JSON Schema


@dataclass
class Position:
    """2D position on the canvas."""
    x: float
    y: float


@dataclass
class NodeInstance:
    """Instance of a node in a workflow."""
    id: str
    type: NodeType
    position: Position
    config: Dict[str, Any] = field(default_factory=dict)
    label: Optional[str] = None

    # Execution state (populated during runtime)
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class Edge:
    """Connection between two nodes."""
    id: str
    source_node_id: str
    source_port_id: str
    target_node_id: str
    target_port_id: str
    condition: Optional[str] = None  # Expression for conditional edges


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    id: str
    name: str
    description: Optional[str]
    nodes: List[NodeInstance]
    edges: List[Edge]

    # Metadata
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None

    # Configuration
    variables: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)

    # Publishing
    is_template: bool = False
    is_public: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class WorkflowVersion:
    """Versioned snapshot of a workflow."""
    id: str
    workflow_id: str
    version: int
    definition: WorkflowDefinition
    change_summary: Optional[str]
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None


@dataclass
class ScheduleConfig:
    """Schedule configuration for workflow execution."""
    enabled: bool = False
    schedule_type: Literal["cron", "interval", "once"] = "cron"
    cron_expression: Optional[str] = None  # e.g., "0 9 * * 1" (Monday 9 AM)
    interval_seconds: Optional[int] = None
    run_at: Optional[datetime] = None  # For one-time scheduling
    timezone: str = "UTC"
    max_runs: Optional[int] = None
    run_count: int = 0


@dataclass
class WorkflowExecution:
    """Record of a workflow execution."""
    id: str
    workflow_id: str
    workflow_version: int
    status: ExecutionStatus

    # Trigger info
    trigger_type: Literal["manual", "schedule", "webhook", "api"]
    triggered_by: Optional[str] = None
    trigger_data: Optional[Dict[str, Any]] = None

    # Execution state
    node_states: Dict[str, NodeInstance] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Results
    outputs: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    error_node_id: Optional[str] = None


@dataclass
class RetryPolicy:
    """Retry configuration for failed nodes."""
    max_retries: int = 3
    initial_delay_seconds: int = 5
    max_delay_seconds: int = 300
    exponential_backoff: bool = True
    retry_on_errors: List[str] = field(default_factory=lambda: ["timeout", "rate_limit"])
```

### Workflow Execution Engine

```python
# src/workflows/engine.py - Simplified interface

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio


class NodeExecutor(ABC):
    """Base class for node executors."""

    @abstractmethod
    async def execute(
        self,
        node: NodeInstance,
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute the node and return outputs."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate node configuration, return list of errors."""
        pass


class WorkflowEngine:
    """Main workflow execution engine."""

    def __init__(
        self,
        node_registry: Dict[NodeType, NodeExecutor],
        state_manager: StateManager,
        scheduler: WorkflowScheduler
    ):
        self.node_registry = node_registry
        self.state_manager = state_manager
        self.scheduler = scheduler

    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        trigger_data: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """Execute a workflow."""
        pass

    async def pause_execution(self, execution_id: str) -> bool:
        """Pause a running execution."""
        pass

    async def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused execution."""
        pass

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        pass

    def validate_workflow(self, workflow: WorkflowDefinition) -> List[str]:
        """Validate workflow graph, return list of errors."""
        # Check for cycles
        # Validate port type compatibility
        # Ensure all required inputs are connected
        # Validate node configurations
        pass


class ExecutionPlanner:
    """Plans execution order for workflow nodes."""

    def create_execution_plan(
        self,
        workflow: WorkflowDefinition
    ) -> List[List[str]]:
        """
        Create execution plan as waves of parallel nodes.
        Returns list of node ID lists, where each inner list
        can be executed in parallel.
        """
        pass


class StateManager:
    """Manages workflow execution state."""

    async def save_checkpoint(
        self,
        execution_id: str,
        node_id: str,
        state: Dict[str, Any]
    ) -> None:
        """Save execution checkpoint for recovery."""
        pass

    async def load_checkpoint(
        self,
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load execution state from checkpoint."""
        pass


class WorkflowScheduler:
    """Schedules workflow executions."""

    async def schedule_workflow(
        self,
        workflow_id: str,
        schedule: ScheduleConfig
    ) -> str:
        """Schedule a workflow, return schedule ID."""
        pass

    async def unschedule_workflow(self, schedule_id: str) -> bool:
        """Remove a scheduled workflow."""
        pass

    async def get_next_run(self, schedule_id: str) -> Optional[datetime]:
        """Get next scheduled run time."""
        pass
```

### API Endpoints

```python
# app/routes/workflows.py

from fastapi import APIRouter, HTTPException, WebSocket, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/workflows", tags=["workflows"])


class NodePosition(BaseModel):
    x: float
    y: float


class NodeConfig(BaseModel):
    id: str
    type: str
    position: NodePosition
    config: Dict[str, Any] = Field(default_factory=dict)
    label: Optional[str] = None


class EdgeConfig(BaseModel):
    id: str
    source_node_id: str
    source_port_id: str
    target_node_id: str
    target_port_id: str
    condition: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: List[NodeConfig]
    edges: List[EdgeConfig]
    variables: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[NodeConfig]] = None
    edges: Optional[List[EdgeConfig]] = None
    variables: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ScheduleCreate(BaseModel):
    enabled: bool = True
    schedule_type: str = "cron"
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    run_at: Optional[str] = None  # ISO datetime
    timezone: str = "UTC"
    max_runs: Optional[int] = None


class ExecuteRequest(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict)
    trigger_data: Dict[str, Any] = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    nodes: List[NodeConfig]
    edges: List[EdgeConfig]
    variables: Dict[str, Any]
    settings: Dict[str, Any]
    version: int
    is_template: bool
    is_public: bool
    tags: List[str]
    created_at: str
    updated_at: str


class ExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    trigger_type: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_ms: Optional[int]
    node_states: Dict[str, Any]
    outputs: Dict[str, Any]
    error_message: Optional[str]


# CRUD Endpoints

@router.post("", response_model=WorkflowResponse)
async def create_workflow(workflow: WorkflowCreate):
    """Create a new workflow."""
    pass


@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(
    skip: int = 0,
    limit: int = 20,
    tag: Optional[str] = None,
    is_template: Optional[bool] = None
):
    """List workflows with pagination and filtering."""
    pass


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """Get workflow by ID."""
    pass


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, workflow: WorkflowUpdate):
    """Update a workflow."""
    pass


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    pass


# Version Endpoints

@router.get("/{workflow_id}/versions", response_model=List[dict])
async def list_workflow_versions(workflow_id: str):
    """List all versions of a workflow."""
    pass


@router.get("/{workflow_id}/versions/{version}", response_model=WorkflowResponse)
async def get_workflow_version(workflow_id: str, version: int):
    """Get specific version of a workflow."""
    pass


@router.post("/{workflow_id}/versions/{version}/restore", response_model=WorkflowResponse)
async def restore_workflow_version(workflow_id: str, version: int):
    """Restore workflow to a previous version."""
    pass


# Execution Endpoints

@router.post("/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    request: ExecuteRequest,
    background_tasks: BackgroundTasks
):
    """Execute a workflow."""
    pass


@router.get("/{workflow_id}/executions", response_model=List[ExecutionResponse])
async def list_executions(
    workflow_id: str,
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None
):
    """List workflow executions."""
    pass


@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: str):
    """Get execution details."""
    pass


@router.post("/executions/{execution_id}/pause")
async def pause_execution(execution_id: str):
    """Pause a running execution."""
    pass


@router.post("/executions/{execution_id}/resume")
async def resume_execution(execution_id: str):
    """Resume a paused execution."""
    pass


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    """Cancel a running execution."""
    pass


# Scheduling Endpoints

@router.post("/{workflow_id}/schedule", response_model=dict)
async def create_schedule(workflow_id: str, schedule: ScheduleCreate):
    """Schedule a workflow for automatic execution."""
    pass


@router.get("/{workflow_id}/schedule", response_model=dict)
async def get_schedule(workflow_id: str):
    """Get workflow schedule."""
    pass


@router.delete("/{workflow_id}/schedule")
async def delete_schedule(workflow_id: str):
    """Remove workflow schedule."""
    pass


# Template Endpoints

@router.get("/templates", response_model=List[WorkflowResponse])
async def list_templates(category: Optional[str] = None):
    """List workflow templates."""
    pass


@router.post("/{workflow_id}/publish-template", response_model=WorkflowResponse)
async def publish_as_template(workflow_id: str, is_public: bool = False):
    """Publish workflow as a template."""
    pass


@router.post("/templates/{template_id}/clone", response_model=WorkflowResponse)
async def clone_template(template_id: str, name: str):
    """Clone a template to create a new workflow."""
    pass


# Node Registry Endpoints

@router.get("/nodes/registry", response_model=List[dict])
async def get_node_registry():
    """Get all available node types and their definitions."""
    pass


@router.post("/nodes/validate", response_model=dict)
async def validate_node_config(node_type: str, config: Dict[str, Any]):
    """Validate node configuration."""
    pass


# WebSocket for live execution updates

@router.websocket("/executions/{execution_id}/live")
async def execution_live_updates(websocket: WebSocket, execution_id: str):
    """WebSocket for real-time execution updates."""
    pass
```

### Database Schema Changes

```sql
-- migrations/005_workflows.sql

-- Workflows table
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Current state
    nodes JSONB NOT NULL DEFAULT '[]',
    edges JSONB NOT NULL DEFAULT '[]',
    variables JSONB NOT NULL DEFAULT '{}',
    settings JSONB NOT NULL DEFAULT '{}',

    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,

    -- Publishing
    is_template BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT FALSE,
    tags JSONB DEFAULT '[]',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    CONSTRAINT workflows_name_user_unique UNIQUE (user_id, name)
);

-- Workflow versions table
CREATE TABLE workflow_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    definition JSONB NOT NULL,
    change_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    CONSTRAINT workflow_version_unique UNIQUE (workflow_id, version)
);

-- Workflow schedules table
CREATE TABLE workflow_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE UNIQUE,
    enabled BOOLEAN DEFAULT TRUE,
    schedule_type VARCHAR(20) NOT NULL,
    cron_expression VARCHAR(100),
    interval_seconds INTEGER,
    run_at TIMESTAMPTZ,
    timezone VARCHAR(50) DEFAULT 'UTC',
    max_runs INTEGER,
    run_count INTEGER DEFAULT 0,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow executions table
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    workflow_version INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- Trigger info
    trigger_type VARCHAR(20) NOT NULL,
    triggered_by UUID REFERENCES users(id),
    trigger_data JSONB,

    -- Execution state
    node_states JSONB NOT NULL DEFAULT '{}',
    variables JSONB NOT NULL DEFAULT '{}',

    -- Results
    outputs JSONB DEFAULT '{}',
    error_message TEXT,
    error_node_id VARCHAR(100),

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Execution checkpoints (for recovery)
CREATE TABLE execution_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES workflow_executions(id) ON DELETE CASCADE,
    node_id VARCHAR(100) NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT checkpoint_unique UNIQUE (execution_id, node_id)
);

-- Indexes
CREATE INDEX idx_workflows_user ON workflows(user_id);
CREATE INDEX idx_workflows_template ON workflows(is_template) WHERE is_template = TRUE;
CREATE INDEX idx_workflows_public ON workflows(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_workflow_versions_workflow ON workflow_versions(workflow_id);
CREATE INDEX idx_workflow_schedules_next_run ON workflow_schedules(next_run_at) WHERE enabled = TRUE;
CREATE INDEX idx_executions_workflow ON workflow_executions(workflow_id);
CREATE INDEX idx_executions_status ON workflow_executions(status);
CREATE INDEX idx_executions_created ON workflow_executions(created_at DESC);
CREATE INDEX idx_checkpoints_execution ON execution_checkpoints(execution_id);
```

### File/Module Structure

```
src/
  workflows/
    __init__.py
    engine.py                      # Main workflow engine
    planner.py                     # Execution planning
    validator.py                   # Graph validation
    state.py                       # State management
    scheduler.py                   # APScheduler integration

    nodes/
      __init__.py
      base.py                      # Base node executor
      registry.py                  # Node type registry

      # Node implementations by category
      triggers/
        __init__.py
        manual.py
        schedule.py
        webhook.py

      research/
        __init__.py
        web_research.py
        competitor.py
        trends.py

      generation/
        __init__.py
        blog.py
        book.py
        social.py
        image.py
        outline.py

      transform/
        __init__.py
        summarize.py
        expand.py
        translate.py
        rewrite.py
        format.py

      seo/
        __init__.py
        meta.py
        keywords.py
        alt_text.py
        structured_data.py

      post_processing/
        __init__.py
        proofread.py
        humanize.py
        fact_check.py

      publishing/
        __init__.py
        wordpress.py
        medium.py
        github.py
        social.py

      control_flow/
        __init__.py
        condition.py
        switch.py
        loop.py
        parallel.py
        merge.py
        delay.py

      utilities/
        __init__.py
        webhook.py
        email.py
        notification.py
        variable.py
        script.py

  types/
    workflows.py                   # Workflow type definitions

app/
  routes/
    workflows.py                   # Workflow API routes

frontend/
  components/
    workflows/
      WorkflowCanvas.tsx           # Main React Flow canvas
      NodePalette.tsx              # Draggable node types
      PropertiesPanel.tsx          # Node configuration
      ExecutionView.tsx            # Live execution status

      nodes/                       # Custom React Flow nodes
        BaseNode.tsx
        TriggerNode.tsx
        GenerationNode.tsx
        ConditionNode.tsx
        PublishNode.tsx
        ...

      WorkflowToolbar.tsx          # Save, run, schedule controls
      WorkflowHistory.tsx          # Version history
      ExecutionHistory.tsx         # Past executions
      TemplateGallery.tsx          # Template browser
```

### Third-Party Dependencies

```
# requirements.txt additions

# Workflow engine
networkx>=3.1                      # Graph algorithms (cycle detection, topological sort)
APScheduler>=3.10.0                # Cron scheduling
croniter>=1.4.0                    # Cron expression parsing

# State management
redis>=5.0.0                       # State storage and pub/sub

# Expression evaluation (for conditions)
simpleeval>=0.9.13                 # Safe expression evaluation
```

```json
// package.json additions
{
  "dependencies": {
    "reactflow": "^11.10.0",
    "@xyflow/react": "^12.0.0",
    "dagre": "^0.8.5",
    "elkjs": "^0.8.2"
  }
}
```

### Estimated Complexity and Risks

| Component | Complexity | Risk Level | Notes |
|-----------|------------|------------|-------|
| Graph Data Model | Medium | Low | Standard DAG representation |
| Workflow Validation | Medium | Medium | Cycle detection, type checking |
| Execution Engine | High | High | Parallel execution, error handling |
| State Management | Medium | Medium | Checkpoint/recovery logic |
| Scheduler Integration | Medium | Low | APScheduler is mature |
| React Flow Canvas | High | Medium | Complex drag-and-drop UI |
| Node Implementations | High | Medium | Many node types to implement |
| WebSocket Updates | Medium | Low | Standard real-time patterns |

**Total Estimated Development Time:** 8-12 weeks

**Key Risks:**
1. Execution engine complexity - parallel execution with proper error handling is challenging
2. Frontend canvas performance with many nodes
3. State management for long-running workflows
4. User experience complexity - visual programming can be confusing

---

## F6: Fact-Checking & Citation Layer

### Overview

An integrated fact-checking system that extracts claims from generated content, verifies them against authoritative sources, and provides inline citations with credibility scoring.

### Architecture Diagram

```
+----------------------------------------------------------------------------------------------------------+
|                                        Generated Content                                                  |
|                              (Blog Post / Book Chapter / Article)                                        |
+----------------------------------------------------------------------------------------------------------+
                                             |
                                             v
                              +------------------------------+
                              |    Claim Extraction          |
                              |    (NLP Pipeline)            |
                              +------------------------------+
                                             |
                                             v
                              +------------------------------+
                              |    Claim Classification      |
                              | - Factual vs Opinion         |
                              | - Verifiable vs Subjective   |
                              | - Priority scoring           |
                              +------------------------------+
                                             |
                                             v
+----------------------------------------------------------------------------------------------------------+
|                                   Verification Pipeline                                                   |
|  +------------------+  +------------------+  +------------------+  +------------------+                   |
|  | Web Search       |  | Academic DB      |  | Fact-Check DB    |  | Domain APIs      |                  |
|  | (Tavily, SERP)   |  | (Semantic Schol.)|  | (ClaimBuster)    |  | (Wikipedia, etc) |                  |
|  +------------------+  +------------------+  +------------------+  +------------------+                   |
+----------------------------------------------------------------------------------------------------------+
                                             |
                                             v
                              +------------------------------+
                              |    Source Credibility        |
                              |    Scoring Engine            |
                              +------------------------------+
                                             |
                                             v
                              +------------------------------+
                              |    Evidence Aggregation      |
                              |    & Confidence Scoring      |
                              +------------------------------+
                                             |
                                             v
                              +------------------------------+
                              |    Citation Generator        |
                              | - APA, MLA, Chicago, etc.    |
                              | - Inline citations           |
                              | - Bibliography               |
                              +------------------------------+
                                             |
                                             v
+----------------------------------------------------------------------------------------------------------+
|                                      Output Layer                                                         |
|  +------------------+  +------------------+  +------------------+  +------------------+                   |
|  | Annotated        |  | Fact-Check       |  | Citation         |  | Trust Badges     |                  |
|  | Content          |  | Report           |  | Bibliography     |  | (UI Components)  |                  |
+----------------------------------------------------------------------------------------------------------+
```

### Data Models

```python
# src/types/fact_checking.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union


class ClaimType(str, Enum):
    """Types of claims that can be extracted."""
    FACTUAL = "factual"              # Verifiable facts
    STATISTICAL = "statistical"       # Numbers, percentages, data
    HISTORICAL = "historical"         # Historical events/dates
    SCIENTIFIC = "scientific"         # Scientific claims
    QUOTE = "quote"                   # Attributed quotes
    DEFINITION = "definition"         # Definitions of terms
    COMPARISON = "comparison"         # Comparative statements
    CAUSAL = "causal"                 # Cause-effect claims
    OPINION = "opinion"               # Opinions (not verifiable)
    PREDICTION = "prediction"         # Future predictions


class VerificationStatus(str, Enum):
    """Status of claim verification."""
    PENDING = "pending"
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"
    FALSE = "false"
    OPINION = "opinion"              # Not verifiable
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class SourceType(str, Enum):
    """Types of sources for verification."""
    ACADEMIC = "academic"             # Peer-reviewed journals
    GOVERNMENT = "government"         # Government sources
    NEWS_MAJOR = "news_major"         # Major news outlets
    NEWS_LOCAL = "news_local"         # Local news
    FACT_CHECK = "fact_check"         # Fact-checking organizations
    ENCYCLOPEDIA = "encyclopedia"     # Wikipedia, Britannica
    ORGANIZATION = "organization"     # NGOs, think tanks
    CORPORATE = "corporate"           # Company sources
    SOCIAL_MEDIA = "social_media"     # Social media
    BLOG = "blog"                     # Blogs
    UNKNOWN = "unknown"


class CitationStyle(str, Enum):
    """Citation formatting styles."""
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    HARVARD = "harvard"
    IEEE = "ieee"
    VANCOUVER = "vancouver"


@dataclass
class TextSpan:
    """A span of text within content."""
    start: int
    end: int
    text: str


@dataclass
class ExtractedClaim:
    """A claim extracted from content."""
    id: str
    text: str
    span: TextSpan
    claim_type: ClaimType
    subject: Optional[str] = None      # What/who the claim is about
    predicate: Optional[str] = None    # The assertion being made
    entities: List[str] = field(default_factory=list)

    # Priority for verification
    priority: float = 0.5              # 0-1 scale
    is_key_claim: bool = False

    # Context
    surrounding_text: Optional[str] = None
    section_title: Optional[str] = None


@dataclass
class SourceCredibility:
    """Credibility assessment of a source."""
    domain: str
    source_type: SourceType

    # Scores (0-1 scale)
    overall_score: float
    factual_accuracy: float
    editorial_standards: float
    transparency: float
    expertise: float

    # Metadata
    media_bias_rating: Optional[str] = None  # From MediaBias/FactCheck
    domain_authority: Optional[int] = None   # Moz domain authority
    alexa_rank: Optional[int] = None

    # Flags
    is_primary_source: bool = False
    is_peer_reviewed: bool = False
    known_for_misinformation: bool = False

    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class VerificationSource:
    """A source used to verify a claim."""
    id: str
    url: str
    title: str
    domain: str
    source_type: SourceType

    # Content
    relevant_excerpt: str
    full_text: Optional[str] = None

    # Verification
    supports_claim: bool = True
    support_strength: float = 0.5       # 0-1 scale

    # Credibility
    credibility: Optional[SourceCredibility] = None

    # Metadata
    published_date: Optional[datetime] = None
    author: Optional[str] = None
    retrieved_at: datetime = field(default_factory=datetime.now)


@dataclass
class ClaimVerification:
    """Verification result for a claim."""
    claim_id: str
    status: VerificationStatus
    confidence: float                   # 0-1 scale

    # Sources
    supporting_sources: List[VerificationSource] = field(default_factory=list)
    contradicting_sources: List[VerificationSource] = field(default_factory=list)

    # Analysis
    explanation: Optional[str] = None
    nuance: Optional[str] = None        # Important context/caveats
    suggested_correction: Optional[str] = None

    # Timing
    verified_at: datetime = field(default_factory=datetime.now)
    verification_time_ms: int = 0


@dataclass
class Citation:
    """A formatted citation."""
    id: str
    source: VerificationSource
    style: CitationStyle

    # Formatted strings
    inline_citation: str               # e.g., "(Smith, 2023)"
    full_citation: str                 # Full bibliography entry
    footnote: Optional[str] = None

    # Position in content
    claim_id: str
    insertion_point: int               # Character position


@dataclass
class FactCheckReport:
    """Complete fact-check report for content."""
    id: str
    content_id: str
    content_type: Literal["blog", "book", "article"]

    # Claims
    total_claims: int
    claims: List[ExtractedClaim]
    verifications: List[ClaimVerification]

    # Summary
    verified_count: int
    disputed_count: int
    unverified_count: int

    # Overall assessment
    overall_accuracy_score: float      # 0-1 scale
    trust_level: Literal["high", "medium", "low", "unverified"]

    # Citations
    citations: List[Citation]
    bibliography: str                  # Formatted bibliography
    citation_style: CitationStyle

    # Annotated content
    annotated_content: Optional[str] = None  # Content with inline citations

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    processing_time_ms: int = 0


@dataclass
class FactCheckSettings:
    """User settings for fact-checking."""
    enabled: bool = True
    auto_check_on_generate: bool = False

    # Claim filtering
    min_claim_priority: float = 0.3
    check_statistics: bool = True
    check_quotes: bool = True
    check_historical: bool = True
    skip_opinions: bool = True

    # Source preferences
    require_academic_sources: bool = False
    min_source_credibility: float = 0.5
    preferred_sources: List[str] = field(default_factory=list)
    blocked_sources: List[str] = field(default_factory=list)

    # Citation
    citation_style: CitationStyle = CitationStyle.APA
    include_inline_citations: bool = True
    generate_bibliography: bool = True

    # UI
    show_trust_badges: bool = True
    highlight_unverified: bool = True
```

### Verification Pipeline

```python
# src/fact_checking/pipeline.py - Simplified interface

from abc import ABC, abstractmethod
from typing import List, Optional


class ClaimExtractor:
    """Extracts verifiable claims from text."""

    async def extract_claims(
        self,
        content: str,
        content_type: str = "blog"
    ) -> List[ExtractedClaim]:
        """
        Extract claims using NLP.
        Uses dependency parsing and named entity recognition.
        """
        pass

    def classify_claim(self, claim: ExtractedClaim) -> ClaimType:
        """Classify claim type using ML model."""
        pass

    def calculate_priority(self, claim: ExtractedClaim) -> float:
        """Calculate verification priority based on claim importance."""
        pass


class VerificationSource(ABC):
    """Base class for verification sources."""

    @abstractmethod
    async def search(
        self,
        claim: ExtractedClaim,
        max_results: int = 5
    ) -> List[VerificationSource]:
        """Search for sources to verify a claim."""
        pass


class WebSearchVerifier(VerificationSource):
    """Verify claims using web search."""
    pass


class AcademicVerifier(VerificationSource):
    """Verify claims using academic databases."""
    pass


class FactCheckDBVerifier(VerificationSource):
    """Check against known fact-check databases."""
    pass


class CredibilityScorer:
    """Scores source credibility."""

    async def score_source(self, url: str) -> SourceCredibility:
        """Calculate credibility score for a source."""
        pass

    def get_cached_score(self, domain: str) -> Optional[SourceCredibility]:
        """Get cached credibility score."""
        pass


class EvidenceAggregator:
    """Aggregates evidence and calculates confidence."""

    def aggregate_evidence(
        self,
        claim: ExtractedClaim,
        sources: List[VerificationSource]
    ) -> ClaimVerification:
        """
        Aggregate evidence from multiple sources.
        Calculate overall confidence score.
        """
        pass


class CitationGenerator:
    """Generates formatted citations."""

    def format_citation(
        self,
        source: VerificationSource,
        style: CitationStyle
    ) -> Citation:
        """Format a citation in the specified style."""
        pass

    def generate_bibliography(
        self,
        citations: List[Citation],
        style: CitationStyle
    ) -> str:
        """Generate formatted bibliography."""
        pass

    def insert_inline_citations(
        self,
        content: str,
        citations: List[Citation]
    ) -> str:
        """Insert inline citations into content."""
        pass


class FactCheckingPipeline:
    """Main fact-checking pipeline."""

    def __init__(
        self,
        extractor: ClaimExtractor,
        verifiers: List[VerificationSource],
        scorer: CredibilityScorer,
        aggregator: EvidenceAggregator,
        generator: CitationGenerator
    ):
        self.extractor = extractor
        self.verifiers = verifiers
        self.scorer = scorer
        self.aggregator = aggregator
        self.generator = generator

    async def check_content(
        self,
        content: str,
        content_id: str,
        content_type: str = "blog",
        settings: Optional[FactCheckSettings] = None
    ) -> FactCheckReport:
        """
        Run complete fact-checking pipeline on content.

        1. Extract claims
        2. Filter and prioritize
        3. Verify each claim
        4. Score sources
        5. Aggregate evidence
        6. Generate citations
        7. Create report
        """
        pass
```

### API Endpoints

```python
# app/routes/fact_check.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/fact-check", tags=["fact-checking"])


class FactCheckRequest(BaseModel):
    """Request to fact-check content."""
    content: str = Field(..., min_length=100, max_length=50000)
    content_id: Optional[str] = None
    content_type: str = "blog"

    # Settings
    citation_style: str = "apa"
    min_claim_priority: float = Field(0.3, ge=0, le=1)
    include_inline_citations: bool = True
    generate_bibliography: bool = True


class ClaimCheckRequest(BaseModel):
    """Request to verify a specific claim."""
    claim_text: str = Field(..., min_length=10, max_length=1000)
    context: Optional[str] = None


class SourceCredibilityRequest(BaseModel):
    """Request to check source credibility."""
    url: str
    refresh: bool = False


class ClaimResponse(BaseModel):
    """Response for an extracted claim."""
    id: str
    text: str
    claim_type: str
    priority: float
    start: int
    end: int


class VerificationResponse(BaseModel):
    """Response for claim verification."""
    claim_id: str
    status: str
    confidence: float
    explanation: Optional[str]
    supporting_sources: List[Dict[str, Any]]
    contradicting_sources: List[Dict[str, Any]]
    suggested_correction: Optional[str]


class CitationResponse(BaseModel):
    """Response for a citation."""
    id: str
    claim_id: str
    inline_citation: str
    full_citation: str
    source_url: str
    source_title: str


class FactCheckReportResponse(BaseModel):
    """Response for complete fact-check report."""
    id: str
    content_id: Optional[str]

    # Summary
    total_claims: int
    verified_count: int
    disputed_count: int
    unverified_count: int
    overall_accuracy_score: float
    trust_level: str

    # Details
    claims: List[ClaimResponse]
    verifications: List[VerificationResponse]
    citations: List[CitationResponse]
    bibliography: str

    # Annotated content
    annotated_content: Optional[str]

    processing_time_ms: int


class CredibilityResponse(BaseModel):
    """Response for source credibility check."""
    domain: str
    source_type: str
    overall_score: float
    factual_accuracy: float
    editorial_standards: float
    is_peer_reviewed: bool
    known_for_misinformation: bool
    media_bias_rating: Optional[str]


# Endpoints

@router.post("/check", response_model=FactCheckReportResponse)
async def fact_check_content(
    request: FactCheckRequest,
    background_tasks: BackgroundTasks
):
    """Run fact-checking on content."""
    pass


@router.post("/check-claim", response_model=VerificationResponse)
async def check_single_claim(request: ClaimCheckRequest):
    """Verify a single claim."""
    pass


@router.get("/reports/{report_id}", response_model=FactCheckReportResponse)
async def get_report(report_id: str):
    """Get a fact-check report by ID."""
    pass


@router.get("/reports", response_model=List[FactCheckReportResponse])
async def list_reports(
    content_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """List fact-check reports."""
    pass


@router.post("/extract-claims", response_model=List[ClaimResponse])
async def extract_claims(content: str = Field(..., min_length=100)):
    """Extract claims from content without verifying."""
    pass


@router.post("/source-credibility", response_model=CredibilityResponse)
async def check_source_credibility(request: SourceCredibilityRequest):
    """Check credibility of a source."""
    pass


@router.get("/credibility-cache", response_model=List[CredibilityResponse])
async def list_credibility_cache(
    domain: Optional[str] = None,
    min_score: Optional[float] = None
):
    """List cached source credibility scores."""
    pass


@router.post("/generate-citations", response_model=List[CitationResponse])
async def generate_citations(
    sources: List[Dict[str, Any]],
    style: str = "apa"
):
    """Generate formatted citations from sources."""
    pass


# Settings endpoints

@router.get("/settings", response_model=Dict[str, Any])
async def get_fact_check_settings():
    """Get user's fact-checking settings."""
    pass


@router.put("/settings", response_model=Dict[str, Any])
async def update_fact_check_settings(settings: Dict[str, Any]):
    """Update user's fact-checking settings."""
    pass
```

### Database Schema Changes

```sql
-- migrations/006_fact_checking.sql

-- Extracted claims table
CREATE TABLE extracted_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES fact_check_reports(id) ON DELETE CASCADE,

    -- Claim content
    text TEXT NOT NULL,
    claim_type VARCHAR(50) NOT NULL,
    subject TEXT,
    predicate TEXT,
    entities JSONB DEFAULT '[]',

    -- Position
    span_start INTEGER NOT NULL,
    span_end INTEGER NOT NULL,
    surrounding_text TEXT,
    section_title TEXT,

    -- Priority
    priority FLOAT NOT NULL DEFAULT 0.5,
    is_key_claim BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Claim verifications table
CREATE TABLE claim_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID REFERENCES extracted_claims(id) ON DELETE CASCADE,

    -- Verification result
    status VARCHAR(30) NOT NULL,
    confidence FLOAT NOT NULL,

    -- Analysis
    explanation TEXT,
    nuance TEXT,
    suggested_correction TEXT,

    -- Timing
    verified_at TIMESTAMPTZ DEFAULT NOW(),
    verification_time_ms INTEGER
);

-- Verification sources table
CREATE TABLE verification_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_id UUID REFERENCES claim_verifications(id) ON DELETE CASCADE,

    -- Source info
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    domain VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,

    -- Content
    relevant_excerpt TEXT NOT NULL,

    -- Relationship to claim
    supports_claim BOOLEAN NOT NULL,
    support_strength FLOAT NOT NULL,

    -- Metadata
    published_date TIMESTAMPTZ,
    author TEXT,
    retrieved_at TIMESTAMPTZ DEFAULT NOW()
);

-- Source credibility cache
CREATE TABLE source_credibility (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL,

    -- Scores
    overall_score FLOAT NOT NULL,
    factual_accuracy FLOAT NOT NULL,
    editorial_standards FLOAT NOT NULL,
    transparency FLOAT NOT NULL,
    expertise FLOAT NOT NULL,

    -- Metadata
    media_bias_rating VARCHAR(50),
    domain_authority INTEGER,

    -- Flags
    is_peer_reviewed BOOLEAN DEFAULT FALSE,
    known_for_misinformation BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fact-check reports table
CREATE TABLE fact_check_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content_id UUID,
    content_type VARCHAR(50) NOT NULL,

    -- Summary
    total_claims INTEGER NOT NULL,
    verified_count INTEGER NOT NULL DEFAULT 0,
    disputed_count INTEGER NOT NULL DEFAULT 0,
    unverified_count INTEGER NOT NULL DEFAULT 0,

    -- Assessment
    overall_accuracy_score FLOAT NOT NULL,
    trust_level VARCHAR(20) NOT NULL,

    -- Citations
    citation_style VARCHAR(20) NOT NULL,
    bibliography TEXT,
    annotated_content TEXT,

    -- Timing
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processing_time_ms INTEGER
);

-- Citations table
CREATE TABLE citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES fact_check_reports(id) ON DELETE CASCADE,
    source_id UUID REFERENCES verification_sources(id) ON DELETE CASCADE,
    claim_id UUID REFERENCES extracted_claims(id) ON DELETE CASCADE,

    -- Formatted citations
    style VARCHAR(20) NOT NULL,
    inline_citation TEXT NOT NULL,
    full_citation TEXT NOT NULL,
    footnote TEXT,

    -- Position
    insertion_point INTEGER NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User fact-check settings
CREATE TABLE fact_check_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,

    enabled BOOLEAN DEFAULT TRUE,
    auto_check_on_generate BOOLEAN DEFAULT FALSE,

    -- Claim filtering
    min_claim_priority FLOAT DEFAULT 0.3,
    check_statistics BOOLEAN DEFAULT TRUE,
    check_quotes BOOLEAN DEFAULT TRUE,
    check_historical BOOLEAN DEFAULT TRUE,
    skip_opinions BOOLEAN DEFAULT TRUE,

    -- Source preferences
    require_academic_sources BOOLEAN DEFAULT FALSE,
    min_source_credibility FLOAT DEFAULT 0.5,
    preferred_sources JSONB DEFAULT '[]',
    blocked_sources JSONB DEFAULT '[]',

    -- Citation
    citation_style VARCHAR(20) DEFAULT 'apa',
    include_inline_citations BOOLEAN DEFAULT TRUE,
    generate_bibliography BOOLEAN DEFAULT TRUE,

    -- UI
    show_trust_badges BOOLEAN DEFAULT TRUE,
    highlight_unverified BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_claims_report ON extracted_claims(report_id);
CREATE INDEX idx_verifications_claim ON claim_verifications(claim_id);
CREATE INDEX idx_sources_verification ON verification_sources(verification_id);
CREATE INDEX idx_credibility_domain ON source_credibility(domain);
CREATE INDEX idx_reports_user ON fact_check_reports(user_id);
CREATE INDEX idx_reports_content ON fact_check_reports(content_id);
CREATE INDEX idx_citations_report ON citations(report_id);
```

### File/Module Structure

```
src/
  fact_checking/
    __init__.py
    pipeline.py                    # Main fact-checking pipeline

    extraction/
      __init__.py
      claim_extractor.py           # NLP-based claim extraction
      claim_classifier.py          # Claim type classification
      priority_scorer.py           # Verification priority

    verification/
      __init__.py
      base.py                      # Base verifier interface
      web_search.py                # Web search verification
      academic.py                  # Academic database search
      fact_check_db.py             # Known fact-check databases
      wikipedia.py                 # Wikipedia verification

    credibility/
      __init__.py
      scorer.py                    # Credibility scoring engine
      media_bias.py                # Media bias integration
      domain_analysis.py           # Domain authority analysis

    evidence/
      __init__.py
      aggregator.py                # Evidence aggregation
      confidence.py                # Confidence scoring

    citation/
      __init__.py
      generator.py                 # Citation generation
      styles/
        __init__.py
        apa.py
        mla.py
        chicago.py
        harvard.py
        ieee.py
      bibliography.py              # Bibliography generation
      inline.py                    # Inline citation insertion

  types/
    fact_checking.py               # Type definitions

app/
  routes/
    fact_check.py                  # Fact-checking API routes

frontend/
  components/
    fact-check/
      FactCheckPanel.tsx           # Main fact-check UI
      ClaimList.tsx                # List of extracted claims
      VerificationCard.tsx         # Single claim verification
      SourceCredibility.tsx        # Source credibility display
      TrustBadge.tsx               # Trust level badge
      CitationTooltip.tsx          # Hover citation display
      BibliographyView.tsx         # Bibliography display
      InlineAnnotation.tsx         # Inline citation styling
      FactCheckSettings.tsx        # Settings panel
```

### Third-Party Dependencies

```
# requirements.txt additions

# NLP for claim extraction
spacy>=3.7.0                       # NLP pipeline
en-core-web-lg>=3.7.0              # English language model
transformers>=4.35.0               # Hugging Face transformers
torch>=2.1.0                       # PyTorch for ML models

# Fact-checking APIs
httpx>=0.25.0                      # Async HTTP client

# Citation formatting
citeproc-py>=0.6.0                 # Citation processing
```

### Integration with Research Module

The fact-checking system integrates with the existing `src/research/web_researcher.py` module.

```python
# Integration example

from src.research.web_researcher import conduct_web_research
from src.fact_checking.verification.web_search import WebSearchVerifier

class IntegratedWebVerifier(WebSearchVerifier):
    """Web verifier using existing research infrastructure."""

    async def search(self, claim: ExtractedClaim, max_results: int = 5):
        # Use existing research module
        results = conduct_web_research(
            keywords=[claim.subject, claim.predicate],
            options=SearchOptions(num_results=max_results)
        )

        # Convert to verification sources
        return self._convert_to_sources(results)
```

### Estimated Complexity and Risks

| Component | Complexity | Risk Level | Notes |
|-----------|------------|------------|-------|
| Claim Extraction (NLP) | High | High | Requires fine-tuned models |
| Claim Classification | Medium | Medium | Can use pre-trained classifiers |
| Web Search Verification | Medium | Low | Extends existing research module |
| Academic Verification | Medium | Medium | API access and rate limits |
| Source Credibility | High | Medium | Requires maintained database |
| Evidence Aggregation | High | High | Complex confidence calculation |
| Citation Generation | Medium | Low | Standard formatting rules |
| UI Components | Medium | Low | Standard React components |

**Total Estimated Development Time:** 6-8 weeks

**Key Risks:**
1. NLP claim extraction accuracy - false positives/negatives affect user trust
2. Source credibility database maintenance is ongoing work
3. API rate limits from fact-checking services
4. False confidence in low-quality verification
5. Legal considerations around labeling content as "verified" or "false"

---

## Cross-Feature Dependencies

```
                    +---------------------------+
                    |   Existing Infrastructure  |
                    +---------------------------+
                              |
        +---------------------+---------------------+
        |                     |                     |
        v                     v                     v
+---------------+     +---------------+     +---------------+
|     F4:       |     |     F5:       |     |     F6:       |
| AI Image Gen  |     | Workflows     |     | Fact-Check    |
+---------------+     +---------------+     +---------------+
        |                     |                     |
        |                     v                     |
        |             +---------------+             |
        +------------>| IMAGE_GENERATE|<------------+
                      |     Node      |
                      +---------------+
                              |
                      +---------------+
                      | FACT_CHECK    |
                      |     Node      |
                      +---------------+
```

### Dependency Matrix

| Feature | Depends On | Provides To |
|---------|------------|-------------|
| F4: Image Gen | LLM Core, Storage | F5 (Image nodes) |
| F5: Workflows | All generation modules | Orchestration for all features |
| F6: Fact-Check | Research module, LLM Core | F5 (Fact-check nodes), Content output |

### Shared Infrastructure

1. **Redis**: Used by all three features
   - F4: Image prompt caching
   - F5: Workflow state management
   - F6: Credibility score caching

2. **Storage (S3/R2)**: Shared by F4 and F5
   - F4: Generated images
   - F5: Workflow execution artifacts

3. **Background Tasks**: Celery/RQ for all features
   - F4: Image generation jobs
   - F5: Workflow execution
   - F6: Batch fact-checking

---

## Infrastructure Requirements

### Database

- **PostgreSQL 15+**: Primary database with JSONB support
- **pgvector extension**: For semantic search in fact-checking

### Caching

- **Redis 7+**: State management, caching, pub/sub

### Storage

- **S3/Cloudflare R2**: Image and artifact storage
- **CloudFront/Cloudflare CDN**: Image delivery

### Background Processing

- **Celery** or **RQ**: Async task processing
- **Redis**: Task broker

### Monitoring

- **Prometheus + Grafana**: Metrics and dashboards
- **Sentry**: Error tracking
- **Structured Logging**: JSON logs for analysis

### Environment Variables

```bash
# Image Generation (F4)
DALLE_API_KEY=
STABILITY_API_KEY=
MIDJOURNEY_API_KEY=
IMAGE_STORAGE_BUCKET=
CDN_URL=
IMAGE_CACHE_TTL_HOURS=24

# Workflows (F5)
WORKFLOW_STATE_REDIS_URL=
SCHEDULER_REDIS_URL=
MAX_CONCURRENT_WORKFLOWS=10
WORKFLOW_TIMEOUT_MINUTES=60

# Fact-Checking (F6)
SEMANTIC_SCHOLAR_API_KEY=
CLAIMBUSTER_API_KEY=
MEDIA_BIAS_API_KEY=
FACT_CHECK_CACHE_TTL_HOURS=168
```

---

## Implementation Priority

| Phase | Features | Duration | Dependencies |
|-------|----------|----------|--------------|
| 1 | F4: Core image abstraction | 2 weeks | None |
| 2 | F4: DALL-E 3 + Storage | 2 weeks | Phase 1 |
| 3 | F6: Claim extraction + basic verification | 3 weeks | Research module |
| 4 | F5: Workflow engine core | 3 weeks | None |
| 5 | F5: Node implementations | 3 weeks | Phases 2, 3, 4 |
| 6 | F4: Additional providers | 2 weeks | Phase 2 |
| 7 | F6: Citation generation | 2 weeks | Phase 3 |
| 8 | F5: Scheduling + UI | 2 weeks | Phase 5 |
| 9 | Integration testing | 2 weeks | All phases |

**Total Timeline: 16-20 weeks**

---

## Appendix: Node Type Definitions

### Complete Node Registry

```python
NODE_DEFINITIONS = {
    # Trigger Nodes
    NodeType.TRIGGER: NodeDefinition(
        type=NodeType.TRIGGER,
        category=NodeCategory.TRIGGERS,
        name="Trigger",
        description="Start workflow execution",
        icon="PlayIcon",
        color="#10B981",
        inputs=[],
        outputs=[
            Port(id="trigger_data", name="Trigger Data", type=PortType.OBJECT)
        ],
        config_schema={
            "type": "object",
            "properties": {
                "trigger_type": {"enum": ["manual", "schedule", "webhook"]},
                "schedule": {"type": "string"},
                "webhook_secret": {"type": "string"}
            }
        }
    ),

    # Generation Nodes
    NodeType.BLOG_GENERATE: NodeDefinition(
        type=NodeType.BLOG_GENERATE,
        category=NodeCategory.GENERATION,
        name="Generate Blog Post",
        description="Generate a complete blog post",
        icon="DocumentTextIcon",
        color="#6366F1",
        inputs=[
            Port(id="topic", name="Topic", type=PortType.TEXT),
            Port(id="research", name="Research", type=PortType.OBJECT, required=False),
            Port(id="outline", name="Outline", type=PortType.OBJECT, required=False)
        ],
        outputs=[
            Port(id="blog", name="Blog Post", type=PortType.BLOG)
        ],
        config_schema={
            "type": "object",
            "properties": {
                "tone": {"enum": ["informative", "conversational", "professional"]},
                "keywords": {"type": "array", "items": {"type": "string"}},
                "proofread": {"type": "boolean"},
                "humanize": {"type": "boolean"}
            }
        }
    ),

    # ... Additional node definitions
}
```
