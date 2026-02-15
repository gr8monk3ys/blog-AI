"""
Blog generation endpoints.

Authorization:
- Blog generation requires content.create permission in the organization
- Pass the organization ID via X-Organization-ID header for org-scoped access
"""

import asyncio
import logging
import uuid
from datetime import datetime
from functools import partial

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from src.blog.make_blog import (
    BlogGenerationError,
    generate_blog_post,
    generate_blog_post_with_research,
    post_process_blog_post,
)
from src.brand.storage import get_brand_voice_storage
from src.organizations import AuthorizationContext
from src.config import get_settings
from src.text_generation.core import (
    GenerationOptions,
    RateLimitError,
    TextGenerationError,
    create_provider_from_env,
)
from src.webhooks import webhook_service

from ..auth import verify_api_key
from ..dependencies import require_content_creation
from ..error_handlers import sanitize_error_message
from ..middleware import increment_usage_for_operation, require_quota
from ..models import BlogGenerationRequest
from ..storage import conversations
from ..websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["blog"])


@router.post(
    "/generate-blog",
    status_code=status.HTTP_201_CREATED,
    summary="Generate a blog post",
    description="""
Generate an AI-powered blog post on any topic.

The generated blog includes:
- SEO-optimized title and description
- Structured sections with subtopics
- Relevant tags
- Optional web research integration
- Proofreading and humanization passes

**Quota Usage**: Each blog generation counts as 1 generation toward your monthly limit.

**Authorization:** Requires content.create permission in the organization.
Pass the organization ID via X-Organization-ID header.
    """,
    responses={
        201: {
            "description": "Blog post generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "type": "blog",
                        "content": {
                            "title": "The Future of AI in Healthcare",
                            "description": "Explore how AI is transforming patient care...",
                            "date": "2024-01-24",
                            "tags": ["AI", "Healthcare"],
                            "sections": [
                                {
                                    "title": "Introduction",
                                    "subtopics": [
                                        {
                                            "title": "The AI Revolution",
                                            "content": "..."
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        401: {"description": "Missing or invalid API key"},
        403: {"description": "Insufficient permissions"},
        429: {"description": "Rate limit or quota exceeded"},
        502: {"description": "AI provider error"},
    }
)
async def generate_blog(
    request: BlogGenerationRequest,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
):
    """
    Generate a blog post.

    Args:
        request: The blog generation request parameters.
        auth_ctx: The authorization context with user and org info.

    Returns:
        The generated blog post content.
    """
    # Use organization_id for scoping if available, fallback to user_id
    scope_id = auth_ctx.organization_id or auth_ctx.user_id
    user_id = auth_ctx.user_id

    logger.info(
        f"Blog generation requested by user: {user_id[:8]}... "
        f"in org {auth_ctx.organization_id}, topic_length: {len(request.topic)}"
    )
    try:
        # Enforce quota before doing any expensive generation work.
        # We call the dependency directly so we reuse the already-authenticated user_id.
        await require_quota(user_id)

        settings = get_settings()
        provider_type = request.provider_type or settings.llm.default_provider or "openai"
        if provider_type not in settings.llm.available_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider not configured: {provider_type}",
            )
        # Create generation options
        options = GenerationOptions(
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        brand_voice = None
        if request.brand_profile_id:
            try:
                storage = get_brand_voice_storage()
                fingerprint = await storage.get_fingerprint(user_id, request.brand_profile_id)
                if fingerprint and fingerprint.voice_summary:
                    brand_voice = fingerprint.voice_summary
            except Exception as e:
                logger.debug("Failed to load brand voice fingerprint: %s", e)

        # Generate blog post (run sync functions in thread pool to avoid blocking)
        if request.research:
            blog_post = await asyncio.to_thread(
                partial(
                    generate_blog_post_with_research,
                    title=request.topic,
                    keywords=request.keywords,
                    tone=request.tone,
                    brand_voice=brand_voice,
                    provider_type=provider_type,
                    options=options,
                )
            )
        else:
            blog_post = await asyncio.to_thread(
                partial(
                    generate_blog_post,
                    title=request.topic,
                    keywords=request.keywords,
                    tone=request.tone,
                    brand_voice=brand_voice,
                    provider_type=provider_type,
                    options=options,
                )
            )

        # Post-process blog post (run sync functions in thread pool)
        if request.proofread or request.humanize:
            provider = await asyncio.to_thread(create_provider_from_env, provider_type)
            blog_post = await asyncio.to_thread(
                partial(
                    post_process_blog_post,
                    blog_post=blog_post,
                    proofread=request.proofread,
                    humanize=request.humanize,
                    provider=provider,
                    options=options,
                )
            )

        # Convert blog post to JSON-serializable format
        blog_post_data = {
            "title": blog_post.title,
            "description": blog_post.description,
            "date": blog_post.date,
            "image": blog_post.image,
            "tags": blog_post.tags,
            "sections": [],
        }

        sources = []
        for s in getattr(blog_post, "sources", []) or []:
            try:
                sources.append(
                    {
                        "id": int(getattr(s, "id", 0) or 0),
                        "title": str(getattr(s, "title", "") or ""),
                        "url": str(getattr(s, "url", "") or ""),
                        "snippet": str(getattr(s, "snippet", "") or ""),
                        "provider": str(getattr(s, "provider", "") or ""),
                    }
                )
            except Exception:
                continue
        if sources:
            blog_post_data["sources"] = sources

        for section in blog_post.sections:
            section_data = {"title": section.title, "subtopics": []}

            for subtopic in section.subtopics:
                subtopic_data = {"title": subtopic.title, "content": subtopic.content}
                section_data["subtopics"].append(subtopic_data)

            blog_post_data["sections"].append(section_data)

        # Add user message to conversation (with persistence and ownership)
        user_message = {
            "role": "user",
            "content": "Generate a blog post",  # Sanitized - don't log actual topic
            "timestamp": datetime.now().isoformat(),
        }
        conversations.append(request.conversation_id, user_message, user_id=user_id)

        # Add assistant message to conversation (with persistence)
        assistant_message = {
            "role": "assistant",
            "content": f"Generated blog post: {blog_post.title[:50]}",  # Truncated
            "timestamp": datetime.now().isoformat(),
        }
        conversations.append(request.conversation_id, assistant_message, user_id=user_id)

        # Send messages via WebSocket
        await manager.send_message(
            {"type": "message", **user_message}, request.conversation_id
        )
        await manager.send_message(
            {"type": "message", **assistant_message}, request.conversation_id
        )

        # Increment usage quota after successful generation
        await increment_usage_for_operation(
            user_id=user_id,
            operation_type="blog",
            tokens_used=4000,  # Estimated tokens
            metadata={
                "topic": request.topic[:50],
                "research": request.research,
                "provider_type": provider_type,
            },
        )

        # Calculate word count for webhook
        word_count = sum(
            len(subtopic.content.split())
            for section in blog_post.sections
            for subtopic in section.subtopics
        )

        # Emit webhook event for content generation (non-blocking)
        content_id = str(uuid.uuid4())
        try:
            await webhook_service.emit_content_generated(
                user_id=user_id,
                content_type="blog",
                title=blog_post.title,
                content_id=content_id,
                word_count=word_count,
                metadata={
                    "topic": request.topic[:100],
                    "tone": request.tone,
                    "research": request.research,
                    "keywords": request.keywords[:5] if request.keywords else [],
                },
            )
        except Exception as webhook_error:
            # Best-effort: never fail the main request if webhook emission fails.
            logger.warning(f"Failed to emit webhook: {webhook_error}")

        logger.info(f"Blog generated successfully: {blog_post.title}")
        return {"success": True, "type": "blog", "content": blog_post_data}
    except ValueError as e:
        logger.warning(f"Validation error in blog generation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=sanitize_error_message(str(e)))
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded in blog generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please wait {e.wait_time:.0f}s before retrying.",
        )
    except TextGenerationError as e:
        logger.error(f"Text generation error in blog: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate content from AI provider. Please try again.",
        )
    except BlogGenerationError as e:
        logger.error(f"Blog generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate blog post. Please try again later.",
        )
    except HTTPException:
        # Preserve explicit HTTP errors (e.g., quota/auth failures).
        raise
    except (AttributeError, KeyError, TypeError) as e:
        logger.error(f"Unexpected error generating blog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )
    except Exception as e:
        # Defensive catch-all: BaseHTTPMiddleware can surface exceptions as
        # ExceptionGroups; normalize to a 500 response for clients/tests.
        logger.error(f"Unhandled error generating blog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )
