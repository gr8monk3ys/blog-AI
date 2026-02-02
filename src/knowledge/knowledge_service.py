"""
Knowledge Base Service for RAG (Retrieval Augmented Generation).

This module provides the main orchestration layer for the knowledge base system,
coordinating document processing, embedding generation, vector storage, and
retrieval for content generation.

Features:
- Document upload and processing pipeline
- Search with relevance scoring and filtering
- Context injection for content generation
- Source citation generation
- Multi-tenant support with user isolation
"""

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..types.knowledge import (
    ChunkingConfig,
    Citation,
    Document,
    DocumentChunk,
    DocumentType,
    DocumentUploadRequest,
    DocumentUploadResponse,
    EmbeddingConfig,
    EmbeddingProvider,
    KnowledgeBaseStats,
    KnowledgeContext,
    KnowledgeSearchRequest,
    SearchFilter,
    SearchResponse,
    SearchResult,
    VectorStoreConfig,
    VectorStoreProvider,
)
from .document_processor import DocumentProcessor, DocumentProcessingError
from .embeddings import EmbeddingGenerator, EmbeddingError
from .vector_store import VectorStore, VectorStoreError, create_vector_store

logger = logging.getLogger(__name__)


class KnowledgeBaseError(Exception):
    """Exception raised when knowledge base operations fail."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        document_id: Optional[str] = None,
    ):
        self.operation = operation
        self.document_id = document_id
        super().__init__(message)


class KnowledgeService:
    """
    Main service for the Knowledge Base / RAG system.

    Orchestrates document processing, embedding generation, vector storage,
    and retrieval for content generation with source citations.
    """

    # Maximum context length in tokens for injection
    MAX_CONTEXT_TOKENS = 4000

    # Default relevance threshold for search results
    DEFAULT_MIN_SCORE = 0.7

    def __init__(
        self,
        document_processor: DocumentProcessor,
        embedding_generator: EmbeddingGenerator,
        vector_store: VectorStore,
        supabase_client: Optional[Any] = None,
    ):
        """
        Initialize the knowledge service.

        Args:
            document_processor: Document parsing and chunking component
            embedding_generator: Embedding generation component
            vector_store: Vector storage component
            supabase_client: Optional Supabase client for metadata storage
        """
        self.document_processor = document_processor
        self.embedding_generator = embedding_generator
        self.vector_store = vector_store
        self.supabase = supabase_client
        self._initialized = False

        # In-memory document metadata cache (for when Supabase is not available)
        self._document_cache: Dict[str, Document] = {}

    @classmethod
    def from_env(cls) -> "KnowledgeService":
        """
        Create a KnowledgeService from environment variables.

        Returns:
            Configured KnowledgeService instance
        """
        # Initialize document processor
        chunking_config = ChunkingConfig(
            chunk_size=int(os.environ.get("KB_CHUNK_SIZE", "512")),
            chunk_overlap=int(os.environ.get("KB_CHUNK_OVERLAP", "50")),
        )
        document_processor = DocumentProcessor(chunking_config)

        # Initialize embedding generator
        embedding_provider = os.environ.get("KB_EMBEDDING_PROVIDER", "openai")
        embedding_config = EmbeddingConfig(
            provider=EmbeddingProvider(embedding_provider),
            model=os.environ.get("KB_EMBEDDING_MODEL", "text-embedding-3-small"),
        )
        embedding_generator = EmbeddingGenerator(embedding_config)

        # Initialize vector store
        vector_provider = os.environ.get("KB_VECTOR_STORE", "chromadb")
        vector_config = VectorStoreConfig(
            provider=VectorStoreProvider(vector_provider),
            index_name=os.environ.get("PINECONE_INDEX_NAME", "knowledge-base"),
            chroma_persist_path=os.environ.get("CHROMA_PERSIST_PATH", "./data/chroma"),
            dimensions=embedding_generator.dimensions,
        )
        vector_store = create_vector_store(vector_config)

        # Initialize Supabase client if available
        supabase_client = None
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if supabase_url and supabase_key:
            try:
                from supabase import create_client

                supabase_client = create_client(supabase_url, supabase_key)
                logger.info("Supabase client initialized for knowledge base")
            except ImportError:
                logger.warning(
                    "supabase package not installed, using in-memory document storage"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase: {e}")

        return cls(
            document_processor=document_processor,
            embedding_generator=embedding_generator,
            vector_store=vector_store,
            supabase_client=supabase_client,
        )

    async def initialize(self) -> None:
        """Initialize all components."""
        if self._initialized:
            return

        try:
            await self.vector_store.initialize()
            self._initialized = True
            logger.info("Knowledge service initialized successfully")
        except Exception as e:
            raise KnowledgeBaseError(
                f"Failed to initialize knowledge service: {e}",
                operation="initialize",
            )

    async def upload_document(
        self,
        content: bytes,
        filename: str,
        user_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentUploadResponse:
        """
        Upload and process a document for the knowledge base.

        Args:
            content: Raw document bytes
            filename: Name of the file
            user_id: ID of the user uploading the document
            title: Optional custom title
            metadata: Optional additional metadata

        Returns:
            DocumentUploadResponse with upload status
        """
        start_time = time.time()

        if not self._initialized:
            await self.initialize()

        try:
            # Process document (parse and chunk)
            custom_metadata = metadata or {}
            if title:
                custom_metadata["title"] = title
            custom_metadata["user_id"] = user_id

            document, chunks = self.document_processor.process_document(
                content=content,
                filename=filename,
                user_id=user_id,
                custom_metadata=custom_metadata,
            )

            # Update document title if provided
            if title:
                document.metadata.title = title

            logger.info(
                f"Processed document {document.id}: {len(chunks)} chunks "
                f"from {filename}"
            )

            # Generate embeddings for chunks
            chunks = await self.embedding_generator.embed_chunks(
                chunks, show_progress=True
            )

            # Store vectors in vector store
            namespace = f"user_{user_id}"
            await self.vector_store.upsert(chunks, namespace=namespace)

            # Store document metadata
            await self._store_document_metadata(document)

            processing_time = (time.time() - start_time) * 1000

            logger.info(
                f"Document {document.id} uploaded successfully: "
                f"{len(chunks)} chunks in {processing_time:.0f}ms"
            )

            return DocumentUploadResponse(
                document_id=document.id,
                status="success",
                message=f"Document processed successfully with {len(chunks)} chunks",
                chunk_count=len(chunks),
                processing_time_ms=processing_time,
            )

        except DocumentProcessingError as e:
            logger.error(f"Document processing error: {e}")
            raise KnowledgeBaseError(
                f"Failed to process document: {e}",
                operation="upload",
                document_id=e.document_name,
            )
        except EmbeddingError as e:
            logger.error(f"Embedding error: {e}")
            raise KnowledgeBaseError(
                f"Failed to generate embeddings: {e}",
                operation="upload",
            )
        except VectorStoreError as e:
            logger.error(f"Vector store error: {e}")
            raise KnowledgeBaseError(
                f"Failed to store vectors: {e}",
                operation="upload",
            )
        except Exception as e:
            logger.error(f"Unexpected error uploading document: {e}", exc_info=True)
            raise KnowledgeBaseError(
                f"Unexpected error: {e}",
                operation="upload",
            )

    async def search(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        min_score: float = DEFAULT_MIN_SCORE,
        filters: Optional[SearchFilter] = None,
    ) -> SearchResponse:
        """
        Search the knowledge base for relevant content.

        Args:
            query: Search query text
            user_id: User ID for namespace isolation
            top_k: Maximum number of results to return
            min_score: Minimum relevance score threshold
            filters: Optional additional filters

        Returns:
            SearchResponse with ranked results
        """
        start_time = time.time()

        if not self._initialized:
            await self.initialize()

        try:
            # Generate query embedding
            query_embedding = await self.embedding_generator.generate_query_embedding(
                query
            )

            # Search vector store
            namespace = f"user_{user_id}"
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k * 2,  # Fetch more for filtering
                filters=filters,
                namespace=namespace,
            )

            # Filter by minimum score
            filtered_results = [r for r in results if r.score >= min_score][:top_k]

            # Enrich results with document metadata
            enriched_results = await self._enrich_search_results(
                filtered_results, user_id
            )

            search_time = (time.time() - start_time) * 1000

            return SearchResponse(
                query=query,
                results=enriched_results,
                total_results=len(enriched_results),
                search_time_ms=search_time,
                model_used=self.embedding_generator.config.model,
            )

        except EmbeddingError as e:
            raise KnowledgeBaseError(
                f"Failed to generate query embedding: {e}",
                operation="search",
            )
        except VectorStoreError as e:
            raise KnowledgeBaseError(
                f"Failed to search vector store: {e}",
                operation="search",
            )

    async def get_generation_context(
        self,
        topic: str,
        user_id: str,
        top_k: int = 5,
        max_tokens: int = MAX_CONTEXT_TOKENS,
    ) -> KnowledgeContext:
        """
        Retrieve relevant context from the knowledge base for content generation.

        Args:
            topic: Topic or query for content generation
            user_id: User ID for namespace isolation
            top_k: Maximum number of chunks to retrieve
            max_tokens: Maximum tokens for context

        Returns:
            KnowledgeContext with formatted context and citations
        """
        # Search for relevant chunks
        search_response = await self.search(
            query=topic,
            user_id=user_id,
            top_k=top_k,
            min_score=self.DEFAULT_MIN_SCORE,
        )

        if not search_response.results:
            return KnowledgeContext(
                query=topic,
                chunks=[],
                citations=[],
                total_tokens=0,
                formatted_context="",
            )

        # Build context and citations
        chunks = []
        citations = []
        context_parts = []
        total_tokens = 0

        for i, result in enumerate(search_response.results):
            # Estimate tokens
            chunk_tokens = len(result.content) // 4
            if total_tokens + chunk_tokens > max_tokens:
                break

            # Create citation
            citation = Citation(
                id=f"citation_{i + 1}",
                document_id=result.document_id,
                document_title=result.document_title,
                chunk_id=result.chunk_id,
                page_number=result.page_number,
                section_title=result.section_title,
                relevance_score=result.score,
                excerpt=result.content[:200] + "..."
                if len(result.content) > 200
                else result.content,
            )
            citations.append(citation)

            # Format context part with citation marker
            context_part = f"[{citation.id}] {result.content}"
            context_parts.append(context_part)
            total_tokens += chunk_tokens

            # Create chunk object
            chunk = DocumentChunk(
                id=result.chunk_id,
                content=result.content,
                metadata=None,  # Simplified for context
            )
            chunks.append(chunk)

        # Format final context
        formatted_context = self._format_context_for_generation(
            context_parts, citations
        )

        return KnowledgeContext(
            query=topic,
            chunks=chunks,
            citations=citations,
            total_tokens=total_tokens,
            formatted_context=formatted_context,
        )

    def _format_context_for_generation(
        self,
        context_parts: List[str],
        citations: List[Citation],
    ) -> str:
        """Format context for injection into generation prompts."""
        if not context_parts:
            return ""

        header = (
            "The following information from your knowledge base may be relevant "
            "to the content you're generating. Use this information where appropriate "
            "and cite sources using the citation markers provided:\n\n"
        )

        context_body = "\n\n---\n\n".join(context_parts)

        # Add citation reference
        citation_refs = "\n\nSource References:\n"
        for citation in citations:
            ref = f"- {citation.id}: \"{citation.document_title}\""
            if citation.page_number:
                ref += f" (p. {citation.page_number})"
            if citation.section_title:
                ref += f" - {citation.section_title}"
            citation_refs += ref + "\n"

        return header + context_body + citation_refs

    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """
        Delete a document and its chunks from the knowledge base.

        Args:
            document_id: ID of the document to delete
            user_id: User ID for verification

        Returns:
            True if deleted successfully
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Delete from vector store
            namespace = f"user_{user_id}"
            await self.vector_store.delete(
                filters={"document_id": document_id},
                namespace=namespace,
            )

            # Delete from metadata storage
            await self._delete_document_metadata(document_id, user_id)

            logger.info(f"Deleted document {document_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise KnowledgeBaseError(
                f"Failed to delete document: {e}",
                operation="delete",
                document_id=document_id,
            )

    async def list_documents(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Document]:
        """
        List documents for a user.

        Args:
            user_id: User ID
            limit: Maximum documents to return
            offset: Pagination offset

        Returns:
            List of Document objects
        """
        if self.supabase:
            try:
                response = (
                    self.supabase.table("kb_documents")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .range(offset, offset + limit - 1)
                    .execute()
                )

                documents = []
                for row in response.data:
                    doc = self._row_to_document(row)
                    documents.append(doc)

                return documents

            except Exception as e:
                logger.error(f"Failed to list documents from Supabase: {e}")

        # Fallback to in-memory cache
        user_docs = [
            doc
            for doc in self._document_cache.values()
            if doc.user_id == user_id
        ]
        user_docs.sort(key=lambda d: d.created_at, reverse=True)
        return user_docs[offset : offset + limit]

    async def get_document(
        self, document_id: str, user_id: str
    ) -> Optional[Document]:
        """
        Get a specific document by ID.

        Args:
            document_id: Document ID
            user_id: User ID for verification

        Returns:
            Document if found and owned by user, None otherwise
        """
        if self.supabase:
            try:
                response = (
                    self.supabase.table("kb_documents")
                    .select("*")
                    .eq("id", document_id)
                    .eq("user_id", user_id)
                    .single()
                    .execute()
                )

                if response.data:
                    return self._row_to_document(response.data)

            except Exception as e:
                logger.error(f"Failed to get document from Supabase: {e}")

        # Fallback to in-memory cache
        doc = self._document_cache.get(document_id)
        if doc and doc.user_id == user_id:
            return doc
        return None

    async def get_stats(self, user_id: str) -> KnowledgeBaseStats:
        """
        Get statistics about the user's knowledge base.

        Args:
            user_id: User ID

        Returns:
            KnowledgeBaseStats with usage statistics
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Get vector store stats
            namespace = f"user_{user_id}"
            vector_stats = await self.vector_store.get_stats(namespace=namespace)

            # Get document stats
            documents = await self.list_documents(user_id, limit=1000)

            # Calculate aggregate stats
            documents_by_type: Dict[str, int] = {}
            total_tokens = 0

            for doc in documents:
                file_type = doc.metadata.file_type.value
                documents_by_type[file_type] = documents_by_type.get(file_type, 0) + 1

            total_chunks = vector_stats.get("namespace_vectors", 0)
            avg_chunk_size = total_tokens / total_chunks if total_chunks > 0 else 0

            oldest = min((d.created_at for d in documents), default=None)
            newest = max((d.created_at for d in documents), default=None)

            return KnowledgeBaseStats(
                total_documents=len(documents),
                total_chunks=total_chunks,
                total_tokens=total_tokens,
                storage_size_bytes=sum(d.metadata.file_size_bytes for d in documents),
                documents_by_type=documents_by_type,
                average_chunk_size=avg_chunk_size,
                oldest_document=oldest,
                newest_document=newest,
            )

        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {e}")
            raise KnowledgeBaseError(
                f"Failed to get stats: {e}",
                operation="stats",
            )

    async def _store_document_metadata(self, document: Document) -> None:
        """Store document metadata in Supabase or cache."""
        if self.supabase:
            try:
                self.supabase.table("kb_documents").upsert(
                    {
                        "id": document.id,
                        "user_id": document.user_id,
                        "filename": document.filename,
                        "title": document.metadata.title,
                        "file_type": document.metadata.file_type.value,
                        "file_size_bytes": document.metadata.file_size_bytes,
                        "page_count": document.metadata.page_count,
                        "chunk_count": document.chunk_count,
                        "status": document.status,
                        "metadata": document.metadata.custom_metadata,
                        "created_at": document.created_at.isoformat(),
                        "updated_at": document.updated_at.isoformat(),
                    }
                ).execute()
                return
            except Exception as e:
                logger.warning(f"Failed to store document in Supabase: {e}")

        # Fallback to in-memory cache
        self._document_cache[document.id] = document

    async def _delete_document_metadata(
        self, document_id: str, user_id: str
    ) -> None:
        """Delete document metadata from Supabase or cache."""
        if self.supabase:
            try:
                self.supabase.table("kb_documents").delete().eq(
                    "id", document_id
                ).eq("user_id", user_id).execute()
                return
            except Exception as e:
                logger.warning(f"Failed to delete document from Supabase: {e}")

        # Fallback to in-memory cache
        if document_id in self._document_cache:
            del self._document_cache[document_id]

    async def _enrich_search_results(
        self,
        results: List[SearchResult],
        user_id: str,
    ) -> List[SearchResult]:
        """Enrich search results with document metadata."""
        if not results:
            return results

        # Get unique document IDs
        doc_ids = list(set(r.document_id for r in results))

        # Fetch document metadata
        doc_metadata = {}
        for doc_id in doc_ids:
            doc = await self.get_document(doc_id, user_id)
            if doc:
                doc_metadata[doc_id] = doc

        # Enrich results
        for result in results:
            if result.document_id in doc_metadata:
                doc = doc_metadata[result.document_id]
                result.document_title = doc.metadata.title

        return results

    def _row_to_document(self, row: Dict[str, Any]) -> Document:
        """Convert a database row to a Document object."""
        metadata = DocumentMetadata(
            title=row.get("title", row.get("filename", "")),
            source=row.get("filename", ""),
            file_type=DocumentType(row.get("file_type", "txt")),
            file_size_bytes=row.get("file_size_bytes", 0),
            page_count=row.get("page_count"),
            custom_metadata=row.get("metadata", {}),
        )

        return Document(
            id=row["id"],
            user_id=row["user_id"],
            filename=row.get("filename", ""),
            content="",  # Content not stored in metadata table
            metadata=metadata,
            status=row.get("status", "ready"),
            chunk_count=row.get("chunk_count", 0),
            created_at=datetime.fromisoformat(row["created_at"])
            if row.get("created_at")
            else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"])
            if row.get("updated_at")
            else datetime.now(),
        )

    async def close(self) -> None:
        """Close all connections."""
        await self.vector_store.close()
        self._initialized = False


# Global service instance
_knowledge_service: Optional[KnowledgeService] = None


def get_knowledge_service() -> KnowledgeService:
    """
    Get or create the global KnowledgeService instance.

    Returns:
        Configured KnowledgeService
    """
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService.from_env()
    return _knowledge_service
