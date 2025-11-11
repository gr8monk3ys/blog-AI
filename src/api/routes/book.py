"""Book API routes."""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from ...config import settings
from ...repositories.file import FileRepository
from ...services.formatters.docx import DOCXFormatter
from ...services.generators.book import BookGenerator
from ...services.llm.openai import OpenAIProvider
from ..models import BookGenerateRequest, BookGenerateResponse, ErrorResponse, OutputFormat

try:
    from ...services.llm.anthropic import AnthropicProvider

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/generate",
    response_model=BookGenerateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def generate_book(request: BookGenerateRequest) -> BookGenerateResponse:
    """Generate a book.

    Args:
        request: Book generation request

    Returns:
        Generated book

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

        # Generate book
        logger.info(f"Generating book: {request.topic}")
        generator = BookGenerator(
            llm_provider=llm,
            num_chapters=request.chapters,
            topics_per_chapter=request.topics_per_chapter,
        )

        book = generator.generate(
            topic=request.topic,
            author=request.author,
            subtitle=request.subtitle,
        )

        # Format output
        if request.output_format == OutputFormat.JSON:
            content = book.model_dump(mode="json")
        elif request.output_format == OutputFormat.DOCX:
            formatter = DOCXFormatter()
            content = formatter.format(book)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported output format for book: {request.output_format}. Use 'json' or 'docx'",
            )

        # Save to file if requested
        file_path = None
        if request.save_to_file:
            repository = FileRepository()
            output_dir = Path("content/books")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{book.generate_slug()}.docx"
            file_path_obj = output_dir / filename

            if isinstance(content, dict):
                formatter = DOCXFormatter()
                file_content = formatter.format(book)
            else:
                file_content = content

            repository.save(file_content, file_path_obj)
            file_path = str(file_path_obj)
            logger.info(f"Saved book to: {file_path}")

        # Prepare metadata
        metadata = {
            "title": book.title,
            "author": book.author,
            "chapters": len(book.chapters),
            "word_count": book.word_count(),
            "provider": request.provider,
        }

        return BookGenerateResponse(
            success=True,
            content=content,
            metadata=metadata,
            file_path=file_path,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating book: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}",
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def book_info() -> dict[str, str]:
    """Get book endpoint information."""
    return {
        "endpoint": "Book Generation",
        "description": "Generate AI-powered books",
        "methods": ["POST /generate"],
    }
