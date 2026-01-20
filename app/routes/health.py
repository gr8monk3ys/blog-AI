"""
Health check and root endpoints.
"""

import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db

router = APIRouter(tags=["health"])


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    version: str
    checks: Dict[str, Any]


class ServiceStatus(BaseModel):
    """Individual service status."""

    status: str
    latency_ms: Optional[float] = None
    message: Optional[str] = None


def check_database(db: Session) -> ServiceStatus:
    """Check database connectivity."""
    import time

    start = time.time()
    try:
        db.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        return ServiceStatus(status="healthy", latency_ms=round(latency, 2))
    except Exception as e:
        return ServiceStatus(status="unhealthy", message=str(e))


def check_llm_config() -> ServiceStatus:
    """Check if LLM API keys are configured."""
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_gemini = bool(os.environ.get("GEMINI_API_KEY"))

    if has_openai or has_anthropic or has_gemini:
        providers = []
        if has_openai:
            providers.append("openai")
        if has_anthropic:
            providers.append("anthropic")
        if has_gemini:
            providers.append("gemini")
        return ServiceStatus(
            status="healthy",
            message=f"Configured providers: {', '.join(providers)}",
        )
    return ServiceStatus(
        status="degraded",
        message="No LLM API keys configured",
    )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint for monitoring and load balancers.

    Checks:
    - Database connectivity
    - LLM provider configuration
    """
    checks = {
        "database": check_database(db).model_dump(),
        "llm_config": check_llm_config().model_dump(),
    }

    # Determine overall status
    all_healthy = all(c.get("status") == "healthy" for c in checks.values())
    any_unhealthy = any(c.get("status") == "unhealthy" for c in checks.values())

    if all_healthy:
        status = "healthy"
    elif any_unhealthy:
        status = "unhealthy"
    else:
        status = "degraded"

    return HealthCheckResponse(
        status=status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0",
        checks=checks,
    )


@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe endpoint.

    Returns 200 if the application is running.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint.

    Returns 200 only if all critical dependencies are available.
    """
    db_status = check_database(db)

    if db_status.status == "unhealthy":
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Database unavailable")

    return {"status": "ready"}


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Blog AI API",
        "version": "1.0.0",
        "api_version": "v1",
        "docs": "/docs",
        "health": "/health",
        "api_base": "/api/v1",
    }
