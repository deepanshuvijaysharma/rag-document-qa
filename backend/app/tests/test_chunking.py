"""Unit and API Integration Tests for Document Chunking Service."""

import os
import shutil
import tempfile
import pymupdf
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.document_service import DocumentService
from app.db.metadata_store import MetadataStore


def create_mock_pdf_bytes(page_texts: list) -> bytes:
    """Helper to generate in-memory valid PDF bytes for testing."""
    doc = pymupdf.open()
    for text in page_texts:
        page = doc.new_page()
        page.insert_text((50, 100), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ============================================================================
# Unit Tests for ChunkingService Logic & Constraints
# ============================================================================

def test_invalid_chunk_size_zero():
    """Test ChunkingService rejects zero chunk size."""
    with pytest.raises(ValueError) as exc:
        ChunkingService(chunk_size=0, chunk_overlap=0)
    assert "chunk_size must be a positive integer" in str(exc.value)


def test_invalid_chunk_size_negative():
    """Test ChunkingService rejects negative chunk size."""
    with pytest.raises(ValueError) as exc:
        ChunkingService(chunk_size=-100, chunk_overlap=0)
    assert "chunk_size must be a positive integer" in str(exc.value)


def test_invalid_chunk_overlap_negative():
    """Test ChunkingService rejects negative overlap."""
    with pytest.raises(ValueError) as exc:
        ChunkingService(chunk_size=500, chunk_overlap=-10)
    assert "chunk_overlap cannot be negative" in str(exc.value)


def test_invalid_chunk_overlap_equal_or_greater_than_size():
    """Test ChunkingService rejects overlap >= chunk_size."""
    with pytest.raises(ValueError) as exc:
        ChunkingService(chunk_size=500, chunk_overlap=500)
    assert "chunk_overlap must be strictly less than chunk_size" in str(exc.value)

    with pytest.raises(ValueError) as exc2:
        ChunkingService(chunk_size=500, chunk_overlap=600)
    assert "chunk_overlap must be strictly less than chunk_size" in str(exc2.value)


def test_chunking_short_document():
    """Test splitting a short single-page document into chunks."""
    chunker = ChunkingService(chunk_size=500, chunk_overlap=50)
    pages = [{
        "page_number": 1,
        "source_filename": "short.pdf",
        "document_id": "doc-101",
        "text": "This is a short document page paragraph explaining system design."
    }]

    chunks = chunker.split_pages_into_chunks(pages)

    assert len(chunks) == 1
    c = chunks[0]
    assert c["page_number"] == 1
    assert c["source_filename"] == "short.pdf"
    assert c["document_id"] == "doc-101"
    assert c["chunk_index"] == 0
    assert c["chunk_id"] == "chunk-doc-101-0"
    assert "system design" in c["text"]


def test_chunking_long_document():
    """Test splitting a long text into multiple sequential chunks."""
    chunker = ChunkingService(chunk_size=100, chunk_overlap=20)
    long_text = "Word " * 150  # ~750 characters

    pages = [{
        "page_number": 1,
        "source_filename": "long.pdf",
        "document_id": "doc-102",
        "text": long_text
    }]

    chunks = chunker.split_pages_into_chunks(pages)

    assert len(chunks) > 1
    for idx, c in enumerate(chunks):
        assert c["page_number"] == 1
        assert c["chunk_index"] == idx
        assert c["chunk_id"] == f"chunk-doc-102-{idx}"
        assert len(c["text"]) > 0


def test_chunking_overlap_verification():
    """Test chunk overlap retains trailing text from preceding chunk."""
    chunker = ChunkingService(chunk_size=50, chunk_overlap=15)
    text = "Alpha Beta Gamma Delta Epsilon Zeta Eta Theta Iota Kappa Lambda Mu"

    pages = [{
        "page_number": 1,
        "source_filename": "overlap.pdf",
        "document_id": "doc-103",
        "text": text
    }]

    chunks = chunker.split_pages_into_chunks(pages)
    assert len(chunks) >= 2

    # Check that tail of chunk 0 overlaps with head of chunk 1
    chunk0_words = set(chunks[0]["text"].split())
    chunk1_words = set(chunks[1]["text"].split())
    overlapping_words = chunk0_words.intersection(chunk1_words)
    assert len(overlapping_words) > 0


def test_chunking_multiple_pages_metadata_preservation():
    """Test chunking across multiple pages preserves distinct page_number and source_filename metadata."""
    chunker = ChunkingService(chunk_size=200, chunk_overlap=20)
    pages = [
        {"page_number": 1, "source_filename": "multi.pdf", "document_id": "doc-104", "text": "Page 1 content about engineering principles."},
        {"page_number": 2, "source_filename": "multi.pdf", "document_id": "doc-104", "text": "Page 2 content about system architecture."}
    ]

    chunks = chunker.split_pages_into_chunks(pages)

    page1_chunks = [c for c in chunks if c["page_number"] == 1]
    page2_chunks = [c for c in chunks if c["page_number"] == 2]

    assert len(page1_chunks) >= 1
    assert len(page2_chunks) >= 1

    assert "engineering principles" in page1_chunks[0]["text"]
    assert "system architecture" in page2_chunks[0]["text"]


def test_chunking_whitespace_and_empty_filtering():
    """Test whitespace-only and empty pages produce no chunks."""
    chunker = ChunkingService()
    pages = [
        {"page_number": 1, "source_filename": "empty.pdf", "document_id": "doc-105", "text": "   \n\t  "},
        {"page_number": 2, "source_filename": "empty.pdf", "document_id": "doc-105", "text": ""}
    ]

    chunks = chunker.split_pages_into_chunks(pages)
    assert len(chunks) == 0


# ============================================================================
# API Integration Tests: Upload Endpoint with Chunks Response
# ============================================================================

@pytest.mark.asyncio
async def test_api_upload_returns_chunks():
    """Test API POST /api/v1/documents/upload returns chunk_count and chunks list."""
    temp_dir = tempfile.mkdtemp(prefix="rag_chunk_test_")
    chroma_dir = os.path.join(temp_dir, "chroma")
    meta_file = os.path.join(temp_dir, "documents.json")

    pdf_service = PDFService()
    chunking_service = ChunkingService(chunk_size=1000, chunk_overlap=200)
    embedding_service = EmbeddingService()
    vector_service = VectorService(persist_directory=chroma_dir, collection_name="chunk_test_col")
    metadata_store = MetadataStore(file_path=meta_file)

    doc_service = DocumentService(
        pdf_service=pdf_service,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
        vector_service=vector_service,
        metadata_store=metadata_store
    )

    app.dependency_overrides = {}
    from app.api.routes.documents import get_document_service
    app.dependency_overrides[get_document_service] = lambda: doc_service

    try:
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
    finally:
        app.dependency_overrides.clear()
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
