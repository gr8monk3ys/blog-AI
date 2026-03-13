"""
HTTPS redirect middleware for production environments.
"""

import logging
from typing import Optional, Set

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS in production.

    Checks for:
    - X-Forwarded-Proto header (common with reverse proxies/load balancers)
    - Direct scheme detection

    Excludes health check endpoints for load balancer compatibility.
    """

    def __init__(self, app, exclude_paths: Optional[Set[str]] = None):
        """
        Initialize the HTTPS redirect middleware.

        Args:
            app: The FastAPI application.
            exclude_paths: Set of paths to exclude from HTTPS redirect.
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or {"/health", "/"}

    async def dispatch(self, request: Request, call_next):
        """Process the request and redirect to HTTPS if needed."""
        # Skip redirect for excluded paths (health checks, etc.)
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Check if request is already HTTPS
        # X-Forwarded-Proto is set by reverse proxies (nginx, AWS ALB, etc.)
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "").lower()
        scheme = forwarded_proto or request.url.scheme

        if scheme != "https":
            # Build HTTPS URL
            https_url = request.url.replace(scheme="https")
            logger.debug(f"Redirecting HTTP to HTTPS: {https_url}")
            return RedirectResponse(url=str(https_url), status_code=301)

        return await call_next(request)
