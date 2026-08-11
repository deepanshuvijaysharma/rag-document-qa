"""Embedding Generation Service Interface."""

from typing import List


class EmbeddingService:
    """Service generating vector embeddings via SentenceTransformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize EmbeddingService with model name."""
        self.model_name = model_name

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector representations for text chunks.
        
        To be implemented in Phase 2 using SentenceTransformers.
        """
        raise NotImplementedError("Embedding generation will be implemented in Phase 2.")

    def embed_query(self, query: str) -> List[float]:
        """Generate dense vector representation for user question.
        
        To be implemented in Phase 2 using SentenceTransformers.
        """
        raise NotImplementedError("Query embedding will be implemented in Phase 2.")
