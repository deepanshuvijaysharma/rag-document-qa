"""Document Management Service."""

import uuid
import logging
from typing import Dict, Any, List
from app.services.pdf_service import PDFService

logger = logging.getLogger("rag_app.document_service")


class DocumentService:
    """Service handling high-level document ingestion and lifecycle."""

    def __init__(self, pdf_service: PDFService = None) -> None:
        """Initialize DocumentService with dependency injection."""
        self.pdf_service = pdf_service or PDFService()

    async def process_pdf_upload(self, raw_filename: str, content: bytes) -> Dict[str, Any]:
        """Validate uploaded PDF, extract page text, and return document structure.
        
        Returns dictionary matching DocumentUploadResponse schema:
        {
            "document_id": "...",
            "filename": "...",
            "file_size": 12345,
            "page_count": 5,
            "status": "processed",
            "pages": [{"page_number": 1, "text": "..."}, ...]
        }
        """
        # 1. Validate file extension, size, and magic headers
        sanitized_filename = self.pdf_service.validate_pdf_file(raw_filename, content)

        # 2. Extract page-indexed text via PyMuPDF
        pages = self.pdf_service.extract_pages(content, filename=sanitized_filename)

        # 3. Generate unique document ID
        doc_id = str(uuid.uuid4())

        logger.info(
            f"Successfully processed PDF upload '{sanitized_filename}' "
            f"(ID: {doc_id}, Pages: {len(pages)}, Size: {len(content)} bytes)"
        )

        return {
            "document_id": doc_id,
            "filename": sanitized_filename,
            "file_size": len(content),
            "page_count": len(pages),
            "status": "processed",
            "pages": pages
        }
