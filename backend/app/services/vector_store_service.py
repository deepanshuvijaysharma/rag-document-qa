"""Vector Store Service Interface (ChromaDB)."""

from typing import List, Dict, Any, Optional


class VectorStoreService:
    """Service wrapping ChromaDB vector indexing and similarity search."""

    def __init__(self, persist_directory: str, collection_name: str) -> None:
        """Initialize VectorStoreService with storage settings."""
        self.persist_directory = persist_directory
        self.collection_name = collection_name

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        """Add text chunks, metadata, and embeddings to Chroma collection.
        
        To be implemented in Phase 2.
        """
        raise NotImplementedError("Vector store indexing will be implemented in Phase 2.")

    def search_similar(self, query_embedding: List[float], top_k: int = 4) -> List[Dict[str, Any]]:
        """Search top-K most similar text chunks.
        
        To be implemented in Phase 3.
        """
        raise NotImplementedError("Vector similarity search will be implemented in Phase 3.")

    def delete_document_vectors(self, doc_id: str) -> int:
        """Purge all vectors belonging to doc_id.
        
        To be implemented in Phase 2.
        """
        raise NotImplementedError("Vector deletion will be implemented in Phase 2.")
