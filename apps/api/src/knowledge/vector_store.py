"""
Vector store implementations for the Knowledge Base system.

This module provides an abstract base class for vector stores and implementations
for Pinecone (production) and ChromaDB (local development).

Features:
- Abstract VectorStore interface
- Pinecone implementation with namespace support
- ChromaDB implementation with local persistence
- Batch upsert and delete operations
- Metadata filtering in similarity search
"""

import logging
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..types.knowledge import (
    DocumentChunk,
    EmbeddingVector,
    SearchFilter,
    SearchResult,
    VectorStoreConfig,
    VectorStoreProvider,
)

logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    """Exception raised when vector store operations fail."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        self.provider = provider
        self.operation = operation
        super().__init__(message)


class VectorStore(ABC):
    """
    Abstract base class for vector stores.

    Defines the interface that all vector store implementations must follow.
    """

    def __init__(self, config: VectorStoreConfig):
        self.config = config

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store connection and create index if needed."""
        pass

    @abstractmethod
    async def upsert(
        self,
        chunks: List[DocumentChunk],
        namespace: Optional[str] = None,
    ) -> int:
        """
        Insert or update document chunks in the vector store.

        Args:
            chunks: List of DocumentChunk objects with embeddings
            namespace: Optional namespace for multi-tenant isolation

        Returns:
            Number of vectors upserted
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: EmbeddingVector,
        top_k: int = 10,
        filters: Optional[SearchFilter] = None,
        namespace: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Optional filters to apply
            namespace: Optional namespace to search within

        Returns:
            List of SearchResult objects
        """
        pass

    @abstractmethod
    async def delete(
        self,
        ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
    ) -> int:
        """
        Delete vectors from the store.

        Args:
            ids: List of vector IDs to delete
            filters: Metadata filters to match for deletion
            namespace: Optional namespace

        Returns:
            Number of vectors deleted
        """
        pass

    @abstractmethod
    async def get_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Args:
            namespace: Optional namespace to get stats for

        Returns:
            Dictionary with store statistics
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the vector store connection."""
        pass


class PineconeVectorStore(VectorStore):
    """
    Pinecone vector store implementation for production use.

    Features:
    - Managed vector database with high availability
    - Namespace support for multi-tenant isolation
    - Metadata filtering
    - Serverless and pod-based index support
    """

    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self.api_key = config.pinecone_api_key or os.environ.get("PINECONE_API_KEY")
        self.environment = config.pinecone_environment or os.environ.get(
            "PINECONE_ENVIRONMENT"
        )

        if not self.api_key:
            raise VectorStoreError(
                "Pinecone API key not provided and PINECONE_API_KEY not set",
                provider="pinecone",
            )

        self._index = None

    async def initialize(self) -> None:
        """Initialize Pinecone client and ensure index exists."""
        try:
            from pinecone import Pinecone, ServerlessSpec
        except ImportError:
            raise VectorStoreError(
                "pinecone package not installed. Install with: pip install pinecone",
                provider="pinecone",
            )

        try:
            pc = Pinecone(api_key=self.api_key)

            # Check if index exists
            existing_indexes = pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes]

            if self.config.index_name not in index_names:
                logger.info(f"Creating Pinecone index: {self.config.index_name}")

                # Create serverless index
                pc.create_index(
                    name=self.config.index_name,
                    dimension=self.config.dimensions,
                    metric=self.config.metric,
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )

                # Wait for index to be ready
                import time

                while not pc.describe_index(self.config.index_name).status["ready"]:
                    time.sleep(1)

            self._index = pc.Index(self.config.index_name)
            logger.info(f"Connected to Pinecone index: {self.config.index_name}")

        except Exception as e:
            raise VectorStoreError(
                f"Failed to initialize Pinecone: {e}",
                provider="pinecone",
                operation="initialize",
            )

    async def upsert(
        self,
        chunks: List[DocumentChunk],
        namespace: Optional[str] = None,
    ) -> int:
        """Upsert document chunks to Pinecone."""
        if not self._index:
            await self.initialize()

        if not chunks:
            return 0

        try:
            # Prepare vectors for upsert
            vectors = []
            for chunk in chunks:
                if chunk.embedding is None:
                    logger.warning(f"Skipping chunk {chunk.id} without embedding")
                    continue

                metadata = {
                    "document_id": chunk.metadata.document_id,
                    "chunk_index": chunk.metadata.chunk_index,
                    "content": chunk.content[:1000],  # Limit metadata size
                    "page_number": chunk.metadata.page_number,
                    "section_title": chunk.metadata.section_title,
                    "token_count": chunk.metadata.token_count,
                    "created_at": chunk.created_at.isoformat(),
                }

                # Remove None values
                metadata = {k: v for k, v in metadata.items() if v is not None}

                vectors.append(
                    {
                        "id": chunk.id,
                        "values": chunk.embedding,
                        "metadata": metadata,
                    }
                )

            # Upsert in batches of 100
            batch_size = 100
            total_upserted = 0

            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                self._index.upsert(
                    vectors=batch,
                    namespace=namespace or self.config.namespace,
                )
                total_upserted += len(batch)

            logger.info(f"Upserted {total_upserted} vectors to Pinecone")
            return total_upserted

        except Exception as e:
            raise VectorStoreError(
                f"Failed to upsert to Pinecone: {e}",
                provider="pinecone",
                operation="upsert",
            )

    async def search(
        self,
        query_embedding: EmbeddingVector,
        top_k: int = 10,
        filters: Optional[SearchFilter] = None,
        namespace: Optional[str] = None,
    ) -> List[SearchResult]:
        """Search Pinecone for similar vectors."""
        if not self._index:
            await self.initialize()

        try:
            # Build filter dict
            filter_dict = {}
            if filters:
                if filters.document_ids:
                    filter_dict["document_id"] = {"$in": filters.document_ids}
                if filters.user_id:
                    filter_dict["user_id"] = filters.user_id
                if filters.metadata_filters:
                    filter_dict.update(filters.metadata_filters)

            # Query Pinecone
            query_response = self._index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace or self.config.namespace,
                filter=filter_dict if filter_dict else None,
            )

            # Convert to SearchResult objects
            results = []
            for match in query_response.matches:
                metadata = match.metadata or {}

                result = SearchResult(
                    chunk_id=match.id,
                    document_id=metadata.get("document_id", ""),
                    content=metadata.get("content", ""),
                    score=match.score,
                    metadata=metadata,
                    document_title=metadata.get("document_title", ""),
                    page_number=metadata.get("page_number"),
                    section_title=metadata.get("section_title"),
                )
                results.append(result)

            return results

        except Exception as e:
            raise VectorStoreError(
                f"Failed to search Pinecone: {e}",
                provider="pinecone",
                operation="search",
            )

    async def delete(
        self,
        ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
    ) -> int:
        """Delete vectors from Pinecone."""
        if not self._index:
            await self.initialize()

        try:
            ns = namespace or self.config.namespace

            if ids:
                # Delete by IDs
                self._index.delete(ids=ids, namespace=ns)
                return len(ids)

            elif filters:
                # Delete by filter
                self._index.delete(filter=filters, namespace=ns)
                # Pinecone doesn't return count for filter deletes
                return -1

            else:
                # Delete all in namespace
                self._index.delete(delete_all=True, namespace=ns)
                return -1

        except Exception as e:
            raise VectorStoreError(
                f"Failed to delete from Pinecone: {e}",
                provider="pinecone",
                operation="delete",
            )

    async def get_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get Pinecone index statistics."""
        if not self._index:
            await self.initialize()

        try:
            stats = self._index.describe_index_stats()

            ns = namespace or self.config.namespace or ""
            ns_stats = stats.namespaces.get(ns, {})

            return {
                "total_vectors": stats.total_vector_count,
                "namespace_vectors": getattr(ns_stats, "vector_count", 0),
                "dimensions": stats.dimension,
                "index_fullness": stats.index_fullness,
            }

        except Exception as e:
            raise VectorStoreError(
                f"Failed to get Pinecone stats: {e}",
                provider="pinecone",
                operation="stats",
            )

    async def close(self) -> None:
        """Close Pinecone connection (no-op for Pinecone)."""
        self._index = None


