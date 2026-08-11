"""PDF Extraction Service using PyMuPDF."""

import os
import re
import logging
from typing import List, Dict, Any, Optional
import pymupdf

from app.core.exceptions import InvalidFileError, CorruptedPDFError, EmptyPDFError

logger = logging.getLogger("rag_app.pdf_service")

# Maximum allowed file size: 25 MB
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024

# Allowed PDF MIME types
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/acrobat",
    "applications/vnd.pdf",
    "text/pdf",
    "text/x-pdf",
    "application/octet-stream",  # Generic binary upload header
}


class PDFService:
    """Service handling PDF file validation and page-by-page text extraction."""

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize input filename to prevent directory path traversal.
        
        Extracts basename and strips any unsafe path components or null bytes.
        """
        if not filename:
            return "document.pdf"
        
        # Take basename only
        clean_name = os.path.basename(filename.replace("\\", "/"))
        # Remove any null bytes or non-printable characters
        clean_name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', clean_name)
        # Ensure it has a valid name
        if not clean_name.strip():
            clean_name = "document.pdf"
            
        return clean_name

    def validate_pdf_file(self, filename: str, content: bytes, content_type: Optional[str] = None) -> str:
        """Validate uploaded PDF file extension, magic bytes, MIME type, and file size.
        
        Returns sanitized filename if valid.
        Raises InvalidFileError if validation fails.
        """
        sanitized_name = self.sanitize_filename(filename)

        # 1. Validate file extension
        if not sanitized_name.lower().endswith(".pdf"):
            logger.warning(f"File validation failed: '{sanitized_name}' lacks .pdf extension.")
            raise InvalidFileError("Only PDF documents (.pdf) are supported.")

        # 2. Validate MIME type if supplied by request
        if content_type:
            clean_mime = content_type.strip().lower()
            if clean_mime not in ALLOWED_MIME_TYPES:
                logger.warning(f"File validation failed: Invalid MIME type '{content_type}' for '{sanitized_name}'.")
                raise InvalidFileError(f"Invalid MIME type '{content_type}'. Only PDF files are supported.")

        # 3. Validate non-empty content
        file_size = len(content)
        if file_size == 0:
            logger.warning("File validation failed: Uploaded file is 0 bytes.")
            raise InvalidFileError("Uploaded file is empty (0 bytes).")

        # 4. Validate file size limits
        if file_size > MAX_FILE_SIZE_BYTES:
            max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
            logger.warning(f"File validation failed: Size {file_size} exceeds {max_mb}MB limit.")
            raise InvalidFileError(f"File size exceeds maximum allowed limit of {max_mb}MB.")

        # 5. Validate magic number bytes (%PDF-)
        if not content.startswith(b"%PDF-"):
            logger.warning(f"File validation failed: Magic number header missing in '{sanitized_name}'.")
            raise InvalidFileError("File content is not a valid PDF document (invalid magic header).")

        return sanitized_name

    def extract_pages(self, pdf_bytes: bytes, filename: str = "document.pdf") -> List[Dict[str, Any]]:
        """Extract text page-by-page from PDF bytes, preserving 1-indexed page numbers.
        
        Returns list of dicts: [{"page_number": 1, "text": "..."}, ...]
        Raises CorruptedPDFError or EmptyPDFError on parsing failure.
        """
        extracted_pages: List[Dict[str, Any]] = []

        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        except Exception as err:
            logger.error(f"PyMuPDF failed opening stream for '{filename}': {err}")
            raise CorruptedPDFError("Unable to open or parse PDF file. The file may be damaged or encrypted.")

        try:
            # Check for damaged or encrypted document
            if doc.is_encrypted or getattr(doc, "is_damaged", False):
                logger.warning(f"PDF '{filename}' is damaged or encrypted.")
                raise CorruptedPDFError("Unable to parse encrypted or damaged PDF document.")

            total_pages = len(doc)
            if total_pages == 0:
                logger.warning(f"PDF '{filename}' has 0 pages or invalid page tree structure.")
                raise CorruptedPDFError("Unable to parse corrupted PDF structure (0 pages found).")

            total_extracted_length = 0

            for page_idx in range(total_pages):
                try:
                    page = doc[page_idx]
                    page_text = page.get_text("text") or ""
                    # Clean up null characters and trim trailing whitespace
                    clean_text = page_text.replace("\x00", "").strip()
                    page_number = page_idx + 1  # 1-indexed page numbering

                    extracted_pages.append({
                        "page_number": page_number,
                        "text": clean_text
                    })
                    total_extracted_length += len(clean_text)
                except Exception as page_err:
                    logger.error(f"Error extracting page {page_idx + 1} from '{filename}': {page_err}")
                    extracted_pages.append({
                        "page_number": page_idx + 1,
                        "text": ""
                    })

            # Check if any extractable text was found across all pages
            if total_extracted_length == 0:
                logger.warning(f"PDF '{filename}' contains zero extractable text across all {total_pages} pages.")
                raise EmptyPDFError("No extractable text found in PDF document (may contain only scanned images without OCR).")

            return extracted_pages

        finally:
            doc.close()
