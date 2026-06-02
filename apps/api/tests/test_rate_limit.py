"""
Unit tests for the rate limiter's core logic.

Covers the in-memory sliding-window backend, tier-limit validation, and the
environment-driven generation-tier loader. These are pure-logic units (no DB,
Redis, or network) and serve as the safety net for refactors of
``app/middleware/rate_limit.py`` (see docs/REMEDIATION_PLAN.md P1.2/P2.2).
"""

import os

import pytest

from app.middleware.rate_limit import (
    DEFAULT_RATE_LIMITS,
    TIER_RATE_LIMITS,
    GenerationRateLimiter,
    InMemoryBackend,
    RateLimiter,
    TierRateLimits,
    _load_generation_tier_limits,
)
from src.types.usage import SubscriptionTier

# ---------------------------------------------------------------------------
# TierRateLimits validation
# ---------------------------------------------------------------------------


def test_tier_rate_limits_valid():
    limits = TierRateLimits(per_minute=10, per_hour=100)
    assert limits.per_minute == 10
    assert limits.per_hour == 100


@pytest.mark.parametrize(
    "per_minute, per_hour",
    [
        (0, 100),  # per_minute must be positive
        (-1, 100),  # negative per_minute
        (10, 0),  # per_hour must be positive
        (10, 5),  # per_hour must be >= per_minute
    ],
)
def test_tier_rate_limits_invalid(per_minute, per_hour):
    with pytest.raises(ValueError):
        TierRateLimits(per_minute=per_minute, per_hour=per_hour)


def test_default_and_configured_tiers_present():
    assert DEFAULT_RATE_LIMITS.per_minute > 0
    # Every subscription tier has a configured request rate limit.
    for tier in (
        SubscriptionTier.FREE,
        SubscriptionTier.STARTER,
        SubscriptionTier.PRO,
        SubscriptionTier.BUSINESS,
    ):
        assert tier in TIER_RATE_LIMITS
        assert TIER_RATE_LIMITS[tier].per_hour >= TIER_RATE_LIMITS[tier].per_minute


# ---------------------------------------------------------------------------
# Generation-tier env loader
# ---------------------------------------------------------------------------


def test_load_generation_tier_limits_defaults(monkeypatch):
    for key in list(os.environ):
        if key.startswith("RATE_LIMIT_GEN_"):
            monkeypatch.delenv(key, raising=False)
    limits = _load_generation_tier_limits()
    assert limits[SubscriptionTier.FREE].per_minute == 5
    assert limits[SubscriptionTier.FREE].per_hour == 30
    assert limits[SubscriptionTier.BUSINESS].per_minute == 60


