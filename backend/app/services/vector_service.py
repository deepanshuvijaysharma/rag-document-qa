"""Dedicated Vector Database Service using ChromaDB."""

import os
import logging
from typing import List, Dict, Any, Optional
import chromadb

from app.config import settings
from app.core.exceptions import VectorStoreError

logger = logging.getLogger("rag_app.vector_service")


class VectorService:
    """Service handling ChromaDB vector index operations, collection CRUD, and similarity queries."""

    # Shared persistent client instance per directory to prevent file lock contention
    _client_cache: Dict[str, chromadb.PersistentClient] = {}

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ) -> None:
        """Initialize VectorService with persistent storage directory and collection boundaries.
        
        Args:
            persist_directory: Storage directory path for ChromaDB files. Defaults to settings.CHROMA_PERSIST_DIRECTORY.
            collection_name: Collection name. Defaults to settings.CHROMA_COLLECTION_NAME.
        """
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME

        # Ensure persist directory path exists
        os.makedirs(self.persist_directory, exist_ok=True)

        # Get or create persistent client instance
        if self.persist_directory not in self._client_cache:
            logger.info(f"Initializing ChromaDB PersistentClient at '{self.persist_directory}'...")
            self._client_cache[self.persist_directory] = chromadb.PersistentClient(path=self.persist_directory)

        self.client = self._client_cache[self.persist_directory]

        # Get or create collection configured with cosine distance space
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Connected to ChromaDB collection '{self.collection_name}'. Current count: {self.collection.count()}")
        except Exception as err:
            logger.error(f"Failed to access ChromaDB collection '{self.collection_name}': {err}")
            raise VectorStoreError(f"Unable to initialize ChromaDB collection '{self.collection_name}': {err}")

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
        """Upsert document text chunks, vector embeddings, and metadata into ChromaDB collection.
        
        Args:
            chunks: List of chunk dictionaries containing chunk_id, document_id, source_filename, page_number, chunk_index, text
            embeddings: List of matching float vector embedding lists
            
        Returns:
            Count of added chunks.
            
        Raises:
            ValueError: If lengths of chunks and embeddings do not match.
            VectorStoreError: If ChromaDB operation fails.
        """
        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch between chunks count ({len(chunks)}) and embeddings count ({len(embeddings)}).")

        ids: List[str] = []
        vectors: List[List[float]] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = chunk.get("chunk_id")
            if not chunk_id:
                raise ValueError("Every chunk must contain a valid 'chunk_id'.")

            ids.append(str(chunk_id))
            vectors.append(embedding)
            documents.append(chunk["text"])
            metadatas.append({
                "document_id": str(chunk["document_id"]),
                "source_filename": str(chunk["source_filename"]),
                "page_number": int(chunk["page_number"]),
                "chunk_index": int(chunk["chunk_index"])
            })

        try:
            self.collection.upsert(
                ids=ids,
                embeddings=vectors,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Successfully upserted {len(ids)} vector chunks into ChromaDB collection '{self.collection_name}'.")
            return len(ids)
        except Exception as err:
            logger.error(f"Failed to upsert chunks into ChromaDB: {err}")
            raise VectorStoreError(f"Error storing document vectors in ChromaDB: {err}")

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform cosine similarity search against stored vector embeddings.
        
        Args:
            query_embedding: 384-dimensional query vector float list
            top_k: Number of nearest neighbor matches to retrieve
            document_id: Optional document ID filter
            
        Returns:
            List of matching chunk dicts with similarity score, text, and page metadata:
            [
                {
                    "chunk_id": "...",
                    "document_id": "...",
                    "source_filename": "...",
                    "page_number": 1,
                    "chunk_index": 0,
                    "text": "...",
                    "distance": 0.12,
                    "score": 0.88
                },
                ...
            ]
        """
        if not query_embedding:
            raise ValueError("query_embedding cannot be empty.")

        if self.collection.count() == 0:
            return []

        where_filter: Optional[Dict[str, Any]] = None
        if document_id:
            where_filter = {"document_id": document_id}

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as err:
            logger.error(f"ChromaDB similarity query failed: {err}")
            raise VectorStoreError(f"Error executing vector similarity search: {err}")

        matches: List[Dict[str, Any]] = []

        if not results or "ids" not in results or not results["ids"] or not results["ids"][0]:
            return matches

        ids_list = results["ids"][0]
        docs_list = results.get("documents", [[]])[0]
        meta_list = results.get("metadatas", [[]])[0]
        dist_list = results.get("distances", [[]])[0]

        for chunk_id, doc_text, metadata, dist in zip(ids_list, docs_list, meta_list, dist_list):
            distance_val = float(dist) if dist is not None else 1.0
            # Calculate cosine similarity score (1.0 - cosine_distance)
            score_val = max(0.0, min(1.0, 1.0 - distance_val))

            matches.append({
                "chunk_id": chunk_id,
                "text": doc_text,
                "document_id": metadata.get("document_id", ""),
                "source_filename": metadata.get("source_filename", ""),
                "page_number": metadata.get("page_number", 1),
                "chunk_index": metadata.get("chunk_index", 0),
                "distance": round(distance_val, 4),
                "score": round(score_val, 4)
            })

        return matches

    def delete_document(self, document_id: str) -> int:
        """Purge all vector chunks associated with a specific document_id.
        
        Args:
            document_id: Parent document UUID string
            
        Returns:
            Number of vectors purged.
        """
        if not document_id:
            raise ValueError("document_id cannot be empty.")

        initial_count = self.collection.count()
        if initial_count == 0:
            return 0

        try:
            self.collection.delete(where={"document_id": document_id})
            new_count = self.collection.count()
            deleted_count = initial_count - new_count
            logger.info(f"Purged document '{document_id}' from ChromaDB collection. Deleted {deleted_count} vector records.")
            return deleted_count
        except Exception as err:
            logger.error(f"Failed to delete document '{document_id}' from ChromaDB: {err}")
            raise VectorStoreError(f"Error purging document vectors from ChromaDB: {err}")

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Retrieve all stored vector chunks and metadata for a specific document."""
        if not document_id:
            return []

        try:
            results = self.collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"]
            )
            chunks: List[Dict[str, Any]] = []
            if results and "ids" in results:
                for chunk_id, doc_text, metadata in zip(results["ids"], results["documents"], results["metadatas"]):
                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": doc_text,
                        "document_id": metadata.get("document_id"),
                        "source_filename": metadata.get("source_filename"),
                        "page_number": metadata.get("page_number"),
                        "chunk_index": metadata.get("chunk_index")
                    })
            return chunks
        except Exception as err:
            logger.error(f"Failed retrieving chunks for document '{document_id}': {err}")
            raise VectorStoreError(f"Error retrieving document vector records: {err}")

    def count(self) -> int:
        """Return total vector count in the collection."""
        return self.collection.count()

    def clear(self) -> None:
        """Delete all vectors in collection (primarily for tests/reset)."""
        try:
            # Delete all items by querying all ids
            all_data = self.collection.get()
            if all_data and "ids" in all_data and all_data["ids"]:
                self.collection.delete(ids=all_data["ids"])
            logger.info(f"Cleared all vector records from collection '{self.collection_name}'.")
        except Exception as err:
            logger.error(f"Failed to clear ChromaDB collection: {err}")
            raise VectorStoreError(f"Error clearing ChromaDB collection: {err}")
