"""
Provider selection helpers for batch generation.

Pure-ish helpers for validating and choosing LLM providers per batch item:
normalization, configured-provider validation, and strategy-based rotation
(single, round-robin, cost-optimized, quality-optimized).

Extracted from app/routes/batch.py to keep that router focused on HTTP
handlers (see docs/REMEDIATION_PLAN.md P2.3).
"""

from typing import Dict, List, Optional

from fastapi import HTTPException, status

from app.models.requests import ALLOWED_PROVIDERS
from src.config import get_settings
from src.types.batch import ProviderStrategy

# Provider rotation state for round-robin (in-memory; rotation is stateless
# across restarts, which is acceptable for best-effort load spreading).
_provider_index: Dict[str, int] = {}


def _default_provider() -> str:
    v = get_settings().llm.default_provider
    return v or "openai"


def _normalize_provider(provider: Optional[str], *, default: str) -> str:
    v = (provider or "").strip().lower() or default
    if v not in ALLOWED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider '{v}'. Allowed: {', '.join(sorted(ALLOWED_PROVIDERS))}",
        )

    configured = get_settings().llm.available_providers
    if configured and v not in configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": f"Provider '{v}' is not configured for this deployment",
                "configured_providers": configured,
            },
        )
    return v


def _validate_configured_providers(preferred: str, fallbacks: List[str]) -> None:
    configured = get_settings().llm.available_providers
    if not configured:
        return

    requested = [preferred] + list(fallbacks or [])
    invalid = [p for p in requested if p not in configured]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "One or more requested providers are not configured for this deployment",
                "invalid_providers": invalid,
                "configured_providers": configured,
            },
        )


def _get_next_provider(
    job_id: str, strategy: ProviderStrategy, preferred: str, fallbacks: List[str]
) -> str:
    """Get the next provider based on strategy."""
    all_providers = [preferred] + [p for p in fallbacks if p != preferred]

    if strategy == ProviderStrategy.SINGLE:
        return preferred
    elif strategy == ProviderStrategy.ROUND_ROBIN:
        if job_id not in _provider_index:
            _provider_index[job_id] = 0
        idx = _provider_index[job_id] % len(all_providers)
        _provider_index[job_id] += 1
        return all_providers[idx]
    elif strategy == ProviderStrategy.COST_OPTIMIZED:
        # Prefer Gemini (cheapest), then Anthropic, then OpenAI
        cost_order = ["gemini", "anthropic", "openai"]
        for p in cost_order:
            if p in all_providers:
                return p
        return preferred
    elif strategy == ProviderStrategy.QUALITY_OPTIMIZED:
        # Prefer OpenAI (GPT-4), then Anthropic, then Gemini
        quality_order = ["openai", "anthropic", "gemini"]
        for p in quality_order:
            if p in all_providers:
                return p
        return preferred
    else:
        return preferred
