"""
Backend server for the Blog AI application.
Provides API endpoints for generating blog posts and books.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.blog.make_blog import generate_blog_post, generate_blog_post_with_research, post_process_blog_post
from src.book.make_book import generate_book, generate_book_with_research, post_process_book
from src.text_generation.core import create_provider_from_env, GenerationOptions

# Initialize FastAPI app
app = FastAPI(title="Blog AI API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Models
class BlogGenerationRequest(BaseModel):
    topic: str
    keywords: List[str] = []
    tone: str = "informative"
    research: bool = False
    proofread: bool = True
    humanize: bool = True
    conversation_id: str

class BookGenerationRequest(BaseModel):
    title: str
    num_chapters: int = 5
    sections_per_chapter: int = 3
    keywords: List[str] = []
    tone: str = "informative"
    research: bool = False
    proofread: bool = True
    humanize: bool = True
    conversation_id: str

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to the Blog AI API"}

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    return {"conversation": conversations[conversation_id]}

@app.post("/generate-blog")
async def generate_blog(request: BlogGenerationRequest):
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
        
        return {
            "success": True,
            "type": "blog",
            "content": blog_post_data
        }
    except Exception as e:
        return {
            "success": False,
            "detail": str(e)
        }

@app.post("/generate-book")
async def generate_book_endpoint(request: BookGenerationRequest):
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
        
        return {
            "success": True,
            "type": "book",
            "content": book_data
        }
    except Exception as e:
        return {
            "success": False,
            "detail": str(e)
        }

@app.websocket("/ws/conversation/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await manager.connect(websocket, conversation_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Add message to conversation
            if conversation_id not in conversations:
                conversations[conversation_id] = []
            
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().isoformat()
            
            conversations[conversation_id].append(message)
            
            # Broadcast message to all connected clients
            await manager.send_message(
                {"type": "message", **message},
                conversation_id
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
