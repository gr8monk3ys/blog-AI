"""
Backend server for the Blog AI application.
Provides API endpoints for generating blog posts and books.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import secrets
import time
import uuid
from collections import defaultdict
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

from src.blog.make_blog import (
    generate_blog_post,
    generate_blog_post_with_research,
    post_process_blog_post,
)
from src.book.make_book import (
    generate_book,
    generate_book_with_research,
    post_process_book,
)
from src.text_generation.core import GenerationOptions, create_provider_from_env

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


# =============================================================================
# HTTPS Redirect Middleware
# =============================================================================
class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS in production.

    Checks for:
    - X-Forwarded-Proto header (common with reverse proxies/load balancers)
    - Direct scheme detection

    Excludes health check endpoints for load balancer compatibility.
    """

    def __init__(self, app, exclude_paths: Optional[set] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or {"/health", "/"}

    async def dispatch(self, request: Request, call_next):
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
            from starlette.responses import RedirectResponse

            return RedirectResponse(url=str(https_url), status_code=301)

        return await call_next(request)


# Add HTTPS redirect middleware in production
# SECURITY: Only enable when HTTPS is properly configured
HTTPS_REDIRECT_ENABLED = os.environ.get("HTTPS_REDIRECT_ENABLED", "false").lower() == "true"
if HTTPS_REDIRECT_ENABLED:
    app.add_middleware(HTTPSRedirectMiddleware)
    logger.info("HTTPS redirect middleware enabled")


# =============================================================================
# Rate Limiting Middleware
# =============================================================================
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse and control API costs.

    Limits:
    - 60 requests per minute per IP for general endpoints
    - 10 requests per minute per IP for generation endpoints (expensive LLM calls)
    """

    def __init__(
        self,
        app,
        general_limit: int = 60,
        generation_limit: int = 10,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.general_limit = general_limit
        self.generation_limit = generation_limit
        self.window_seconds = window_seconds
        self.request_counts: Dict[str, List[float]] = defaultdict(list)
        self.generation_endpoints = {"/generate-blog", "/generate-book"}

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, handling proxy headers."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _clean_old_requests(self, ip: str, current_time: float) -> None:
        """Remove requests outside the current time window."""
        cutoff = current_time - self.window_seconds
        self.request_counts[ip] = [t for t in self.request_counts[ip] if t > cutoff]

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in {"/", "/health", "/docs", "/openapi.json", "/redoc"}:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Clean old requests
        self._clean_old_requests(client_ip, current_time)

        # Determine rate limit based on endpoint
        is_generation = request.url.path in self.generation_endpoints
        limit = self.generation_limit if is_generation else self.general_limit

        # Check if over limit
        if len(self.request_counts[client_ip]) >= limit:
            logger.warning(
                f"Rate limit exceeded for IP: {client_ip}, endpoint: {request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {limit} requests per minute for this endpoint.",
                headers={"Retry-After": str(self.window_seconds)},
            )

        # Record this request
        self.request_counts[client_ip].append(current_time)

        # Add rate limit headers to response
        response = await call_next(request)
        remaining = limit - len(self.request_counts[client_ip])
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(
            int(current_time + self.window_seconds)
        )

        return response


# Add rate limiting middleware
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
if RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        general_limit=int(os.environ.get("RATE_LIMIT_GENERAL", "60")),
        generation_limit=int(os.environ.get("RATE_LIMIT_GENERATION", "10")),
        window_seconds=60,
    )

# API Key authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


# =============================================================================
# API Key Storage (File-based persistence with secure hashing)
# =============================================================================
class APIKeyStore:
    """
    File-based API key storage with secure hashing.

    API keys are stored as SHA-256 hashes for security. The plain-text key
    is only returned once when created and cannot be retrieved later.
    This is a stepping stone to Redis/database storage in production.
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = Path(
            storage_path or os.environ.get("API_KEY_STORAGE_PATH", "./data/api_keys.json")
        )
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, str] = {}  # user_id -> hashed_key
        self._load()
        logger.info(f"API key storage initialized at: {self.storage_path}")

    def _hash_key(self, api_key: str) -> str:
        """Hash an API key using SHA-256."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def _load(self) -> None:
        """Load API keys from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    self._cache = json.load(f)
                logger.info(f"Loaded {len(self._cache)} API keys from storage")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading API keys: {e}")
                self._cache = {}
        else:
            self._cache = {}

    def _save(self) -> None:
        """Save API keys to disk."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self._cache, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving API keys: {e}")

    def create_key(self, user_id: str) -> str:
        """
        Create a new API key for a user.

        Returns the plain-text key (only returned once - cannot be retrieved later).
        """
        plain_key = secrets.token_urlsafe(32)
        hashed_key = self._hash_key(plain_key)
        self._cache[user_id] = hashed_key
        self._save()
        logger.info(f"Created new API key for user: {user_id}")
        return plain_key

    def get_or_create_key(self, user_id: str) -> Optional[str]:
        """
        Get existing key status or create a new key.

        If user already has a key, returns None (key cannot be retrieved).
        If user doesn't have a key, creates one and returns the plain-text key.
        """
        if user_id in self._cache:
            return None  # Key exists but cannot be retrieved
        return self.create_key(user_id)

    def verify_key(self, api_key: str) -> Optional[str]:
        """
        Verify an API key and return the associated user_id.

        Uses constant-time comparison to prevent timing attacks.
        Returns None if the key is invalid.
        """
        hashed_input = self._hash_key(api_key)
        for user_id, stored_hash in self._cache.items():
            if secrets.compare_digest(stored_hash, hashed_input):
                return user_id
        return None

    def revoke_key(self, user_id: str) -> bool:
        """Revoke a user's API key."""
        if user_id in self._cache:
            del self._cache[user_id]
            self._save()
            logger.info(f"Revoked API key for user: {user_id}")
            return True
        return False

    def user_has_key(self, user_id: str) -> bool:
        """Check if a user has an API key."""
        return user_id in self._cache


