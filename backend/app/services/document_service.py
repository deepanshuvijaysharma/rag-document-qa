"""Document Management Service Orchestrating Ingestion, Chunking, Embedding, and Storage."""

import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.db.metadata_store import MetadataStore
from app.core.exceptions import DocumentNotFoundError, VectorStoreError

logger = logging.getLogger("rag_app.document_service")


class DocumentService:
    """Service orchestrating PDF upload, text parsing, semantic chunking, vector embedding, and ChromaDB indexing."""

    def __init__(
        self,
        pdf_service: Optional[PDFService] = None,
        chunking_service: Optional[ChunkingService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        vector_service: Optional[VectorService] = None,
        metadata_store: Optional[MetadataStore] = None
    ) -> None:
        """Initialize DocumentService with dependency injection."""
        self.pdf_service = pdf_service or PDFService()
        self.chunking_service = chunking_service or ChunkingService()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_service = vector_service or VectorService()
        self.metadata_store = metadata_store or MetadataStore()

    async def process_pdf_upload(
        self, raw_filename: str, content: bytes, content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate uploaded PDF, extract page text, chunk, embed, index in ChromaDB, and save metadata.
        
        Enforces atomic ingestion rollback safety: if vector storage fails, partial vectors are purged.
        Preventing duplicate ingestion: if identical file was previously ingested, existing vectors & metadata are cleaned.
        
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
        file_size = len(content)

        # 2. Check for duplicate ingestion by filename and file size
        existing_doc = self.metadata_store.find_by_filename_and_size(sanitized_filename, file_size)
        if existing_doc:
            logger.info(f"Duplicate document upload detected for '{sanitized_filename}'. Purging prior vector records.")
            self.delete_document(existing_doc["id"])

        # 3. Extract page-indexed text via PyMuPDF
        pages = self.pdf_service.extract_pages(content, filename=sanitized_filename)

        # 4. Generate unique document ID
        doc_id = str(uuid.uuid4())

        # 5. Split extracted pages into semantic text chunks
        chunks = self.chunking_service.split_pages_into_chunks(
            pages=pages,
            doc_id=doc_id,
            filename=sanitized_filename
        )

        # 6. Generate vector embeddings & index into ChromaDB with atomic rollback safety
        try:
            chunk_texts = [c["text"] for c in chunks]
            embeddings = self.embedding_service.embed_documents(chunk_texts)
            self.vector_service.add_chunks(chunks=chunks, embeddings=embeddings)
        except Exception as err:
            logger.error(f"Ingestion failed for '{sanitized_filename}' (ID: {doc_id}). Executing rollback: {err}")
            # Rollback: delete any partial vectors in ChromaDB
            try:
                self.vector_service.delete_document(doc_id)
            except Exception as rollback_err:
                logger.error(f"Rollback cleanup failed for '{doc_id}': {rollback_err}")
            raise err

        # 7. Persist document metadata in MetadataStore
        now_iso = datetime.utcnow().isoformat()
        doc_record = {
            "id": doc_id,
            "document_id": doc_id,
            "filename": sanitized_filename,
            "file_size": file_size,
            "page_count": len(pages),
            "chunk_count": len(chunks),
            "upload_timestamp": now_iso,
            "status": "processed",
            "pages": pages,
            "chunks": chunks
        }
        self.metadata_store.save_document(doc_record)

        logger.info(
            f"Successfully ingested and indexed PDF upload '{sanitized_filename}' "
            f"(ID: {doc_id}, Pages: {len(pages)}, Chunks: {len(chunks)}, Vectors Indexed: {len(embeddings)})"
        )

        return doc_record

    def list_documents(self) -> List[Dict[str, Any]]:
        """Retrieve summary list of all ingested active documents."""
        return self.metadata_store.list_documents()

    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Retrieve full document details including pages and chunks by document_id."""
        doc = self.metadata_store.get_document(document_id)
        if not doc:
            raise DocumentNotFoundError(f"Document with ID '{document_id}' was not found.")
        return doc

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Purge document metadata and all associated vector embeddings from ChromaDB.
        
        Returns:
            Dict summary: {"document_id": "...", "filename": "...", "vectors_purged": N}
        """
        doc = self.metadata_store.get_document(document_id)
        if not doc:
            raise DocumentNotFoundError(f"Document with ID '{document_id}' was not found.")

        filename = doc["filename"]

        # 1. Purge vectors from ChromaDB
        vectors_purged = self.vector_service.delete_document(document_id)

        # 2. Delete metadata record
        self.metadata_store.delete_document(document_id)

        logger.info(f"Successfully deleted document '{filename}' (ID: {document_id}). Purged {vectors_purged} vector chunks.")

        return {
            "document_id": document_id,
            "filename": filename,
            "status": "deleted",
            "vectors_purged": vectors_purged
        }
