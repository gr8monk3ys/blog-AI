"""
Chrome Extension API endpoints.

Provides simplified endpoints for the Blog AI Chrome extension:
- Authentication validation
- User information
- Content generation (blog, outline, summary, expand)
- Usage statistics
"""

import asyncio
import logging
from datetime import datetime
from functools import partial
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.blog.make_blog import (
    BlogGenerationError,
    generate_blog_post,
    generate_blog_post_with_research,
    post_process_blog_post,
)
from src.config import get_settings
from src.planning.content_outline import generate_content_outline
from src.text_generation.core import (
    GenerationOptions,
    RateLimitError,
    TextGenerationError,
    create_provider_from_env,
    generate_text,
)
from src.types.providers import ProviderType

from ..auth import api_key_store, verify_api_key
from ..error_handlers import sanitize_error_message
from ..middleware import increment_usage_for_operation, require_quota
from src.usage.quota_service import get_usage_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extension", tags=["extension"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ExtensionAuthRequest(BaseModel):
    """Request model for extension authentication."""

    api_key: str = Field(..., min_length=1, description="API key to validate")


class ExtensionAuthResponse(BaseModel):
    """Response model for extension authentication."""

    success: bool
    email: Optional[str] = None
    user_id: Optional[str] = None
    tier: Optional[str] = None
    message: Optional[str] = None


class ExtensionUserResponse(BaseModel):
    """Response model for user information."""

    success: bool
    user_id: str
    email: Optional[str] = None
    tier: str = "free"
    quota_used: int = 0
    quota_limit: int = 100
    quota_remaining: int = 100


class ExtensionGenerateRequest(BaseModel):
    """Request model for extension content generation."""

    topic: str = Field(..., min_length=1, max_length=5000, description="Topic or text to generate from")
    tone: str = Field(default="professional", description="Writing tone")
    target_length: int = Field(default=1000, ge=100, le=5000, description="Target word count")
    keywords: List[str] = Field(default_factory=list, description="SEO keywords")
    research: bool = Field(default=False, description="Include web research")
    proofread: bool = Field(default=True, description="Proofread content")
    provider_type: Optional[ProviderType] = Field(
        default=None,
        description="LLM provider to use (openai, anthropic, gemini). Defaults to the deployment default.",
    )
    action: Literal["blog", "outline", "summary", "expand"] = Field(
        default="blog", description="Generation action type"
    )


class ExtensionGenerateResponse(BaseModel):
    """Response model for content generation."""

    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class ExtensionUsageResponse(BaseModel):
    """Response model for usage statistics."""

    success: bool
    generations_used: int = 0
    generations_limit: int = 100
    generations_remaining: int = 100
    tokens_used: int = 0
    reset_date: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/auth",
    response_model=ExtensionAuthResponse,
    summary="Validate API key for extension",
    description="Validates an API key and returns user information for the Chrome extension.",
    responses={
        200: {"description": "API key validation result"},
        400: {"description": "Invalid request"},
    },
)
async def extension_auth(request: ExtensionAuthRequest):
    """
    Validate API key for the Chrome extension.

    This endpoint is used by the extension to verify the API key
    and retrieve basic user information.
    """
    try:
        # Verify the API key
        user_id = api_key_store.verify_key(request.api_key)

        if user_id:
            logger.info(f"Extension auth successful for user: {user_id}")
            return ExtensionAuthResponse(
                success=True,
                user_id=user_id,
                email=f"{user_id}@blogai.com",  # Placeholder - replace with actual user lookup
                tier="pro",  # Placeholder - replace with actual tier lookup
                message="Authentication successful",
            )
        logger.warning("Extension auth failed: Invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extension auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        )


def _resolve_provider(provider_type: Optional[str]) -> str:
    settings = get_settings()
    provider = (provider_type or settings.llm.default_provider or "openai").strip().lower()
    allowed = {"openai", "anthropic", "gemini"}
    if provider not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider '{provider}'. Allowed: {', '.join(sorted(allowed))}",
        )

    configured = settings.llm.available_providers
    if configured and provider not in configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": f"Provider '{provider}' is not configured for this deployment",
                "configured_providers": configured,
            },
        )

    return provider


