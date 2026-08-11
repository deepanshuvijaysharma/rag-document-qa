"""Custom Domain Exceptions for Document Processing."""

from fastapi import HTTPException, status

# HTTP 422 Unprocessable Content (replaces deprecated HTTP_422_UNPROCESSABLE_ENTITY name)
HTTP_422_UNPROCESSABLE = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


class InvalidFileError(HTTPException):
    """Raised when an uploaded file fails extension, magic number, or size validation."""

    def __init__(self, detail: str = "Invalid file upload."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class CorruptedPDFError(HTTPException):
    """Raised when PyMuPDF fails to parse a corrupted or encrypted PDF file."""

    def __init__(self, detail: str = "Unable to parse corrupted or unreadable PDF document."):
        super().__init__(status_code=HTTP_422_UNPROCESSABLE, detail=detail)


class EmptyPDFError(HTTPException):
    """Raised when a PDF contains no pages or zero extractable text."""

    def __init__(self, detail: str = "The uploaded PDF document contains no extractable text."):
        super().__init__(status_code=HTTP_422_UNPROCESSABLE, detail=detail)
