"""Document & Chunk Data Schemas (Pydantic Models)."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PageContent(BaseModel):
    """Extracted text page properties preserving page numbers."""
    page_number: int = Field(..., ge=1, description="1-indexed page number within document")
    text: str = Field(..., description="Raw text content extracted from page")


class DocumentChunk(BaseModel):
    """Extracted semantic text chunk with preserved page and source metadata."""
    chunk_id: str = Field(..., description="Unique UUID identifier for chunk")
    document_id: str = Field(..., description="Parent document UUID")
    source_filename: str = Field(..., description="Source document filename")
    page_number: int = Field(..., ge=1, description="1-indexed page number where chunk originated")
    chunk_index: int = Field(..., ge=0, description="Sequential 0-indexed position of chunk within document")
    text: str = Field(..., description="Cleaned chunk text content")


class DocumentBase(BaseModel):
    """Base document properties."""
    filename: str = Field(..., description="Original or sanitized name of uploaded document")


class DocumentUploadResponse(DocumentBase):
    """Response schema returned upon successful document upload, text extraction, and chunking."""
    document_id: str = Field(..., description="Unique UUID identifier for uploaded document")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int = Field(..., description="Total number of pages extracted")
    chunk_count: int = Field(..., description="Total number of chunks generated")
    status: str = Field(default="processed", description="Document processing status")
    pages: List[PageContent] = Field(default_factory=list, description="Extracted pages with numbers")
    chunks: List[DocumentChunk] = Field(default_factory=list, description="Generated semantic text chunks")


class DocumentResponse(DocumentBase):
    """Schema for stored document metadata."""
    id: str = Field(..., description="Unique UUID identifier of document")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int = Field(..., description="Total number of pages parsed")
    chunk_count: int = Field(default=0, description="Total number of chunks generated")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    status: str = Field(default="processed", description="Processing status")

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Schema for listing all active documents."""
    documents: List[DocumentResponse]
    total_count: int
