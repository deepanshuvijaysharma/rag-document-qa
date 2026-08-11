"""Chat & Citation Data Schemas (Pydantic Models)."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SourceCitation(BaseModel):
    """Source document citation model."""
    document_id: str = Field(..., description="Unique UUID of source document")
    filename: str = Field(..., description="Source document filename")
    page_number: int = Field(..., ge=1, description="1-indexed page number of retrieved chunk")
    chunk_id: str = Field(..., description="Unique UUID of retrieved text chunk")
    relevance_score: float = Field(..., description="Cosine similarity relevance score (0.0 to 1.0)")

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    """Incoming user chat query payload."""
    message: str = Field(..., min_length=1, description="User natural language question")
    document_id: Optional[str] = Field(default=None, description="Optional document UUID to scope question")
    conversation_id: Optional[str] = Field(default=None, description="Optional conversation session ID")


class ChatResponse(BaseModel):
    """Grounded RAG chat query response payload."""
    conversation_id: str = Field(..., description="Unique conversation session UUID")
    answer: str = Field(..., description="Generated grounded answer string")
    sources: List[SourceCitation] = Field(default_factory=list, description="List of source citations used")

    model_config = ConfigDict(from_attributes=True)
