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

from app.middleware import HTTPSRedirectMiddleware, RateLimitMiddleware
from app.routes import (
    blog_router,
    book_router,
    conversations_router,
    health_router,
    websocket_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Blog AI API",
    description="AI-powered content generation API for blog posts and books",
    version="1.0.0",
)

# CORS configuration - use environment variable for allowed origins
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# Add HTTPS redirect middleware in production
HTTPS_REDIRECT_ENABLED = os.environ.get("HTTPS_REDIRECT_ENABLED", "false").lower() == "true"
if HTTPS_REDIRECT_ENABLED:
    app.add_middleware(HTTPSRedirectMiddleware)
    logger.info("HTTPS redirect middleware enabled")

# Add rate limiting middleware
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
if RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        general_limit=int(os.environ.get("RATE_LIMIT_GENERAL", "60")),
        generation_limit=int(os.environ.get("RATE_LIMIT_GENERATION", "10")),
        window_seconds=60,
    )


# =============================================================================
# Include Routers
# =============================================================================

# Health and root endpoints (no auth required)
app.include_router(health_router)

# Main API routes (at root level for backward compatibility)
app.include_router(conversations_router)
app.include_router(blog_router)
app.include_router(book_router)
app.include_router(websocket_router)

# Create versioned API router
api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

# Add versioned routes
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(blog_router)
api_v1_router.include_router(book_router)

# Include versioned router
app.include_router(api_v1_router)


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
