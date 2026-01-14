"""
Backend server for the Blog AI application.
Provides API endpoints for generating blog posts and books.
"""
import os
import re
import json
import uuid
import logging
import secrets
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, field_validator

from src.blog.make_blog import generate_blog_post, generate_blog_post_with_research, post_process_blog_post
from src.book.make_book import generate_book, generate_book_with_research, post_process_book
from src.text_generation.core import create_provider_from_env, GenerationOptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Blog AI API")

# CORS configuration - use environment variable for allowed origins
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# API Key authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEYS: Dict[str, str] = {}  # In production, load from secure storage

def get_or_create_api_key(user_id: str) -> str:
    """Generate or retrieve API key for a user."""
    if user_id not in API_KEYS:
        API_KEYS[user_id] = secrets.token_urlsafe(32)
    return API_KEYS[user_id]

async def verify_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)) -> str:
    """Verify API key and return user_id. In dev mode, allows requests without key."""
    # Development mode - allow requests without API key
    if os.environ.get("DEV_MODE", "true").lower() == "true":
        return "dev_user"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key"
        )

    # Find user by API key
    for user_id, key in API_KEYS.items():
        if secrets.compare_digest(key, api_key):
            return user_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key"
    )

# Input validation constants
MAX_TOPIC_LENGTH = 500
MAX_KEYWORD_LENGTH = 100
MAX_KEYWORDS_COUNT = 20
MAX_CHAPTERS = 50
MAX_SECTIONS_PER_CHAPTER = 20
ALLOWED_TONES = {"informative", "casual", "professional", "friendly", "formal", "conversational"}

