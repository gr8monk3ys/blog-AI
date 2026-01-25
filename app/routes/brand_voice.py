"""
Brand Voice Training API Routes.

Endpoints for analyzing, training, and scoring brand voices.
Includes security validation for all inputs.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ValidationError, field_validator

from ..auth import verify_api_key


# =============================================================================
# Security Constants
# =============================================================================

ALLOWED_PROVIDERS: Set[str] = {"openai", "anthropic", "gemini"}
BLOCKED_HOSTNAMES: Set[str] = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "metadata.google.internal", "169.254.169.254",
}

DANGEROUS_HTML_PATTERNS = [
    re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<style[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<iframe[^>]*>.*?</iframe>", re.IGNORECASE | re.DOTALL),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
]

from src.brand.analyzer import VoiceAnalyzer
from src.brand.scorer import VoiceScorer
from src.brand.storage import get_brand_voice_storage
from src.brand.trainer import VoiceTrainer
from src.types.brand import (
    ContentType,
    SampleAnalysis,
    TrainingStatus,
    VoiceFingerprint,
    VoiceSample,
    VoiceScore,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/brand-voice", tags=["Brand Voice Training"])


# Request/Response models
class AnalyzeSampleRequest(BaseModel):
    """Request to analyze a content sample with security validation."""
    content: str = Field(..., min_length=50, max_length=50000, description="Content to analyze")
    content_type: str = Field(default="text", max_length=20, description="Type of content")
    provider: str = Field(default="openai", description="LLM provider")

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v):
        """Sanitize content to remove dangerous HTML."""
        if not v:
            raise ValueError("Content is required")
        v = str(v).strip()
        for pattern in DANGEROUS_HTML_PATTERNS:
            v = pattern.sub("", v)
        if len(v) < 50:
            raise ValueError("Content must be at least 50 characters after sanitization")
        return v

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v):
        """Validate provider against whitelist."""
        if not v:
            return "openai"
        v = str(v).lower().strip()
        if v not in ALLOWED_PROVIDERS:
            raise ValueError(f"Invalid provider. Allowed: {', '.join(sorted(ALLOWED_PROVIDERS))}")
        return v


class AnalyzeSampleResponse(BaseModel):
    """Response from sample analysis."""
    success: bool
    analysis: SampleAnalysis
    quality_score: float


class AddSampleRequest(BaseModel):
    """Request to add a voice sample to a profile with security validation."""
    profile_id: str = Field(..., max_length=100, description="Brand profile ID")
    content: str = Field(..., min_length=50, max_length=50000, description="Sample content")
    content_type: str = Field(default="text", max_length=20)
    title: Optional[str] = Field(default=None, max_length=200)
    source_url: Optional[str] = Field(default=None, max_length=500)
    source_platform: Optional[str] = Field(default=None, max_length=100)
    is_primary_example: bool = False

    @field_validator("profile_id")
    @classmethod
    def validate_profile_id(cls, v):
        """Validate profile ID format."""
        if not v or not v.strip():
            raise ValueError("Profile ID is required")
        v = str(v).strip()
        if not re.match(r"^[a-zA-Z0-9_-]{1,100}$", v):
            raise ValueError("Invalid profile ID format")
        return v

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v):
        """Sanitize content to remove dangerous HTML."""
        if not v:
            raise ValueError("Content is required")
        v = str(v).strip()
        for pattern in DANGEROUS_HTML_PATTERNS:
            v = pattern.sub("", v)
        if len(v) < 50:
            raise ValueError("Content must be at least 50 characters after sanitization")
        return v

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v):
        """Validate source URL for SSRF protection."""
        if v is None:
            return None
        v = str(v).strip()
        if not v:
            return None

        from urllib.parse import urlparse
        try:
            parsed = urlparse(v)
        except Exception:
            raise ValueError("Invalid URL format")

        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")

        if not parsed.hostname:
            raise ValueError("URL must include hostname")

        hostname = parsed.hostname.lower()
        if hostname in BLOCKED_HOSTNAMES:
            raise ValueError(f"URL hostname not allowed")

        # Block private IPs
        import ipaddress
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_reserved:
                raise ValueError("Private/internal IP addresses are not allowed")
        except ValueError:
            pass

        return v


class TrainVoiceRequest(BaseModel):
    """Request to train voice from samples with security validation."""
    profile_id: str = Field(..., max_length=100, description="Brand profile ID")
    sample_ids: Optional[List[str]] = Field(
        default=None,
        max_length=100,
        description="Specific sample IDs to use (None = all samples)"
    )
    provider: str = Field(default="openai")

    @field_validator("profile_id")
    @classmethod
    def validate_profile_id(cls, v):
        """Validate profile ID format."""
        if not v or not v.strip():
            raise ValueError("Profile ID is required")
        v = str(v).strip()
        if not re.match(r"^[a-zA-Z0-9_-]{1,100}$", v):
            raise ValueError("Invalid profile ID format")
        return v

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v):
        """Validate provider against whitelist."""
        if not v:
            return "openai"
        v = str(v).lower().strip()
        if v not in ALLOWED_PROVIDERS:
            raise ValueError(f"Invalid provider. Allowed: {', '.join(sorted(ALLOWED_PROVIDERS))}")
        return v

    @field_validator("sample_ids")
    @classmethod
    def validate_sample_ids(cls, v):
        """Validate sample ID formats."""
        if v is None:
            return None
        validated = []
        for sid in v:
            sid = str(sid).strip()
            if not re.match(r"^[a-zA-Z0-9_-]{1,100}$", sid):
                raise ValueError(f"Invalid sample ID format: {sid[:20]}...")
            validated.append(sid)
        return validated[:100]


class TrainVoiceResponse(BaseModel):
    """Response from voice training."""
    success: bool
    fingerprint: VoiceFingerprint
    sample_count: int
    training_quality: float
    voice_summary: str


class ScoreContentRequest(BaseModel):
    """Request to score content against brand voice with security validation."""
    profile_id: str = Field(..., max_length=100, description="Brand profile ID")
    content: str = Field(..., min_length=20, max_length=50000, description="Content to score")
    content_type: str = Field(default="text", max_length=20)
    provider: str = Field(default="openai")

    @field_validator("profile_id")
    @classmethod
    def validate_profile_id(cls, v):
        """Validate profile ID format."""
        if not v or not v.strip():
            raise ValueError("Profile ID is required")
        v = str(v).strip()
        if not re.match(r"^[a-zA-Z0-9_-]{1,100}$", v):
            raise ValueError("Invalid profile ID format")
        return v

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v):
        """Sanitize content to remove dangerous HTML."""
        if not v:
            raise ValueError("Content is required")
        v = str(v).strip()
        for pattern in DANGEROUS_HTML_PATTERNS:
            v = pattern.sub("", v)
        if len(v) < 20:
            raise ValueError("Content must be at least 20 characters after sanitization")
        return v

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v):
        """Validate provider against whitelist."""
        if not v:
            return "openai"
        v = str(v).lower().strip()
        if v not in ALLOWED_PROVIDERS:
            raise ValueError(f"Invalid provider. Allowed: {', '.join(sorted(ALLOWED_PROVIDERS))}")
        return v


class ScoreContentResponse(BaseModel):
    """Response from content scoring."""
    success: bool
    score: VoiceScore
    grade: str
    passed: bool  # True if score >= 0.7


@router.post("/analyze", response_model=AnalyzeSampleResponse)
async def analyze_sample(
    request: AnalyzeSampleRequest,
    user_id: str = Depends(verify_api_key),
):
    """
    Analyze a content sample for voice characteristics.

    Extracts vocabulary patterns, sentence structures, tone distribution,
    and style metrics from the provided content.
    """
    try:
        content_type = ContentType(request.content_type)
    except ValueError:
        content_type = ContentType.TEXT

    analyzer = VoiceAnalyzer(request.provider)
    analysis = analyzer.analyze(request.content, content_type)

    return AnalyzeSampleResponse(
        success=True,
        analysis=analysis,
        quality_score=analysis.quality_score,
    )


@router.post("/samples")
async def add_sample(
    request: AddSampleRequest,
    user_id: str = Depends(verify_api_key),
):
    """
    Add a voice sample to a brand profile.

    Samples are used to train the voice fingerprint. Adding more diverse
    samples improves training quality.
    """
    try:
        content_type = ContentType(request.content_type)
    except ValueError:
        content_type = ContentType.TEXT

    # Create sample (ID will be assigned by storage layer)
    sample = VoiceSample(
        id="",  # Will be assigned by storage
        profile_id=request.profile_id,
        title=request.title,
        content=request.content,
        content_type=content_type,
        word_count=len(request.content.split()),
        source_url=request.source_url,
        source_platform=request.source_platform,
        is_primary_example=request.is_primary_example,
        is_analyzed=False,
    )

    try:
        storage = get_brand_voice_storage()
        sample_id = await storage.add_sample(sample)
        samples = await storage.get_samples(request.profile_id)

        return {
            "success": True,
            "sample_id": sample_id,
            "word_count": sample.word_count,
            "message": f"Sample added. Total samples for profile: {len(samples)}",
        }
    except ValidationError as e:
        logger.warning(f"Validation error adding sample: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sample data: {str(e)}"
        )
    except ConnectionError as e:
        logger.error(f"Storage connection error adding sample: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error adding sample: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add sample. Please try again later."
        )


@router.get("/samples/{profile_id}")
async def list_samples(
    profile_id: str,
    user_id: str = Depends(verify_api_key),
):
    """
    List all voice samples for a brand profile.
    """
    try:
        storage = get_brand_voice_storage()
        samples = await storage.get_samples(profile_id)

        return {
            "profile_id": profile_id,
            "sample_count": len(samples),
            "samples": [
                {
                    "id": s.id,
                    "title": s.title,
                    "word_count": s.word_count,
                    "content_type": s.content_type.value,
                    "is_analyzed": s.is_analyzed,
                    "quality_score": s.quality_score,
                    "is_primary_example": s.is_primary_example,
                }
                for s in samples
            ],
        }
    except ConnectionError as e:
        logger.error(f"Storage connection error listing samples: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error listing samples: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list samples. Please try again later."
        )


@router.delete("/samples/{profile_id}/{sample_id}")
async def delete_sample(
    profile_id: str,
    sample_id: str,
    user_id: str = Depends(verify_api_key),
):
    """
    Delete a voice sample from a profile.
    """
    try:
        storage = get_brand_voice_storage()
        deleted = await storage.delete_sample(profile_id, sample_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sample not found"
            )

        samples = await storage.get_samples(profile_id)

        return {
            "success": True,
            "message": "Sample deleted",
            "remaining_samples": len(samples),
        }
    except HTTPException:
        raise
    except ConnectionError as e:
        logger.error(f"Storage connection error deleting sample: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting sample: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete sample. Please try again later."
        )


@router.post("/train", response_model=TrainVoiceResponse)
async def train_voice(
    request: TrainVoiceRequest,
    user_id: str = Depends(verify_api_key),
):
    """
    Train a voice fingerprint from samples.

    Aggregates analysis from all samples into a unified voice fingerprint
    that can be used for content generation and scoring.
    """
    try:
        storage = get_brand_voice_storage()
        samples = await storage.get_samples(request.profile_id)

        if not samples:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No samples found for this profile. Add samples first."
            )

        # Filter to specific samples if requested
        if request.sample_ids:
            samples = [s for s in samples if s.id in request.sample_ids]
            if not samples:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No matching samples found"
                )

        trainer = VoiceTrainer(request.provider)
        fingerprint = trainer.train(request.profile_id, samples)

        # Store fingerprint
        await storage.save_fingerprint(fingerprint)

        # Update sample analysis status for all samples in profile
        all_samples = await storage.get_samples(request.profile_id)
        for sample in all_samples:
            if not sample.is_analyzed:
                # Mark as analyzed (analysis was done during training)
                await storage.update_sample_analysis(
                    sample.id,
                    sample.analysis_result or SampleAnalysis(),
                    sample.quality_score
                )

        return TrainVoiceResponse(
            success=True,
            fingerprint=fingerprint,
            sample_count=fingerprint.sample_count,
            training_quality=fingerprint.training_quality,
            voice_summary=fingerprint.voice_summary,
        )
    except HTTPException:
        raise
    except ConnectionError as e:
        logger.error(f"Storage connection error training voice: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later."
        )
    except ValueError as e:
        logger.warning(f"Invalid training data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid training data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error training voice: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to train voice. Please try again later."
        )


@router.get("/fingerprint/{profile_id}")
async def get_fingerprint(
    profile_id: str,
    user_id: str = Depends(verify_api_key),
):
    """
    Get the trained voice fingerprint for a profile.
    """
    try:
        storage = get_brand_voice_storage()
        fingerprint = await storage.get_fingerprint(profile_id)

        if not fingerprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No trained fingerprint found. Train the voice first."
            )

        return {
            "success": True,
            "fingerprint": fingerprint.model_dump(),
        }
    except HTTPException:
        raise
    except ConnectionError as e:
        logger.error(f"Storage connection error getting fingerprint: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error getting fingerprint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get fingerprint. Please try again later."
        )


@router.post("/score", response_model=ScoreContentResponse)
async def score_content(
    request: ScoreContentRequest,
    user_id: str = Depends(verify_api_key),
):
    """
    Score content against a trained brand voice.

    Returns consistency scores and suggestions for improvement.
    """
    try:
        storage = get_brand_voice_storage()
        fingerprint = await storage.get_fingerprint(request.profile_id)

        if not fingerprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No trained fingerprint found. Train the voice first."
            )

        try:
            content_type = ContentType(request.content_type)
        except ValueError:
            content_type = ContentType.TEXT

        scorer = VoiceScorer(request.provider)
        score = scorer.score(request.content, fingerprint, content_type)

        # Determine grade
        grade = (
            "A+" if score.overall_score >= 0.95
            else "A" if score.overall_score >= 0.85
            else "B" if score.overall_score >= 0.75
            else "C" if score.overall_score >= 0.65
            else "D" if score.overall_score >= 0.5
            else "F"
        )

        return ScoreContentResponse(
            success=True,
            score=score,
            grade=grade,
            passed=score.overall_score >= 0.7,
        )
    except HTTPException:
        raise
    except ConnectionError as e:
        logger.error(f"Storage connection error scoring content: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later."
        )
    except ValueError as e:
        logger.warning(f"Invalid content for scoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error scoring content: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to score content. Please try again later."
        )


@router.get("/status/{profile_id}")
async def get_training_status(
    profile_id: str,
    user_id: str = Depends(verify_api_key),
):
    """
    Get the training status for a profile.
    """
    try:
        storage = get_brand_voice_storage()
        samples = await storage.get_samples(profile_id)
        fingerprint = await storage.get_fingerprint(profile_id)

        if fingerprint:
            training_status = TrainingStatus.TRAINED
            quality = fingerprint.training_quality
        elif samples:
            training_status = TrainingStatus.UNTRAINED
            quality = 0.0
        else:
            training_status = TrainingStatus.UNTRAINED
            quality = 0.0

        return {
            "profile_id": profile_id,
            "status": training_status.value,
            "sample_count": len(samples),
            "training_quality": quality,
            "has_fingerprint": fingerprint is not None,
            "voice_summary": fingerprint.voice_summary if fingerprint else None,
        }
    except ConnectionError as e:
        logger.error(f"Storage connection error getting training status: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error getting training status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get training status. Please try again later."
        )
