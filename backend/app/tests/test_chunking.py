"""Unit and Integration Tests for Document Chunking Service."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.chunking_service import ChunkingService
from app.tests.test_pdf_ingestion import create_mock_pdf_bytes


# ============================================================================
# Unit Tests: ChunkingService Configuration & Logic
# ============================================================================

def test_invalid_chunk_size_zero():
    """Test ChunkingService raises ValueError when chunk_size <= 0."""
    with pytest.raises(ValueError) as exc_info:
        ChunkingService(chunk_size=0, chunk_overlap=10)
    assert "chunk_size must be a positive integer" in str(exc_info.value)


def test_invalid_chunk_size_negative():
    """Test ChunkingService raises ValueError when chunk_size < 0."""
    with pytest.raises(ValueError) as exc_info:
        ChunkingService(chunk_size=-500, chunk_overlap=10)
    assert "chunk_size must be a positive integer" in str(exc_info.value)


def test_invalid_chunk_overlap_negative():
    """Test ChunkingService raises ValueError when chunk_overlap < 0."""
    with pytest.raises(ValueError) as exc_info:
        ChunkingService(chunk_size=1000, chunk_overlap=-20)
    assert "chunk_overlap cannot be negative" in str(exc_info.value)


def test_invalid_chunk_overlap_equal_or_greater_than_size():
    """Test ChunkingService raises ValueError when chunk_overlap >= chunk_size."""
    with pytest.raises(ValueError) as exc_info:
        ChunkingService(chunk_size=500, chunk_overlap=500)
    assert "must be strictly less than chunk_size" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        ChunkingService(chunk_size=500, chunk_overlap=600)
    assert "must be strictly less than chunk_size" in str(exc_info.value)


def test_chunking_short_document():
    """Test document text shorter than chunk_size creates a single chunk."""
    chunker = ChunkingService(chunk_size=1000, chunk_overlap=100)
    pages = [{"page_number": 1, "text": "Short document content."}]
    
    chunks = chunker.split_pages_into_chunks(pages, doc_id="doc-123", filename="short.pdf")
    
    assert len(chunks) == 1
    assert chunks[0]["chunk_id"] is not None
    assert chunks[0]["document_id"] == "doc-123"
    assert chunks[0]["source_filename"] == "short.pdf"
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["text"] == "Short document content."


def test_chunking_long_document():
    """Test long document text splits into multiple chunks."""
    chunker = ChunkingService(chunk_size=100, chunk_overlap=20)
    long_text = "Word " * 150  # ~750 characters long text
    pages = [{"page_number": 1, "text": long_text}]
    
    chunks = chunker.split_pages_into_chunks(pages, doc_id="doc-long", filename="long.pdf")
    
    assert len(chunks) > 1
    for idx, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == idx
        assert chunk["document_id"] == "doc-long"
        assert chunk["source_filename"] == "long.pdf"
        assert chunk["page_number"] == 1
        assert len(chunk["text"]) <= 120  # Bound check including separator leeway


def test_chunking_overlap_verification():
    """Test adjacent chunks preserve configured overlap content."""
    chunker = ChunkingService(chunk_size=100, chunk_overlap=30)
    text = "Paragraph 1 containing distinct sentences. Paragraph 2 explaining another detail in length. Paragraph 3 summarizing."
    pages = [{"page_number": 1, "text": text}]
    
    chunks = chunker.split_pages_into_chunks(pages, doc_id="doc-overlap", filename="overlap.pdf")
    assert len(chunks) >= 2
    
    # Check that chunk 1 ends with text present at the start of chunk 2
    chunk1_end = chunks[0]["text"][-20:]
    assert any(part in chunks[1]["text"] for part in chunk1_end.split())


def test_chunking_multiple_pages_metadata_preservation():
    """Test chunking preserves page numbers across multi-page input."""
    chunker = ChunkingService(chunk_size=200, chunk_overlap=50)
    pages = [
        {"page_number": 1, "text": "Page 1 " + ("content " * 20)},
        {"page_number": 2, "text": "Page 2 " + ("information " * 20)},
        {"page_number": 3, "text": "Page 3 " + ("summary " * 20)},
    ]
    
    chunks = chunker.split_pages_into_chunks(pages, doc_id="doc-multi", filename="multi.pdf")
    
    # Verify sequential chunk_index
    for idx, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == idx
        assert chunk["document_id"] == "doc-multi"
        assert chunk["source_filename"] == "multi.pdf"
        assert chunk["page_number"] in [1, 2, 3]

    # Verify that page 1 chunks have page_number 1, page 2 has page_number 2, page 3 has page_number 3
    page1_chunks = [c for c in chunks if c["page_number"] == 1]
    page2_chunks = [c for c in chunks if c["page_number"] == 2]
    page3_chunks = [c for c in chunks if c["page_number"] == 3]

    assert len(page1_chunks) >= 1
    assert len(page2_chunks) >= 1
    assert len(page3_chunks) >= 1
    assert "Page 1" in page1_chunks[0]["text"]
    assert "Page 2" in page2_chunks[0]["text"]
    assert "Page 3" in page3_chunks[0]["text"]


def test_chunking_whitespace_and_empty_filtering():
    """Test whitespace-only pages or empty chunks are filtered out."""
    chunker = ChunkingService(chunk_size=500, chunk_overlap=100)
    pages = [
        {"page_number": 1, "text": "   \n\n  \t  "},
        {"page_number": 2, "text": "Valid text on page 2."},
        {"page_number": 3, "text": ""},
    ]
    
    chunks = chunker.split_pages_into_chunks(pages, doc_id="doc-empty", filename="empty.pdf")
    
    assert len(chunks) == 1
    assert chunks[0]["page_number"] == 2
    assert chunks[0]["text"] == "Valid text on page 2."


# ============================================================================
# API Integration Tests: Upload Endpoint with Chunks Response
# ============================================================================

@pytest.mark.asyncio
async def test_api_upload_returns_chunks():
    """Test API POST /api/v1/documents/upload returns chunk_count and chunks list."""
    pdf_bytes = create_mock_pdf_bytes([
        "Page 1 paragraph containing architecture explanation for RAG Document Q&A.",
        "Page 2 paragraph detailing vector embedding and retrieval mechanisms."
    ])

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("architecture.pdf", pdf_bytes, "application/pdf")}
        )

        assert response.status_code == 200
        data = response.json()

        assert "chunk_count" in data
        assert data["chunk_count"] == 2
        assert len(data["chunks"]) == 2

        # Verify chunk #1
        c1 = data["chunks"][0]
        assert c1["chunk_id"] is not None
        assert c1["document_id"] == data["document_id"]
        assert c1["source_filename"] == "architecture.pdf"
        assert c1["page_number"] == 1
        assert c1["chunk_index"] == 0
        assert "Page 1" in c1["text"]

        # Verify chunk #2
        c2 = data["chunks"][1]
        assert c2["page_number"] == 2
        assert c2["chunk_index"] == 1
        assert "Page 2" in c2["text"]