# Initialize API key storage
api_key_store = APIKeyStore()


def get_or_create_api_key(user_id: str) -> Optional[str]:
    """Generate or retrieve API key for a user."""
    return api_key_store.get_or_create_key(user_id)


async def verify_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)) -> str:
    """Verify API key and return user_id. In dev mode, allows requests without key."""
    # Development mode - allow requests without API key
    # SECURITY: Default is FALSE - must explicitly enable dev mode
    if os.environ.get("DEV_MODE", "false").lower() == "true":
        return "dev_user"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key"
        )

    # Verify API key using secure storage
    user_id = api_key_store.verify_key(api_key)
    if user_id:
        return user_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
    )


# Input validation constants
MAX_TOPIC_LENGTH = 500
MAX_KEYWORD_LENGTH = 100
MAX_KEYWORDS_COUNT = 20
MAX_CHAPTERS = 50
MAX_SECTIONS_PER_CHAPTER = 20
ALLOWED_TONES = {
    "informative",
    "casual",
    "professional",
    "friendly",
    "formal",
    "conversational",
}

# Patterns commonly used in prompt injection attacks
PROMPT_INJECTION_PATTERNS = [
    # System prompt override attempts
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"override\s+(system|previous|prior)\s+(prompt|instructions?|rules?)",
    r"new\s+system\s+prompt",
    r"system\s*:\s*",
    r"assistant\s*:\s*",
    r"human\s*:\s*",
    r"user\s*:\s*",
    # Role manipulation
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(if\s+)?(you\s+are\s+)?",
    r"pretend\s+(to\s+be|you\s+are)",
    r"roleplay\s+as",
    r"simulate\s+being",
    # Delimiter abuse
    r"```+",
    r"---+",
    r"===+",
    r"\[\[.*?\]\]",
    # Output manipulation
    r"print\s+the\s+(system\s+)?prompt",
    r"reveal\s+(your|the)\s+(system\s+)?prompt",
    r"show\s+(your|the)\s+(system\s+)?prompt",
    r"output\s+(your|the)\s+instructions",
]

# Compile patterns for efficiency
COMPILED_INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in PROMPT_INJECTION_PATTERNS
]


def sanitize_text(text: str) -> str:
    """Sanitize text input to prevent prompt injection.

    This function:
    1. Strips and normalizes whitespace
    2. Detects and neutralizes common prompt injection patterns
    3. Escapes potentially dangerous characters
    """
    if not text:
        return ""

    # Strip and normalize whitespace
    text = text.strip()
    text = re.sub(r"\s+", " ", text)

    # Check for injection patterns and log warnings
    for pattern in COMPILED_INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning(
                f"Potential prompt injection detected and neutralized: {text[:100]}..."
            )
            # Replace the matched pattern with a neutralized version
            text = pattern.sub("[FILTERED]", text)

    # Escape angle brackets to prevent HTML/XML injection in prompts
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    return text


def contains_injection_attempt(text: str) -> bool:
    """Check if text contains potential prompt injection attempts."""
    if not text:
        return False

    for pattern in COMPILED_INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False


