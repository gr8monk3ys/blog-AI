"""
Book generation endpoints.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from src.book.make_book import (
    generate_book,
    generate_book_with_research,
    post_process_book,
)
from src.text_generation.core import GenerationOptions, create_provider_from_env

from ..auth import verify_api_key
from ..models import BookGenerationRequest
from ..storage import conversations
from ..websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["book"])


@router.post("/generate-book", status_code=status.HTTP_201_CREATED)
async def generate_book_endpoint(
    request: BookGenerationRequest, user_id: str = Depends(verify_api_key)
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

        # Generate book
        if request.research:
            book = generate_book_with_research(
                title=request.title,
                num_chapters=request.num_chapters,
                sections_per_chapter=request.sections_per_chapter,
                keywords=request.keywords,
                tone=request.tone,
                provider_type="openai",
                options=options,
            )
        else:
            book = generate_book(
                title=request.title,
                num_chapters=request.num_chapters,
                sections_per_chapter=request.sections_per_chapter,
                keywords=request.keywords,
                tone=request.tone,
                provider_type="openai",
                options=options,
            )

        # Post-process book
        if request.proofread or request.humanize:
            provider = create_provider_from_env("openai")
            book = post_process_book(
                book=book,
                proofread=request.proofread,
                humanize=request.humanize,
                provider=provider,
                options=options,
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

        # Add user message to conversation (with persistence)
        user_message = {
            "role": "user",
            "content": "Generate a book",  # Sanitized - don't log actual title
            "timestamp": datetime.now().isoformat(),
        }
        conversations.append(request.conversation_id, user_message)

        # Add assistant message to conversation (with persistence)
        assistant_message = {
            "role": "assistant",
            "content": f"Generated book with {len(book.chapters)} chapters",  # Sanitized
            "timestamp": datetime.now().isoformat(),
        }
        conversations.append(request.conversation_id, assistant_message)

        # Send messages via WebSocket
        await manager.send_message(
            {"type": "message", **user_message}, request.conversation_id
        )
        await manager.send_message(
            {"type": "message", **assistant_message}, request.conversation_id
        )

        logger.info(f"Book generated successfully: {book.title}")
        return {"success": True, "type": "book", "content": book_data}
    except ValueError as e:
        logger.warning(f"Validation error in book generation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating book: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate book. Please try again later.",
        )