def test_load_generation_tier_limits_env_override(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_GEN_FREE_PER_MINUTE", "7")
    monkeypatch.setenv("RATE_LIMIT_GEN_FREE_PER_HOUR", "70")
    limits = _load_generation_tier_limits()
    assert limits[SubscriptionTier.FREE].per_minute == 7
    assert limits[SubscriptionTier.FREE].per_hour == 70


def test_load_generation_tier_limits_invalid_falls_back(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_GEN_FREE_PER_MINUTE", "not-a-number")
    limits = _load_generation_tier_limits()
    assert limits[SubscriptionTier.FREE].per_minute == 5  # default


# ---------------------------------------------------------------------------
# InMemoryBackend sliding window
# ---------------------------------------------------------------------------


async def test_in_memory_record_request_counts_within_window():
    backend = InMemoryBackend()
    t = 1000.0
    count1, oldest1 = await backend.record_request("user:a", t, window_seconds=60)
    count2, oldest2 = await backend.record_request("user:a", t + 1, window_seconds=60)
    assert count1 == 1
    assert count2 == 2
    # Oldest timestamp in the window stays at the first request.
    assert oldest2 == pytest.approx(t)


async def test_in_memory_expires_outside_window():
    backend = InMemoryBackend()
    t = 1000.0
    await backend.record_request("user:b", t, window_seconds=60)
    # A request 61s later falls outside the 60s window; the old one is dropped.
    count, oldest = await backend.record_request("user:b", t + 61, window_seconds=60)
    assert count == 1
    assert oldest == pytest.approx(t + 61)


async def test_in_memory_get_request_count_does_not_record():
    backend = InMemoryBackend()
    t = 1000.0
    await backend.record_request("user:c", t, window_seconds=60)
    # Reading the count must not add to the window.
    n1 = await backend.get_request_count("user:c", t + 2, window_seconds=60)
    n2 = await backend.get_request_count("user:c", t + 3, window_seconds=60)
    assert n1 == 1
    assert n2 == 1


async def test_in_memory_get_request_count_unknown_key_is_zero():
    backend = InMemoryBackend()
    assert await backend.get_request_count("nobody", 1000.0, window_seconds=60) == 0


async def test_in_memory_keys_are_isolated():
    backend = InMemoryBackend()
    t = 1000.0
    await backend.record_request("user:x", t, window_seconds=60)
    await backend.record_request("user:x", t + 1, window_seconds=60)
    count_y, _ = await backend.record_request("user:y", t + 2, window_seconds=60)
    assert count_y == 1


async def test_in_memory_cleanup_drops_expired_entries():
    backend = InMemoryBackend()
    t = 1000.0
    await backend.record_request("user:z", t, window_seconds=60)
    await backend.cleanup("user:z", t + 120, window_seconds=60)
    assert await backend.get_request_count("user:z", t + 120, window_seconds=60) == 0


# ---------------------------------------------------------------------------
# RateLimiter / GenerationRateLimiter check_rate_limit behavior
# ---------------------------------------------------------------------------


async def test_general_rate_limiter_allows_under_limit_blocks_over():
    backend = InMemoryBackend()
    limiter = RateLimiter(backend=backend)
    # FREE general tier: 10 per minute.
    limit = TIER_RATE_LIMITS[SubscriptionTier.FREE].per_minute
    for _ in range(limit):
        result = await limiter.check_rate_limit("u1", SubscriptionTier.FREE)
        assert result.allowed is True
    blocked = await limiter.check_rate_limit("u1", SubscriptionTier.FREE)
    assert blocked.allowed is False
    assert blocked.window == "minute"
    assert blocked.retry_after is not None and blocked.retry_after >= 1


async def test_generation_rate_limiter_is_tighter_than_general():
    backend = InMemoryBackend()
    gen = GenerationRateLimiter(backend=backend)
    # FREE generation tier defaults to 5 per minute (tighter than general's 10).
    for _ in range(5):
        assert (await gen.check_rate_limit("u2", SubscriptionTier.FREE)).allowed is True
    assert (await gen.check_rate_limit("u2", SubscriptionTier.FREE)).allowed is False


async def test_general_and_generation_buckets_are_separate():
    # Sharing one backend, the two limiters must not contend because their
    # window keys are prefixed differently ("" vs "gen:").
    backend = InMemoryBackend()
    general = RateLimiter(backend=backend)
    gen = GenerationRateLimiter(backend=backend)

    # Exhaust the generation limit (5/min for FREE).
    for _ in range(5):
        await gen.check_rate_limit("shared", SubscriptionTier.FREE)
    assert (
        await gen.check_rate_limit("shared", SubscriptionTier.FREE)
    ).allowed is False

    # The general limiter for the same user is unaffected.
    assert (
        await general.check_rate_limit("shared", SubscriptionTier.FREE)
    ).allowed is True


async def test_remaining_decrements_per_request():
    backend = InMemoryBackend()
    limiter = RateLimiter(backend=backend)
    first = await limiter.check_rate_limit("u3", SubscriptionTier.FREE)
    second = await limiter.check_rate_limit("u3", SubscriptionTier.FREE)
    assert first.remaining > second.remaining
