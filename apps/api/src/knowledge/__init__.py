"""
Knowledge Base / RAG (Retrieval Augmented Generation) System.

This package provides a comprehensive knowledge base system for the Blog AI platform,
enabling users to upload documents, process them into searchable chunks, and retrieve
relevant context during content generation.

Key Components:
- document_processor: Parse and chunk documents (PDF, DOCX, TXT, MD)
- embeddings: Generate vector embeddings using OpenAI or Voyage AI
- vector_store: Store and search vectors using Pinecone or ChromaDB
- knowledge_service: Orchestrate the full knowledge base pipeline

Usage:
    from src.knowledge import KnowledgeService

    # Initialize the service
    service = KnowledgeService.from_env()

    # Upload a document
    doc_id = await service.upload_document(file_bytes, filename, user_id)

    # Search the knowledge base
    results = await service.search("query", user_id, top_k=5)

    # Get context for generation
    context = await service.get_generation_context("topic", user_id)
"""

from .document_processor import DocumentProcessor, DocumentProcessingError
from .embeddings import EmbeddingGenerator, EmbeddingError
from .knowledge_service import KnowledgeService, KnowledgeBaseError
from .vector_store import (
    VectorStore,
    ChromaVectorStore,
    PineconeVectorStore,
    VectorStoreError,
)

__all__ = [
    # Main service
    "KnowledgeService",
    "KnowledgeBaseError",
    # Document processing
    "DocumentProcessor",
    "DocumentProcessingError",
    # Embeddings
    "EmbeddingGenerator",
    "EmbeddingError",
    # Vector stores
    "VectorStore",
    "ChromaVectorStore",
    "PineconeVectorStore",
    "VectorStoreError",
]
