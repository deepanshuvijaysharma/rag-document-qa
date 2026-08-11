"""Document Data Schemas (Pydantic Models)."""

from datetime import datetime
from typing import List, Optional

try:
    from pydantic import BaseModel, Field

    class DocumentBase(BaseModel):
        """Base document properties."""
        filename: str = Field(..., description="Original name of the uploaded document")

    class DocumentCreate(DocumentBase):
        """Schema for document upload payload."""
        pass

    class DocumentResponse(DocumentBase):
        """Schema for document metadata returned by API."""
        id: str = Field(..., description="Unique UUID identifier of document")
        file_size: int = Field(..., description="File size in bytes")
        page_count: int = Field(..., description="Total number of pages parsed")
        chunk_count: int = Field(..., description="Total number of chunks generated")
        upload_timestamp: datetime = Field(..., description="Upload timestamp")
        status: str = Field(default="processed", description="Processing status: processing, processed, error")

        class Config:
            from_attributes = True

    class DocumentListResponse(BaseModel):
        """Schema for listing all active documents."""
        documents: List[DocumentResponse]
        total_count: int

except ImportError:
    class DocumentBase:  # type: ignore
        pass
    class DocumentCreate:  # type: ignore
        pass
    class DocumentResponse:  # type: ignore
        pass
    class DocumentListResponse:  # type: ignore
        pass
