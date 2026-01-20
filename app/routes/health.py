"""
Health check and root endpoints.
"""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


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
