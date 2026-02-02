"""
Knowledge Base API endpoints.

Provides REST API endpoints for:
- Document upload and processing
- Document listing and deletion
- Knowledge base search
- Statistics and monitoring
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field

from src.knowledge import KnowledgeService, KnowledgeBaseError
from src.knowledge.knowledge_service import get_knowledge_service
from src.types.knowledge import DocumentType, SearchFilter

from ..auth import verify_api_key
from ..error_handlers import sanitize_error_message
from ..middleware import require_quota

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


# =============================================================================
# Request/Response Models
# =============================================================================


class DocumentUploadResponse(BaseModel):
    """Response from document upload."""

    success: bool
    document_id: str
    message: str
    chunk_count: int
    processing_time_ms: float


class DocumentResponse(BaseModel):
    """Document metadata response."""

    id: str
    filename: str
    title: str
    file_type: str
    file_size_bytes: int
    page_count: Optional[int]
    chunk_count: int
    status: str
    created_at: str
    metadata: Dict[str, Any] = {}


class DocumentListResponse(BaseModel):
    """Response for document listing."""

    success: bool
    documents: List[DocumentResponse]
    total: int
    limit: int
    offset: int


class SearchRequest(BaseModel):
    """Request for knowledge base search."""

    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.7, ge=0.0, le=1.0)
    document_ids: Optional[List[str]] = None
    file_types: Optional[List[str]] = None


class SearchResultItem(BaseModel):
    """A single search result."""

    chunk_id: str
    document_id: str
    document_title: str
    content: str
    score: float
    page_number: Optional[int]
    section_title: Optional[str]


class SearchResponse(BaseModel):
    """Response from knowledge base search."""

    success: bool
    query: str
    results: List[SearchResultItem]
    total_results: int
    search_time_ms: float


class StatsResponse(BaseModel):
    """Knowledge base statistics response."""

    success: bool
    total_documents: int
    total_chunks: int
    storage_size_bytes: int
    documents_by_type: Dict[str, int]
    oldest_document: Optional[str]
    newest_document: Optional[str]


class DeleteResponse(BaseModel):
    """Response from document deletion."""

    success: bool
    message: str


# =============================================================================
# Dependency Injection
# =============================================================================


async def get_service() -> KnowledgeService:
    """Get the knowledge service instance."""
    service = get_knowledge_service()
    await service.initialize()
    return service


# =============================================================================
# API Endpoints
# =============================================================================


@router.post(
    "/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description="""
Upload a document to the knowledge base. The document will be parsed,
chunked, embedded, and stored for later retrieval during content generation.

**Supported file types:**
- PDF (.pdf)
- Microsoft Word (.docx)
- Plain text (.txt)
- Markdown (.md)

**File size limit:** 10MB