# =============================================================================
# Conversation Storage (File-based persistence)
# =============================================================================
class ConversationStore:
    """
    File-based conversation storage for persistence across restarts.

    Conversations are stored as JSON files in a configurable directory.
    This is a stepping stone to Redis/database storage in production.
    """

    def __init__(self, storage_dir: str = None):
        self.storage_dir = Path(
            storage_dir
            or os.environ.get("CONVERSATION_STORAGE_DIR", "./data/conversations")
        )
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, List[Dict]] = {}  # In-memory cache for performance
        logger.info(f"Conversation storage initialized at: {self.storage_dir}")

    def _get_file_path(self, conversation_id: str) -> Path:
        """Get the file path for a conversation."""
        # Sanitize conversation_id to prevent path traversal
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "", conversation_id)
        return self.storage_dir / f"{safe_id}.json"

    def get(self, conversation_id: str) -> List[Dict]:
        """Get a conversation by ID, loading from disk if not cached."""
        if conversation_id in self._cache:
            return self._cache[conversation_id]

        file_path = self._get_file_path(conversation_id)
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    self._cache[conversation_id] = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading conversation {conversation_id}: {e}")
                self._cache[conversation_id] = []
        else:
            self._cache[conversation_id] = []

        return self._cache[conversation_id]

    def append(self, conversation_id: str, message: Dict) -> None:
        """Append a message to a conversation and persist to disk."""
        if conversation_id not in self._cache:
            self.get(conversation_id)  # Load from disk if exists

        self._cache[conversation_id].append(message)
        self._save(conversation_id)

    def _save(self, conversation_id: str) -> None:
        """Save a conversation to disk."""
        file_path = self._get_file_path(conversation_id)
        try:
            with open(file_path, "w") as f:
                json.dump(self._cache[conversation_id], f, indent=2)
        except IOError as e:
            logger.error(f"Error saving conversation {conversation_id}: {e}")

    def __contains__(self, conversation_id: str) -> bool:
        """Check if a conversation exists."""
        if conversation_id in self._cache:
            return True
        return self._get_file_path(conversation_id).exists()

    def __getitem__(self, conversation_id: str) -> List[Dict]:
        """Get a conversation by ID (dict-like access)."""
        return self.get(conversation_id)

    def __setitem__(self, conversation_id: str, messages: List[Dict]) -> None:
        """Set a conversation (dict-like access)."""
        self._cache[conversation_id] = messages
        self._save(conversation_id)


# Initialize conversation storage
conversations = ConversationStore()


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)

    async def send_message(self, message: Dict[str, Any], conversation_id: str):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                await connection.send_json(message)


manager = ConnectionManager()


# Models with validation
class BlogGenerationRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH)
    keywords: List[str] = Field(default=[], max_length=MAX_KEYWORDS_COUNT)
    tone: str = Field(default="informative")
    research: bool = False
    proofread: bool = True
    humanize: bool = True
    conversation_id: str = Field(..., min_length=1, max_length=100)

    @field_validator("topic")
    @classmethod
    def sanitize_topic(cls, v: str) -> str:
        if contains_injection_attempt(v):
            logger.warning(f"Prompt injection attempt in topic: {v[:100]}...")
        return sanitize_text(v)

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        validated = []
        for keyword in v:
            if len(keyword) > MAX_KEYWORD_LENGTH:
                raise ValueError(
                    f"Keyword exceeds maximum length of {MAX_KEYWORD_LENGTH}"
                )
            validated.append(sanitize_text(keyword))
        return validated

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str) -> str:
        if v.lower() not in ALLOWED_TONES:
            raise ValueError(f"Tone must be one of: {', '.join(ALLOWED_TONES)}")
        return v.lower()

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v: str) -> str:
        # Only allow alphanumeric, hyphens, and underscores
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Conversation ID contains invalid characters")
        return v


class BookGenerationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH)
    num_chapters: int = Field(default=5, ge=1, le=MAX_CHAPTERS)
    sections_per_chapter: int = Field(default=3, ge=1, le=MAX_SECTIONS_PER_CHAPTER)
    keywords: List[str] = Field(default=[], max_length=MAX_KEYWORDS_COUNT)
    tone: str = Field(default="informative")
    research: bool = False
    proofread: bool = True
    humanize: bool = True
    conversation_id: str = Field(..., min_length=1, max_length=100)

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        if contains_injection_attempt(v):
            logger.warning(f"Prompt injection attempt in title: {v[:100]}...")
        return sanitize_text(v)

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        validated = []
        for keyword in v:
            if len(keyword) > MAX_KEYWORD_LENGTH:
                raise ValueError(
                    f"Keyword exceeds maximum length of {MAX_KEYWORD_LENGTH}"
                )
            validated.append(sanitize_text(keyword))
        return validated

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str) -> str:
        if v.lower() not in ALLOWED_TONES:
            raise ValueError(f"Tone must be one of: {', '.join(ALLOWED_TONES)}")
        return v.lower()

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Conversation ID contains invalid characters")
        return v


