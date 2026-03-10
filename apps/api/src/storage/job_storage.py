"""
Job storage with Redis backend and in-memory fallback.

This module provides persistent job storage for batch processing with:
- Redis as primary storage for durability
- In-memory fallback when Redis is unavailable
- Automatic TTL management for job data
- Thread-safe operations
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .redis_client import redis_client

logger = logging.getLogger(__name__)

# Redis key prefixes
JOB_PREFIX = "batch:job:"
RESULTS_PREFIX = "batch:results:"
CANCEL_PREFIX = "batch:cancel:"
OWNER_PREFIX = "batch:owner:"
JOB_INDEX_KEY = "batch:job_index"
USER_JOBS_PREFIX = "batch:user_jobs:"  # Sorted set per user

# Default TTL for job data (7 days)
DEFAULT_TTL = 86400 * 7


class JobStorage:
    """
    Redis-backed job storage with fallback to in-memory.

    Provides persistent storage for batch jobs, results, and cancellation
    flags with automatic fallback to in-memory when Redis is unavailable.
    """

    def __init__(self) -> None:
        """Initialize JobStorage with empty fallback storage."""
        # In-memory fallback storage
        self._fallback_jobs: Dict[str, dict] = {}
        self._fallback_results: Dict[str, List[dict]] = {}
        self._fallback_cancel_flags: Dict[str, bool] = {}
        self._fallback_owners: Dict[str, str] = {}  # job_id -> user_id
        self._using_fallback: bool = False

    async def _get_redis(self):
        """Get Redis client, returns None if unavailable."""
        client = await redis_client.get_client()
        self._using_fallback = client is None
        return client

    @property
    def using_fallback(self) -> bool:
        """Check if currently using in-memory fallback."""
        return self._using_fallback

    # =========================================================================
    # Job Operations
    # =========================================================================

    async def save_job(
        self,
        job_id: str,
        job_data: dict,
        ttl: int = DEFAULT_TTL,
    ) -> bool:
        """
        Save a job to storage.

        Args:
            job_id: Unique job identifier
            job_data: Job data as dictionary
            ttl: Time-to-live in seconds (default: 7 days)

        Returns:
            True if saved successfully
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{JOB_PREFIX}{job_id}"
                # Store job data as JSON
                await redis.set(key, json.dumps(job_data), ex=ttl)
                # Add to job index for listing
                await redis.zadd(
                    JOB_INDEX_KEY,
                    {job_id: datetime.now().timestamp()},
                )
                logger.debug(f"Saved job {job_id} to Redis")
                return True
            except Exception as e:
                logger.warning(f"Redis save_job error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        self._fallback_jobs[job_id] = job_data
        logger.debug(f"Saved job {job_id} to in-memory storage")
        return True

    async def get_job(self, job_id: str) -> Optional[dict]:
        """
        Get a job from storage.

        Args:
            job_id: Unique job identifier

        Returns:
            Job data as dictionary, or None if not found
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{JOB_PREFIX}{job_id}"
                data = await redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis get_job error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        return self._fallback_jobs.get(job_id)

    async def update_job(self, job_id: str, updates: dict) -> bool:
        """
        Update specific fields in a job.

        Args:
            job_id: Unique job identifier
            updates: Dictionary of fields to update

        Returns:
            True if updated successfully
        """
        job_data = await self.get_job(job_id)
        if job_data is None:
            logger.warning(f"Job {job_id} not found for update")
            return False

        # Merge updates
        job_data.update(updates)

        # Save back
        return await self.save_job(job_id, job_data)

    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a job and its associated data.

        Args:
            job_id: Unique job identifier

        Returns:
            True if deleted successfully
        """
        redis = await self._get_redis()

        if redis:
            try:
                # Get owner to remove from user's job index
                owner = await self.get_owner(job_id)

                pipeline = redis.pipeline()
                pipeline.delete(f"{JOB_PREFIX}{job_id}")
                pipeline.delete(f"{RESULTS_PREFIX}{job_id}")
                pipeline.delete(f"{CANCEL_PREFIX}{job_id}")
                pipeline.delete(f"{OWNER_PREFIX}{job_id}")
                pipeline.zrem(JOB_INDEX_KEY, job_id)
                if owner:
                    pipeline.zrem(f"{USER_JOBS_PREFIX}{owner}", job_id)
                await pipeline.execute()
                logger.debug(f"Deleted job {job_id} from Redis")
            except Exception as e:
                logger.warning(f"Redis delete_job error: {str(e)}")

        # Also clean from fallback
        self._fallback_jobs.pop(job_id, None)
        self._fallback_results.pop(job_id, None)
        self._fallback_cancel_flags.pop(job_id, None)
        self._fallback_owners.pop(job_id, None)

        return True

    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict]:
        """
        List jobs with optional filtering.

        Args:
            status: Optional status filter
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of job data dictionaries
        """
        redis = await self._get_redis()
        jobs: List[dict] = []

        if redis:
            try:
                # Get job IDs from sorted set (most recent first)
                job_ids = await redis.zrevrange(
                    JOB_INDEX_KEY,
                    0,
                    -1,
                )

                for job_id in job_ids:
                    job_data = await self.get_job(job_id)
                    if job_data:
                        if status is None or job_data.get("status") == status:
                            jobs.append(job_data)
            except Exception as e:
                logger.warning(f"Redis list_jobs error: {str(e)}, falling back to memory")
                jobs = []

        # Fallback or merge with in-memory
        if not jobs or self._using_fallback:
            for job_id, job_data in self._fallback_jobs.items():
                if job_data not in jobs:
                    if status is None or job_data.get("status") == status:
                        jobs.append(job_data)

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)

        # Apply pagination
        return jobs[offset : offset + limit]

    async def job_exists(self, job_id: str) -> bool:
        """
        Check if a job exists.

        Args:
            job_id: Unique job identifier

        Returns:
            True if job exists
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{JOB_PREFIX}{job_id}"
                return await redis.exists(key) > 0
            except Exception as e:
                logger.warning(f"Redis job_exists error: {str(e)}")

        return job_id in self._fallback_jobs

    # =========================================================================
    # Results Operations
    # =========================================================================

    async def save_results(
        self,
        job_id: str,
        results: List[dict],
        ttl: int = DEFAULT_TTL,
    ) -> bool:
        """
        Save batch results to storage.

        Args:
            job_id: Unique job identifier
            results: List of result dictionaries
            ttl: Time-to-live in seconds

        Returns:
            True if saved successfully
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{RESULTS_PREFIX}{job_id}"
                await redis.set(key, json.dumps(results), ex=ttl)
                logger.debug(f"Saved {len(results)} results for job {job_id} to Redis")
                return True
            except Exception as e:
                logger.warning(f"Redis save_results error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        self._fallback_results[job_id] = results
        logger.debug(f"Saved {len(results)} results for job {job_id} to in-memory storage")
        return True

    async def get_results(self, job_id: str) -> List[dict]:
        """
        Get batch results from storage.

        Args:
            job_id: Unique job identifier

        Returns:
            List of result dictionaries
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{RESULTS_PREFIX}{job_id}"
                data = await redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis get_results error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        return self._fallback_results.get(job_id, [])

    async def append_result(self, job_id: str, result: dict) -> bool:
        """
        Append a single result to the results list.

        Args:
            job_id: Unique job identifier
            result: Result dictionary to append

        Returns:
            True if appended successfully
        """
        results = await self.get_results(job_id)
        results.append(result)
        return await self.save_results(job_id, results)

    # =========================================================================
    # Cancel Flag Operations
    # =========================================================================

    async def set_cancel_flag(self, job_id: str, cancelled: bool) -> bool:
        """
        Set cancellation flag for a job.

        Args:
            job_id: Unique job identifier
            cancelled: Whether the job should be cancelled

        Returns:
            True if set successfully
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{CANCEL_PREFIX}{job_id}"
                if cancelled:
                    # Set with 1 hour TTL (cancellation doesn't need long persistence)
                    await redis.set(key, "1", ex=3600)
                else:
                    await redis.delete(key)
                return True
            except Exception as e:
                logger.warning(f"Redis set_cancel_flag error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        self._fallback_cancel_flags[job_id] = cancelled
        return True

    async def get_cancel_flag(self, job_id: str) -> bool:
        """
        Get cancellation flag for a job.

        Args:
            job_id: Unique job identifier

        Returns:
            True if job should be cancelled
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{CANCEL_PREFIX}{job_id}"
                value = await redis.get(key)
                return value == "1"
            except Exception as e:
                logger.warning(f"Redis get_cancel_flag error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        return self._fallback_cancel_flags.get(job_id, False)

    # =========================================================================
    # Owner Operations (Multi-Tenant Support)
    # =========================================================================

    async def set_owner(
        self,
        job_id: str,
        user_id: str,
        ttl: int = DEFAULT_TTL,
    ) -> bool:
        """
        Set the owner of a job.

        Args:
            job_id: Unique job identifier
            user_id: User ID who owns this job
            ttl: Time-to-live in seconds

        Returns:
            True if set successfully
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{OWNER_PREFIX}{job_id}"
                await redis.set(key, user_id, ex=ttl)
                # Also add to user's job index
                user_jobs_key = f"{USER_JOBS_PREFIX}{user_id}"
                await redis.zadd(
                    user_jobs_key,
                    {job_id: datetime.now().timestamp()},
                )
                return True
            except Exception as e:
                logger.warning(f"Redis set_owner error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        self._fallback_owners[job_id] = user_id
        return True

    async def get_owner(self, job_id: str) -> Optional[str]:
        """
        Get the owner of a job.

        Args:
            job_id: Unique job identifier

        Returns:
            User ID who owns the job, or None if no owner set
        """
        redis = await self._get_redis()

        if redis:
            try:
                key = f"{OWNER_PREFIX}{job_id}"
                return await redis.get(key)
            except Exception as e:
                logger.warning(f"Redis get_owner error: {str(e)}, falling back to memory")

        # Fallback to in-memory
        return self._fallback_owners.get(job_id)

    async def verify_ownership(self, job_id: str, user_id: str) -> bool:
        """
        Verify that a user owns a job.

        For backwards compatibility, jobs without an owner are accessible
        to any authenticated user (legacy jobs).

        Args:
            job_id: Unique job identifier
            user_id: User ID to verify

        Returns:
            True if user owns the job or no owner is set (legacy)
        """
        owner = await self.get_owner(job_id)
        if owner is None:
            # Legacy job without ownership - allow access
            return True
        return owner == user_id

    async def get_job_if_owned(
        self,
        job_id: str,
        user_id: str,
    ) -> Optional[dict]:
        """
        Get a job only if the user owns it.

        Args:
            job_id: Unique job identifier
            user_id: User ID requesting access

        Returns:
            Job data if user owns it, None otherwise
        """
        if not await self.verify_ownership(job_id, user_id):
            return None
        return await self.get_job(job_id)

    async def list_user_jobs(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict]:
        """
        List jobs owned by a specific user.

        Args:
            user_id: User ID to filter by
            status: Optional status filter
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of job data dictionaries owned by the user
        """
        redis = await self._get_redis()
        jobs: List[dict] = []

        if redis:
            try:
                # Get job IDs from user's sorted set (most recent first)
                user_jobs_key = f"{USER_JOBS_PREFIX}{user_id}"
                job_ids = await redis.zrevrange(user_jobs_key, 0, -1)

                for job_id in job_ids:
                    job_data = await self.get_job(job_id)
                    if job_data:
                        if status is None or job_data.get("status") == status:
                            jobs.append(job_data)
            except Exception as e:
                logger.warning(f"Redis list_user_jobs error: {str(e)}, falling back to memory")
                jobs = []

        # Fallback or merge with in-memory
        if not jobs or self._using_fallback:
            for job_id, job_data in self._fallback_jobs.items():
                owner = self._fallback_owners.get(job_id)
                if owner == user_id and job_data not in jobs:
                    if status is None or job_data.get("status") == status:
                        jobs.append(job_data)

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)

        # Apply pagination
        return jobs[offset : offset + limit]

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def get_storage_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage stats
        """
        redis = await self._get_redis()
        stats = {
            "backend": "redis" if redis else "memory",
            "redis_available": redis is not None,
        }

        if redis:
            try:
                # Count jobs in Redis
                job_count = await redis.zcard(JOB_INDEX_KEY)
                stats["job_count"] = job_count
            except Exception as e:
                stats["error"] = str(e)
        else:
            stats["job_count"] = len(self._fallback_jobs)
            stats["results_count"] = len(self._fallback_results)

        return stats

    async def cleanup_expired(self) -> int:
        """
        Clean up expired entries from fallback storage.

        Redis handles TTL automatically, this is for in-memory cleanup.

        Returns:
            Number of entries cleaned up
        """
        # In-memory storage doesn't have TTL, so we can implement
        # a simple cleanup based on creation time if needed
        # For now, just return 0 as Redis handles this automatically
        return 0

    async def migrate_to_redis(self) -> int:
        """
        Migrate in-memory data to Redis if available.

        Call this after Redis becomes available to persist
        any data that was stored in memory during fallback.

        Returns:
            Number of items migrated
        """
        redis = await self._get_redis()
        if not redis:
            return 0

        migrated = 0

        # Migrate jobs
        for job_id, job_data in self._fallback_jobs.items():
            try:
                await self.save_job(job_id, job_data)
                migrated += 1
            except Exception as e:
                logger.warning(f"Failed to migrate job {job_id}: {str(e)}")

        # Migrate results
        for job_id, results in self._fallback_results.items():
            try:
                await self.save_results(job_id, results)
            except Exception as e:
                logger.warning(f"Failed to migrate results for {job_id}: {str(e)}")

        # Migrate cancel flags
        for job_id, cancelled in self._fallback_cancel_flags.items():
            try:
                await self.set_cancel_flag(job_id, cancelled)
            except Exception as e:
                logger.warning(f"Failed to migrate cancel flag for {job_id}: {str(e)}")

        if migrated > 0:
            logger.info(f"Migrated {migrated} jobs from memory to Redis")

        return migrated


# Singleton instance
job_storage = JobStorage()
