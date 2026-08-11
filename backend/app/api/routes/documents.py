"""Document Management API Endpoints."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, Depends, status, Path

from app.schemas.documents import DocumentUploadResponse, DocumentListResponse, DocumentResponse
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
    summary="Upload and Ingest PDF Document",
    description="Uploads a PDF file, validates format/headers, extracts text per page, chunks text, generates embeddings, stores vectors in ChromaDB, and returns ingestion result."
)
async def upload_document(
    file: UploadFile = File(..., description="PDF document file to process"),
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentUploadResponse:
    """Endpoint for PDF document upload, chunking, vector embedding, and ChromaDB indexing."""
    if not file or not file.filename:
        raise InvalidFileError("No file provided in upload request.")

    # Read uploaded file bytes in memory safely
    content = await file.read()

    # Process complete PDF ingestion pipeline
    result = await document_service.process_pdf_upload(
        raw_filename=file.filename,
        content=content,
        content_type=file.content_type
    )

    return DocumentUploadResponse(**result)


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Ingested Documents",
    description="Retrieves a summary list of all active ingested PDF documents."
)
async def list_documents(
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentListResponse:
    """Endpoint to list all active ingested documents."""
    docs = document_service.list_documents()
    formatted_docs = [DocumentResponse(**doc) for doc in docs]
    return DocumentListResponse(documents=formatted_docs, total_count=len(formatted_docs))


@router.get(
    "/{document_id}",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Document Details",
    description="Retrieves complete document metadata including extracted pages and chunks for a given document_id."
)
async def get_document(
    document_id: str = Path(..., description="Unique UUID identifier of document"),
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentUploadResponse:
    """Endpoint to retrieve single document details with pages and chunks."""
    result = document_service.get_document(document_id)
    return DocumentUploadResponse(**result)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Document",
    description="Deletes document metadata and purges all associated vector embeddings from ChromaDB."
)
async def delete_document(
    document_id: str = Path(..., description="Unique UUID identifier of document to delete"),
    document_service: DocumentService = Depends(get_document_service)
) -> Dict[str, Any]:
    """Endpoint to delete document metadata and purge ChromaDB vector embeddings."""
    return document_service.delete_document(document_id)
