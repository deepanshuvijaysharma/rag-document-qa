"""Unit and Integration Tests for ChromaDB Vector Database Layer."""

import os
import shutil
import tempfile
import pytest

from app.services.vector_service import VectorService
from app.services.embedding_service import EmbeddingService
from app.core.exceptions import VectorStoreError


@pytest.fixture
def temp_vector_service():
    """Fixture providing an isolated temporary VectorService instance."""
    temp_dir = tempfile.mkdtemp(prefix="chroma_test_")
    service = VectorService(persist_directory=temp_dir, collection_name="test_collection")
    yield service
    # Cleanup temp directory after test execution
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


def test_vector_service_initialization(temp_vector_service):
    """Test VectorService initializes with clean collection."""
    assert temp_vector_service.collection_name == "test_collection"
    assert temp_vector_service.count() == 0


def test_vector_service_add_chunks_and_count(temp_vector_service):
    """Test adding document chunks and embeddings updates collection count."""
    embedder = EmbeddingService()
    chunks = [
        {
            "chunk_id": "chunk-101",
            "document_id": "doc-001",
            "source_filename": "architecture.pdf",
            "page_number": 1,
            "chunk_index": 0,
            "text": "Retrieval-Augmented Generation architecture uses vector database storage."
        },
        {
            "chunk_id": "chunk-102",
            "document_id": "doc-001",
            "source_filename": "architecture.pdf",
            "page_number": 2,
            "chunk_index": 1,
            "text": "PyMuPDF parses PDF pages preserving exact 1-indexed page metadata."
        }
    ]

    embeddings = embedder.embed_documents([c["text"] for c in chunks])
    added_count = temp_vector_service.add_chunks(chunks, embeddings)

    assert added_count == 2
    assert temp_vector_service.count() == 2


def test_vector_service_similarity_search(temp_vector_service):
    """Test cosine similarity search returns top-k nearest chunks with metadata and scores."""
    embedder = EmbeddingService()
    chunks = [
        {
            "chunk_id": "chunk-a1",
            "document_id": "doc-finance",
            "source_filename": "quarterly_report.pdf",
            "page_number": 5,
            "chunk_index": 0,
            "text": "Q4 financial revenue grew 25% year-over-year reaching $50 million."
        },
        {
            "chunk_id": "chunk-a2",
            "document_id": "doc-finance",
            "source_filename": "quarterly_report.pdf",
            "page_number": 12,
            "chunk_index": 1,
            "text": "Operational costs were reduced by automating cloud infrastructure."
        }
    ]

    embeddings = embedder.embed_documents([c["text"] for c in chunks])
    temp_vector_service.add_chunks(chunks, embeddings)

    query_vec = embedder.embed_query("What was the Q4 revenue growth?")
    matches = temp_vector_service.similarity_search(query_vec, top_k=1)

    assert len(matches) == 1
    top_match = matches[0]

    assert top_match["chunk_id"] == "chunk-a1"
    assert top_match["document_id"] == "doc-finance"
    assert top_match["source_filename"] == "quarterly_report.pdf"
    assert top_match["page_number"] == 5
    assert top_match["chunk_index"] == 0
    assert "revenue grew 25%" in top_match["text"]
    assert "score" in top_match
    assert top_match["score"] > 0.5


def test_vector_service_document_filtering(temp_vector_service):
    """Test similarity search filters results strictly by document_id when provided."""
    embedder = EmbeddingService()
    chunks_doc_a = [
        {
            "chunk_id": "chunk-docA-1",
            "document_id": "doc-A",
            "source_filename": "document_A.pdf",
            "page_number": 1,
            "chunk_index": 0,
            "text": "Document A explains machine learning model training techniques."
        }
    ]
    chunks_doc_b = [
        {
            "chunk_id": "chunk-docB-1",
            "document_id": "doc-B",
            "source_filename": "document_B.pdf",
            "page_number": 1,
            "chunk_index": 0,
            "text": "Document B details machine learning deployment in production."
        }
    ]

    embed_a = embedder.embed_documents([c["text"] for c in chunks_doc_a])
    embed_b = embedder.embed_documents([c["text"] for c in chunks_doc_b])

    temp_vector_service.add_chunks(chunks_doc_a, embed_a)
    temp_vector_service.add_chunks(chunks_doc_b, embed_b)

    query_vec = embedder.embed_query("machine learning")

    # Filter for doc-A only
    matches_a = temp_vector_service.similarity_search(query_vec, top_k=5, document_id="doc-A")
    assert len(matches_a) == 1
    assert matches_a[0]["document_id"] == "doc-A"
    assert matches_a[0]["chunk_id"] == "chunk-docA-1"

    # Filter for doc-B only
    matches_b = temp_vector_service.similarity_search(query_vec, top_k=5, document_id="doc-B")
    assert len(matches_b) == 1
    assert matches_b[0]["document_id"] == "doc-B"
    assert matches_b[0]["chunk_id"] == "chunk-docB-1"


def test_vector_service_delete_document(temp_vector_service):
    """Test deleting document purges only matching document vectors."""
    embedder = EmbeddingService()
    chunks = [
        {
            "chunk_id": "del-1",
            "document_id": "doc-to-delete",
            "source_filename": "purge.pdf",
            "page_number": 1,
            "chunk_index": 0,
            "text": "This content will be purged."
        },
        {
            "chunk_id": "keep-1",
            "document_id": "doc-to-keep",
            "source_filename": "keep.pdf",
            "page_number": 1,
            "chunk_index": 0,
            "text": "This content must remain in the index."
        }
    ]

    embeddings = embedder.embed_documents([c["text"] for c in chunks])
    temp_vector_service.add_chunks(chunks, embeddings)
    assert temp_vector_service.count() == 2

    # Delete doc-to-delete
    purged_count = temp_vector_service.delete_document("doc-to-delete")
    assert purged_count == 1
    assert temp_vector_service.count() == 1

    # Verify only doc-to-keep remains
    query_vec = embedder.embed_query("content")
    matches = temp_vector_service.similarity_search(query_vec, top_k=10)
    assert len(matches) == 1
    assert matches[0]["document_id"] == "doc-to-keep"


def test_vector_service_clear(temp_vector_service):
    """Test clear() removes all vectors from collection."""
    embedder = EmbeddingService()
    chunks = [
        {"chunk_id": "c1", "document_id": "d1", "source_filename": "f.pdf", "page_number": 1, "chunk_index": 0, "text": "Sample text."}
    ]
    embeddings = embedder.embed_documents([c["text"] for c in chunks])
    temp_vector_service.add_chunks(chunks, embeddings)

    assert temp_vector_service.count() == 1
    temp_vector_service.clear()
    assert temp_vector_service.count() == 0


def test_vector_service_invalid_inputs(temp_vector_service):
    """Test VectorService handles input validation errors correctly."""
    # Length mismatch
    with pytest.raises(ValueError) as exc1:
        temp_vector_service.add_chunks(
            chunks=[{"chunk_id": "1", "document_id": "d", "source_filename": "f", "page_number": 1, "chunk_index": 0, "text": "a"}],
            embeddings=[]
        )
    assert "Mismatch between chunks count" in str(exc1.value)

    # Empty query embedding
    with pytest.raises(ValueError) as exc2:
        temp_vector_service.similarity_search(query_embedding=[])
    assert "query_embedding cannot be empty" in str(exc2.value)
