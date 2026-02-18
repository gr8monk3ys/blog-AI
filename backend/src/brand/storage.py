"""
Brand Voice Storage Layer.

Production: Postgres (Neon) via asyncpg helpers in `src.db`.
Dev/test: in-memory fallback when the database is not configured.
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict

from src.db import fetch as db_fetch
from src.db import fetchrow as db_fetchrow
from src.db import is_database_configured
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


def _coerce_uuid(value: str, field_name: str) -> str:
    try:
        return str(uuid.UUID(str(value).strip()))
    except Exception as e:
        raise ValueError(f"Invalid {field_name}") from e


class BaseBrandVoiceStorage(ABC):
    """Abstract base class for brand voice storage implementations."""

    @abstractmethod
    async def get_samples(self, user_id: str, profile_id: str) -> List[VoiceSample]:
        """Return all samples for a profile belonging to a user."""

    @abstractmethod
    async def add_sample(self, user_id: str, sample: VoiceSample) -> str:
        """Add a sample and return its ID."""

    @abstractmethod
    async def delete_sample(self, user_id: str, profile_id: str, sample_id: str) -> bool:
        """Delete a sample. Returns True if deleted, False if not found."""

    @abstractmethod
    async def get_fingerprint(self, user_id: str, profile_id: str) -> Optional[VoiceFingerprint]:
        """Return the fingerprint for a profile belonging to a user."""

    @abstractmethod
    async def save_fingerprint(self, user_id: str, fingerprint: VoiceFingerprint) -> str:
        """Upsert a fingerprint and return its ID."""

    @abstractmethod
    async def update_sample_analysis(
        self,
        user_id: str,
        sample_id: str,
        analysis: SampleAnalysis,
        quality_score: float,
    ) -> bool:
        """Attach analysis to a sample. Returns True if updated."""


class InMemoryBrandVoiceStorage(BaseBrandVoiceStorage):
    """In-memory storage for local development and tests."""

    def __init__(self) -> None:
        # Keyed by (user_id, profile_id)
        self._samples: Dict[Tuple[str, str], List[VoiceSample]] = {}
        self._fingerprints: Dict[Tuple[str, str], VoiceFingerprint] = {}
        logger.info("Initialized in-memory brand voice storage")

    async def get_samples(self, user_id: str, profile_id: str) -> List[VoiceSample]:
        return self._samples.get((user_id, profile_id), [])

    async def add_sample(self, user_id: str, sample: VoiceSample) -> str:
        sample_id = str(uuid.uuid4())
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

        key = (user_id, sample.profile_id)
        if key not in self._samples:
            self._samples[key] = []
        self._samples[key].append(new_sample)
        return sample_id

    async def delete_sample(self, user_id: str, profile_id: str, sample_id: str) -> bool:
        key = (user_id, profile_id)
        samples = self._samples.get(key, [])
        if not samples:
            return False
        kept = [s for s in samples if s.id != sample_id]
        deleted = len(kept) != len(samples)
        self._samples[key] = kept
        return deleted

    async def get_fingerprint(self, user_id: str, profile_id: str) -> Optional[VoiceFingerprint]:
        return self._fingerprints.get((user_id, profile_id))

    async def save_fingerprint(self, user_id: str, fingerprint: VoiceFingerprint) -> str:
        fingerprint_id = fingerprint.id or str(uuid.uuid4())
        updated = VoiceFingerprint(
            id=fingerprint_id,
            profile_id=fingerprint.profile_id,
            vocabulary_profile=fingerprint.vocabulary_profile,
            sentence_patterns=fingerprint.sentence_patterns,
            tone_distribution=fingerprint.tone_distribution,
            style_metrics=fingerprint.style_metrics,
            voice_summary=fingerprint.voice_summary,
            sample_count=fingerprint.sample_count,
            training_quality=fingerprint.training_quality,
            last_trained_at=datetime.now(timezone.utc).isoformat(),
        )
        self._fingerprints[(user_id, fingerprint.profile_id)] = updated
        return fingerprint_id

    async def update_sample_analysis(
        self,
        user_id: str,
        sample_id: str,
        analysis: SampleAnalysis,
        quality_score: float,
    ) -> bool:
        for (owner_id, _profile_id), samples in self._samples.items():
            if owner_id != user_id:
                continue
            for sample in samples:
                if sample.id == sample_id:
                    sample.is_analyzed = True
                    sample.analysis_result = analysis
                    sample.quality_score = quality_score
                    return True
        return False


class PostgresBrandVoiceStorage(BaseBrandVoiceStorage):
    """Postgres-backed storage for production use (Neon / managed Postgres)."""

    def _parse_content_type(self, value: str) -> ContentType:
        try:
            return ContentType(value)
        except ValueError:
            return ContentType.TEXT

    def _sample_from_row(self, row) -> VoiceSample:
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

    def _fingerprint_from_row(self, row) -> VoiceFingerprint:
        last_trained_at = row.get("last_trained_at")
        if isinstance(last_trained_at, datetime):
            last_trained_at = last_trained_at.astimezone(timezone.utc).isoformat()
        return VoiceFingerprint(
            id=str(row["id"]),
            profile_id=str(row["profile_id"]),
            vocabulary_profile=VocabularyProfile(**(row.get("vocabulary_profile") or {})),
            sentence_patterns=SentencePatterns(**(row.get("sentence_patterns") or {})),
            tone_distribution=ToneDistribution(**(row.get("tone_distribution") or {})),
            style_metrics=StyleMetrics(**(row.get("style_metrics") or {})),
            voice_summary=row.get("voice_summary", ""),
            sample_count=row.get("sample_count", 0),
            training_quality=row.get("training_quality", 0.0),
            last_trained_at=last_trained_at,
        )

    async def get_samples(self, user_id: str, profile_id: str) -> List[VoiceSample]:
        pid = _coerce_uuid(profile_id, "profile_id")
        rows = await db_fetch(
            """
            SELECT *
              FROM voice_samples
             WHERE user_id = $1
               AND profile_id = $2::uuid
             ORDER BY created_at ASC
            """,
            user_id,
            pid,
        )
        return [self._sample_from_row(row) for row in rows]

    async def add_sample(self, user_id: str, sample: VoiceSample) -> str:
        pid = _coerce_uuid(sample.profile_id, "profile_id")
        row = await db_fetchrow(
            """
            INSERT INTO voice_samples (
              user_id,
              profile_id,
              title,
              content,
              content_type,
              word_count,
              source_url,
              source_platform,
              is_analyzed,
              analysis_result,
              quality_score,
              is_primary_example
            )
            VALUES ($1, $2::uuid, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id
            """,
            user_id,
            pid,
            sample.title,
            sample.content,
            sample.content_type.value,
            sample.word_count,
            sample.source_url,
            sample.source_platform,
            sample.is_analyzed,
            sample.analysis_result.model_dump() if sample.analysis_result else None,
            sample.quality_score,
            sample.is_primary_example,
        )
        if not row:
            raise RuntimeError("Failed to insert sample")
        return str(row["id"])

    async def delete_sample(self, user_id: str, profile_id: str, sample_id: str) -> bool:
        pid = _coerce_uuid(profile_id, "profile_id")
        sid = _coerce_uuid(sample_id, "sample_id")
        row = await db_fetchrow(
            """
            DELETE FROM voice_samples
             WHERE user_id = $1
               AND profile_id = $2::uuid
               AND id = $3::uuid
            RETURNING id
            """,
            user_id,
            pid,
            sid,
        )
        return bool(row)

    async def get_fingerprint(self, user_id: str, profile_id: str) -> Optional[VoiceFingerprint]:
        pid = _coerce_uuid(profile_id, "profile_id")
        row = await db_fetchrow(
            """
            SELECT *
              FROM voice_fingerprints
             WHERE user_id = $1
               AND profile_id = $2::uuid
             LIMIT 1
            """,
            user_id,
            pid,
        )
        if not row:
            return None
        return self._fingerprint_from_row(row)

    async def save_fingerprint(self, user_id: str, fingerprint: VoiceFingerprint) -> str:
        pid = _coerce_uuid(fingerprint.profile_id, "profile_id")
        row = await db_fetchrow(
            """
            INSERT INTO voice_fingerprints (
              user_id,
              profile_id,
              vocabulary_profile,
              sentence_patterns,
              tone_distribution,
              style_metrics,
              voice_summary,
              sample_count,
              training_quality,
              last_trained_at
            )
            VALUES ($1, $2::uuid, $3, $4, $5, $6, $7, $8, $9, NOW())
            ON CONFLICT (user_id, profile_id)
            DO UPDATE SET
              vocabulary_profile = EXCLUDED.vocabulary_profile,
              sentence_patterns = EXCLUDED.sentence_patterns,
              tone_distribution = EXCLUDED.tone_distribution,
              style_metrics = EXCLUDED.style_metrics,
              voice_summary = EXCLUDED.voice_summary,
              sample_count = EXCLUDED.sample_count,
              training_quality = EXCLUDED.training_quality,
              last_trained_at = NOW(),
              updated_at = NOW()
            RETURNING id
            """,
            user_id,
            pid,
            fingerprint.vocabulary_profile.model_dump(),
            fingerprint.sentence_patterns.model_dump(),
            fingerprint.tone_distribution.model_dump(),
            fingerprint.style_metrics.model_dump(),
            fingerprint.voice_summary,
            fingerprint.sample_count,
            fingerprint.training_quality,
        )
        if not row:
            raise RuntimeError("Failed to save fingerprint")
        return str(row["id"])

    async def update_sample_analysis(
        self,
        user_id: str,
        sample_id: str,
        analysis: SampleAnalysis,
        quality_score: float,
    ) -> bool:
        sid = _coerce_uuid(sample_id, "sample_id")
        row = await db_fetchrow(
            """
            UPDATE voice_samples
               SET is_analyzed = TRUE,
                   analysis_result = $1,
                   quality_score = $2,
                   updated_at = NOW()
             WHERE user_id = $3
               AND id = $4::uuid
            RETURNING id
            """,
            analysis.model_dump(),
            quality_score,
            user_id,
            sid,
        )
        return bool(row)


class BrandVoiceStorage:
    """Storage factory (Postgres when configured, otherwise in-memory)."""

    _instance: Optional[BaseBrandVoiceStorage] = None

    @classmethod
    def get_storage(cls) -> BaseBrandVoiceStorage:
        if cls._instance is not None:
            return cls._instance

        if is_database_configured():
            cls._instance = PostgresBrandVoiceStorage()
            logger.info("Using Postgres storage for brand voice")
        else:
            cls._instance = InMemoryBrandVoiceStorage()
            logger.info("DATABASE_URL not configured. Using in-memory brand voice storage")

        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None


def get_brand_voice_storage() -> BaseBrandVoiceStorage:
    return BrandVoiceStorage.get_storage()

