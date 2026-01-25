"""
Brand Voice Storage Layer.

Provides persistent storage for voice samples and fingerprints using Supabase,
with an in-memory fallback for local development when Supabase is not configured.
"""

import logging
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from src.types.brand import (
    ContentType,
    SampleAnalysis,
    SentencePatterns,
    StyleMetrics,
    ToneDistribution,
    VocabularyProfile,
    VoiceFingerprint,
    VoiceSample,
)

logger = logging.getLogger(__name__)


class BaseBrandVoiceStorage(ABC):
    """Abstract base class for brand voice storage implementations."""

    @abstractmethod
    async def get_samples(self, profile_id: str) -> List[VoiceSample]:
        """Get all voice samples for a profile."""
        pass

    @abstractmethod
    async def add_sample(self, sample: VoiceSample) -> str:
        """Add a voice sample and return its ID."""
        pass

    @abstractmethod
    async def delete_sample(self, profile_id: str, sample_id: str) -> bool:
        """Delete a voice sample. Returns True if deleted, False if not found."""
        pass

    @abstractmethod
    async def get_fingerprint(self, profile_id: str) -> Optional[VoiceFingerprint]:
        """Get the voice fingerprint for a profile."""
        pass

    @abstractmethod
    async def save_fingerprint(self, fingerprint: VoiceFingerprint) -> str:
        """Save or update a voice fingerprint. Returns the fingerprint ID."""
        pass

    @abstractmethod
    async def update_sample_analysis(
        self, sample_id: str, analysis: SampleAnalysis, quality_score: float
    ) -> bool:
        """Update sample with analysis results."""
        pass


class InMemoryBrandVoiceStorage(BaseBrandVoiceStorage):
    """In-memory storage for local development and testing."""

    def __init__(self) -> None:
        self._samples: Dict[str, List[VoiceSample]] = {}
        self._fingerprints: Dict[str, VoiceFingerprint] = {}
        self._sample_id_counter = 0
        logger.info("Initialized in-memory brand voice storage")

    async def get_samples(self, profile_id: str) -> List[VoiceSample]:
        """Get all voice samples for a profile."""
        return self._samples.get(profile_id, [])

    async def add_sample(self, sample: VoiceSample) -> str:
        """Add a voice sample and return its ID."""
        self._sample_id_counter += 1
        sample_id = f"sample-{self._sample_id_counter}"

        # Create a new sample with the generated ID
        new_sample = VoiceSample(
            id=sample_id,
            profile_id=sample.profile_id,
            title=sample.title,
            content=sample.content,
            content_type=sample.content_type,
            word_count=sample.word_count,
            source_url=sample.source_url,
            source_platform=sample.source_platform,
            is_analyzed=sample.is_analyzed,
            analysis_result=sample.analysis_result,
            quality_score=sample.quality_score,
            is_primary_example=sample.is_primary_example,
        )

        if sample.profile_id not in self._samples:
            self._samples[sample.profile_id] = []
        self._samples[sample.profile_id].append(new_sample)

        logger.debug(f"Added sample {sample_id} for profile {sample.profile_id}")
        return sample_id

    async def delete_sample(self, profile_id: str, sample_id: str) -> bool:
        """Delete a voice sample. Returns True if deleted, False if not found."""
        if profile_id not in self._samples:
            return False

        samples = self._samples[profile_id]
        original_count = len(samples)
        self._samples[profile_id] = [s for s in samples if s.id != sample_id]

        deleted = len(self._samples[profile_id]) < original_count
        if deleted:
            logger.debug(f"Deleted sample {sample_id} from profile {profile_id}")
        return deleted

    async def get_fingerprint(self, profile_id: str) -> Optional[VoiceFingerprint]:
        """Get the voice fingerprint for a profile."""
        return self._fingerprints.get(profile_id)

    async def save_fingerprint(self, fingerprint: VoiceFingerprint) -> str:
        """Save or update a voice fingerprint. Returns the fingerprint ID."""
        fingerprint_id = fingerprint.id or f"fp-{uuid.uuid4()}"

        updated_fingerprint = VoiceFingerprint(
            id=fingerprint_id,
            profile_id=fingerprint.profile_id,
            vocabulary_profile=fingerprint.vocabulary_profile,
            sentence_patterns=fingerprint.sentence_patterns,
            tone_distribution=fingerprint.tone_distribution,
            style_metrics=fingerprint.style_metrics,
            voice_summary=fingerprint.voice_summary,
            sample_count=fingerprint.sample_count,
            training_quality=fingerprint.training_quality,
            last_trained_at=datetime.utcnow().isoformat(),
        )

        self._fingerprints[fingerprint.profile_id] = updated_fingerprint
        logger.debug(f"Saved fingerprint {fingerprint_id} for profile {fingerprint.profile_id}")
        return fingerprint_id

    async def update_sample_analysis(
        self, sample_id: str, analysis: SampleAnalysis, quality_score: float
    ) -> bool:
        """Update sample with analysis results."""
        for profile_samples in self._samples.values():
            for sample in profile_samples:
                if sample.id == sample_id:
                    sample.is_analyzed = True
                    sample.analysis_result = analysis
                    sample.quality_score = quality_score
                    logger.debug(f"Updated analysis for sample {sample_id}")
                    return True
        return False


