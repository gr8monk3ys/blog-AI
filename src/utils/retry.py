"""Retry utilities with exponential backoff."""

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from ..exceptions import RetryExhaustedError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each attempt
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated function that retries on failure

    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def call_api():
            return api.request()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        # Final attempt failed
                        break

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor

            # All attempts exhausted
            raise RetryExhaustedError(
                message=f"Failed to execute {func.__name__} after {max_attempts} attempts",
                attempts=max_attempts,
                original_error=last_exception,
                details={
                    "function": func.__name__,
                    "initial_delay": initial_delay,
                    "backoff_factor": backoff_factor,
                },
            )

        return wrapper

    return decorator


def async_retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator that retries an async function with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each attempt
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated async function that retries on failure

    Example:
        @async_retry_with_backoff(max_attempts=3, initial_delay=1.0)
        async def call_api():
            return await api.request()
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        # Final attempt failed
                        break

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff_factor

            # All attempts exhausted
            raise RetryExhaustedError(
                message=f"Failed to execute {func.__name__} after {max_attempts} attempts",
                attempts=max_attempts,
                original_error=last_exception,
                details={
                    "function": func.__name__,
                    "initial_delay": initial_delay,
                    "backoff_factor": backoff_factor,
                },
            )

        return wrapper

    return decorator
