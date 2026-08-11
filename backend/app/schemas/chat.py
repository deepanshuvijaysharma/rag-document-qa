"""Chat & Citation Data Schemas (Pydantic Models)."""

from typing import List, Optional

try:
    from pydantic import BaseModel, Field

    class Citation(BaseModel):
        """Source document citation model."""
        document_id: str = Field(..., description="Unique ID of source document")
        filename: str = Field(..., description="Document filename")
        page_number: int = Field(..., description="Page number of retrieved chunk")
        snippet: str = Field(..., description="Excerpt text snippet from chunk")
        similarity_score: float = Field(..., description="Vector similarity score")

    class ChatQueryRequest(BaseModel):
        """Incoming user chat query schema."""
        message: str = Field(..., min_length=1, description="User natural language question")
        conversation_id: Optional[str] = Field(default=None, description="Optional conversation session ID")
        top_k: int = Field(default=4, ge=1, le=10, description="Number of context chunks to retrieve")

    class ChatQueryResponse(BaseModel):
        """Non-streaming chat query response schema."""
        answer: str = Field(..., description="Generated answer text grounded in context")
        citations: List[Citation] = Field(default_factory=list, description="Source citations")
        conversation_id: str = Field(..., description="Conversation session ID")

except ImportError:
    class Citation:  # type: ignore
        pass
    class ChatQueryRequest:  # type: ignore
        pass
    class ChatQueryResponse:  # type: ignore
        pass
