"""Unit and API Integration Tests for PDF Ingestion Pipeline."""

import os
import pymupdf
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.pdf_service import PDFService
from app.core.exceptions import InvalidFileError, CorruptedPDFError, EmptyPDFError

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))


# ============================================================================
# Helper Functions: PDF Test Fixture Generators
# ============================================================================

def create_mock_pdf_bytes(pages_text: list[str]) -> bytes:
    """Create a real valid PDF in memory using PyMuPDF containing provided text per page."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((50, 100), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_blank_pdf_bytes(page_count: int = 1) -> bytes:
    """Create a PDF document with empty pages containing zero text."""
    doc = pymupdf.open()
    for _ in range(page_count):
        doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ============================================================================
# Unit Tests: PDFService Logic & Validation
# ============================================================================

def test_pdf_service_valid_single_page():
    """Test PDFService extracts single page text and preserves page_number=1."""
    service = PDFService()
    pdf_bytes = create_mock_pdf_bytes(["Sample text content for page 1"])
    
    filename = service.validate_pdf_file("test.pdf", pdf_bytes, content_type="application/pdf")
    assert filename == "test.pdf"

    pages = service.extract_pages(pdf_bytes, filename)
    assert len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert "Sample text content for page 1" in pages[0]["text"]


def test_pdf_service_valid_multi_page_preservation():
    """Test PDFService extracts multi-page text and preserves 1-indexed page numbers."""
    service = PDFService()
    pages_input = [
        "First page content text.",
        "Second page distinct information.",
        "Third page summary content."
    ]
    pdf_bytes = create_mock_pdf_bytes(pages_input)
    
    pages = service.extract_pages(pdf_bytes, "multipage.pdf")
    assert len(pages) == 3
    
    for idx, expected_text in enumerate(pages_input):
        assert pages[idx]["page_number"] == idx + 1
        assert expected_text in pages[idx]["text"]


def test_pdf_service_path_traversal_sanitization():
    """Test PDFService sanitizes filenames with dangerous relative paths."""
    service = PDFService()
    
    safe_1 = service.sanitize_filename("../../etc/passwd.pdf")
    assert safe_1 == "passwd.pdf"
    
    safe_2 = service.sanitize_filename("C:\\Windows\\System32\\malicious.pdf")
    assert safe_2 == "malicious.pdf"


def test_pdf_service_invalid_extension():
    """Test PDFService rejects files without .pdf extension."""
    service = PDFService()
    with pytest.raises(InvalidFileError) as exc_info:
        service.validate_pdf_file("file.txt", b"%PDF-mock content")
    assert "Only PDF documents (.pdf) are supported" in str(exc_info.value.detail)


def test_pdf_service_invalid_mime_type():
    """Test PDFService rejects files with non-PDF MIME type."""
    service = PDFService()
    with pytest.raises(InvalidFileError) as exc_info:
        service.validate_pdf_file("file.pdf", b"%PDF-mock content", content_type="image/png")
    assert "Invalid MIME type" in str(exc_info.value.detail)


def test_pdf_service_invalid_magic_header():
    """Test PDFService rejects files lacking %PDF- magic bytes."""
    service = PDFService()
    with pytest.raises(InvalidFileError) as exc_info:
        service.validate_pdf_file("fake.pdf", b"NOT_A_PDF_MAGIC_HEADER")
    assert "invalid magic header" in str(exc_info.value.detail)


def test_pdf_service_corrupted_pdf_bytes():
    """Test PDFService handles malformed PDF stream gracefully."""
    service = PDFService()
    corrupted_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ncorrupted junk bytes"
    
    with pytest.raises(CorruptedPDFError) as exc_info:
        service.extract_pages(corrupted_bytes, "corrupt.pdf")
    assert "Unable to parse" in str(exc_info.value.detail)


def test_pdf_service_empty_text_pdf():
    """Test PDFService raises EmptyPDFError if PDF has zero text."""
    service = PDFService()
    blank_pdf = create_blank_pdf_bytes(page_count=2)
    
    with pytest.raises(EmptyPDFError) as exc_info:
        service.extract_pages(blank_pdf, "blank.pdf")
    assert "No extractable text found" in str(exc_info.value.detail)


# ============================================================================
# API Integration Tests: POST /api/v1/documents/upload & /api/documents/upload
# ============================================================================

@pytest.mark.asyncio
async def test_api_upload_valid_pdf_v1_endpoint():
    """Test API POST /api/v1/documents/upload with a valid PDF file."""
    pdf_bytes = create_mock_pdf_bytes(["Page 1 API Test Text", "Page 2 API Test Text"])
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_report.pdf", pdf_bytes, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "document_id" in data
        assert data["filename"] == "sample_report.pdf"
        assert data["page_count"] == 2
        assert data["status"] == "processed"
        assert len(data["pages"]) == 2
        assert data["pages"][0]["page_number"] == 1
        assert "Page 1 API Test Text" in data["pages"][0]["text"]
        assert data["pages"][1]["page_number"] == 2
        assert "Page 2 API Test Text" in data["pages"][1]["text"]


@pytest.mark.asyncio
async def test_api_upload_valid_pdf_alias_endpoint():
    """Test API POST /api/documents/upload route alias."""
    pdf_bytes = create_mock_pdf_bytes(["Alias endpoint test text"])
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("alias_doc.pdf", pdf_bytes, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "alias_doc.pdf"
        assert data["page_count"] == 1


@pytest.mark.asyncio
async def test_api_upload_invalid_extension():
    """Test API POST /api/v1/documents/upload returns HTTP 400 for non-PDF file."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("notes.txt", b"plain text file", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Only PDF documents (.pdf) are supported" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_upload_corrupted_pdf():
    """Test API POST /api/v1/documents/upload returns HTTP 422 for malformed PDF."""
    corrupted_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ncorrupted junk content"
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("broken.pdf", corrupted_bytes, "application/pdf")}
        )
        
        assert response.status_code == 422
        assert "Unable to parse" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_upload_real_fixture_pdf():
    """Test API POST /api/v1/documents/upload with real on-disk PDF fixture."""
    fixture_path = os.path.join(ROOT_DIR, "documents", "sample_architecture.pdf")
    with open(fixture_path, "rb") as f:
        real_pdf_bytes = f.read()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_architecture.pdf", real_pdf_bytes, "application/pdf")}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["filename"] == "sample_architecture.pdf"
        assert data["page_count"] == 2
        assert data["pages"][0]["page_number"] == 1
        assert "Page 1" in data["pages"][0]["text"]
        assert data["pages"][1]["page_number"] == 2
        assert "Page 2" in data["pages"][1]["text"]
