"""
API routes for the tool registry system.

This module provides endpoints for:
- Listing all available tools
- Getting tool details and schemas
- Executing tools
- Filtering tools by category
- Scoring generated content
- Generating content variations (A/B testing)
"""

import asyncio
import logging
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from ..auth import verify_api_key
from ..error_handlers import sanitize_error_message
from ..middleware import increment_usage_for_operation, require_quota

from src.scoring import score_content
from src.tools import (
    ToolCategory,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolListResponse,
    get_registry,
)
from src.types.scoring import (
    ContentScoreRequest,
    ContentScoreResult,
    VariationGenerationRequest,
    VariationGenerationResult,
)
from src.types.tools import CategoryInfo, ToolDefinition, ToolMetadata
from src.types.usage import QuotaExceededError
from src.usage.quota_service import get_usage_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["tools"])


class GenerationOptionsRequest(BaseModel):
    """Validated generation options for LLM providers."""

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0-2.0)"
    )
    max_tokens: int = Field(
        default=2000,
        gt=0,
        le=16000,
        description="Maximum tokens to generate"
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Top-p sampling (0.0-1.0)"
    )
    frequency_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty (-2.0 to 2.0)"
    )
    presence_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty (-2.0 to 2.0)"
    )


class ToolExecuteRequest(BaseModel):
    """Request body for tool execution."""

    inputs: dict = Field(..., description="Tool input values")
    brand_profile_id: Optional[str] = Field(
        default=None,
        description="Brand profile UUID to apply a trained brand voice",
        max_length=100,
    )
    provider_type: Literal["openai", "anthropic", "gemini"] = Field(
        default="openai",
        description="LLM provider to use (openai, anthropic, or gemini)"
    )
    options: Optional[GenerationOptionsRequest] = Field(
        default=None,
        description="Generation options with validated ranges"
    )

    @field_validator("brand_profile_id")
    @classmethod
    def validate_brand_profile_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None
        import re

        if not re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            v,
            re.IGNORECASE,
        ):
            raise ValueError("brand_profile_id must be a valid UUID")
        return v


@router.get("", response_model=ToolListResponse)
async def list_tools(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search term"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    include_premium: bool = Query(True, description="Include premium tools"),
    include_beta: bool = Query(True, description="Include beta tools"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    user_id: str = Depends(verify_api_key),
):
    """
    List all available tools with optional filtering.

    - Filter by category (blog, email, social, etc.)
    - Search by name, description, or tags
    - Filter by tags
    - Paginate results
    """
    registry = get_registry()

    # Auto-discover tools if registry is empty
    if len(registry._tools) == 0:
        registry.auto_discover()

    # Parse category if provided
    category_enum = None
    if category:
        try:
            category_enum = ToolCategory(category.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {category}. Valid categories: {[c.value for c in ToolCategory]}"
            )

    # Parse tags if provided
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    return registry.list_tools(
        category=category_enum,
        tags=tag_list,
        search=search,
        include_premium=include_premium,
        include_beta=include_beta,
        limit=limit,
        offset=offset,
    )


@router.get("/categories", response_model=List[CategoryInfo])
async def list_categories(
    user_id: str = Depends(verify_api_key),
):
    """
    List all tool categories with their metadata and tool counts.
    """
    registry = get_registry()

    # Auto-discover if needed
    if len(registry._tools) == 0:
        registry.auto_discover()

    return registry.list_categories()


@router.get("/stats")
async def get_stats(
    user_id: str = Depends(verify_api_key),
):
    """
    Get statistics about the tool registry.
    """
    registry = get_registry()

    # Auto-discover if needed
    if len(registry._tools) == 0:
        registry.auto_discover()

    return registry.get_stats()


@router.get("/{tool_id}", response_model=ToolDefinition)
async def get_tool(
    tool_id: str,
    user_id: str = Depends(verify_api_key),
):
    """
    Get detailed information about a specific tool.

    Returns the complete tool definition including:
    - Metadata (name, description, category)
    - Input schema (all input fields)
    - Output schema
    - Prompt template
    - Examples
    """
    registry = get_registry()

    # Auto-discover if needed
    if len(registry._tools) == 0:
        registry.auto_discover()

    if not registry.has_tool(tool_id):
        raise HTTPException(
            status_code=404,
            detail=f"Tool not found: {tool_id}"
        )

    return registry.get_definition(tool_id)


@router.post("/{tool_id}/execute", response_model=ToolExecutionResult)
async def execute_tool(
    tool_id: str,
    request: ToolExecuteRequest,
    user_id: str = Depends(require_quota),
):
    """
    Execute a tool with the provided inputs.

    The inputs must match the tool's input schema. The response includes:
    - success: Whether execution succeeded
    - output: The generated content
    - execution_time_ms: Time taken
    - error: Error message if failed
    """
    registry = get_registry()

    # Auto-discover if needed
    if len(registry._tools) == 0:
        registry.auto_discover()

    if not registry.has_tool(tool_id):
        raise HTTPException(
            status_code=404,
            detail=f"Tool not found: {tool_id}"
        )

    # Build execution request with validated options
    options_dict = None
    if request.options:
        options_dict = {
            "temperature": request.options.temperature,
            "max_tokens": request.options.max_tokens,
            "top_p": request.options.top_p,
            "frequency_penalty": request.options.frequency_penalty,
            "presence_penalty": request.options.presence_penalty,
        }

    inputs = dict(request.inputs or {})
    # If a brand profile is provided, load the trained fingerprint summary and
    # inject it as `brand_voice` so tools can either use it explicitly or we can
    # append it as a generic instruction (see BaseTool).
    if request.brand_profile_id:
        try:
            from src.brand.storage import get_brand_voice_storage

            storage = get_brand_voice_storage()
            fingerprint = await storage.get_fingerprint(user_id, request.brand_profile_id)
            if fingerprint and fingerprint.voice_summary and not inputs.get("brand_voice"):
                inputs["brand_voice"] = fingerprint.voice_summary
        except Exception as e:
            logger.debug("Failed to load brand voice fingerprint: %s", e)

    exec_request = ToolExecutionRequest(
        tool_id=tool_id,
        inputs=inputs,
        provider_type=request.provider_type,
        options=options_dict,
    )

    # Execute the tool
    result = await asyncio.to_thread(registry.execute, exec_request)

    if not result.success:
        logger.warning(f"Tool execution failed: {tool_id} - {result.error}")
        # Return 422 Unprocessable Entity for execution failures
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "output": None,
                "execution_time_ms": result.execution_time_ms,
                "error": result.error,
                "tool_id": result.tool_id,
            }
        )

    # Increment quota usage after successful generation
    await increment_usage_for_operation(
        user_id=user_id,
        operation_type="tool",
        tokens_used=int(result.tokens_used or 0),
        metadata={
            "tool_id": tool_id,
            "provider_type": request.provider_type,
            "brand_profile_id": request.brand_profile_id,
        },
    )

    return result


