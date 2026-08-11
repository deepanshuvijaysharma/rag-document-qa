"""Pydantic Schemas for Vector Retrieval."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RetrievalQueryRequest(BaseModel):
    """Schema for incoming vector retrieval search request."""
    query: str = Field(..., min_length=1, description="Search query text")
    document_id: Optional[str] = Field(default=None, description="Optional document ID to scope search")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of top matching chunks to return")


class RetrievalResultItem(BaseModel):
    """Normalized structured context chunk returned by vector retrieval."""
    text: str = Field(..., description="Chunk text content")
    document_id: str = Field(..., description="Parent document UUID")
    filename: str = Field(..., description="Source document filename")
    page_number: int = Field(..., ge=1, description="1-indexed page number where chunk originated")
    chunk_id: str = Field(..., description="Unique chunk UUID identifier")
    score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    distance: float = Field(..., description="Cosine distance value")

    model_config = ConfigDict(from_attributes=True)


class RetrievalResponse(BaseModel):
    """Structured response container for vector retrieval search."""
    query: str = Field(..., description="Original user search query")
    total_results: int = Field(..., description="Total matching chunks returned")
    results: List[RetrievalResultItem] = Field(default_factory=list, description="Top matching chunk results")
