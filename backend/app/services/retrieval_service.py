"""Vector & Hybrid Retrieval Service for Grounded RAG Context Assembly."""

import re
import logging
from typing import List, Dict, Any, Optional

from app.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.core.exceptions import VectorStoreError, EmbeddingError

logger = logging.getLogger("rag_app.retrieval_service")


class RetrievalService:
    """Service handling query vectorization, ChromaDB similarity search, and hybrid keyword re-ranking."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_service: Optional[VectorService] = None
    ) -> None:
        """Initialize RetrievalService with dependency injection."""
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_service = vector_service or VectorService()

    def _compute_keyword_overlap(self, query: str, text: str) -> float:
        """Calculate token overlap ratio between query keywords and candidate text chunk."""
        query_words = set(re.findall(r"\w+", query.lower()))
        if not query_words:
            return 0.0
        text_words = set(re.findall(r"\w+", text.lower()))
        matched_words = query_words.intersection(text_words)
        return len(matched_words) / len(query_words)

    def search(
        self,
        query: str,
        top_k: int = 4,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Hybrid search combining dense vector embeddings with sparse keyword term overlap.
        
        Args:
            query: User natural language search question
            top_k: Maximum number of context chunks to retrieve (default: 4)
            document_id: Optional document UUID filter
            
        Returns:
            Dict matching RetrievalResponse schema:
            {
                "query": "...",
                "total_results": 2,
                "results": [
                    {
                        "text": "...",
                        "document_id": "...",
                        "filename": "...",
                        "page_number": 1,
                        "chunk_id": "...",
                        "score": 0.89,
                        "distance": 0.11
                    },
                    ...
                ]
            }
        """
        if not query or not query.strip():
            logger.warning("Retrieval search rejected: empty query string.")
            raise ValueError("Query string cannot be empty or whitespace-only.")

        if top_k <= 0:
            raise ValueError("top_k must be a positive integer greater than 0.")

        clean_query = query.strip()

        # 1. Vectorize search query using embedding service
        try:
            query_embedding = self.embedding_service.embed_query(clean_query)
        except Exception as err:
            logger.error(f"Failed to generate embedding for query '{clean_query}': {err}")
            raise EmbeddingError(f"Error vectorizing search query: {err}")

        # 2. Query ChromaDB vector index for nearest neighbors (fetch candidates for hybrid reranking)
        fetch_k = max(top_k * 2, 8)
        try:
            matches = self.vector_service.similarity_search(
                query_embedding=query_embedding,
                top_k=fetch_k,
                document_id=document_id
            )
        except Exception as err:
            logger.error(f"ChromaDB retrieval failed for query '{clean_query}': {err}")
            raise VectorStoreError(f"Error searching vector store: {err}")

        # 3. Hybrid Reranking: Dense Cosine Similarity (70%) + Sparse Keyword Overlap (30%)
        normalized_results: List[Dict[str, Any]] = []
        for match in matches:
            dense_score = match["score"]
            kw_overlap = self._compute_keyword_overlap(clean_query, match["text"])
            hybrid_score = round((0.7 * dense_score) + (0.3 * kw_overlap), 4)

            normalized_results.append({
                "text": match["text"],
                "document_id": match["document_id"],
                "filename": match["source_filename"],
                "page_number": match["page_number"],
                "chunk_id": match["chunk_id"],
                "score": max(dense_score, hybrid_score),
                "distance": match["distance"]
            })

        # Sort candidate results by hybrid score descending and limit to top_k
        normalized_results.sort(key=lambda x: x["score"], reverse=True)
        final_results = normalized_results[:top_k]

        logger.info(
            f"Hybrid retrieval query '{clean_query}' returned {len(final_results)} results "
            f"(top_k={top_k}, doc_filter={document_id or 'ALL'})."
        )

        return {
            "query": clean_query,
            "total_results": len(final_results),
            "results": final_results
        }