@router.get("/category/{category}", response_model=List[ToolMetadata])
async def get_tools_by_category(
    category: str,
    user_id: str = Depends(verify_api_key),
):
    """
    Get all tools in a specific category.
    """
    registry = get_registry()

    # Auto-discover if needed
    if len(registry._tools) == 0:
        registry.auto_discover()

    try:
        category_enum = ToolCategory(category.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {category}. Valid categories: {[c.value for c in ToolCategory]}"
        )

    return registry.get_tools_by_category(category_enum)


@router.post("/{tool_id}/validate")
async def validate_inputs(
    tool_id: str,
    inputs: dict,
    user_id: str = Depends(verify_api_key),
):
    """
    Validate inputs for a tool without executing it.

    Returns validation errors if any, or empty list if valid.
    """
    registry = get_registry()

    # Auto-discover if needed
    if len(registry._tools) == 0:
        registry.auto_discover()

    if not registry.has_tool(tool_id):
        raise HTTPException(
            status_code=404,
            detail=f"Tool not found: {tool_id}"
        )

    tool = registry.get_tool(tool_id)
    errors = tool.validate_inputs(inputs)

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


class ContentScoreRequestBody(BaseModel):
    """Request body for content scoring."""

    text: str = Field(..., min_length=1, description="Content to score")
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Target keywords for SEO analysis"
    )


@router.post("/{tool_id}/score", response_model=ContentScoreResult)
async def score_tool_content(
    tool_id: str,
    request: ContentScoreRequestBody,
    user_id: str = Depends(verify_api_key),
):
    """
    Score generated content for readability, SEO, and engagement.

    Returns comprehensive scoring with:
    - Overall score (0-100)
    - Readability metrics (Flesch-Kincaid)
    - SEO analysis (keyword density, structure)
    - Engagement analysis (hooks, CTAs, emotional words)
    - Improvement suggestions
    """
    registry = get_registry()

    # Auto-discover if needed
    if len(registry._tools) == 0:
        registry.auto_discover()

    if not registry.has_tool(tool_id):
        raise HTTPException(
            status_code=404,
            detail=f"Tool not found: {tool_id}"
        )

    # Get tool category for content type weighting
    tool = registry.get_tool(tool_id)
    definition = tool.get_definition()
    content_type = definition.metadata.category.value if hasattr(definition.metadata.category, 'value') else str(definition.metadata.category)

    # Score the content
    try:
        result = score_content(
            text=request.text,
            keywords=request.keywords,
            content_type=content_type,
        )
        return result
    except ValueError as e:
        logger.warning(f"Invalid content for scoring: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content: {sanitize_error_message(str(e))}"
        )
    except Exception as e:
        logger.error(f"Unexpected content scoring error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Scoring failed. Please try again."
        )


