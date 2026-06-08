"""
Unit tests for batch provider-selection strategy logic.

Covers _get_next_provider across all ProviderStrategy modes. These are pure
(strategy-driven) selections; provider validation (which depends on settings)
is exercised by the route tests. Establishes a safety net for the batch
provider extraction (docs/REMEDIATION_PLAN.md P2.3).
"""

from app.routes.batch_providers import _get_next_provider, _provider_index
from src.types.batch import ProviderStrategy


def test_single_strategy_always_returns_preferred():
    assert (
        _get_next_provider("job1", ProviderStrategy.SINGLE, "openai", ["gemini"])
        == "openai"
    )


def test_round_robin_cycles_through_providers():
    _provider_index.pop("rr-job", None)
    seq = [
        _get_next_provider(
            "rr-job", ProviderStrategy.ROUND_ROBIN, "openai", ["gemini", "anthropic"]
        )
        for _ in range(4)
    ]
    # preferred + fallbacks (deduped) = [openai, gemini, anthropic], cycling.
    assert seq == ["openai", "gemini", "anthropic", "openai"]


def test_round_robin_dedups_preferred_in_fallbacks():
    _provider_index.pop("rr-dedup", None)
    seq = [
        _get_next_provider(
            "rr-dedup", ProviderStrategy.ROUND_ROBIN, "openai", ["openai", "gemini"]
        )
        for _ in range(3)
    ]
    assert seq == ["openai", "gemini", "openai"]


def test_cost_optimized_prefers_cheapest_available():
    assert (
        _get_next_provider(
            "c1", ProviderStrategy.COST_OPTIMIZED, "openai", ["gemini", "anthropic"]
        )
        == "gemini"
    )
    # Falls through cost order when gemini absent.
    assert (
        _get_next_provider(
            "c2", ProviderStrategy.COST_OPTIMIZED, "openai", ["anthropic"]
        )
        == "anthropic"
    )


def test_quality_optimized_prefers_openai_available():
    assert (
        _get_next_provider(
            "q1", ProviderStrategy.QUALITY_OPTIMIZED, "gemini", ["openai", "anthropic"]
        )
        == "openai"
    )
    assert (
        _get_next_provider(
            "q2", ProviderStrategy.QUALITY_OPTIMIZED, "gemini", ["anthropic"]
        )
        == "anthropic"
    )


def test_cost_optimized_falls_back_to_preferred_when_none_match():
    # No provider in the cost order is present besides preferred itself.
    assert (
        _get_next_provider("c3", ProviderStrategy.COST_OPTIMIZED, "openai", [])
        == "openai"
    )
