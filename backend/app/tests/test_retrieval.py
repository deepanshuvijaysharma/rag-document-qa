"""Unit and API Integration Tests for Vector Retrieval Layer."""

import os
import shutil
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock

from app.main import app
from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.document_service import DocumentService
from app.services.retrieval_service import RetrievalService
from app.db.metadata_store import MetadataStore
from app.core.exceptions import VectorStoreError

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))


@pytest.fixture
def temp_retrieval_environment():
    """Fixture providing isolated temporary storage and ingestion services for retrieval tests."""
    temp_dir = tempfile.mkdtemp(prefix="rag_retrieval_test_")
    chroma_dir = os.path.join(temp_dir, "chroma")
    meta_file = os.path.join(temp_dir, "documents.json")

    pdf_service = PDFService()
    chunking_service = ChunkingService(chunk_size=1000, chunk_overlap=200)
    embedding_service = EmbeddingService()
    vector_service = VectorService(persist_directory=chroma_dir, collection_name="retrieval_test_col")
    metadata_store = MetadataStore(file_path=meta_file)

    doc_service = DocumentService(
        pdf_service=pdf_service,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
        vector_service=vector_service,
        metadata_store=metadata_store
    )

    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        vector_service=vector_service
    )

    app.dependency_overrides = {}
    from app.api.routes.documents import get_document_service
    from app.api.routes.retrieval import get_retrieval_service

    app.dependency_overrides[get_document_service] = lambda: doc_service
    app.dependency_overrides[get_retrieval_service] = lambda: retrieval_service

    yield {
        "doc_service": doc_service,
        "retrieval_service": retrieval_service,
        "vector_service": vector_service,
        "temp_dir": temp_dir
    }

    app.dependency_overrides.clear()
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_retrieval_relevant_query_employee_handbook(temp_retrieval_environment):
    """Test searching for annual leave policy in sample employee handbook PDF."""
    handbook_path = os.path.join(ROOT_DIR, "documents", "sample_employee_handbook.pdf")
    with open(handbook_path, "rb") as f:
        pdf_bytes = f.read()

    doc_service = temp_retrieval_environment["doc_service"]
    doc_record = await doc_service.process_pdf_upload("sample_employee_handbook.pdf", pdf_bytes, "application/pdf")
    doc_id = doc_record["document_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/retrieval/search",
            json={"query": "What is the annual leave policy?", "top_k": 2}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["query"] == "What is the annual leave policy?"
        assert data["total_results"] >= 1
        top_result = data["results"][0]

        assert top_result["document_id"] == doc_id
        assert top_result["filename"] == "sample_employee_handbook.pdf"
        assert top_result["page_number"] == 1
        assert "20 days of paid annual leave" in top_result["text"]
        assert top_result["score"] > 0.5


@pytest.mark.asyncio
async def test_retrieval_top_k_parameter(temp_retrieval_environment):
    """Test top_k parameter restricts the maximum number of returned results."""
    handbook_path = os.path.join(ROOT_DIR, "documents", "sample_employee_handbook.pdf")
    with open(handbook_path, "rb") as f:
        pdf_bytes = f.read()

    doc_service = temp_retrieval_environment["doc_service"]
    await doc_service.process_pdf_upload("sample_employee_handbook.pdf", pdf_bytes, "application/pdf")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp_1 = await client.post("/api/v1/retrieval/search", json={"query": "policy rules", "top_k": 1})
        assert resp_1.status_code == 200
        assert len(resp_1.json()["results"]) == 1

        resp_2 = await client.post("/api/v1/retrieval/search", json={"query": "policy rules", "top_k": 2})
        assert resp_2.status_code == 200
        assert len(resp_2.json()["results"]) == 2


@pytest.mark.asyncio
async def test_retrieval_document_filtering(temp_retrieval_environment):
    """Test scoping retrieval query by document_id filters out other documents."""
    doc_service = temp_retrieval_environment["doc_service"]

    # Ingest handbook PDF
    handbook_path = os.path.join(ROOT_DIR, "documents", "sample_employee_handbook.pdf")
    with open(handbook_path, "rb") as f:
        hb_bytes = f.read()
    rec_hb = await doc_service.process_pdf_upload("handbook.pdf", hb_bytes, "application/pdf")

    # Ingest architecture PDF
    arch_path = os.path.join(ROOT_DIR, "documents", "sample_architecture.pdf")
    with open(arch_path, "rb") as f:
        arch_bytes = f.read()
    rec_arch = await doc_service.process_pdf_upload("architecture.pdf", arch_bytes, "application/pdf")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Search scoped to handbook
        resp_hb = await client.post(
            "/api/retrieval/search",
            json={"query": "working hours", "document_id": rec_hb["document_id"], "top_k": 5}
        )
        assert resp_hb.status_code == 200
        for item in resp_hb.json()["results"]:
            assert item["document_id"] == rec_hb["document_id"]
            assert item["filename"] == "handbook.pdf"

        # Search scoped to architecture
        resp_arch = await client.post(
            "/api/retrieval/search",
            json={"query": "working hours", "document_id": rec_arch["document_id"], "top_k": 5}
        )
        assert resp_arch.status_code == 200
        for item in resp_arch.json()["results"]:
            assert item["document_id"] == rec_arch["document_id"]
            assert item["filename"] == "architecture.pdf"


@pytest.mark.asyncio
async def test_retrieval_no_results_and_nonexistent_filter(temp_retrieval_environment):
    """Test retrieval against empty vector store or non-existent document ID returns empty results list."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Empty vector store
        resp1 = await client.post("/api/v1/retrieval/search", json={"query": "leave policy", "top_k": 4})
        assert resp1.status_code == 200
        assert resp1.json()["total_results"] == 0
        assert resp1.json()["results"] == []

        # Non-existent document ID filter
        resp2 = await client.post(
            "/api/v1/retrieval/search",
            json={"query": "leave policy", "document_id": "non-existent-uuid-1234", "top_k": 4}
        )
        assert resp2.status_code == 200
        assert resp2.json()["total_results"] == 0
        assert resp2.json()["results"] == []


@pytest.mark.asyncio
async def test_retrieval_malformed_query_rejection(temp_retrieval_environment):
    """Test empty or whitespace-only query payloads are rejected with HTTP 400/422 validation error."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Empty string
        resp1 = await client.post("/api/v1/retrieval/search", json={"query": "", "top_k": 4})
        assert resp1.status_code in [400, 422]

        # Whitespace-only string
        resp2 = await client.post("/api/v1/retrieval/search", json={"query": "   \n\t  ", "top_k": 4})
        assert resp2.status_code in [400, 422]


def test_retrieval_service_vector_store_failure():
    """Test RetrievalService catches and handles vector store exceptions cleanly."""
    mock_embed = MagicMock()
    mock_embed.embed_query.return_value = [0.1] * 384

    mock_vec = MagicMock()
    mock_vec.similarity_search.side_effect = Exception("ChromaDB connection timeout")

    service = RetrievalService(embedding_service=mock_embed, vector_service=mock_vec)

    with pytest.raises(VectorStoreError) as exc_info:
        service.search("Test query")
    assert "Error searching vector store" in str(exc_info.value.detail)