class VariationExecuteRequest(BaseModel):
    """Request body for generating content variations."""

    inputs: dict = Field(..., description="Tool input values")
    brand_profile_id: Optional[str] = Field(
        default=None,
        description="Brand profile UUID to apply a trained brand voice",
        max_length=100,
    )
    variation_count: int = Field(
        default=2,
        ge=2,
        le=3,
        description="Number of variations to generate (2-3)"
    )
    provider_type: Literal["openai", "anthropic", "gemini"] = Field(
        default="openai",
        description="LLM provider to use"
    )
    include_scores: bool = Field(
        default=True,
        description="Whether to include scores for each variation"
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords for SEO scoring"
    )

    @field_validator("brand_profile_id")
    @classmethod
    def validate_brand_profile_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None
        import re

        if not re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            v,
            re.IGNORECASE,
        ):
            raise ValueError("brand_profile_id must be a valid UUID")
        return v


@router.post("/{tool_id}/variations", response_model=VariationGenerationResult)
async def generate_variations(
    tool_id: str,
    request: VariationExecuteRequest,
    user_id: str = Depends(require_quota),
):
    """
    Generate multiple content variations for A/B testing.

    Each variation uses slightly different parameters:
    - Variation A: Standard temperature, default style
    - Variation B: Higher temperature, more creative style
    - Variation C: Lower temperature, more concise style

    Returns all variations with optional scores for comparison.
    """
    registry = get_registry()

    # Auto-discover if needed
    if len(registry._tools) == 0:
        registry.auto_discover()

    if not registry.has_tool(tool_id):
        raise HTTPException(
            status_code=404,
            detail=f"Tool not found: {tool_id}"
        )

    tool = registry.get_tool(tool_id)

    # Ensure the user has enough remaining quota for the number of requested
    # variations. We treat each variation as a generation.
    try:
        stats = await get_usage_stats(user_id)
        remaining = int(stats.remaining or 0)
        if remaining != -1 and remaining < int(request.variation_count or 2):
            err = QuotaExceededError(
                error=(
                    f"Not enough remaining quota to generate {request.variation_count} variations "
                    f"(remaining: {remaining}). Upgrade to continue."
                ),
                tier=stats.tier,
                current_usage=stats.current_usage,
                quota_limit=stats.quota_limit,
                reset_date=stats.reset_date,
            )
            raise HTTPException(status_code=429, detail=err.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Failed to validate remaining quota for variations: %s", e)

    inputs = dict(request.inputs or {})
    if request.brand_profile_id:
        try:
            from src.brand.storage import get_brand_voice_storage

            storage = get_brand_voice_storage()
            fingerprint = await storage.get_fingerprint(user_id, request.brand_profile_id)
            if fingerprint and fingerprint.voice_summary and not inputs.get("brand_voice"):
                inputs["brand_voice"] = fingerprint.voice_summary
        except Exception as e:
            logger.debug("Failed to load brand voice fingerprint: %s", e)

    # Execute variations
    result = await asyncio.to_thread(
        tool.execute_variations,
        inputs=inputs,
        variation_count=request.variation_count,
        provider_type=request.provider_type,
        include_scores=request.include_scores,
        keywords=request.keywords,
    )

    if not result.success:
        logger.warning(f"Variation generation failed: {tool_id} - {result.error}")
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "tool_id": result.tool_id,
                "variations": [],
                "error": result.error,
                "execution_time_ms": result.execution_time_ms,
            }
        )

    # Increment quota usage once per generated variation.
    generated_count = len(result.variations or [])
    for _ in range(generated_count):
        await increment_usage_for_operation(
            user_id=user_id,
            operation_type="tool",
            tokens_used=0,
            metadata={
                "tool_id": tool_id,
                "provider_type": request.provider_type,
                "variation": True,
                "requested_variations": request.variation_count,
                "generated_variations": generated_count,
                "brand_profile_id": request.brand_profile_id,
            },
        )

    return result


@router.post("/score", response_model=ContentScoreResult)
async def score_content_generic(
    request: ContentScoreRequestBody,
    user_id: str = Depends(verify_api_key),
):
    """
    Score any content without associating with a specific tool.

    Uses default blog content type weighting.
    """
    try:
        result = score_content(
            text=request.text,
            keywords=request.keywords,
            content_type="blog",
        )
        return result
    except ValueError as e:
        logger.warning(f"Invalid content for generic scoring: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content: {sanitize_error_message(str(e))}"
        )
    except Exception as e:
        logger.error(f"Unexpected content scoring error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Scoring failed. Please try again."
        )
