"""
Content Remix API Routes.

Endpoints for transforming content across multiple formats.

Authorization:
- Read-only operations (list formats, preview) require content.view permission
- Transform operations require content.create permission
- Pass the organization ID via X-Organization-ID header for org-scoped access
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.organizations import AuthorizationContext
from src.remix.service import get_remix_service
from src.types.remix import (
    ContentFormat,
    RemixRequest,
    RemixResponse,
    RemixPreviewRequest,
    RemixPreviewResponse,
    get_available_formats,
    get_format_info,
)

from ..auth import verify_api_key
from ..dependencies import require_content_access, require_content_creation
from ..error_handlers import sanitize_error_message
from ..middleware import increment_usage_for_operation, require_quota


router = APIRouter(prefix="/remix", tags=["Content Remix"])


# Request/Response models for the API
class RemixRequestAPI(BaseModel):
    """API request for content remix."""
    source_content: Dict[str, Any] = Field(
        ...,
        description="Source content to remix (blog post with title, body, etc.)"
    )
    target_formats: List[str] = Field(
        ...,
        description="Target format identifiers (e.g., 'twitter_thread', 'linkedin_post')"
    )
    preserve_voice: bool = Field(
        default=True,
        description="Preserve brand voice during transformation"
    )
    brand_profile_id: Optional[str] = Field(
        default=None,
        description="Brand profile ID for voice matching"
    )
    tone_override: Optional[str] = Field(
        default=None,
        description="Override tone (e.g., 'casual', 'professional')"
    )
    conversation_id: str = Field(
        ...,
        description="Conversation ID for tracking"
    )
    provider: str = Field(
        default="openai",
        description="LLM provider to use"
    )


class PreviewRequestAPI(BaseModel):
    """API request for remix preview."""
    source_content: Dict[str, Any] = Field(
        ...,
        description="Source content to preview"
    )
    target_format: str = Field(
        ...,
        description="Target format identifier"
    )


class FormatInfo(BaseModel):
    """Information about a content format."""
    format: str
    name: str
    icon: str
    description: str
    max_length: int
    platform: str
    supports_images: bool


class AnalyzeRequestAPI(BaseModel):
    """API request for content analysis only."""
    source_content: Dict[str, Any] = Field(
        ...,
        description="Source content to analyze"
    )
    provider: str = Field(
        default="openai",
        description="LLM provider to use"
    )


@router.get("/formats", response_model=List[FormatInfo])
async def list_formats():
    """
    Get all available content formats for remix.

    Returns metadata about each format including name, icon, description,
    max length, platform, and whether it supports images.
    """
    formats = get_available_formats()
    return [FormatInfo(**f) for f in formats]


@router.get("/formats/{format_id}", response_model=FormatInfo)
async def get_format(format_id: str):
    """
    Get information about a specific format.

    Args:
        format_id: The format identifier (e.g., 'twitter_thread')

    Returns format metadata including constraints and capabilities.
    """
    try:
        format_enum = ContentFormat(format_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Format '{format_id}' not found"
        )

    info = get_format_info(format_enum)
    return FormatInfo(format=format_id, **info)


@router.post("/analyze")
async def analyze_content(request: AnalyzeRequestAPI):
    """
    Analyze content without transformation.

    Returns content analysis including summary, key points,
    suggested formats, and content structure.
    """
    from src.remix.analyzer import ContentAnalyzer

    analyzer = ContentAnalyzer(request.provider)
    analysis = analyzer.analyze(request.source_content)

    return {
        "success": True,
        "analysis": analysis.model_dump(),
        "suggested_formats": [
            {
                "format": fmt.value,
                **get_format_info(fmt)
            }
            for fmt in analysis.suggested_formats
        ]
    }


@router.post("/preview", response_model=RemixPreviewResponse)
async def preview_remix(request: PreviewRequestAPI):
    """
    Preview how content will be transformed.

    Returns a quick preview without full generation, including:
    - Estimated length
    - Key elements that will be emphasized
    - Sample hook
    - Confidence score
    """
    try:
        format_enum = ContentFormat(request.target_format)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format: {request.target_format}"
        )

    service = get_remix_service()
    preview_request = RemixPreviewRequest(
        source_content=request.source_content,
        target_format=format_enum,
    )

    return await service.preview(preview_request)


@router.post("/transform", response_model=RemixResponse)
async def transform_content(
    request: RemixRequestAPI,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
):
    """
    Transform content into multiple formats.

    This is the main remix endpoint. It:
    1. Analyzes the source content
    2. Transforms to each requested format in parallel
    3. Scores quality of each transformation
    4. Returns all transformed content with metrics

    **Authorization:** Requires content.create permission in the organization.
    """
    # Use organization_id for scoping if available, fallback to user_id
    scope_id = auth_ctx.organization_id or auth_ctx.user_id
    user_id = auth_ctx.user_id
    # Validate formats
    target_formats = []
    for fmt_str in request.target_formats:
        try:
            target_formats.append(ContentFormat(fmt_str))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format: {fmt_str}"
            )

    if not target_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one target format is required"
        )

    if len(target_formats) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 formats per request"
        )

    # Create internal request
    remix_request = RemixRequest(
        source_content=request.source_content,
        target_formats=target_formats,
        preserve_voice=request.preserve_voice,
        brand_profile_id=request.brand_profile_id,
        tone_override=request.tone_override,
        conversation_id=request.conversation_id,
    )

    # Get service with specified provider
    service = get_remix_service(request.provider)

    result = await service.remix(remix_request)

    # Increment usage after successful transformation
    await increment_usage_for_operation(
        user_id=user_id,
        operation_type="remix",
        tokens_used=2000 * len(target_formats),  # Estimated tokens per format
        metadata={
            "formats": [f.value for f in target_formats],
            "format_count": len(target_formats),
        },
    )

    return result


@router.post("/transform/{format_id}")
async def transform_single_format(
    format_id: str,
    request: RemixRequestAPI,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
):
    """
    Transform content into a single format.

    Convenience endpoint for transforming to just one format.

    **Authorization:** Requires content.create permission in the organization.
    """
    try:
        format_enum = ContentFormat(format_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Format '{format_id}' not found"
        )

    # Override target formats
    request.target_formats = [format_id]

    return await transform_content(request, auth_ctx)


@router.post("/batch")
async def batch_transform(
    requests: List[RemixRequestAPI],
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
):
    """
    Transform multiple pieces of content in batch.

    Each request in the batch is processed independently.
    Returns results for all requests.

    **Authorization:** Requires content.create permission in the organization.
    """
    if len(requests) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 items per batch"
        )

    results = []
    for req in requests:
        try:
            result = await transform_content(req, auth_ctx)
            results.append({
                "success": True,
                "conversation_id": req.conversation_id,
                "result": result,
            })
        except HTTPException as e:
            results.append({
                "success": False,
                "conversation_id": req.conversation_id,
                "error": e.detail,
            })
        except ValueError as e:
            results.append({
                "success": False,
                "conversation_id": req.conversation_id,
                "error": f"Invalid input: {sanitize_error_message(str(e))}",
            })
        except Exception as e:
            results.append({
                "success": False,
                "conversation_id": req.conversation_id,
                "error": "Transformation failed unexpectedly",
            })

    return {
        "total": len(requests),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results,
    }
