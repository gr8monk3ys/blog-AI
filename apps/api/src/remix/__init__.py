"""
Content Remix Engine.

Transform content across multiple formats with intelligent adaptation.
"""

from src.remix.analyzer import ContentAnalyzer, analyze_content
from src.remix.adapters import (
    FormatAdapter,
    TwitterThreadAdapter,
    LinkedInPostAdapter,
    EmailNewsletterAdapter,
    YouTubeScriptAdapter,
    InstagramCarouselAdapter,
    PodcastNotesAdapter,
    GenericAdapter,
    get_adapter,
    ADAPTERS,
)
from src.remix.service import (
    RemixService,
    get_remix_service,
    remix_content,
    preview_remix,
)

__all__ = [
    # Analyzer
    "ContentAnalyzer",
    "analyze_content",
    # Adapters
    "FormatAdapter",
    "TwitterThreadAdapter",
    "LinkedInPostAdapter",
    "EmailNewsletterAdapter",
    "YouTubeScriptAdapter",
    "InstagramCarouselAdapter",
    "PodcastNotesAdapter",
    "GenericAdapter",
    "get_adapter",
    "ADAPTERS",
    # Service
    "RemixService",
    "get_remix_service",
    "remix_content",
    "preview_remix",
]
