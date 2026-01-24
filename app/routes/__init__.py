"""API routes for the Blog AI application."""

from .analytics import router as analytics_router
from .blog import router as blog_router
from .book import router as book_router
from .bulk import router as bulk_router
from .conversations import router as conversations_router
from .export import router as export_router
from .health import router as health_router
from .tools import router as tools_router
from .usage import router as usage_router
from .websocket import router as websocket_router

__all__ = [
    "analytics_router",
    "blog_router",
    "book_router",
    "bulk_router",
    "conversations_router",
    "export_router",
    "health_router",
    "tools_router",
    "usage_router",
    "websocket_router",
]
