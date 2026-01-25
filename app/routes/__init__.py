"""API routes for the Blog AI application."""

from .analytics import router as analytics_router
from .batch import router as batch_router
from .blog import router as blog_router
from .book import router as book_router
from .brand_voice import router as brand_voice_router
from .bulk import router as bulk_router
from .conversations import router as conversations_router
from .export import router as export_router
from .health import router as health_router
from .images import router as images_router
from .payments import router as payments_router
from .remix import router as remix_router
from .tools import router as tools_router
from .usage import router as usage_router
from .websocket import router as websocket_router

__all__ = [
    "analytics_router",
    "batch_router",
    "blog_router",
    "book_router",
    "brand_voice_router",
    "bulk_router",
    "conversations_router",
    "export_router",
    "health_router",
    "images_router",
    "payments_router",
    "remix_router",
    "tools_router",
    "usage_router",
    "websocket_router",
]
