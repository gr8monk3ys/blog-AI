"""FAQ API routes."""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from ...config import settings
from ...repositories.file import FileRepository
from ...services.formatters.faq_html import FAQHTMLFormatter
from ...services.formatters.faq_md import FAQMarkdownFormatter
from ...services.generators.faq import FAQGenerator
from ...services.llm.openai import OpenAIProvider
from ..models import ErrorResponse, FAQGenerateRequest, FAQGenerateResponse, OutputFormat

try:
    from ...services.llm.anthropic import AnthropicProvider

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/generate",
    response_model=FAQGenerateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def generate_faq(request: FAQGenerateRequest) -> FAQGenerateResponse:
    """Generate an FAQ.

    Args:
        request: FAQ generation request

    Returns:
        Generated FAQ

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

        # Generate FAQ
        logger.info(f"Generating FAQ: {request.topic}")
        generator = FAQGenerator(
            llm_provider=llm,
            num_questions=request.questions,
            include_intro=request.include_intro,
            include_conclusion=request.include_conclusion,
        )

        faq = generator.generate(request.topic)

        # Format output
        if request.output_format == OutputFormat.JSON:
            content = faq.model_dump(mode="json")
        elif request.output_format == OutputFormat.MARKDOWN:
            formatter = FAQMarkdownFormatter()
            content = formatter.format(faq)
        elif request.output_format == OutputFormat.HTML:
            formatter = FAQHTMLFormatter()
            content = formatter.format(faq)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported output format for FAQ: {request.output_format}. Use 'json', 'markdown', or 'html'",
            )

        # Save to file if requested
        file_path = None
        if request.save_to_file:
            repository = FileRepository()
            output_dir = Path("content/faq")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Determine extension
            if request.output_format == OutputFormat.HTML:
                ext = "html"
            else:
                ext = "md"

            filename = f"{faq.metadata.generate_slug()}.{ext}"
            file_path_obj = output_dir / filename

            if isinstance(content, dict):
                # Convert to markdown by default
                formatter = FAQMarkdownFormatter()
                file_content = formatter.format(faq)
            else:
                file_content = content

            repository.save(file_content, file_path_obj)
            file_path = str(file_path_obj)
            logger.info(f"Saved FAQ to: {file_path}")

        # Prepare metadata
        metadata = {
            "title": faq.metadata.title,
            "questions": len(faq.items),
            "categories": faq.get_categories(),
            "word_count": faq.word_count(),
            "provider": request.provider,
        }

        return FAQGenerateResponse(
            success=True,
            content=content,
            metadata=metadata,
            file_path=file_path,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating FAQ: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}",
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def faq_info() -> dict[str, str]:
    """Get FAQ endpoint information."""
    return {
        "endpoint": "FAQ Generation",
        "description": "Generate AI-powered FAQs",
        "methods": ["POST /generate"],
    }
