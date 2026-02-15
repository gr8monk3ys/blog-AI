"""
Non-sensitive configuration endpoints for the frontend/clients.

These endpoints expose runtime capabilities (for example which LLM providers are
configured) without leaking secrets.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.config import get_settings

router = APIRouter(tags=["config"])


class LLMConfigResponse(BaseModel):
    """LLM provider capabilities for the current deployment."""

    default_provider: Optional[str] = Field(
        default=None,
        description="Default provider the backend will use when none is specified",
    )
    available_providers: List[str] = Field(
        default_factory=list,
        description="Providers that are configured and available",
    )
    models: Dict[str, str] = Field(
        default_factory=dict,
        description="Model names per provider (non-sensitive)",
    )


@router.get(
    "/config/llm",
    response_model=LLMConfigResponse,
    summary="Get LLM provider configuration",
    description="Returns which LLM providers are configured, plus the default provider.",
)
async def get_llm_config() -> LLMConfigResponse:
    settings = get_settings()
    llm = settings.llm

    return LLMConfigResponse(
        default_provider=llm.default_provider,
        available_providers=llm.available_providers,
        models={
            "openai": llm.openai_model,
            "anthropic": llm.anthropic_model,
            "gemini": llm.gemini_model,
        },
    )