class SupabaseBrandVoiceStorage(BaseBrandVoiceStorage):
    """Supabase-backed storage for production use."""

    def __init__(self, supabase_url: str, supabase_key: str) -> None:
        self._supabase_url = supabase_url
        self._supabase_key = supabase_key
        self._client = None
        logger.info("Initialized Supabase brand voice storage")

    def _get_client(self):
        """Get or create Supabase client (lazy initialization)."""
        if self._client is not None:
            return self._client

        try:
            from supabase import create_client

            self._client = create_client(self._supabase_url, self._supabase_key)
            return self._client
        except ImportError:
            logger.error("Supabase Python client not installed. Run: pip install supabase")
            raise RuntimeError("Supabase client not available")
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            raise

    def _parse_content_type(self, value: str) -> ContentType:
        """Parse content type from string."""
        try:
            return ContentType(value)
        except ValueError:
            return ContentType.TEXT

    def _sample_from_row(self, row: dict) -> VoiceSample:
        """Convert a database row to a VoiceSample."""
        analysis_result = None
        if row.get("analysis_result"):
            analysis_data = row["analysis_result"]
            analysis_result = SampleAnalysis(
                vocabulary=VocabularyProfile(**analysis_data.get("vocabulary", {})),
                sentences=SentencePatterns(**analysis_data.get("sentences", {})),
                tone=ToneDistribution(**analysis_data.get("tone", {})),
                style=StyleMetrics(**analysis_data.get("style", {})),
                key_characteristics=analysis_data.get("key_characteristics", []),
                quality_score=analysis_data.get("quality_score", 0.0),
            )

        return VoiceSample(
            id=str(row["id"]),
            profile_id=str(row["profile_id"]),
            title=row.get("title"),
            content=row["content"],
            content_type=self._parse_content_type(row.get("content_type", "text")),
            word_count=row.get("word_count", 0),
            source_url=row.get("source_url"),
            source_platform=row.get("source_platform"),
            is_analyzed=row.get("is_analyzed", False),
            analysis_result=analysis_result,
            quality_score=row.get("quality_score", 0.0),
            is_primary_example=row.get("is_primary_example", False),
        )

    def _fingerprint_from_row(self, row: dict) -> VoiceFingerprint:
        """Convert a database row to a VoiceFingerprint."""
        return VoiceFingerprint(
            id=str(row["id"]),
            profile_id=str(row["profile_id"]),
            vocabulary_profile=VocabularyProfile(**row.get("vocabulary_profile", {})),
            sentence_patterns=SentencePatterns(**row.get("sentence_patterns", {})),
            tone_distribution=ToneDistribution(**row.get("tone_distribution", {})),
            style_metrics=StyleMetrics(**row.get("style_metrics", {})),
            voice_summary=row.get("voice_summary", ""),
            sample_count=row.get("sample_count", 0),
            training_quality=row.get("training_quality", 0.0),
            last_trained_at=row.get("last_trained_at"),
        )

    async def get_samples(self, profile_id: str) -> List[VoiceSample]:
        """Get all voice samples for a profile."""
        try:
            client = self._get_client()
            result = (
                client.table("voice_samples")
                .select("*")
                .eq("profile_id", profile_id)
                .order("created_at", desc=False)
                .execute()
            )

            if not result.data:
                return []

            return [self._sample_from_row(row) for row in result.data]

        except Exception as e:
            logger.error(f"Error fetching samples for profile {profile_id}: {e}")
            raise

    async def add_sample(self, sample: VoiceSample) -> str:
        """Add a voice sample and return its ID."""
        try:
            client = self._get_client()

            # Prepare data for insertion
            data = {
                "profile_id": sample.profile_id,
                "title": sample.title,
                "content": sample.content,
                "content_type": sample.content_type.value,
                "word_count": sample.word_count,
                "source_url": sample.source_url,
                "source_platform": sample.source_platform,
                "is_analyzed": sample.is_analyzed,
                "quality_score": sample.quality_score,
                "is_primary_example": sample.is_primary_example,
            }

            # Include analysis result if present
            if sample.analysis_result:
                data["analysis_result"] = sample.analysis_result.model_dump()

            result = client.table("voice_samples").insert(data).execute()

            if not result.data or len(result.data) == 0:
                raise RuntimeError("Failed to insert sample")

            sample_id = str(result.data[0]["id"])
            logger.info(f"Added sample {sample_id} for profile {sample.profile_id}")
            return sample_id

        except Exception as e:
            logger.error(f"Error adding sample for profile {sample.profile_id}: {e}")
            raise

    async def delete_sample(self, profile_id: str, sample_id: str) -> bool:
        """Delete a voice sample. Returns True if deleted, False if not found."""
        try:
            client = self._get_client()

            # First check if sample exists
            existing = (
                client.table("voice_samples")
                .select("id")
                .eq("id", sample_id)
                .eq("profile_id", profile_id)
                .execute()
            )

            if not existing.data:
                return False

            # Delete the sample
            client.table("voice_samples").delete().eq("id", sample_id).execute()

            logger.info(f"Deleted sample {sample_id} from profile {profile_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting sample {sample_id}: {e}")
            raise

    async def get_fingerprint(self, profile_id: str) -> Optional[VoiceFingerprint]:
        """Get the voice fingerprint for a profile."""
        try:
            client = self._get_client()

            result = (
                client.table("voice_fingerprints")
                .select("*")
                .eq("profile_id", profile_id)
                .limit(1)
                .execute()
            )

            if not result.data:
                return None

            return self._fingerprint_from_row(result.data[0])

        except Exception as e:
            logger.error(f"Error fetching fingerprint for profile {profile_id}: {e}")
            raise

    async def save_fingerprint(self, fingerprint: VoiceFingerprint) -> str:
        """Save or update a voice fingerprint. Returns the fingerprint ID."""
        try:
            client = self._get_client()

            # Prepare data
            data = {
                "profile_id": fingerprint.profile_id,
                "vocabulary_profile": fingerprint.vocabulary_profile.model_dump(),
                "sentence_patterns": fingerprint.sentence_patterns.model_dump(),
                "tone_distribution": fingerprint.tone_distribution.model_dump(),
                "style_metrics": fingerprint.style_metrics.model_dump(),
                "voice_summary": fingerprint.voice_summary,
                "sample_count": fingerprint.sample_count,
                "training_quality": fingerprint.training_quality,
                "last_trained_at": datetime.utcnow().isoformat(),
            }

            # Check if fingerprint already exists for this profile
            existing = (
                client.table("voice_fingerprints")
                .select("id")
                .eq("profile_id", fingerprint.profile_id)
                .limit(1)
                .execute()
            )

            if existing.data:
                # Update existing fingerprint
                fingerprint_id = str(existing.data[0]["id"])
                client.table("voice_fingerprints").update(data).eq(
                    "id", fingerprint_id
                ).execute()
                logger.info(f"Updated fingerprint {fingerprint_id} for profile {fingerprint.profile_id}")
            else:
                # Insert new fingerprint
                result = client.table("voice_fingerprints").insert(data).execute()
                if not result.data:
                    raise RuntimeError("Failed to insert fingerprint")
                fingerprint_id = str(result.data[0]["id"])
                logger.info(f"Created fingerprint {fingerprint_id} for profile {fingerprint.profile_id}")

            return fingerprint_id

        except Exception as e:
            logger.error(f"Error saving fingerprint for profile {fingerprint.profile_id}: {e}")
            raise

    async def update_sample_analysis(
        self, sample_id: str, analysis: SampleAnalysis, quality_score: float
    ) -> bool:
        """Update sample with analysis results."""
        try:
            client = self._get_client()

            data = {
                "is_analyzed": True,
                "analysis_result": analysis.model_dump(),
                "quality_score": quality_score,
            }

            result = (
                client.table("voice_samples")
                .update(data)
                .eq("id", sample_id)
                .execute()
            )

            success = bool(result.data)
            if success:
                logger.debug(f"Updated analysis for sample {sample_id}")
            return success

        except Exception as e:
            logger.error(f"Error updating analysis for sample {sample_id}: {e}")
            raise


