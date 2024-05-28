"""
Enhanced batch generation types for Tier 1 features.

This module extends the existing bulk generation system with:
- Provider strategies for multi-LLM distribution
- Cost estimation models
- CSV import/export schemas
- Job priority and scheduling
- Security validation for all inputs
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# =============================================================================
# Security Constants (inline for independence from app.validators)
# =============================================================================

ALLOWED_PROVIDERS: Set[str] = {"openai", "anthropic", "gemini"}
CSV_FORMULA_CHARS: Set[str] = {"=", "+", "-", "@", "\t", "\r", "\n"}


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
    SINGLE = "single"  # Use one provider for all
    ROUND_ROBIN = "round_robin"  # Rotate through available providers
    LOAD_BALANCED = "load_balanced"  # Route based on current load
    COST_OPTIMIZED = "cost_optimized"  # Route to cheapest available
    QUALITY_OPTIMIZED = "quality_optimized"  # Route to highest quality


class ExportFormat(str, Enum):
    """Supported export formats for batch results."""
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    ZIP = "zip"


# Provider cost estimates (per 1K tokens, approximate)
PROVIDER_COSTS = {
    "openai": {"input": 0.01, "output": 0.03, "name": "GPT-4"},
    "anthropic": {"input": 0.008, "output": 0.024, "name": "Claude 3.5 Sonnet"},
    "gemini": {"input": 0.00025, "output": 0.0005, "name": "Gemini 1.5 Pro"},
}

# Average tokens per content type
ESTIMATED_TOKENS = {
    "blog": {"input": 500, "output": 3000},
    "email": {"input": 200, "output": 500},
    "social": {"input": 100, "output": 280},
    "book_chapter": {"input": 800, "output": 5000},
}


class CostEstimate(BaseModel):
    """Cost estimation for a batch job."""
    estimated_input_tokens: int = Field(description="Estimated input tokens")
    estimated_output_tokens: int = Field(description="Estimated output tokens")
    estimated_cost_usd: float = Field(description="Total estimated cost in USD")
    cost_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Cost per provider if multi-provider"
    )
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Estimation confidence (0-1)"
    )
    provider_recommendations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recommended providers with cost comparison"
    )


class CSVImportRow(BaseModel):
    """Schema for CSV batch import rows with security validation."""
    topic: str = Field(..., min_length=1, max_length=500)
    keywords: Optional[str] = Field(
        default=None,
        description="Comma-separated keywords"
    )
    tone: Optional[str] = Field(default="professional")
    content_type: Optional[str] = Field(default="blog")
    custom_instructions: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("topic", mode="before")
    @classmethod
    def sanitize_topic(cls, v):
        """Sanitize topic field to prevent CSV formula injection."""
        if v is None:
            return v
        v = str(v).strip()
        # Strip formula injection characters from start
        while v and v[0] in CSV_FORMULA_CHARS:
            v = v[1:].strip()
        return v

    @field_validator("keywords", mode="before")
    @classmethod
    def parse_keywords(cls, v):
        """Parse comma-separated keywords with sanitization."""
        if v is None:
            return None
        if isinstance(v, list):
            v = ",".join(str(k) for k in v)
        v = str(v).strip()
        # Strip formula injection characters
        while v and v[0] in CSV_FORMULA_CHARS:
            v = v[1:].strip()
        return v

    @field_validator("custom_instructions", mode="before")
    @classmethod
    def sanitize_instructions(cls, v):
        """Sanitize custom instructions field."""
        if v is None:
            return None
        v = str(v).strip()
        # Strip formula injection characters
        while v and v[0] in CSV_FORMULA_CHARS:
            v = v[1:].strip()
        return v if v else None


class CSVExportRow(BaseModel):
    """Schema for CSV batch export rows."""
    index: int
    topic: str
    status: str
    title: Optional[str] = None
    content_preview: Optional[str] = Field(
        default=None,
        description="First 500 chars of content"
    )
    word_count: Optional[int] = None
    provider_used: Optional[str] = None
    execution_time_ms: int = 0
    error: Optional[str] = None


class BatchItemInput(BaseModel):
    """Single item in a batch request with security validation."""
    topic: str = Field(..., min_length=3, max_length=500)
    keywords: List[str] = Field(default_factory=list, max_length=20)
    tone: str = Field(default="professional", max_length=50)
    content_type: str = Field(default="blog", max_length=50)
    custom_instructions: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("topic", mode="before")
    @classmethod
    def sanitize_topic(cls, v):
        """Sanitize and validate topic."""
        if v is None:
            raise ValueError("Topic is required")
        v = str(v).strip()
        # Remove control characters
        v = "".join(char for char in v if char.isprintable() or char in "\n\t")
        if len(v) < 3:
            raise ValueError("Topic must be at least 3 characters")
        return v

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v):
        """Validate and sanitize keywords list."""
        if not v:
            return []
        validated = []
        for kw in v:
            if not kw or not kw.strip():
                continue
            kw = str(kw).strip().lower()
            # Remove control characters
            kw = "".join(char for char in kw if char.isprintable())
            # Enforce max keyword length
            if len(kw) > 50:
                kw = kw[:50]
            if kw:
                validated.append(kw)
        return validated[:20]  # Enforce max count

    @field_validator("custom_instructions", mode="before")
    @classmethod
    def sanitize_instructions(cls, v):
        """Sanitize custom instructions."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None
        # Remove control characters except newlines
        v = "".join(char for char in v if char.isprintable() or char == "\n")
        return v[:1000] if v else None


