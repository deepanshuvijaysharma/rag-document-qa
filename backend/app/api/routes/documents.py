"""Document Management API Endpoints."""

import logging
from fastapi import APIRouter, UploadFile, File, Depends, status
from app.schemas.documents import DocumentUploadResponse
from app.services.document_service import DocumentService
from app.core.exceptions import InvalidFileError

logger = logging.getLogger("rag_app.api.documents")

router = APIRouter()


def get_document_service() -> DocumentService:
    """Dependency provider for DocumentService instance."""
    return DocumentService()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload PDF Document",
    description="Uploads a PDF file, validates format/MIME/headers, extracts text per page preserving page numbers, and returns extracted document structure."
)
async def upload_document(
    file: UploadFile = File(..., description="PDF document file to process"),
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentUploadResponse:
    """Endpoint for PDF document upload and text extraction."""
    if not file or not file.filename:
        raise InvalidFileError("No file provided in upload request.")

    # Read uploaded file bytes in memory safely
    content = await file.read()

    # Process PDF ingestion pipeline
    result = await document_service.process_pdf_upload(
        raw_filename=file.filename,
        content=content,
        content_type=file.content_type
    )

    return DocumentUploadResponse(**result)