@router.get(
    "/user",
    response_model=ExtensionUserResponse,
    summary="Get user information for extension",
    description="Returns user information and quota status for the Chrome extension.",
    responses={
        200: {"description": "User information"},
        401: {"description": "Unauthorized"},
    },
)
async def extension_user(user_id: str = Depends(verify_api_key)):
    """
    Get user information for the Chrome extension.

    Returns user details including quota usage.
    """
    try:
        # Get usage stats
        usage = await get_usage_stats(user_id)

        return ExtensionUserResponse(
            success=True,
            user_id=user_id,
            email=f"{user_id}@blogai.com",  # Placeholder
            tier="pro",  # Placeholder
            quota_used=usage.get("generations_used", 0),
            quota_limit=usage.get("generations_limit", 100),
            quota_remaining=usage.get("generations_remaining", 100),
        )
    except Exception as e:
        logger.error(f"Extension user info error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information",
        )


@router.post(
    "/generate",
    response_model=ExtensionGenerateResponse,
    summary="Generate content from extension",
    description="""
Generate AI-powered content from the Chrome extension.

Supports multiple generation types:
- **blog**: Generate a full blog post
- **outline**: Generate a content outline
- **summary**: Summarize the provided text
- **expand**: Expand short text into a longer article
    """,
    responses={
        200: {"description": "Generated content"},
        400: {"description": "Invalid request"},
        401: {"description": "Unauthorized"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Generation error"},
    },
)
async def extension_generate(
    request: ExtensionGenerateRequest,
    user_id: str = Depends(require_quota),
):
    """
    Generate content for the Chrome extension.

    Handles multiple generation types with simplified parameters.
    """
    logger.info(f"Extension generate: action={request.action}, user={user_id}")

    try:
        provider_type = _resolve_provider(request.provider_type)

        # Create generation options
        options = GenerationOptions(
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9,
        )

        result = None

        if request.action == "blog":
            result = await _generate_blog(request, options, provider_type)
        elif request.action == "outline":
            result = await _generate_outline(request, options, provider_type)
        elif request.action == "summary":
            result = await _generate_summary(request, options, provider_type)
        elif request.action == "expand":
            result = await _generate_expansion(request, options, provider_type)
        else:
            raise ValueError(f"Unknown action: {request.action}")

        # Track usage
        await increment_usage_for_operation(
            user_id=user_id,
            operation_type=f"extension_{request.action}",
            tokens_used=2000,  # Estimated
            metadata={"source": "chrome_extension", "action": request.action},
        )

        logger.info(f"Extension generation successful: {request.action}")

        return ExtensionGenerateResponse(
            success=True,
            data=result,
        )

    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded: {str(e)}")
        wait_time = getattr(e, "wait_time", None)
        message = (
            f"Rate limit exceeded. Please wait {wait_time:.0f}s before retrying."
            if isinstance(wait_time, (int, float))
            else "Rate limit exceeded. Please try again shortly."
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message,
        )
    except TextGenerationError as e:
        logger.error(f"Text generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate content. Please try again.",
        )
    except BlogGenerationError as e:
        logger.error(f"Blog generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate blog post. Please try again.",
        )
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=sanitize_error_message(str(e)),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extension generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        )


@router.get(
    "/usage",
    response_model=ExtensionUsageResponse,
    summary="Get usage statistics for extension",
    description="Returns usage statistics and quota information for the Chrome extension.",
    responses={
        200: {"description": "Usage statistics"},
        401: {"description": "Unauthorized"},
    },
)
async def extension_usage(user_id: str = Depends(verify_api_key)):
    """
    Get usage statistics for the Chrome extension.

    Returns generation counts and quota information.
    """
    try:
        usage = await get_usage_stats(user_id)

        return ExtensionUsageResponse(
            success=True,
            generations_used=usage.get("generations_used", 0),
            generations_limit=usage.get("generations_limit", 100),
            generations_remaining=usage.get("generations_remaining", 100),
            tokens_used=usage.get("tokens_used", 0),
            reset_date=usage.get("reset_date"),
        )
    except Exception as e:
        logger.error(f"Extension usage error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics",
        )


# =============================================================================
# Generation Helpers
# =============================================================================


