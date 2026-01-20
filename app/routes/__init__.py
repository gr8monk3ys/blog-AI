"""API routes for the Blog AI application."""

from .blog import router as blog_router
from .book import router as book_router
from .conversations import router as conversations_router
from .health import router as health_router
from .websocket import router as websocket_router

__all__ = [
    "blog_router",
    "book_router",
    "conversations_router",
    "health_router",
    "websocket_router",
]