# =============================================================================
# API Router for versioning
# =============================================================================
# Create versioned API router
api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])


# =============================================================================
# Utility Functions
# =============================================================================
def sanitize_for_log(text: str, max_length: int = 30) -> str:
    """Sanitize text for logging - truncate and remove sensitive patterns."""
    if not text:
        return "[empty]"
    # Truncate and add ellipsis
    sanitized = text[:max_length] + "..." if len(text) > max_length else text
    # Remove newlines and excessive whitespace
    sanitized = re.sub(r"\s+", " ", sanitized)
    return sanitized


# =============================================================================
# Routes
# =============================================================================
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@app.get("/")
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


@app.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str, user_id: str = Depends(verify_api_key)
):
    # Validate conversation_id format
    if not re.match(r"^[a-zA-Z0-9_-]+$", conversation_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format",
        )

    return {"conversation": conversations.get(conversation_id)}


@app.post("/generate-blog", status_code=status.HTTP_201_CREATED)
async def generate_blog(
    request: BlogGenerationRequest, user_id: str = Depends(verify_api_key)
):
    logger.info(
        f"Blog generation requested by user: {user_id}, topic_length: {len(request.topic)}"
    )
    try:
        # Create generation options
        options = GenerationOptions(
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        # Generate blog post
        if request.research:
            blog_post = generate_blog_post_with_research(
                title=request.topic,
                keywords=request.keywords,
                tone=request.tone,
                provider_type="openai",
                options=options,
            )
        else:
            blog_post = generate_blog_post(
                title=request.topic,
                keywords=request.keywords,
                tone=request.tone,
                provider_type="openai",
                options=options,
            )

        # Post-process blog post
        if request.proofread or request.humanize:
            provider = create_provider_from_env("openai")
            blog_post = post_process_blog_post(
                blog_post=blog_post,
                proofread=request.proofread,
                humanize=request.humanize,
                provider=provider,
                options=options,
            )

        # Convert blog post to JSON-serializable format
        blog_post_data = {
            "title": blog_post.title,
            "description": blog_post.description,
            "date": blog_post.date,
            "image": blog_post.image,
            "tags": blog_post.tags,
            "sections": [],
        }

        for section in blog_post.sections:
            section_data = {"title": section.title, "subtopics": []}

            for subtopic in section.subtopics:
                subtopic_data = {"title": subtopic.title, "content": subtopic.content}

                section_data["subtopics"].append(subtopic_data)

            blog_post_data["sections"].append(section_data)

        # Add user message to conversation (with persistence)
        user_message = {
            "role": "user",
            "content": "Generate a blog post",  # Sanitized - don't log actual topic
            "timestamp": datetime.now().isoformat(),
        }
        conversations.append(request.conversation_id, user_message)

        # Add assistant message to conversation (with persistence)
        assistant_message = {
            "role": "assistant",
            "content": f"Generated blog post: {blog_post.title[:50]}",  # Truncated for logs
            "timestamp": datetime.now().isoformat(),
        }
        conversations.append(request.conversation_id, assistant_message)

        # Send messages via WebSocket
        await manager.send_message(
            {"type": "message", **user_message}, request.conversation_id
        )
        await manager.send_message(
            {"type": "message", **assistant_message}, request.conversation_id
        )

        logger.info(f"Blog generated successfully: {blog_post.title}")
        return {"success": True, "type": "blog", "content": blog_post_data}
    except ValueError as e:
        logger.warning(f"Validation error in blog generation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating blog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate blog post. Please try again later.",
        )


@app.post("/generate-book", status_code=status.HTTP_201_CREATED)
async def generate_book_endpoint(
    request: BookGenerationRequest, user_id: str = Depends(verify_api_key)
):
    logger.info(
        f"Book generation requested by user: {user_id}, title_length: {len(request.title)}, chapters: {request.num_chapters}"
    )
    try:
        # Create generation options
        options = GenerationOptions(
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        # Generate book
        if request.research:
            book = generate_book_with_research(
                title=request.title,
                num_chapters=request.num_chapters,
                sections_per_chapter=request.sections_per_chapter,
                keywords=request.keywords,
                tone=request.tone,
                provider_type="openai",
                options=options,
            )
        else:
            book = generate_book(
                title=request.title,
                num_chapters=request.num_chapters,
                sections_per_chapter=request.sections_per_chapter,
                keywords=request.keywords,
                tone=request.tone,
                provider_type="openai",
                options=options,
            )

        # Post-process book
        if request.proofread or request.humanize:
            provider = create_provider_from_env("openai")
            book = post_process_book(
                book=book,
                proofread=request.proofread,
                humanize=request.humanize,
                provider=provider,
                options=options,
            )

        # Convert book to JSON-serializable format
        book_data = {
            "title": book.title,
            "description": book.description,
            "date": book.date,
            "image": book.image,
            "tags": book.tags,
            "chapters": [],
        }

        for chapter in book.chapters:
            chapter_data = {
                "number": chapter.number,
                "title": chapter.title,
                "topics": [],
            }

            for topic in chapter.topics:
                topic_data = {"title": topic.title, "content": topic.content}

                chapter_data["topics"].append(topic_data)

            book_data["chapters"].append(chapter_data)

        # Add user message to conversation (with persistence)
        user_message = {
            "role": "user",
            "content": "Generate a book",  # Sanitized - don't log actual title
            "timestamp": datetime.now().isoformat(),
        }
        conversations.append(request.conversation_id, user_message)

        # Add assistant message to conversation (with persistence)
        assistant_message = {
            "role": "assistant",
            "content": f"Generated book with {len(book.chapters)} chapters",  # Sanitized
            "timestamp": datetime.now().isoformat(),
        }
        conversations.append(request.conversation_id, assistant_message)

        # Send messages via WebSocket
        await manager.send_message(
            {"type": "message", **user_message}, request.conversation_id
        )
        await manager.send_message(
            {"type": "message", **assistant_message}, request.conversation_id
        )

        logger.info(f"Book generated successfully: {book.title}")
        return {"success": True, "type": "book", "content": book_data}
    except ValueError as e:
        logger.warning(f"Validation error in book generation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating book: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate book. Please try again later.",
        )


# WebSocket message model for validation
class WebSocketMessage(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=10000)
    timestamp: Optional[str] = None


@app.websocket("/ws/conversation/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    # Validate conversation_id format
    if not re.match(r"^[a-zA-Z0-9_-]+$", conversation_id):
        await websocket.close(code=4000, reason="Invalid conversation ID format")
        return

    await manager.connect(websocket, conversation_id)
    logger.info(f"WebSocket connected for conversation: {conversation_id}")

    try:
        while True:
            data = await websocket.receive_text()

            # Parse and validate message
            try:
                raw_message = json.loads(data)
                # Validate message structure
                message = WebSocketMessage(**raw_message).model_dump()
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received on WebSocket: {conversation_id}")
                await websocket.send_json(
                    {"type": "error", "detail": "Invalid JSON format"}
                )
                continue
            except ValueError as e:
                logger.warning(f"Invalid message format on WebSocket: {str(e)}")
                await websocket.send_json({"type": "error", "detail": str(e)})
                continue

            # Add timestamp if not present
            if not message.get("timestamp"):
                message["timestamp"] = datetime.now().isoformat()

            # Add message to conversation (with persistence)
            conversations.append(conversation_id, message)

            # Broadcast message to all connected clients
            await manager.send_message({"type": "message", **message}, conversation_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation: {conversation_id}")
        manager.disconnect(websocket, conversation_id)
    except Exception as e:
        logger.error(
            f"WebSocket error for conversation {conversation_id}: {str(e)}",
            exc_info=True,
        )
        manager.disconnect(websocket, conversation_id)


# =============================================================================
# Versioned API Routes (v1)
# =============================================================================
# Add versioned routes to the router
# These provide the same functionality as the root endpoints but under /api/v1/


@api_v1_router.get("/conversations/{conversation_id}")
async def get_conversation_v1(
    conversation_id: str, user_id: str = Depends(verify_api_key)
):
    """Get conversation history (API v1)."""
    return await get_conversation(conversation_id, user_id)


@api_v1_router.post("/generate-blog", status_code=status.HTTP_201_CREATED)
async def generate_blog_v1(
    request: BlogGenerationRequest, user_id: str = Depends(verify_api_key)
):
    """Generate a blog post (API v1)."""
    return await generate_blog(request, user_id)


@api_v1_router.post("/generate-book", status_code=status.HTTP_201_CREATED)
async def generate_book_v1(
    request: BookGenerationRequest, user_id: str = Depends(verify_api_key)
):
    """Generate a book (API v1)."""
    return await generate_book_endpoint(request, user_id)


# Include the versioned router in the app
app.include_router(api_v1_router)


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