class BrandVoiceStorage:
    """
    Factory class for brand voice storage.

    Automatically selects between Supabase and in-memory storage based on
    environment configuration.
    """

    _instance: Optional[BaseBrandVoiceStorage] = None

    @classmethod
    def get_storage(cls) -> BaseBrandVoiceStorage:
        """
        Get or create the storage instance.

        Uses Supabase if SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_KEY)
        are configured, otherwise falls back to in-memory storage.
        """
        if cls._instance is not None:
            return cls._instance

        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")

        if supabase_url and supabase_key:
            try:
                cls._instance = SupabaseBrandVoiceStorage(supabase_url, supabase_key)
                logger.info("Using Supabase storage for brand voice")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase storage: {e}. Falling back to in-memory.")
                cls._instance = InMemoryBrandVoiceStorage()
        else:
            logger.info(
                "Supabase not configured (SUPABASE_URL and SUPABASE_KEY not set). "
                "Using in-memory storage for brand voice."
            )
            cls._instance = InMemoryBrandVoiceStorage()

        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the storage instance. Useful for testing."""
        cls._instance = None


# Convenience function for getting the storage instance
def get_brand_voice_storage() -> BaseBrandVoiceStorage:
    """Get the brand voice storage instance."""
    return BrandVoiceStorage.get_storage()
