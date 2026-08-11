"""Unit Tests for Vector Embedding Service."""

import pytest
from app.services.embedding_service import EmbeddingService
from app.config import settings


def test_embedding_service_initialization_defaults():
    """Test EmbeddingService initializes using settings.EMBEDDING_MODEL by default."""
    service = EmbeddingService()
    assert service.model_name == settings.EMBEDDING_MODEL
    assert service.dimension == 384


def test_embedding_service_model_caching():
    """Test EmbeddingService reuses cached SentenceTransformer instance across objects."""
    service1 = EmbeddingService()
    service2 = EmbeddingService()
    
    model1 = service1._get_model()
    model2 = service2._get_model()
    
    # Assert exact object identity in cache memory
    assert model1 is model2


def test_single_query_embedding():
    """Test embed_query returns a 384-dimensional list of floats."""
    service = EmbeddingService()
    query = "What is Retrieval-Augmented Generation?"
    
    vector = service.embed_query(query)
    
    assert isinstance(vector, list)
    assert len(vector) == 384
    assert all(isinstance(val, float) for val in vector)


def test_embedding_dimension_consistency():
    """Test same text produces consistent vector dimensions and reproducible values."""
    service = EmbeddingService()
    text = "Dense vector embeddings represent text semantics."
    
    v1 = service.embed_query(text)
    v2 = service.embed_query(text)
    
    assert len(v1) == 384
    assert len(v2) == 384
    # Identical input must yield identical floating point values
    assert pytest.approx(v1, rel=1e-5) == v2


def test_batch_document_embedding():
    """Test embed_documents processes multiple document chunks in batches."""
    service = EmbeddingService()
    chunks = [
        "First document chunk text describing PDF ingestion.",
        "Second chunk text covering recursive character text splitting.",
        "Third chunk detailing vector storage in ChromaDB."
    ]
    
    vectors = service.embed_documents(chunks)
    
    assert isinstance(vectors, list)
    assert len(vectors) == 3
    for vec in vectors:
        assert isinstance(vec, list)
        assert len(vec) == 384
        assert all(isinstance(val, float) for val in vec)


def test_batch_document_empty_list():
    """Test embed_documents returns empty list when given empty input list."""
    service = EmbeddingService()
    vectors = service.embed_documents([])
    assert vectors == []


def test_query_empty_text_rejection():
    """Test embed_query raises ValueError for empty or whitespace-only text."""
    service = EmbeddingService()
    
    with pytest.raises(ValueError) as exc1:
        service.embed_query("")
    assert "cannot be empty" in str(exc1.value)

    with pytest.raises(ValueError) as exc2:
        service.embed_query("   \n\t  ")
    assert "cannot be empty" in str(exc2.value)


def test_batch_empty_text_rejection():
    """Test embed_documents raises ValueError if any chunk in batch is empty."""
    service = EmbeddingService()
    chunks = ["Valid chunk text.", "   ", "Another valid chunk."]
    
    with pytest.raises(ValueError) as exc:
        service.embed_documents(chunks)
    assert "cannot be empty or whitespace-only" in str(exc.value)