# Patterns commonly used in prompt injection attacks
PROMPT_INJECTION_PATTERNS = [
    # System prompt override attempts
    r'ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)',
    r'disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)',
    r'forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)',
    r'override\s+(system|previous|prior)\s+(prompt|instructions?|rules?)',
    r'new\s+system\s+prompt',
    r'system\s*:\s*',
    r'assistant\s*:\s*',
    r'human\s*:\s*',
    r'user\s*:\s*',
    # Role manipulation
    r'you\s+are\s+now\s+',
    r'act\s+as\s+(if\s+)?(you\s+are\s+)?',
    r'pretend\s+(to\s+be|you\s+are)',
    r'roleplay\s+as',
    r'simulate\s+being',
    # Delimiter abuse
    r'```+',
    r'---+',
    r'===+',
    r'\[\[.*?\]\]',
    # Output manipulation
    r'print\s+the\s+(system\s+)?prompt',
    r'reveal\s+(your|the)\s+(system\s+)?prompt',
    r'show\s+(your|the)\s+(system\s+)?prompt',
    r'output\s+(your|the)\s+instructions',
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
    text = re.sub(r'\s+', ' ', text)

    # Check for injection patterns and log warnings
    for pattern in COMPILED_INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning(f"Potential prompt injection detected and neutralized: {text[:100]}...")
            # Replace the matched pattern with a neutralized version
            text = pattern.sub('[FILTERED]', text)

    # Escape angle brackets to prevent HTML/XML injection in prompts
    text = text.replace('<', '&lt;').replace('>', '&gt;')

    return text


def contains_injection_attempt(text: str) -> bool:
    """Check if text contains potential prompt injection attempts."""
    if not text:
        return False

    for pattern in COMPILED_INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False

# Store conversations
conversations = {}

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

    @field_validator('topic')
    @classmethod
    def sanitize_topic(cls, v: str) -> str:
        if contains_injection_attempt(v):
            logger.warning(f"Prompt injection attempt in topic: {v[:100]}...")
        return sanitize_text(v)

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        validated = []
        for keyword in v:
            if len(keyword) > MAX_KEYWORD_LENGTH:
                raise ValueError(f"Keyword exceeds maximum length of {MAX_KEYWORD_LENGTH}")
            validated.append(sanitize_text(keyword))
        return validated

    @field_validator('tone')
    @classmethod
    def validate_tone(cls, v: str) -> str:
        if v.lower() not in ALLOWED_TONES:
            raise ValueError(f"Tone must be one of: {', '.join(ALLOWED_TONES)}")
        return v.lower()

    @field_validator('conversation_id')
    @classmethod
    def validate_conversation_id(cls, v: str) -> str:
        # Only allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
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

    @field_validator('title')
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        if contains_injection_attempt(v):
            logger.warning(f"Prompt injection attempt in title: {v[:100]}...")
        return sanitize_text(v)

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        validated = []
        for keyword in v:
            if len(keyword) > MAX_KEYWORD_LENGTH:
                raise ValueError(f"Keyword exceeds maximum length of {MAX_KEYWORD_LENGTH}")
            validated.append(sanitize_text(keyword))
        return validated

    @field_validator('tone')
    @classmethod
    def validate_tone(cls, v: str) -> str:
        if v.lower() not in ALLOWED_TONES:
            raise ValueError(f"Tone must be one of: {', '.join(ALLOWED_TONES)}")
        return v.lower()

    @field_validator('conversation_id')
    @classmethod
    def validate_conversation_id(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Conversation ID contains invalid characters")
        return v

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to the Blog AI API"}

@app.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user_id: str = Depends(verify_api_key)
):
    # Validate conversation_id format
    if not re.match(r'^[a-zA-Z0-9_-]+$', conversation_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format"
        )

    if conversation_id not in conversations:
        conversations[conversation_id] = []
    return {"conversation": conversations[conversation_id]}

@app.post("/generate-blog", status_code=status.HTTP_201_CREATED)
async def generate_blog(
    request: BlogGenerationRequest,
    user_id: str = Depends(verify_api_key)
):
    logger.info(f"Blog generation requested by user: {user_id}, topic: {request.topic[:50]}...")
    try:
        # Create generation options
        options = GenerationOptions(
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        # Generate blog post
        if request.research:
            blog_post = generate_blog_post_with_research(
                title=request.topic,
                keywords=request.keywords,
                tone=request.tone,
                provider_type="openai",
                options=options
            )
        else:
            blog_post = generate_blog_post(
                title=request.topic,
                keywords=request.keywords,
                tone=request.tone,
                provider_type="openai",
                options=options
            )
        
        # Post-process blog post
        if request.proofread or request.humanize:
            provider = create_provider_from_env("openai")
            blog_post = post_process_blog_post(
                blog_post=blog_post,
                proofread=request.proofread,
                humanize=request.humanize,
                provider=provider,
                options=options
            )
        
        # Convert blog post to JSON-serializable format
        blog_post_data = {
            "title": blog_post.title,
            "description": blog_post.description,
            "date": blog_post.date,
            "image": blog_post.image,
            "tags": blog_post.tags,
            "sections": []
        }
        
        for section in blog_post.sections:
            section_data = {
                "title": section.title,
                "subtopics": []
            }
            
            for subtopic in section.subtopics:
                subtopic_data = {
                    "title": subtopic.title,
                    "content": subtopic.content
                }
                
                section_data["subtopics"].append(subtopic_data)
            
            blog_post_data["sections"].append(section_data)
        
        # Add to conversation
        if request.conversation_id not in conversations:
            conversations[request.conversation_id] = []
        
        # Add user message
        user_message = {
            "role": "user",
            "content": f"Generate a blog post about '{request.topic}'",
            "timestamp": datetime.now().isoformat()
        }
        conversations[request.conversation_id].append(user_message)
        
        # Add assistant message
        assistant_message = {
            "role": "assistant",
            "content": f"I've generated a blog post titled '{blog_post.title}'",
            "timestamp": datetime.now().isoformat()
        }
        conversations[request.conversation_id].append(assistant_message)
        
        # Send messages via WebSocket
        await manager.send_message(
            {"type": "message", **user_message},
            request.conversation_id
        )
        await manager.send_message(
            {"type": "message", **assistant_message},
            request.conversation_id
        )
        
        logger.info(f"Blog generated successfully: {blog_post.title}")
        return {
            "success": True,
            "type": "blog",
            "content": blog_post_data
        }
    except ValueError as e:
        logger.warning(f"Validation error in blog generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating blog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate blog post. Please try again later."
        )

@app.post("/generate-book", status_code=status.HTTP_201_CREATED)
async def generate_book_endpoint(
    request: BookGenerationRequest,
    user_id: str = Depends(verify_api_key)
):
    logger.info(f"Book generation requested by user: {user_id}, title: {request.title[:50]}...")
    try:
        # Create generation options
        options = GenerationOptions(
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0
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
                options=options
            )
        else:
            book = generate_book(
                title=request.title,
                num_chapters=request.num_chapters,
                sections_per_chapter=request.sections_per_chapter,
                keywords=request.keywords,
                tone=request.tone,
                provider_type="openai",
                options=options
            )
        
        # Post-process book
        if request.proofread or request.humanize:
            provider = create_provider_from_env("openai")
            book = post_process_book(
                book=book,
                proofread=request.proofread,
                humanize=request.humanize,
                provider=provider,
                options=options
            )
        
        # Convert book to JSON-serializable format
        book_data = {
            "title": book.title,
            "description": book.description,
            "date": book.date,
            "image": book.image,
            "tags": book.tags,
            "chapters": []
        }
        
        for chapter in book.chapters:
            chapter_data = {
                "number": chapter.number,
                "title": chapter.title,
                "topics": []
            }
            
            for topic in chapter.topics:
                topic_data = {
                    "title": topic.title,
                    "content": topic.content
                }
                
                chapter_data["topics"].append(topic_data)
            
            book_data["chapters"].append(chapter_data)
        
        # Add to conversation
        if request.conversation_id not in conversations:
            conversations[request.conversation_id] = []
        
        # Add user message
        user_message = {
            "role": "user",
            "content": f"Generate a book titled '{request.title}'",
            "timestamp": datetime.now().isoformat()
        }
        conversations[request.conversation_id].append(user_message)
        
        # Add assistant message
        assistant_message = {
            "role": "assistant",
            "content": f"I've generated a book titled '{book.title}' with {len(book.chapters)} chapters",
            "timestamp": datetime.now().isoformat()
        }
        conversations[request.conversation_id].append(assistant_message)
        
        # Send messages via WebSocket
        await manager.send_message(
            {"type": "message", **user_message},
            request.conversation_id
        )
        await manager.send_message(
            {"type": "message", **assistant_message},
            request.conversation_id
        )
        
        logger.info(f"Book generated successfully: {book.title}")
        return {
            "success": True,
            "type": "book",
            "content": book_data
        }
    except ValueError as e:
        logger.warning(f"Validation error in book generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating book: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate book. Please try again later."
        )

# WebSocket message model for validation
class WebSocketMessage(BaseModel):
    role: str = Field(..., pattern=r'^(user|assistant|system)$')
    content: str = Field(..., min_length=1, max_length=10000)
    timestamp: Optional[str] = None

@app.websocket("/ws/conversation/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    # Validate conversation_id format
    if not re.match(r'^[a-zA-Z0-9_-]+$', conversation_id):
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
                await websocket.send_json({"type": "error", "detail": "Invalid JSON format"})
                continue
            except ValueError as e:
                logger.warning(f"Invalid message format on WebSocket: {str(e)}")
                await websocket.send_json({"type": "error", "detail": str(e)})
                continue

            # Add message to conversation
            if conversation_id not in conversations:
                conversations[conversation_id] = []

            # Add timestamp if not present
            if not message.get("timestamp"):
                message["timestamp"] = datetime.now().isoformat()

            conversations[conversation_id].append(message)

            # Broadcast message to all connected clients
            await manager.send_message(
                {"type": "message", **message},
                conversation_id
            )
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation: {conversation_id}")
        manager.disconnect(websocket, conversation_id)
    except Exception as e:
        logger.error(f"WebSocket error for conversation {conversation_id}: {str(e)}", exc_info=True)
        manager.disconnect(websocket, conversation_id)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
