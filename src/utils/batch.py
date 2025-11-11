"""Batch processing utilities for blog-AI.

Provides utilities for processing multiple content generations in parallel,
with progress tracking, error handling, and resume capabilities.
"""

import asyncio
import json
import logging
from collections.abc import Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T")


class JobStatus(str, Enum):
    """Status of a batch job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchItem(Generic[T]):
    """Single item in a batch job."""

    id: str
    input: T
    status: JobStatus = JobStatus.PENDING
    result: Any | None = None
    error: str | None = None
    attempts: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class BatchJob(Generic[T]):
    """Batch processing job with state tracking."""

    job_id: str
    items: list[BatchItem[T]] = field(default_factory=list)
    total: int = 0
    completed: int = 0
    failed: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: JobStatus = JobStatus.PENDING

    def add_item(self, item_id: str, input_data: T) -> None:
        """Add an item to the batch."""
        item = BatchItem(id=item_id, input=input_data)
        self.items.append(item)
        self.total += 1

    def get_pending_items(self) -> list[BatchItem[T]]:
        """Get all pending items."""
        return [item for item in self.items if item.status == JobStatus.PENDING]

    def get_failed_items(self) -> list[BatchItem[T]]:
        """Get all failed items."""
        return [item for item in self.items if item.status == JobStatus.FAILED]

    def update_progress(self) -> None:
        """Update progress counters."""
        self.completed = sum(1 for item in self.items if item.status == JobStatus.COMPLETED)
        self.failed = sum(1 for item in self.items if item.status == JobStatus.FAILED)

        # Update overall status
        if self.completed + self.failed == self.total:
            self.status = JobStatus.COMPLETED
            self.completed_at = datetime.now()

    def get_progress_percentage(self) -> float:
        """Get completion percentage."""
        if self.total == 0:
            return 0.0
        return (self.completed + self.failed) / self.total * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "items": [
                {
                    "id": item.id,
                    "status": item.status.value,
                    "error": item.error,
                    "attempts": item.attempts,
                    "started_at": item.started_at.isoformat() if item.started_at else None,
                    "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                }
                for item in self.items
            ],
        }


class BatchProcessor(Generic[T]):
    """
    Process multiple items in parallel with progress tracking.

    Supports async processing, error handling, retry logic, and state persistence.
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        max_retries: int = 3,
        state_dir: Path | None = None,
    ):
        """
        Initialize batch processor.

        Args:
            max_concurrent: Maximum number of concurrent operations (default: 5)
            max_retries: Maximum retry attempts per item (default: 3)
            state_dir: Directory for saving job state (optional)
        """
        self._max_concurrent = max_concurrent
        self._max_retries = max_retries
        self._state_dir = state_dir
        self._semaphore = asyncio.Semaphore(max_concurrent)

        if state_dir:
            state_dir.mkdir(parents=True, exist_ok=True)

    async def process_batch(
        self,
        job: BatchJob[T],
        processor: Callable[[T], Any] | Callable[[T], Coroutine[Any, Any, Any]],
        on_progress: Callable[[BatchJob[T]], None] | None = None,
    ) -> BatchJob[T]:
        """
        Process all items in a batch.

        Args:
            job: Batch job to process
            processor: Function or coroutine to process each item
            on_progress: Optional callback for progress updates

        Returns:
            Completed batch job
        """
        logger.info(f"Starting batch job {job.job_id} with {job.total} items")
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()

        # Save initial state
        self._save_state(job)

        # Get pending items (for resume support)
        pending_items = job.get_pending_items()
        logger.info(f"Processing {len(pending_items)} pending items")

        # Process items concurrently
        tasks = [self._process_item(item, processor, job, on_progress) for item in pending_items]

        await asyncio.gather(*tasks, return_exceptions=True)

        # Update final status
        job.update_progress()
        self._save_state(job)

        logger.info(
            f"Batch job {job.job_id} completed: "
            f"{job.completed} succeeded, {job.failed} failed"
        )

        return job

    async def _process_item(
        self,
        item: BatchItem[T],
        processor: Callable[[T], Any] | Callable[[T], Coroutine[Any, Any, Any]],
        job: BatchJob[T],
        on_progress: Callable[[BatchJob[T]], None] | None = None,
    ) -> None:
        """Process a single item with retry logic."""
        async with self._semaphore:
            while item.attempts < self._max_retries:
                try:
                    item.attempts += 1
                    item.status = JobStatus.RUNNING
                    item.started_at = datetime.now()

                    logger.debug(f"Processing item {item.id} (attempt {item.attempts})")

                    # Call processor (support both sync and async)
                    if asyncio.iscoroutinefunction(processor):
                        result = await processor(item.input)
                    else:
                        result = await asyncio.to_thread(processor, item.input)

                    # Success
                    item.result = result
                    item.status = JobStatus.COMPLETED
                    item.completed_at = datetime.now()

                    logger.info(f"✓ Item {item.id} completed")
                    break

                except Exception as e:
                    error_msg = f"{type(e).__name__}: {e}"
                    logger.error(f"✗ Item {item.id} failed (attempt {item.attempts}): {error_msg}")

                    item.error = error_msg

                    # If max retries reached, mark as failed
                    if item.attempts >= self._max_retries:
                        item.status = JobStatus.FAILED
                        item.completed_at = datetime.now()
                        logger.error(f"✗ Item {item.id} failed permanently after {item.attempts} attempts")
                    else:
                        # Reset status for retry
                        item.status = JobStatus.PENDING
                        # Exponential backoff
                        await asyncio.sleep(2**item.attempts)

            # Update progress
            job.update_progress()
            self._save_state(job)

            # Call progress callback
            if on_progress:
                on_progress(job)

    def _save_state(self, job: BatchJob[T]) -> None:
        """Save job state to disk."""
        if not self._state_dir:
            return

        state_file = self._state_dir / f"{job.job_id}.json"
        try:
            with open(state_file, "w") as f:
                json.dump(job.to_dict(), f, indent=2)
            logger.debug(f"Saved job state to {state_file}")
        except Exception as e:
            logger.error(f"Failed to save job state: {e}")

    def load_state(self, job_id: str) -> dict[str, Any] | None:
        """Load job state from disk."""
        if not self._state_dir:
            return None

        state_file = self._state_dir / f"{job_id}.json"
        if not state_file.exists():
            return None

        try:
            with open(state_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load job state: {e}")
            return None


def read_topics_from_file(file_path: Path) -> list[str]:
    """
    Read topics from a text file.

    Supports:
    - One topic per line
    - Lines starting with # are comments
    - Empty lines are ignored

    Args:
        file_path: Path to topics file

    Returns:
        List of topic strings

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Topics file not found: {file_path}")

    topics = []
    with open(file_path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            topics.append(line)

    logger.info(f"Loaded {len(topics)} topics from {file_path}")
    return topics


def create_progress_bar(job: BatchJob, width: int = 50) -> str:
    """
    Create a text-based progress bar.

    Args:
        job: Batch job
        width: Width of progress bar (default: 50)

    Returns:
        Progress bar string
    """
    percentage = job.get_progress_percentage()
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)

    return (
        f"[{bar}] {percentage:.1f}% "
        f"({job.completed}/{job.total} completed, {job.failed} failed)"
    )
