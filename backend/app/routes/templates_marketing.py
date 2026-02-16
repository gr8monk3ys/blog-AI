"""
API routes for the marketing copy template library.

Provides endpoints for:
- Listing all marketing templates with optional category filtering
- Listing template categories with counts
- Getting single template details
- Generating content from a template using an LLM provider
"""

import asyncio
import logging
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from ..auth import verify_api_key
from ..error_handlers import sanitize_error_message
from ..middleware import increment_usage_for_operation, require_quota
from src.templates.template_engine import (
    generate_from_template,
    get_all_templates,
    get_categories,
    get_template,
    get_templates_by_category,
)
from src.types.providers import GenerationOptions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates/marketing", tags=["marketing-templates"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class GenerationOptionsRequest(BaseModel):
    """Validated generation options for LLM providers."""

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0-2.0)",
    )
    max_tokens: int = Field(
        default=2000,
        gt=0,
        le=16000,
        description="Maximum tokens to generate",
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Top-p sampling (0.0-1.0)",
    )
    frequency_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty (-2.0 to 2.0)",
    )
    presence_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty (-2.0 to 2.0)",
    )


class TemplateGenerateRequest(BaseModel):
    """Request body for generating content from a marketing template."""

    fields: Dict[str, Any] = Field(
        ...,
        description="Template field values keyed by field name",
    )
    provider_type: Literal["openai", "anthropic", "gemini"] = Field(
        default="openai",
        description="LLM provider to use",
    )
    options: Optional[GenerationOptionsRequest] = Field(
        default=None,
        description="Generation options with validated ranges",
    )

    @field_validator("fields")
    @classmethod
    def validate_fields_not_empty(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not v:
            raise ValueError("fields must not be empty")
        return v


class CategoryResponse(BaseModel):
    """A single template category."""

    id: str
    name: str
    description: str
    icon: str
    template_count: int


class TemplateSummaryResponse(BaseModel):
    """Summary of a single template (without the raw prompt)."""

    id: str
    name: str
    category: str
    description: str
    fields: List[Dict[str, Any]]
    output_format: Dict[str, str]
    char_limits: Dict[str, int]


class TemplateListResponse(BaseModel):
    """Response containing a list of templates."""

    success: bool = True
    data: List[TemplateSummaryResponse]
    total: int


class TemplateDetailResponse(BaseModel):
    """Full template detail including prompt template."""

    success: bool = True
    data: Dict[str, Any]


class TemplateGenerateResponse(BaseModel):
    """Response from template content generation."""

    success: bool
    template_id: str
    output: Any = None
    raw_text: str = ""
    execution_time_ms: int = 0
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=TemplateListResponse,
    responses={
        400: {"description": "Invalid category filter"},
    },
)
async def list_marketing_templates(
    category: Optional[str] = Query(
        None,
        description="Filter by category slug (e.g. advertising, email, product)",
    ),
    search: Optional[str] = Query(
        None,
        description="Search templates by name or description",
    ),
    user_id: str = Depends(verify_api_key),
) -> TemplateListResponse:
    """
    List all marketing copy templates.

    Optionally filter by category or search by name/description.
    Returns template metadata without the raw prompt template.
    """
    try:
        if category:
            templates = get_templates_by_category(category)
        else:
            templates = get_all_templates()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": sanitize_error_message(str(exc)), "success": False},
        )

    # Apply search filter if provided
    if search:
        term = search.lower()
        templates = [
            t for t in templates
            if term in t["name"].lower() or term in t["description"].lower()
        ]

    return TemplateListResponse(
        success=True,
        data=templates,
        total=len(templates),
    )


@router.get(
    "/categories",
    response_model=List[CategoryResponse],
)
async def list_template_categories(
    user_id: str = Depends(verify_api_key),
) -> List[CategoryResponse]:
    """
    List all template categories with metadata and template counts.
    """
    categories = get_categories()
    return [CategoryResponse(**cat) for cat in categories]


@router.get(
    "/{template_id}",
    response_model=TemplateDetailResponse,
    responses={
        404: {"description": "Template not found"},
    },
)
async def get_template_detail(
    template_id: str,
    user_id: str = Depends(verify_api_key),
) -> TemplateDetailResponse:
    """
    Get full details of a specific marketing template.

    Returns the complete template definition including field schemas,
    prompt template, output format, and character limits.
    """
    try:
        template = get_template(template_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Template not found: {template_id}", "success": False},
        )

    return TemplateDetailResponse(success=True, data=template)


@router.post(
    "/{template_id}/generate",
    response_model=TemplateGenerateResponse,
    responses={
        400: {"description": "Invalid fields or validation error"},
        404: {"description": "Template not found"},
        422: {"description": "Generation failed"},
        500: {"description": "Internal server error"},
    },
)
async def generate_template_content(
    template_id: str,
    request: TemplateGenerateRequest,
    user_id: str = Depends(require_quota),
) -> TemplateGenerateResponse:
    """
    Generate marketing copy from a template.

    Fills the template prompt with the supplied fields and calls the
    selected LLM provider. Returns the generated content parsed as
    structured JSON when possible, with the raw text as a fallback.
    """
    # Verify the template exists before attempting generation
    try:
        get_template(template_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Template not found: {template_id}", "success": False},
        )

    # Build GenerationOptions from the validated request
    gen_options: Optional[GenerationOptions] = None
    if request.options:
        gen_options = GenerationOptions(
            temperature=request.options.temperature,
            max_tokens=request.options.max_tokens,
            top_p=request.options.top_p,
            frequency_penalty=request.options.frequency_penalty,
            presence_penalty=request.options.presence_penalty,
        )

    # Run synchronous generation in a thread pool to avoid blocking
    try:
        result = await asyncio.to_thread(
            generate_from_template,
            template_id=template_id,
            fields=request.fields,
            provider_type=request.provider_type,
            options=gen_options,
        )
    except Exception as exc:
        logger.error(
            "Unexpected error generating template %s: %s",
            template_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Generation failed unexpectedly", "success": False},
        )

    if not result["success"]:
        error_msg = result.get("error", "Unknown generation error")
        # Return 400 for validation errors, 422 for generation failures
        if "Validation errors" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": sanitize_error_message(error_msg), "success": False},
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": sanitize_error_message(error_msg),
                "success": False,
                "template_id": template_id,
                "execution_time_ms": result.get("execution_time_ms", 0),
            },
        )

    # Increment quota usage after successful generation
    await increment_usage_for_operation(
        user_id=user_id,
        operation_type="template",
        tokens_used=0,
        metadata={
            "template_id": template_id,
            "provider_type": request.provider_type,
        },
    )

    return TemplateGenerateResponse(
        success=True,
        template_id=result["template_id"],
        output=result["output"],
        raw_text=result["raw_text"],
        execution_time_ms=result["execution_time_ms"],
        error=None,
    )
