from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import sys
import os
from pathlib import Path

# Add parent directory to path to import generation modules
sys.path.append(str(Path(__file__).parent.parent))
from make_mdx import generate_blog_post
from make_book import create_title, create_book_structure, generate_topic_content, DocumentConfig

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerationRequest(BaseModel):
    topic: str
    type: str  # 'blog' or 'book'
    conversation_id: Optional[str] = None

class SectionEditRequest(BaseModel):
    file_path: str
    section_id: str
    new_content: str
    instructions: str

# Store conversations (in-memory for now, could be moved to a database)
conversations: Dict[str, List[Dict]] = {}

@app.post("/generate")
async def generate_content(request: GenerationRequest):
    try:
        if request.type == "blog":
            content = generate_blog_post(request.topic)
            return {
                "success": True,
                "type": "blog",
                "content": content,
                "file_path": f"content/blog/{content['filename']}"
            }
        elif request.type == "book":
            doc_config = DocumentConfig()
            title = create_title(request.topic, doc_config)
            book = create_book_structure(title)
            
            # Generate content for each chapter
            for chapter in book.chapters:
                for topic in chapter.topics:
                    generate_topic_content(topic, chapter, book)
            
            output_path = os.path.join(doc_config.directory, book.output_file)
            doc_config.doc.save(output_path)
            
            return {
                "success": True,
                "type": "book",
                "title": title,
                "file_path": output_path
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid content type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/edit-section")
async def edit_section(request: SectionEditRequest):
    try:
        # Implementation for editing specific sections
        # This would need to parse the MDX/DOCX file, find the section,
        # and update it with new content based on instructions
        return {"success": True, "message": "Section updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/conversation/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    
    try:
        while True:
            message = await websocket.receive_text()
            # Store message in conversation history
            conversations[conversation_id].append(json.loads(message))
            # Send acknowledgment
            await websocket.send_json({"status": "received"})
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    return {"conversation": conversations.get(conversation_id, [])}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
