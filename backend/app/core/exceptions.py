"""Custom Domain Exceptions for Document Processing, Embeddings, Vector Store & LLM Services."""

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


class DocumentNotFoundError(HTTPException):
    """Raised when a requested document is not found in metadata store."""

    def __init__(self, detail: str = "Requested document was not found."):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class EmbeddingError(HTTPException):
    """Raised when vector embedding generation fails due to model execution or invalid input."""

    def __init__(self, detail: str = "Failed to generate vector embedding."):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class VectorStoreError(HTTPException):
    """Raised when ChromaDB collection operations fail."""

    def __init__(self, detail: str = "Vector database storage operation failed."):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class LLMProviderError(HTTPException):
    """Raised when an LLM provider API call or initialization fails."""

    def __init__(self, detail: str = "LLM provider service error."):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
