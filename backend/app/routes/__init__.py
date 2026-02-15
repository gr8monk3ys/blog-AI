"""API routes for the Blog AI application."""

from .analytics import router as analytics_router
from .batch import router as batch_router
from .blog import router as blog_router
from .book import router as book_router
from .brand_voice import router as brand_voice_router
from .bulk import router as bulk_router
from .config import router as config_router
from .content import router as content_router
from .conversations import router as conversations_router
from .export import router as export_router
from .extension import router as extension_router
from .health import router as health_router
from .images import router as images_router
from .organizations import router as organizations_router
from .payments import router as payments_router
from .remix import router as remix_router
from .social import router as social_router
from .sso import router as sso_router
from .sso_admin import router as sso_admin_router
from .streaming import router as streaming_router
from .tools import router as tools_router
from .usage import router as usage_router
from .webhooks import router as webhooks_router
from .websocket import router as websocket_router
from .zapier import router as zapier_router

__all__ = [
    "analytics_router",
    "batch_router",
    "blog_router",
    "book_router",
    "brand_voice_router",
    "bulk_router",
    "config_router",
    "content_router",
    "conversations_router",
    "export_router",
    "extension_router",
    "health_router",
    "images_router",
    "organizations_router",
    "payments_router",
    "remix_router",
    "social_router",
    "sso_router",
    "sso_admin_router",
    "streaming_router",
    "tools_router",
    "usage_router",
    "webhooks_router",
    "websocket_router",
    "zapier_router",
]
