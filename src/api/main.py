"""FastAPI application for blog-AI."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import settings
from .models import ErrorResponse, HealthResponse
from .routes import blog, book, faq

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting blog-AI API")
    logger.info(f"Version: {app.version}")
    logger.info(f"Environment: {settings.environment}")

    yield

    # Shutdown
    logger.info("Shutting down blog-AI API")


# Create FastAPI app
app = FastAPI(
    title="blog-AI API",
    description="REST API for AI-powered content generation",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=f"HTTP_{exc.status_code}",
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            details={"message": str(exc)},
            code="INTERNAL_ERROR",
        ).model_dump(),
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status and available providers
    """
    # Check provider availability
    providers = {
        "openai": bool(settings.openai_api_key),
        "anthropic": False,
    }

    # Try to import anthropic
    try:
        import anthropic  # noqa: F401

        providers["anthropic"] = bool(settings.anthropic_api_key)
    except ImportError:
        pass

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        providers=providers,
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "blog-AI API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


# Include routers
app.include_router(blog.router, prefix="/api/v1/blog", tags=["Blog"])
app.include_router(book.router, prefix="/api/v1/book", tags=["Book"])
app.include_router(faq.router, prefix="/api/v1/faq", tags=["FAQ"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
