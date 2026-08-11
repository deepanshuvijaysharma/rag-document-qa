"""Retrieval Service Interface."""

from typing import List, Dict, Any


class RetrievalService:
    """Service orchestrating question embedding, ChromaDB search, and distance filtering."""

    def __init__(self) -> None:
        """Initialize RetrievalService."""
        pass

    def retrieve_relevant_context(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Retrieve relevant context chunks with metadata for user query.
        
        To be implemented in Phase 3.
        """
        raise NotImplementedError("Context retrieval will be implemented in Phase 3.")