class ChromaVectorStore(VectorStore):
    """
    ChromaDB vector store implementation for local development.

    Features:
    - Local persistence with optional embedding functions
    - No external dependencies for development
    - Full-text search capabilities
    - Easy debugging and inspection
    """

    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self.persist_path = config.chroma_persist_path or os.environ.get(
            "CHROMA_PERSIST_PATH", "./data/chroma"
        )
        self.collection_name = config.chroma_collection_name or "knowledge_base"
        self._client = None
        self._collection = None

    async def initialize(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise VectorStoreError(
                "chromadb package not installed. Install with: pip install chromadb",
                provider="chromadb",
            )

        try:
            # Create persistent client
            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_path,
                anonymized_telemetry=False,
            )

            self._client = chromadb.Client(settings)

            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.config.metric},
            )

            logger.info(
                f"Initialized ChromaDB collection: {self.collection_name} "
                f"at {self.persist_path}"
            )

        except Exception as e:
            raise VectorStoreError(
                f"Failed to initialize ChromaDB: {e}",
                provider="chromadb",
                operation="initialize",
            )

    async def upsert(
        self,
        chunks: List[DocumentChunk],
        namespace: Optional[str] = None,
    ) -> int:
        """Upsert document chunks to ChromaDB."""
        if not self._collection:
            await self.initialize()

        if not chunks:
            return 0

        try:
            ids = []
            embeddings = []
            documents = []
            metadatas = []

            for chunk in chunks:
                if chunk.embedding is None:
                    logger.warning(f"Skipping chunk {chunk.id} without embedding")
                    continue

                # Add namespace prefix to ID if provided
                chunk_id = (
                    f"{namespace}_{chunk.id}" if namespace else chunk.id
                )

                ids.append(chunk_id)
                embeddings.append(chunk.embedding)
                documents.append(chunk.content)

                metadata = {
                    "document_id": chunk.metadata.document_id,
                    "chunk_index": chunk.metadata.chunk_index,
                    "page_number": chunk.metadata.page_number or -1,
                    "section_title": chunk.metadata.section_title or "",
                    "token_count": chunk.metadata.token_count,
                    "created_at": chunk.created_at.isoformat(),
                    "namespace": namespace or "default",
                }

                metadatas.append(metadata)

            # Upsert to collection
            self._collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

            # Persist
            self._client.persist()

            logger.info(f"Upserted {len(ids)} vectors to ChromaDB")
            return len(ids)

        except Exception as e:
            raise VectorStoreError(
                f"Failed to upsert to ChromaDB: {e}",
                provider="chromadb",
                operation="upsert",
            )

    async def search(
        self,
        query_embedding: EmbeddingVector,
        top_k: int = 10,
        filters: Optional[SearchFilter] = None,
        namespace: Optional[str] = None,
    ) -> List[SearchResult]:
        """Search ChromaDB for similar vectors."""
        if not self._collection:
            await self.initialize()

        try:
            # Build where clause
            where = {}
            if namespace:
                where["namespace"] = namespace
            if filters:
                if filters.document_ids:
                    where["document_id"] = {"$in": filters.document_ids}
                if filters.user_id:
                    where["user_id"] = filters.user_id
                if filters.metadata_filters:
                    where.update(filters.metadata_filters)

            # Query collection
            query_result = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where if where else None,
                include=["documents", "metadatas", "distances"],
            )

            # Convert to SearchResult objects
            results = []

            if query_result["ids"] and query_result["ids"][0]:
                for i, chunk_id in enumerate(query_result["ids"][0]):
                    # ChromaDB returns distances, convert to similarity scores
                    distance = query_result["distances"][0][i]
                    score = 1 - distance  # For cosine distance

                    metadata = query_result["metadatas"][0][i] if query_result["metadatas"] else {}
                    content = query_result["documents"][0][i] if query_result["documents"] else ""

                    result = SearchResult(
                        chunk_id=chunk_id,
                        document_id=metadata.get("document_id", ""),
                        content=content,
                        score=score,
                        metadata=metadata,
                        document_title=metadata.get("document_title", ""),
                        page_number=metadata.get("page_number"),
                        section_title=metadata.get("section_title"),
                    )
                    results.append(result)

            return results

        except Exception as e:
            raise VectorStoreError(
                f"Failed to search ChromaDB: {e}",
                provider="chromadb",
                operation="search",
            )

    async def delete(
        self,
        ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
    ) -> int:
        """Delete vectors from ChromaDB."""
        if not self._collection:
            await self.initialize()

        try:
            if ids:
                # Optionally prefix IDs with namespace
                if namespace:
                    ids = [f"{namespace}_{id}" for id in ids]
                self._collection.delete(ids=ids)
                self._client.persist()
                return len(ids)

            elif filters or namespace:
                where = {}
                if namespace:
                    where["namespace"] = namespace
                if filters:
                    where.update(filters)

                self._collection.delete(where=where)
                self._client.persist()
                return -1  # Count unknown

            return 0

        except Exception as e:
            raise VectorStoreError(
                f"Failed to delete from ChromaDB: {e}",
                provider="chromadb",
                operation="delete",
            )

    async def get_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get ChromaDB collection statistics."""
        if not self._collection:
            await self.initialize()

        try:
            count = self._collection.count()

            # Get namespace-specific count if provided
            ns_count = count
            if namespace:
                result = self._collection.get(
                    where={"namespace": namespace},
                    include=[],
                )
                ns_count = len(result["ids"]) if result["ids"] else 0

            return {
                "total_vectors": count,
                "namespace_vectors": ns_count,
                "collection_name": self.collection_name,
                "persist_path": self.persist_path,
            }

        except Exception as e:
            raise VectorStoreError(
                f"Failed to get ChromaDB stats: {e}",
                provider="chromadb",
                operation="stats",
            )

    async def close(self) -> None:
        """Close ChromaDB connection and persist data."""
        if self._client:
            self._client.persist()
        self._collection = None
        self._client = None


def create_vector_store(config: Optional[VectorStoreConfig] = None) -> VectorStore:
    """
    Factory function to create a vector store based on configuration.

    Args:
        config: Vector store configuration. If None, uses environment to auto-detect.

    Returns:
        Configured VectorStore instance
    """
    if config is None:
        # Auto-detect based on environment
        if os.environ.get("PINECONE_API_KEY"):
            config = VectorStoreConfig(
                provider=VectorStoreProvider.PINECONE,
                index_name=os.environ.get("PINECONE_INDEX_NAME", "knowledge-base"),
            )
        else:
            config = VectorStoreConfig(
                provider=VectorStoreProvider.CHROMA,
                chroma_persist_path=os.environ.get("CHROMA_PERSIST_PATH", "./data/chroma"),
            )

    provider_map = {
        VectorStoreProvider.PINECONE: PineconeVectorStore,
        VectorStoreProvider.CHROMA: ChromaVectorStore,
    }

    provider_class = provider_map.get(config.provider)
    if not provider_class:
        raise VectorStoreError(f"Unsupported vector store provider: {config.provider}")

    return provider_class(config)