class EnhancedBatchRequest(BaseModel):
    """Enhanced batch generation request with security validation."""
    items: List[BatchItemInput] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Items to generate (max 100)"
    )

    # Provider configuration
    provider_strategy: ProviderStrategy = Field(
        default=ProviderStrategy.SINGLE,
        description="How to distribute work across providers"
    )
    preferred_provider: str = Field(
        default="openai",
        description="Preferred provider (openai, anthropic, gemini)"
    )
    fallback_providers: List[str] = Field(
        default_factory=lambda: ["anthropic", "gemini"],
        description="Fallback providers if primary fails"
    )

    # Processing options
    parallel_limit: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max parallel generations"
    )
    priority: JobPriority = Field(default=JobPriority.NORMAL)

    # Content options
    research_enabled: bool = Field(default=False)
    proofread_enabled: bool = Field(default=True)
    humanize_enabled: bool = Field(default=False)
    brand_profile_id: Optional[str] = Field(default=None, max_length=100)

    # Scheduling
    scheduled_at: Optional[datetime] = Field(default=None)

    # Metadata
    name: Optional[str] = Field(default=None, max_length=100)
    tags: List[str] = Field(default_factory=list, max_length=10)
    webhook_url: Optional[str] = Field(default=None, max_length=500)
    conversation_id: str = Field(..., min_length=1, max_length=100)

    @field_validator("preferred_provider")
    @classmethod
    def validate_preferred_provider(cls, v):
        """Validate provider against whitelist."""
        if not v:
            return "openai"
        v = str(v).lower().strip()
        if v not in ALLOWED_PROVIDERS:
            raise ValueError(
                f"Invalid provider '{v}'. Allowed: {', '.join(sorted(ALLOWED_PROVIDERS))}"
            )
        return v

    @field_validator("fallback_providers")
    @classmethod
    def validate_fallback_providers(cls, v):
        """Validate fallback providers against whitelist."""
        if not v:
            return []
        validated = []
        for provider in v:
            provider = str(provider).lower().strip()
            if provider in ALLOWED_PROVIDERS:
                validated.append(provider)
        return validated

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v):
        """Validate webhook URL for SSRF protection."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None

        # Import validator here to avoid circular imports
        try:
            from app.validators import validate_url
            is_valid, error = validate_url(v, resolve_dns=False)
            if not is_valid:
                raise ValueError(f"Invalid webhook URL: {error}")
        except ImportError:
            # Fallback validation if validators not available
            from urllib.parse import urlparse
            parsed = urlparse(v)
            if parsed.scheme not in ("http", "https"):
                raise ValueError("Webhook URL must use http or https")
            if not parsed.hostname:
                raise ValueError("Webhook URL must include hostname")
            blocked = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254"}
            if parsed.hostname.lower() in blocked:
                raise ValueError("Webhook URL hostname not allowed")
        return v

    @field_validator("brand_profile_id")
    @classmethod
    def validate_brand_profile_id(cls, v):
        """Validate brand profile ID format."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None
        # Only allow alphanumeric, dash, underscore
        import re
        if not re.match(r"^[a-zA-Z0-9_-]{1,100}$", v):
            raise ValueError("Invalid brand profile ID format")
        return v

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v):
        """Validate conversation ID format."""
        if not v or not v.strip():
            raise ValueError("Conversation ID is required")
        v = str(v).strip()
        # Only allow alphanumeric, dash, underscore
        import re
        if not re.match(r"^[a-zA-Z0-9_-]{1,100}$", v):
            raise ValueError("Invalid conversation ID format")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate and sanitize tags."""
        if not v:
            return []
        validated = []
        for tag in v:
            tag = str(tag).strip().lower()
            # Remove special characters
            tag = "".join(char for char in tag if char.isalnum() or char in "-_")
            if tag and len(tag) <= 50:
                validated.append(tag)
        return validated[:10]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {"topic": "AI in Healthcare", "keywords": ["AI", "healthcare"]},
                    {"topic": "Sustainable Tech", "keywords": ["green", "sustainability"]}
                ],
                "provider_strategy": "round_robin",
                "parallel_limit": 5,
                "research_enabled": True,
                "conversation_id": "conv-123"
            }
        }
    )


class EnhancedBatchItemResult(BaseModel):
    """Enhanced result for a single batch item."""
    index: int
    item_id: str = Field(default_factory=lambda: str(uuid4()))
    status: JobStatus = Field(default=JobStatus.PENDING)
    topic: str

    # Results
    content: Optional[Dict[str, Any]] = Field(default=None)
    error: Optional[str] = Field(default=None)
    retry_count: int = Field(default=0)

    # Execution metadata
    provider_used: Optional[str] = Field(default=None)
    execution_time_ms: int = Field(default=0)
    token_count: int = Field(default=0)
    cost_usd: float = Field(default=0.0)

    started_at: Optional[str] = Field(default=None)
    completed_at: Optional[str] = Field(default=None)


class EnhancedBatchStatus(BaseModel):
    """Enhanced batch job status with Tier 1 features."""
    job_id: str
    name: Optional[str] = None
    status: JobStatus = Field(default=JobStatus.PENDING)

    # Progress
    total_items: int
    completed_items: int = 0
    failed_items: int = 0
    progress_percentage: float = 0.0

    # Provider tracking
    provider_strategy: ProviderStrategy = ProviderStrategy.SINGLE
    providers_used: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of items per provider"
    )

    # Cost tracking
    estimated_cost_usd: float = Field(default=0.0)
    actual_cost_usd: float = Field(default=0.0)
    total_tokens_used: int = Field(default=0)

    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Control
    can_cancel: bool = True
    can_retry_failed: bool = False
    priority: JobPriority = JobPriority.NORMAL


class RetryRequest(BaseModel):
    """Request to retry failed items in a batch job."""
    item_indices: Optional[List[int]] = Field(
        default=None,
        description="Specific items to retry (empty = all failed)"
    )
    change_provider: Optional[str] = Field(
        default=None,
        description="Use different provider for retry"
    )


def estimate_batch_cost(
    items: List[BatchItemInput],
    provider: str = "openai",
    strategy: ProviderStrategy = ProviderStrategy.SINGLE,
    research_enabled: bool = False,
) -> CostEstimate:
    """
    Estimate cost for a batch job.

    Args:
        items: List of items to generate
        provider: Primary provider
        strategy: Distribution strategy
        research_enabled: Whether research is enabled (adds tokens)

    Returns:
        CostEstimate with breakdown
    """
    total_input_tokens = 0
    total_output_tokens = 0

    for item in items:
        content_type = item.content_type
        tokens = ESTIMATED_TOKENS.get(content_type, ESTIMATED_TOKENS["blog"])

        input_tokens = tokens["input"]
        output_tokens = tokens["output"]

        # Research adds ~500 input tokens for context
        if research_enabled:
            input_tokens += 500

        # Keywords add tokens
        input_tokens += len(item.keywords) * 10

        total_input_tokens += input_tokens
        total_output_tokens += output_tokens

    # Calculate costs per provider
    cost_breakdown = {}
    provider_recommendations = []

    for prov_name, costs in PROVIDER_COSTS.items():
        input_cost = (total_input_tokens / 1000) * costs["input"]
        output_cost = (total_output_tokens / 1000) * costs["output"]
        total_cost = input_cost + output_cost
        cost_breakdown[prov_name] = round(total_cost, 4)

        provider_recommendations.append({
            "provider": prov_name,
            "display_name": costs["name"],
            "estimated_cost": round(total_cost, 4),
            "input_cost": round(input_cost, 4),
            "output_cost": round(output_cost, 4),
        })

    # Sort recommendations by cost
    provider_recommendations.sort(key=lambda x: x["estimated_cost"])

    # Calculate primary cost based on strategy
    if strategy == ProviderStrategy.COST_OPTIMIZED:
        # Use cheapest provider
        estimated_cost = min(cost_breakdown.values())
    elif strategy == ProviderStrategy.ROUND_ROBIN:
        # Average across all providers
        estimated_cost = sum(cost_breakdown.values()) / len(cost_breakdown)
    else:
        # Use selected provider
        estimated_cost = cost_breakdown.get(provider, cost_breakdown["openai"])

    return CostEstimate(
        estimated_input_tokens=total_input_tokens,
        estimated_output_tokens=total_output_tokens,
        estimated_cost_usd=round(estimated_cost, 4),
        cost_breakdown=cost_breakdown,
        confidence=0.8 if not research_enabled else 0.7,
        provider_recommendations=provider_recommendations,
    )
