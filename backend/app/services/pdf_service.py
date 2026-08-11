"""PDF Extraction Service Interface (PyMuPDF)."""

from typing import List, Dict, Any


class PDFService:
    """Service handling PyMuPDF parsing with page number preservation."""

    def __init__(self) -> None:
        """Initialize PDFService."""
        pass

    def extract_pages(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """Extract text page-by-page preserving 1-indexed page numbers.
        
        To be implemented in Phase 2 using PyMuPDF (fitz).
        """
        raise NotImplementedError("PDF text extraction will be implemented in Phase 2.")
