"""
Job store abstraction for bulk and batch generation routes.

This module provides type-safe wrappers around JobStorage for different
job types (bulk generation and enhanced batch), with proper serialization
and deserialization of Pydantic models.
"""

import logging
from typing import Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel

from .job_storage import job_storage, DEFAULT_TTL

logger = logging.getLogger(__name__)

# Type variable for job status models
T = TypeVar("T", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)


class TypedJobStore(Generic[T, R]):
    """
    Type-safe job store wrapper for a specific job type.

    Handles serialization/deserialization of Pydantic models and provides
    a clean interface for job management with ownership tracking.

    Type Parameters:
        T: The job status model type (e.g., BulkGenerationStatus)
        R: The result item model type (e.g., BulkGenerationItemResult)
    """

    def __init__(
        self,
        job_type: str,
        status_model: Type[T],
        result_model: Type[R],
        ttl: int = DEFAULT_TTL,
    ) -> None:
        """
        Initialize a typed job store.

        Args:
            job_type: Prefix for job type (e.g., "bulk" or "enhanced_batch")
            status_model: Pydantic model class for job status
            result_model: Pydantic model class for result items
            ttl: Default TTL for job data in seconds
        """
        self._job_type = job_type
        self._status_model = status_model
        self._result_model = result_model
        self._ttl = ttl

    def _make_job_id(self, job_id: str) -> str:
        """Create a prefixed job ID for storage."""
        return f"{self._job_type}:{job_id}"

    def _strip_job_id(self, prefixed_id: str) -> str:
        """Strip the type prefix from a job ID."""
        prefix = f"{self._job_type}:"
        if prefixed_id.startswith(prefix):
            return prefixed_id[len(prefix):]
        return prefixed_id

    async def save_job(
        self,
        job_id: str,
        status: T,
        user_id: str,
    ) -> bool:
        """
        Save a job with ownership.

        Args:
            job_id: Unique job identifier
            status: Job status model instance
            user_id: Owner user ID

        Returns:
            True if saved successfully
        """
        prefixed_id = self._make_job_id(job_id)
        job_data = status.model_dump(mode="json")

        result = await job_storage.save_job(prefixed_id, job_data, self._ttl)
        if result:
            await job_storage.set_owner(prefixed_id, user_id, self._ttl)
        return result

    async def get_job(self, job_id: str) -> Optional[T]:
        """
        Get a job by ID.

        Args:
            job_id: Unique job identifier

        Returns:
            Job status model instance, or None if not found
        """
        prefixed_id = self._make_job_id(job_id)
        job_data = await job_storage.get_job(prefixed_id)

        if job_data is None:
            return None

        try:
            return self._status_model.model_validate(job_data)
        except Exception as e:
            logger.warning(f"Failed to deserialize job {job_id}: {e}")
            return None

    async def get_job_if_owned(
        self,
        job_id: str,
        user_id: str,
    ) -> Optional[T]:
        """
        Get a job only if the user owns it.

        Args:
            job_id: Unique job identifier
            user_id: User ID requesting access

        Returns:
            Job status model instance if user owns it, None otherwise
        """
        prefixed_id = self._make_job_id(job_id)

        if not await job_storage.verify_ownership(prefixed_id, user_id):
            return None

        return await self.get_job(job_id)

    async def update_job(
        self,
        job_id: str,
        **updates,
    ) -> bool:
        """
        Update specific fields in a job.

        Args:
            job_id: Unique job identifier
            **updates: Fields to update

        Returns:
            True if updated successfully
        """
        prefixed_id = self._make_job_id(job_id)
        return await job_storage.update_job(prefixed_id, updates)

    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a job and its associated data.

        Args:
            job_id: Unique job identifier

        Returns:
            True if deleted successfully
        """
        prefixed_id = self._make_job_id(job_id)
        return await job_storage.delete_job(prefixed_id)

    async def list_jobs(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[T]:
        """
        List jobs owned by a user.

        Args:
            user_id: User ID to filter by
            status: Optional status filter
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of job status model instances
        """
        # Get raw job data from storage
        jobs_data = await job_storage.list_user_jobs(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset,
        )

        # Filter by job type and deserialize
        jobs: List[T] = []
        prefix = f"{self._job_type}:"

        for job_data in jobs_data:
            job_id = job_data.get("job_id", "")
            # Check if this job belongs to our type
            # (job_id in data might not have prefix, but we store with prefix)
            try:
                job = self._status_model.model_validate(job_data)
                jobs.append(job)
            except Exception as e:
                logger.warning(f"Failed to deserialize job: {e}")

        return jobs

    async def save_results(
        self,
        job_id: str,
        results: List[R],
    ) -> bool:
        """
        Save batch results.

        Args:
            job_id: Unique job identifier
            results: List of result model instances

        Returns:
            True if saved successfully
        """
        prefixed_id = self._make_job_id(job_id)
        results_data = [r.model_dump(mode="json") for r in results]
        return await job_storage.save_results(prefixed_id, results_data, self._ttl)

    async def get_results(self, job_id: str) -> List[R]:
        """
        Get batch results.

        Args:
            job_id: Unique job identifier

        Returns:
            List of result model instances
        """
        prefixed_id = self._make_job_id(job_id)
        results_data = await job_storage.get_results(prefixed_id)

        results: List[R] = []
        for data in results_data:
            try:
                results.append(self._result_model.model_validate(data))
            except Exception as e:
                logger.warning(f"Failed to deserialize result: {e}")

        return results

    async def set_cancel_flag(
        self,
        job_id: str,
        cancelled: bool,
    ) -> bool:
        """
        Set cancellation flag for a job.

        Args:
            job_id: Unique job identifier
            cancelled: Whether the job should be cancelled

        Returns:
            True if set successfully
        """
        prefixed_id = self._make_job_id(job_id)
        return await job_storage.set_cancel_flag(prefixed_id, cancelled)

    async def get_cancel_flag(self, job_id: str) -> bool:
        """
        Get cancellation flag for a job.

        Args:
            job_id: Unique job identifier

        Returns:
            True if job should be cancelled
        """
        prefixed_id = self._make_job_id(job_id)
        return await job_storage.get_cancel_flag(prefixed_id)

    async def verify_ownership(
        self,
        job_id: str,
        user_id: str,
    ) -> bool:
        """
        Verify that a user owns a job.

        Args:
            job_id: Unique job identifier
            user_id: User ID to verify

        Returns:
            True if user owns the job
        """
        prefixed_id = self._make_job_id(job_id)
        return await job_storage.verify_ownership(prefixed_id, user_id)

    @property
    def using_fallback(self) -> bool:
        """Check if currently using in-memory fallback."""
        return job_storage.using_fallback


# Lazy initialization of typed stores to avoid circular imports
_bulk_store: Optional["TypedJobStore"] = None
_batch_store: Optional["TypedJobStore"] = None


def get_bulk_job_store() -> "TypedJobStore":
    """
    Get the bulk generation job store.

    Returns:
        TypedJobStore configured for bulk generation jobs
    """
    global _bulk_store
    if _bulk_store is None:
        # Import here to avoid circular imports
        from app.models.bulk import BulkGenerationStatus, BulkGenerationItemResult

        _bulk_store = TypedJobStore(
            job_type="bulk",
            status_model=BulkGenerationStatus,
            result_model=BulkGenerationItemResult,
        )
    return _bulk_store


def get_batch_job_store() -> "TypedJobStore":
    """
    Get the enhanced batch generation job store.

    Returns:
        TypedJobStore configured for enhanced batch jobs
    """
    global _batch_store
    if _batch_store is None:
        # Import here to avoid circular imports
        from src.types.batch import EnhancedBatchStatus, EnhancedBatchItemResult

        _batch_store = TypedJobStore(
            job_type="enhanced_batch",
            status_model=EnhancedBatchStatus,
            result_model=EnhancedBatchItemResult,
        )
    return _batch_store