async def _generate_blog(request: ExtensionGenerateRequest, options: GenerationOptions, provider_type: str) -> dict:
    """Generate a blog post."""
    def _generate():
        if request.research:
            return generate_blog_post_with_research(
                title=request.topic[:200],  # Limit title length
                keywords=request.keywords[:10],  # Limit keywords
                tone=request.tone,
                provider_type=provider_type,
                options=options,
            )
        return generate_blog_post(
            title=request.topic[:200],  # Limit title length
            keywords=request.keywords[:10],  # Limit keywords
            tone=request.tone,
            provider_type=provider_type,
            options=options,
        )

    blog_post = await asyncio.to_thread(_generate)

    # Post-process if requested
    if request.proofread:
        provider = await asyncio.to_thread(create_provider_from_env, provider_type)
        blog_post = await asyncio.to_thread(
            partial(
                post_process_blog_post,
                blog_post=blog_post,
                proofread=True,
                humanize=False,
                provider=provider,
                options=options,
            )
        )

    # Convert to dict
    return {
        "title": blog_post.title,
        "description": blog_post.description,
        "date": blog_post.date,
        "tags": blog_post.tags,
        "sections": [
            {
                "title": section.title,
                "subtopics": [
                    {"title": subtopic.title, "content": subtopic.content}
                    for subtopic in section.subtopics
                ],
            }
            for section in blog_post.sections
        ],
    }


async def _generate_outline(request: ExtensionGenerateRequest, options: GenerationOptions, provider_type: str) -> dict:
    """Generate a content outline."""
    # Determine number of sections based on target length
    num_sections = 3 if request.target_length < 1000 else 5 if request.target_length < 2000 else 7

    provider = await asyncio.to_thread(create_provider_from_env, provider_type)
    outline = await asyncio.to_thread(
        partial(
            generate_content_outline,
            title=request.topic[:200],
            num_sections=num_sections,
            provider=provider,
            options=options,
        )
    )

    return {
        "title": f"Outline: {request.topic[:100]}",
        "description": f"Content outline for '{request.topic[:100]}'",
        "sections": [
            {
                "title": section.title,
                "subtopics": [
                    {"title": subtopic.title, "content": subtopic.description or ""}
                    for subtopic in section.subtopics
                ],
            }
            for section in outline.sections
        ],
    }


async def _generate_summary(request: ExtensionGenerateRequest, options: GenerationOptions, provider_type: str) -> dict:
    """Generate a text summary."""
    # Limit summary length
    max_words = min(request.target_length, 300)

    prompt = f"""Summarize the following text in approximately {max_words} words.
Maintain the key points and essential information.
Write in a {request.tone} tone.

Text to summarize:
{request.topic}

Summary:"""

    provider = await asyncio.to_thread(create_provider_from_env, provider_type)

    summary = await asyncio.to_thread(
        generate_text,
        provider=provider,
        prompt=prompt,
        options=GenerationOptions(
            temperature=0.5,
            max_tokens=1000,
        ),
    )

    return {
        "title": "Summary",
        "description": "AI-generated summary of the provided text",
        "content": summary.strip(),
        "sections": [
            {
                "title": "Summary",
                "subtopics": [{"title": "", "content": summary.strip()}],
            }
        ],
    }


async def _generate_expansion(request: ExtensionGenerateRequest, options: GenerationOptions, provider_type: str) -> dict:
    """Expand short text into a longer article."""
    prompt = f"""Expand the following text into a comprehensive article of approximately {request.target_length} words.
Add relevant details, examples, and explanations while maintaining the original meaning and intent.
Write in a {request.tone} tone.
{f"Include these keywords naturally: {', '.join(request.keywords[:5])}" if request.keywords else ""}

Original text:
{request.topic}

Expanded article:"""

    provider = await asyncio.to_thread(create_provider_from_env, provider_type)

    expanded = await asyncio.to_thread(
        generate_text,
        provider=provider,
        prompt=prompt,
        options=GenerationOptions(
            temperature=0.7,
            max_tokens=4000,
        ),
    )

    # Parse expanded content into sections
    paragraphs = [p.strip() for p in expanded.split("\n\n") if p.strip()]

    # Group paragraphs into sections
    sections = []
    current_section = {"title": "Introduction", "subtopics": []}

    for i, para in enumerate(paragraphs):
        if para.startswith("#") or (len(para) < 100 and para.endswith(":")):
            # This looks like a heading
            if current_section["subtopics"]:
                sections.append(current_section)
            current_section = {
                "title": para.lstrip("#").strip().rstrip(":"),
                "subtopics": [],
            }
        else:
            current_section["subtopics"].append({"title": "", "content": para})

    if current_section["subtopics"]:
        sections.append(current_section)

    # Ensure we have at least one section
    if not sections:
        sections = [
            {
                "title": "Article",
                "subtopics": [{"title": "", "content": expanded.strip()}],
            }
        ]

    return {
        "title": f"Expanded: {request.topic[:50]}...",
        "description": f"Expanded article based on: {request.topic[:100]}",
        "sections": sections,
    }
