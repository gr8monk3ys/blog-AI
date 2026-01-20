"""
Backend server for the Blog AI application.
Provides API endpoints for generating blog posts and books.

This is the main entry point that assembles the modular components
from the app package.
"""

import logging
import os

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import get_config, setup_logging
from app.db import init_db
from app.middleware import HTTPSRedirectMiddleware, RateLimitMiddleware
from app.routes import (
    blog_router,
    book_router,
    conversations_router,
    health_router,
    websocket_router,
)
from app.routes.auth import router as auth_router

# Load configuration
config = get_config()

# Setup structured logging
setup_logging(
    level=config.log_level,
    json_format=config.log_format == "json",
)
logger = logging.getLogger(__name__)

# Validate configuration and log warnings
warnings = config.validate()
for warning in warnings:
    logger.warning(warning)

# Initialize FastAPI app
app = FastAPI(
    title="Blog AI API",
    description="AI-powered content generation API for blog posts and books",
    version="1.0.0",
    docs_url="/docs" if config.is_development else None,
    redoc_url="/redoc" if config.is_development else None,
)

# =============================================================================
# Middleware
# =============================================================================

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors.allowed_origins,
    allow_credentials=config.cors.allow_credentials,
    allow_methods=config.cors.allowed_methods,
    allow_headers=config.cors.allowed_headers,
)

# Add HTTPS redirect middleware in production
if config.https_redirect:
    app.add_middleware(HTTPSRedirectMiddleware)
    logger.info("HTTPS redirect middleware enabled")

# Add rate limiting middleware
if config.rate_limit.enabled:
    app.add_middleware(
        RateLimitMiddleware,
        general_limit=config.rate_limit.general_limit,
        generation_limit=config.rate_limit.generation_limit,
        window_seconds=config.rate_limit.window_seconds,
    )
    logger.info("Rate limiting middleware enabled")


# =============================================================================
# Startup/Shutdown Events
# =============================================================================
@app.on_event("startup")
async def startup_event():
    """Initialize resources on application startup."""
    logger.info("Starting Blog AI API...")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    logger.info(f"Blog AI API started in {config.environment} mode")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on application shutdown."""
    logger.info("Shutting down Blog AI API...")


# =============================================================================
# Include Routers
# =============================================================================

# Health and root endpoints (no auth required)
app.include_router(health_router)

# Authentication routes
app.include_router(auth_router)

# Main API routes (at root level for backward compatibility)
app.include_router(conversations_router)
app.include_router(blog_router)
app.include_router(book_router)
app.include_router(websocket_router)

# Create versioned API router
api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

# Add versioned routes
api_v1_router.include_router(auth_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(blog_router)
api_v1_router.include_router(book_router)

# Include versioned router
app.include_router(api_v1_router)


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=config.host,
        port=config.port,
        reload=config.is_development,
    )
