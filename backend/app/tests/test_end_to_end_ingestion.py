"""End-to-End Integration Tests for Full Document Ingestion & Lifecycle Pipeline."""

import os
import shutil
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.document_service import DocumentService
from app.db.metadata_store import MetadataStore
from app.tests.test_pdf_ingestion import create_mock_pdf_bytes

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))


@pytest.fixture
def temp_environment():
    """Fixture providing isolated temporary storage for ChromaDB and metadata store."""
    temp_dir = tempfile.mkdtemp(prefix="rag_e2e_test_")
    chroma_dir = os.path.join(temp_dir, "chroma")
    meta_file = os.path.join(temp_dir, "documents.json")

    pdf_service = PDFService()
    chunking_service = ChunkingService(chunk_size=1000, chunk_overlap=200)
    embedding_service = EmbeddingService()
    vector_service = VectorService(persist_directory=chroma_dir, collection_name="e2e_test_collection")
    metadata_store = MetadataStore(file_path=meta_file)

    doc_service = DocumentService(
        pdf_service=pdf_service,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
        vector_service=vector_service,
        metadata_store=metadata_store
    )

    # Dependency override helper for FastAPI endpoints
    app.dependency_overrides = {}
    from app.api.routes.documents import get_document_service
    app.dependency_overrides[get_document_service] = lambda: doc_service

    yield {
        "doc_service": doc_service,
        "vector_service": vector_service,
        "metadata_store": metadata_store,
        "temp_dir": temp_dir
    }

    app.dependency_overrides.clear()
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_end_to_end_pdf_ingestion_and_lifecycle(temp_environment):
    """Test full document pipeline: Upload -> Extract -> Chunk -> Embed -> Chroma -> List -> Get -> Delete -> Purge."""
    fixture_path = os.path.join(ROOT_DIR, "documents", "sample_architecture.pdf")
    with open(fixture_path, "rb") as f:
        real_pdf_bytes = f.read()

    vector_service = temp_environment["vector_service"]
    metadata_store = temp_environment["metadata_store"]

    assert vector_service.count() == 0

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. POST /api/v1/documents/upload - Real PDF Upload & Indexing
        upload_resp = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_architecture.pdf", real_pdf_bytes, "application/pdf")}
        )
        assert upload_resp.status_code == 200
        upload_data = upload_resp.json()

        doc_id = upload_data["document_id"]
        assert doc_id is not None
        assert upload_data["filename"] == "sample_architecture.pdf"
        assert upload_data["page_count"] == 2
        assert upload_data["chunk_count"] == 2
        assert upload_data["status"] == "processed"
        assert len(upload_data["pages"]) == 2
        assert len(upload_data["chunks"]) == 2

        # Verify ChromaDB vector store now holds 2 vector chunks
        assert vector_service.count() == 2

        # 2. GET /api/v1/documents - List Ingested Documents
        list_resp = await client.get("/api/v1/documents")
        assert list_resp.status_code == 200
        list_data = list_resp.json()

        assert list_data["total_count"] == 1
        assert len(list_data["documents"]) == 1
        doc_item = list_data["documents"][0]
        assert doc_item["id"] == doc_id
        assert doc_item["filename"] == "sample_architecture.pdf"
        assert doc_item["page_count"] == 2
        assert doc_item["chunk_count"] == 2

        # 3. GET /api/v1/documents/{document_id} - Get Document Details
        get_resp = await client.get(f"/api/v1/documents/{doc_id}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()

        assert get_data["document_id"] == doc_id
        assert get_data["filename"] == "sample_architecture.pdf"
        assert len(get_data["pages"]) == 2
        assert len(get_data["chunks"]) == 2

        # Verify vector similarity search finds retrieved chunks
        query_vec = temp_environment["doc_service"].embedding_service.embed_query("source of truth")
        matches = vector_service.similarity_search(query_vec, top_k=2)
        assert len(matches) > 0
        assert matches[0]["document_id"] == doc_id
        assert matches[0]["source_filename"] == "sample_architecture.pdf"

        # 4. DELETE /api/v1/documents/{document_id} - Delete Document & Purge Vectors
        del_resp = await client.delete(f"/api/v1/documents/{doc_id}")
        assert del_resp.status_code == 200
        del_data = del_resp.json()

        assert del_data["document_id"] == doc_id
        assert del_data["status"] == "deleted"
        assert del_data["vectors_purged"] == 2

        # Verify vectors purged from ChromaDB
        assert vector_service.count() == 0

        # Verify document list is now empty
        list_after = await client.get("/api/v1/documents")
        assert list_after.json()["total_count"] == 0

        # Verify GET deleted document returns HTTP 404
        get_after = await client.get(f"/api/v1/documents/{doc_id}")
        assert get_after.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_document_reingestion(temp_environment):
    """Test re-uploading identical file cleans previous vectors and metadata before re-indexing."""
    pdf_bytes = create_mock_pdf_bytes(["Sample text content for duplicate test"])
    vector_service = temp_environment["vector_service"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First upload
        r1 = await client.post("/api/documents/upload", files={"file": ("dup.pdf", pdf_bytes, "application/pdf")})
        assert r1.status_code == 200
        id1 = r1.json()["document_id"]
        assert vector_service.count() == 1

        # Second upload (same filename and size)
        r2 = await client.post("/api/documents/upload", files={"file": ("dup.pdf", pdf_bytes, "application/pdf")})
        assert r2.status_code == 200
        id2 = r2.json()["document_id"]

        # Vector count should still be 1 (old purged, new added)
        assert vector_service.count() == 1
        
        # Document list should contain only 1 active document
        list_resp = await client.get("/api/documents")
        assert list_resp.json()["total_count"] == 1
        assert list_resp.json()["documents"][0]["id"] == id2
