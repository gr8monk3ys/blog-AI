"""
Type definitions for the Knowledge Base / RAG system.

This module defines the data structures used throughout the knowledge base system
for document processing, embedding generation, and retrieval operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union


class DocumentType(str, Enum):
    """Supported document types for the knowledge base."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "md"
    HTML = "html"


class ChunkingStrategy(str, Enum):
    """Strategies for splitting documents into chunks."""

    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
    RECURSIVE = "recursive"


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""

    OPENAI = "openai"
    VOYAGE = "voyage"
    COHERE = "cohere"


class VectorStoreProvider(str, Enum):
    """Supported vector store providers."""

    PINECONE = "pinecone"
    CHROMA = "chromadb"
    PGVECTOR = "pgvector"


@dataclass
class DocumentMetadata:
    """Metadata associated with an uploaded document."""

    title: str
    source: str
    file_type: DocumentType
    file_size_bytes: int
    page_count: Optional[int] = None
    author: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    language: str = "en"
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Represents an uploaded document in the knowledge base."""

    id: str
    user_id: str
    filename: str
    content: str
    metadata: DocumentMetadata
    status: Literal["processing", "ready", "error", "deleted"] = "processing"
    error_message: Optional[str] = None
    chunk_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""

    document_id: str
    chunk_index: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    start_char: int = 0
    end_char: int = 0
    token_count: int = 0
    overlap_with_previous: int = 0
    overlap_with_next: int = 0


@dataclass
class DocumentChunk:
    """A chunk of text from a document, ready for embedding."""

    id: str
    content: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ChunkingConfig:
    """Configuration for document chunking."""

    strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    chunk_size: int = 512  # Target tokens per chunk
    chunk_overlap: int = 50  # Overlap tokens between chunks
    min_chunk_size: int = 100  # Minimum tokens per chunk
    max_chunk_size: int = 1024  # Maximum tokens per chunk
    separators: List[str] = field(
        default_factory=lambda: ["\n\n", "\n", ". ", " ", ""]
    )
    preserve_paragraphs: bool = True
    preserve_sentences: bool = True


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation."""

    provider: EmbeddingProvider = EmbeddingProvider.OPENAI
    model: str = "text-embedding-3-small"
    dimensions: int = 1536
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class EmbeddingResult:
    """Result of an embedding operation."""

    chunk_id: str
    embedding: List[float]
    model: str
    dimensions: int
    tokens_used: int


@dataclass
class VectorStoreConfig:
    """Configuration for vector store."""

    provider: VectorStoreProvider = VectorStoreProvider.CHROMA
    index_name: str = "knowledge_base"
    namespace: Optional[str] = None
    metric: Literal["cosine", "euclidean", "dotproduct"] = "cosine"
    dimensions: int = 1536

    # Pinecone-specific
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None

    # ChromaDB-specific
    chroma_persist_path: Optional[str] = None
    chroma_collection_name: str = "knowledge_base"


@dataclass
class SearchFilter:
    """Filters for knowledge base search."""

    document_ids: Optional[List[str]] = None
    file_types: Optional[List[DocumentType]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None


@dataclass
class SearchResult:
    """A single search result from the knowledge base."""

    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    document_title: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None


@dataclass
class SearchResponse:
    """Response from a knowledge base search."""

    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    model_used: str


@dataclass
class Citation:
    """A citation reference for generated content."""

    id: str
    document_id: str
    document_title: str
    chunk_id: str
    page_number: Optional[int]
    section_title: Optional[str]
    relevance_score: float
    excerpt: str


@dataclass
class KnowledgeContext:
    """Context retrieved from knowledge base for content generation."""

    query: str
    chunks: List[DocumentChunk]
    citations: List[Citation]
    total_tokens: int
    formatted_context: str


@dataclass
class KnowledgeBaseStats:
    """Statistics about the knowledge base."""

    total_documents: int
    total_chunks: int
    total_tokens: int
    storage_size_bytes: int
    documents_by_type: Dict[str, int]
    average_chunk_size: float
    oldest_document: Optional[datetime] = None
    newest_document: Optional[datetime] = None


@dataclass
class DocumentUploadRequest:
    """Request to upload a document to the knowledge base."""

    filename: str
    content: bytes
    file_type: Optional[DocumentType] = None
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunking_config: Optional[ChunkingConfig] = None


@dataclass
class DocumentUploadResponse:
    """Response from document upload."""

    document_id: str
    status: str
    message: str
    chunk_count: int = 0
    processing_time_ms: float = 0


@dataclass
class KnowledgeSearchRequest:
    """Request to search the knowledge base."""

    query: str
    top_k: int = 5
    min_score: float = 0.7
    filters: Optional[SearchFilter] = None
    include_content: bool = True
    rerank: bool = False


# Type aliases for clarity
EmbeddingVector = List[float]
DocumentId = str
ChunkId = str
UserId = str
