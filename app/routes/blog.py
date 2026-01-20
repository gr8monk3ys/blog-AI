"""
Blog generation endpoints.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from src.blog.make_blog import (
    generate_blog_post,
    generate_blog_post_with_research,
    post_process_blog_post,
)
from src.text_generation.core import GenerationOptions, create_provider_from_env

from ..auth import verify_api_key
from ..models import BlogGenerationRequest
from ..storage import conversations
from ..websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["blog"])


@router.post("/generate-blog", status_code=status.HTTP_201_CREATED)
async def generate_blog(
    request: BlogGenerationRequest, user_id: str = Depends(verify_api_key)
):
    """
    Generate a blog post.

    Args:
        request: The blog generation request parameters.
        user_id: The authenticated user ID.

    Returns:
        The generated blog post content.
    """
    logger.info(
        f"Blog generation requested by user: {user_id}, topic_length: {len(request.topic)}"
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

        # Generate blog post
        if request.research:
            blog_post = generate_blog_post_with_research(
                title=request.topic,
                keywords=request.keywords,
                tone=request.tone,
                provider_type="openai",
                options=options,
            )
        else:
            blog_post = generate_blog_post(
                title=request.topic,
                keywords=request.keywords,
                tone=request.tone,
                provider_type="openai",
                options=options,
            )

        # Post-process blog post
        if request.proofread or request.humanize:
            provider = create_provider_from_env("openai")
            blog_post = post_process_blog_post(
                blog_post=blog_post,
                proofread=request.proofread,
                humanize=request.humanize,
                provider=provider,
                options=options,
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

        for section in blog_post.sections:
            section_data = {"title": section.title, "subtopics": []}

            for subtopic in section.subtopics:
                subtopic_data = {"title": subtopic.title, "content": subtopic.content}
                section_data["subtopics"].append(subtopic_data)

            blog_post_data["sections"].append(section_data)

        # Add user message to conversation (with persistence)
        user_message = {
            "role": "user",
            "content": "Generate a blog post",  # Sanitized - don't log actual topic
            "timestamp": datetime.now().isoformat(),
        }
        conversations.append(request.conversation_id, user_message)

        # Add assistant message to conversation (with persistence)
        assistant_message = {
            "role": "assistant",
            "content": f"Generated blog post: {blog_post.title[:50]}",  # Truncated
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

        logger.info(f"Blog generated successfully: {blog_post.title}")
        return {"success": True, "type": "blog", "content": blog_post_data}
    except ValueError as e:
        logger.warning(f"Validation error in blog generation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating blog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate blog post. Please try again later.",
        )
