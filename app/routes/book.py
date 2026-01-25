"""
Book generation endpoints.
"""

import asyncio
import logging
from datetime import datetime
from functools import partial

from fastapi import APIRouter, Depends, HTTPException, status

from src.book.make_book import (
    BookGenerationError,
    generate_book,
    generate_book_with_research,
    post_process_book,
)
from src.text_generation.core import (
    GenerationOptions,
    RateLimitError,
    TextGenerationError,
    create_provider_from_env,
)

from ..auth import verify_api_key
from ..error_handlers import sanitize_error_message
from ..middleware import increment_usage_for_operation, require_quota
from ..models import BookGenerationRequest
from ..storage import conversations
from ..websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["book"])


@router.post(
    "/generate-book",
    status_code=status.HTTP_201_CREATED,
    summary="Generate a complete book",
    description="""
Generate an AI-powered book with multiple chapters and sections.

The generated book includes:
- Customizable number of chapters (1-20)
- Configurable sections per chapter (1-10)
- Structured topics within each chapter
- Optional web research integration
- Proofreading and humanization passes

**Quota Usage**: Book generations count as multiple generations based on chapter count.
Each chapter counts toward your monthly limit.
    """,
    responses={
        201: {
            "description": "Book generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "type": "book",
                        "content": {
                            "title": "Complete Guide to Machine Learning",
                            "description": "A comprehensive exploration...",
                            "date": "2024-01-24",
                            "tags": ["Machine Learning", "AI"],
                            "chapters": [
                                {
                                    "number": 1,
                                    "title": "Introduction to ML",
                                    "topics": [
                                        {
                                            "title": "What is ML?",
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
        429: {"description": "Rate limit or quota exceeded"},
        502: {"description": "AI provider error"},
    }
)
async def generate_book_endpoint(
    request: BookGenerationRequest, user_id: str = Depends(require_quota)
):
    """
    Generate a book.

    Args:
        request: The book generation request parameters.
        user_id: The authenticated user ID.

    Returns:
        The generated book content.
    """
    logger.info(
        f"Book generation requested by user: {user_id}, "
        f"title_length: {len(request.title)}, chapters: {request.num_chapters}"
    )
    try:
        # Create generation options
        options = GenerationOptions(
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        # Generate book (run sync functions in thread pool to avoid blocking)
        if request.research:
            book = await asyncio.to_thread(
                partial(
                    generate_book_with_research,
                    title=request.title,
                    num_chapters=request.num_chapters,
                    sections_per_chapter=request.sections_per_chapter,
                    keywords=request.keywords,
                    tone=request.tone,
                    provider_type="openai",
                    options=options,
                )
            )
        else:
            book = await asyncio.to_thread(
                partial(
                    generate_book,
                    title=request.title,
                    num_chapters=request.num_chapters,
                    sections_per_chapter=request.sections_per_chapter,
                    keywords=request.keywords,
                    tone=request.tone,
                    provider_type="openai",
                    options=options,
                )
            )

        # Post-process book (run sync functions in thread pool)
        if request.proofread or request.humanize:
            provider = await asyncio.to_thread(create_provider_from_env, "openai")
            book = await asyncio.to_thread(
                partial(
                    post_process_book,
                    book=book,
                    proofread=request.proofread,
                    humanize=request.humanize,
                    provider=provider,
                    options=options,
                )
            )

        # Convert book to JSON-serializable format
        book_data = {
            "title": book.title,
            "description": book.description,
            "date": book.date,
            "image": book.image,
            "tags": book.tags,
            "chapters": [],
        }

        for chapter in book.chapters:
            chapter_data = {
                "number": chapter.number,
                "title": chapter.title,
                "topics": [],
            }

            for topic in chapter.topics:
                topic_data = {"title": topic.title, "content": topic.content}
                chapter_data["topics"].append(topic_data)

            book_data["chapters"].append(chapter_data)

        # Add user message to conversation (with persistence and ownership)
        user_message = {
            "role": "user",
            "content": "Generate a book",  # Sanitized - don't log actual title
            "timestamp": datetime.now().isoformat(),
        }
        conversations.append(request.conversation_id, user_message, user_id=user_id)

        # Add assistant message to conversation (with persistence)
        assistant_message = {
            "role": "assistant",
            "content": f"Generated book with {len(book.chapters)} chapters",  # Sanitized
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
        # Books count as multiple generations based on chapter count
        generation_count = max(1, request.num_chapters)
        estimated_tokens = 4000 * generation_count
        await increment_usage_for_operation(
            user_id=user_id,
            operation_type="book",
            tokens_used=estimated_tokens,
            metadata={
                "title": request.title[:50],
                "chapters": request.num_chapters,
                "research": request.research,
            },
        )

        logger.info(f"Book generated successfully: {book.title}")
        return {"success": True, "type": "book", "content": book_data}
    except ValueError as e:
        logger.warning(f"Validation error in book generation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=sanitize_error_message(str(e)))
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded in book generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please wait {e.wait_time:.0f}s before retrying.",
        )
    except TextGenerationError as e:
        logger.error(f"Text generation error in book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate content from AI provider. Please try again.",
        )
    except BookGenerationError as e:
        logger.error(f"Book generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate book. Please try again later.",
        )
    except Exception as e:
        logger.error(f"Unexpected error generating book: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        )
