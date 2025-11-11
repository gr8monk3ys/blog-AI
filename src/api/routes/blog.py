"""Blog post API routes."""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from ...config import settings
from ...repositories.file import FileRepository
from ...services.formatters.mdx import MDXFormatter
from ...services.generators.blog import BlogGenerator
from ...services.llm.openai import OpenAIProvider
from ..models import BlogGenerateRequest, BlogGenerateResponse, ErrorResponse, OutputFormat

try:
    from ...services.llm.anthropic import AnthropicProvider

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/generate",
    response_model=BlogGenerateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def generate_blog(request: BlogGenerateRequest) -> BlogGenerateResponse:
    """Generate a blog post.

    Args:
        request: Blog generation request

    Returns:
        Generated blog post

    Raises:
        HTTPException: If generation fails
    """
    try:
        # Initialize LLM provider
        if request.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Anthropic provider not available. Install with: pip install anthropic",
                )
            llm = AnthropicProvider(
                temperature=request.temperature or settings.temperature,
            )
        else:
            llm = OpenAIProvider(
                temperature=request.temperature or settings.temperature,
            )

        # Generate blog post
        logger.info(f"Generating blog post: {request.topic}")
        generator = BlogGenerator(
            llm_provider=llm,
            num_sections=request.sections,
        )

        blog = generator.generate(request.topic)

        # Format output
        if request.output_format == OutputFormat.JSON:
            content = blog.model_dump(mode="json")
        elif request.output_format in [OutputFormat.MARKDOWN, OutputFormat.MDX]:
            formatter = MDXFormatter()
            content = formatter.format(blog)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported output format for blog: {request.output_format}",
            )

        # Save to file if requested
        file_path = None
        if request.save_to_file:
            repository = FileRepository()
            output_dir = Path("content/blog")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{blog.metadata.generate_slug()}.mdx"
            file_path_obj = output_dir / filename

            if isinstance(content, dict):
                formatter = MDXFormatter()
                file_content = formatter.format(blog)
            else:
                file_content = content

            repository.save(file_content, file_path_obj)
            file_path = str(file_path_obj)
            logger.info(f"Saved blog post to: {file_path}")

        # Prepare metadata
        metadata = {
            "title": blog.title,
            "sections": len(blog.sections),
            "word_count": blog.word_count(),
            "tags": blog.metadata.tags,
            "provider": request.provider,
        }

        return BlogGenerateResponse(
            success=True,
            content=content,
            metadata=metadata,
            file_path=file_path,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating blog post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}",
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def blog_info() -> dict[str, str]:
    """Get blog endpoint information."""
    return {
        "endpoint": "Blog Post Generation",
        "description": "Generate AI-powered blog posts",
        "methods": ["POST /generate"],
    }
