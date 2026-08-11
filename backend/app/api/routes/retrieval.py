"""Vector Retrieval API Endpoints for testing and RAG context search."""

import logging
from fastapi import APIRouter, Depends, status

from app.schemas.retrieval import RetrievalQueryRequest, RetrievalResponse
from app.services.retrieval_service import RetrievalService
from app.core.exceptions import InvalidFileError

logger = logging.getLogger("rag_app.api.retrieval")

router = APIRouter()


def get_retrieval_service() -> RetrievalService:
    """Dependency provider for RetrievalService instance."""
    return RetrievalService()


@router.post(
    "/search",
    response_model=RetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Vector Similarity Search Endpoint",
    description="Embeds query text, performs vector similarity search in ChromaDB, and returns top-K relevant document chunks with page numbers and similarity scores."
)
async def search_retrieval(
    payload: RetrievalQueryRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
) -> RetrievalResponse:
    """Endpoint executing vector similarity retrieval."""
    if not payload.query or not payload.query.strip():
        raise InvalidFileError("Query string cannot be empty.")

    result = retrieval_service.search(
        query=payload.query,
        top_k=payload.top_k,
        document_id=payload.document_id
    )

    return RetrievalResponse(**result)