**Processing:** Documents are processed asynchronously. Large documents
may take several seconds to process.
    """,
    responses={
        201: {"description": "Document uploaded and processed successfully"},
        400: {"description": "Invalid file type or content"},
        401: {"description": "Missing or invalid API key"},
        413: {"description": "File too large"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Processing error"},
    },
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    title: Optional[str] = Form(
        None, description="Custom title for the document"
    ),
    user_id: str = Depends(require_quota),
    service: KnowledgeService = Depends(get_service),
):
    """
    Upload a document to the knowledge base.

    The document will be parsed, split into chunks, embedded, and stored
    in the vector database for retrieval during content generation.
    """
    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".doc", ".txt", ".md", ".markdown"}
    filename = file.filename or "unknown"
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {extension}. Allowed types: {', '.join(allowed_extensions)}",
        )

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file",
        )

    # Check file size (10MB limit)
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_size // (1024 * 1024)}MB",
        )

    # Upload and process document
    try:
        response = await service.upload_document(
            content=content,
            filename=filename,
            user_id=user_id,
            title=title,
        )

        logger.info(
            f"Document uploaded: {response.document_id} by user {user_id}"
        )

        return DocumentUploadResponse(
            success=True,
            document_id=response.document_id,
            message=response.message,
            chunk_count=response.chunk_count,
            processing_time_ms=response.processing_time_ms,
        )

    except KnowledgeBaseError as e:
        logger.error(f"Knowledge base error during upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_error_message(str(e)),
        )
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document. Please try again.",
        )


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List documents",
    description="List all documents in your knowledge base with pagination.",
    responses={
        200: {"description": "Documents retrieved successfully"},
        401: {"description": "Missing or invalid API key"},
    },
)
async def list_documents(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum documents to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    user_id: str = Depends(require_quota),
    service: KnowledgeService = Depends(get_service),
):
    """List all documents in the user's knowledge base."""
    try:
        documents = await service.list_documents(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

        doc_responses = []
        for doc in documents:
            doc_responses.append(
                DocumentResponse(
                    id=doc.id,
                    filename=doc.filename,
                    title=doc.metadata.title,
                    file_type=doc.metadata.file_type.value,
                    file_size_bytes=doc.metadata.file_size_bytes,
                    page_count=doc.metadata.page_count,
                    chunk_count=doc.chunk_count,
                    status=doc.status,
                    created_at=doc.created_at.isoformat(),
                    metadata=doc.metadata.custom_metadata,
                )
            )

        return DocumentListResponse(
            success=True,
            documents=doc_responses,
            total=len(doc_responses),
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
    description="Get details of a specific document.",
    responses={
        200: {"description": "Document details retrieved successfully"},
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Document not found"},
    },
)
async def get_document(
    document_id: str,
    user_id: str = Depends(require_quota),
    service: KnowledgeService = Depends(get_service),
):
    """Get details of a specific document."""
    try:
        document = await service.get_document(document_id, user_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            title=document.metadata.title,
            file_type=document.metadata.file_type.value,
            file_size_bytes=document.metadata.file_size_bytes,
            page_count=document.metadata.page_count,
            chunk_count=document.chunk_count,
            status=document.status,
            created_at=document.created_at.isoformat(),
            metadata=document.metadata.custom_metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document",
        )


@router.delete(
    "/documents/{document_id}",
    response_model=DeleteResponse,
    summary="Delete a document",
    description="Delete a document and all its chunks from the knowledge base.",
    responses={
        200: {"description": "Document deleted successfully"},
        401: {"description": "Missing or invalid API key"},
        404: {"description": "Document not found"},
    },
)
async def delete_document(
    document_id: str,
    user_id: str = Depends(require_quota),
    service: KnowledgeService = Depends(get_service),
):
    """Delete a document from the knowledge base."""
    try:
        # Verify document exists and belongs to user
        document = await service.get_document(document_id, user_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        # Delete document
        await service.delete_document(document_id, user_id)

        logger.info(f"Document deleted: {document_id} by user {user_id}")

        return DeleteResponse(
            success=True,
            message=f"Document {document_id} deleted successfully",
        )

    except HTTPException:
        raise
    except KnowledgeBaseError as e:
        logger.error(f"Knowledge base error during deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_error_message(str(e)),
        )
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search knowledge base",
    description="""
Search your knowledge base for relevant content. Returns ranked results
based on semantic similarity to your query.

**Use cases:**
- Find relevant information before content generation
- Discover related documents
- Research existing content

**Filtering:**
- Filter by specific document IDs
- Filter by file type
- Adjust minimum relevance score
    """,
    responses={
        200: {"description": "Search completed successfully"},
        400: {"description": "Invalid search parameters"},
        401: {"description": "Missing or invalid API key"},
    },
)
async def search_knowledge_base(
    request: SearchRequest,
    user_id: str = Depends(require_quota),
    service: KnowledgeService = Depends(get_service),
):
    """Search the knowledge base for relevant content."""
    try:
        # Build filters
        filters = None
        if request.document_ids or request.file_types:
            file_type_enums = None
            if request.file_types:
                file_type_enums = [
                    DocumentType(ft) for ft in request.file_types
                ]

            filters = SearchFilter(
                document_ids=request.document_ids,
                file_types=file_type_enums,
            )

        # Execute search
        response = await service.search(
            query=request.query,
            user_id=user_id,
            top_k=request.top_k,
            min_score=request.min_score,
            filters=filters,
        )

        # Convert to response model
        result_items = []
        for result in response.results:
            result_items.append(
                SearchResultItem(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    document_title=result.document_title,
                    content=result.content,
                    score=result.score,
                    page_number=result.page_number,
                    section_title=result.section_title,
                )
            )

        return SearchResponse(
            success=True,
            query=request.query,
            results=result_items,
            total_results=response.total_results,
            search_time_ms=response.search_time_ms,
        )

    except KnowledgeBaseError as e:
        logger.error(f"Knowledge base error during search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_error_message(str(e)),
        )
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search knowledge base",
        )


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get knowledge base statistics",
    description="Get statistics about your knowledge base usage.",
    responses={
        200: {"description": "Statistics retrieved successfully"},
        401: {"description": "Missing or invalid API key"},
    },
)
async def get_knowledge_base_stats(
    user_id: str = Depends(require_quota),
    service: KnowledgeService = Depends(get_service),
):
    """Get statistics about the user's knowledge base."""
    try:
        stats = await service.get_stats(user_id)

        return StatsResponse(
            success=True,
            total_documents=stats.total_documents,
            total_chunks=stats.total_chunks,
            storage_size_bytes=stats.storage_size_bytes,
            documents_by_type=stats.documents_by_type,
            oldest_document=stats.oldest_document.isoformat()
            if stats.oldest_document
            else None,
            newest_document=stats.newest_document.isoformat()
            if stats.newest_document
            else None,
        )

    except KnowledgeBaseError as e:
        logger.error(f"Knowledge base error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=sanitize_error_message(str(e)),
        )
    except Exception as e:
        logger.error(f"Error getting knowledge base stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get knowledge base statistics",
        )
