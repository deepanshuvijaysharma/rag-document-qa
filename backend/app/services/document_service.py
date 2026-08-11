"""Document Management Service Orchestrating Ingestion, Chunking, Embedding, and Storage."""

import uuid
import logging
from typing import Dict, Any, Optional
from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService

logger = logging.getLogger("rag_app.document_service")


class DocumentService:
    """Service orchestrating PDF upload, text parsing, semantic chunking, vector embedding, and ChromaDB indexing."""

    def __init__(
        self,
        pdf_service: Optional[PDFService] = None,
        chunking_service: Optional[ChunkingService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        vector_service: Optional[VectorService] = None
    ) -> None:
        """Initialize DocumentService with dependency injection."""
        self.pdf_service = pdf_service or PDFService()
        self.chunking_service = chunking_service or ChunkingService()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_service = vector_service or VectorService()

    async def process_pdf_upload(
        self, raw_filename: str, content: bytes, content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate uploaded PDF, extract page text, chunk, embed, and index in ChromaDB.
        
        Returns dictionary matching DocumentUploadResponse schema:
        {
            "document_id": "...",
            "filename": "...",
            "file_size": 12345,
            "page_count": 5,
            "chunk_count": 8,
            "status": "processed",
            "pages": [{"page_number": 1, "text": "..."}, ...],
            "chunks": [{"chunk_id": "...", "page_number": 1, "chunk_index": 0, "text": "..."}, ...]
        }
        """
        # 1. Validate file extension, size, MIME type, and magic headers
        sanitized_filename = self.pdf_service.validate_pdf_file(
            filename=raw_filename,
            content=content,
            content_type=content_type
        )

        # 2. Extract page-indexed text via PyMuPDF
        pages = self.pdf_service.extract_pages(content, filename=sanitized_filename)

        # 3. Generate unique document ID
        doc_id = str(uuid.uuid4())

        # 4. Split extracted pages into semantic text chunks
        chunks = self.chunking_service.split_pages_into_chunks(
            pages=pages,
            doc_id=doc_id,
            filename=sanitized_filename
        )

        # 5. Generate vector embeddings for generated chunks
        chunk_texts = [c["text"] for c in chunks]
        embeddings = self.embedding_service.embed_documents(chunk_texts)

        # 6. Index chunks and vector embeddings into ChromaDB vector store
        self.vector_service.add_chunks(chunks=chunks, embeddings=embeddings)

        logger.info(
            f"Successfully processed and indexed PDF upload '{sanitized_filename}' "
            f"(ID: {doc_id}, Pages: {len(pages)}, Chunks: {len(chunks)}, Indexed Vectors: {len(embeddings)})"
        )

        return {
            "document_id": doc_id,
            "filename": sanitized_filename,
            "file_size": len(content),
            "page_count": len(pages),
            "chunk_count": len(chunks),
            "status": "processed",
            "pages": pages,
            "chunks": chunks
        }

    def delete_document(self, document_id: str) -> int:
        """Purge document vector embeddings and metadata from vector database index."""
        return self.vector_service.delete_document(document_id)
