"""Document Data Schemas (Pydantic Models)."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PageContent(BaseModel):
    """Extracted text page properties preserving page numbers."""
    page_number: int = Field(..., ge=1, description="1-indexed page number within document")
    text: str = Field(..., description="Raw text content extracted from page")


class DocumentBase(BaseModel):
    """Base document properties."""
    filename: str = Field(..., description="Original or sanitized name of uploaded document")


class DocumentUploadResponse(DocumentBase):
    """Response schema returned upon successful document upload & text extraction."""
    document_id: str = Field(..., description="Unique UUID identifier for uploaded document")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int = Field(..., description="Total number of pages extracted")
    status: str = Field(default="processed", description="Document processing status")
    pages: List[PageContent] = Field(default_factory=list, description="Extracted pages with numbers")


class DocumentResponse(DocumentBase):
    """Schema for stored document metadata."""
    id: str = Field(..., description="Unique UUID identifier of document")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int = Field(..., description="Total number of pages parsed")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    status: str = Field(default="processed", description="Processing status")

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Schema for listing all active documents."""
    documents: List[DocumentResponse]
    total_count: int
