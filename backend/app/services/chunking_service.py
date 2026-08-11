"""Dedicated Document Text Chunking Service."""

import uuid
import logging
from typing import List, Dict, Any, Optional

from app.config import settings

logger = logging.getLogger("rag_app.chunking_service")


class RecursiveCharacterTextSplitter:
    """Pure-Python Recursive Character Text Splitter matching LangChain chunking semantics."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ) -> None:
        """Initialize RecursiveCharacterTextSplitter with strict parameter guardrails."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer greater than 0.")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")
        if chunk_overlap >= chunk_size:
            raise ValueError(f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size}).")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text by separators until pieces fit within chunk_size."""
        final_chunks: List[str] = []
        separator = separators[-1]
        new_separators: List[str] = []

        for i, _s in enumerate(separators):
            if _s == "":
                separator = _s
                break
            if _s in text:
                separator = _s
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator else list(text)
        good_splits: List[str] = []

        for s in splits:
            if len(s) < self.chunk_size:
                good_splits.append(s)
            else:
                if good_splits:
                    merged = self._merge_splits(good_splits, separator)
                    final_chunks.extend(merged)
                    good_splits = []
                if not new_separators:
                    final_chunks.append(s)
                else:
                    other_chunks = self._split_text(s, new_separators)
                    final_chunks.extend(other_chunks)

        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            final_chunks.extend(merged)

        return final_chunks

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        """Merge split pieces together respecting chunk_size and chunk_overlap boundaries."""
        docs: List[str] = []
        current_doc: List[str] = []
        total = 0

        for s in splits:
            len_s = len(s) + (len(separator) if current_doc else 0)
            if total + len_s > self.chunk_size:
                if total > 0:
                    doc = separator.join(current_doc)
                    if doc.strip():
                        docs.append(doc.strip())
                    while total > self.chunk_overlap or (total + len_s > self.chunk_size and total > 0):
                        total -= len(current_doc[0]) + (len(separator) if len(current_doc) > 1 else 0)
                        current_doc.pop(0)
                        if not current_doc:
                            break
            current_doc.append(s)
            total += len_s

        if current_doc:
            doc = separator.join(current_doc)
            if doc.strip():
                docs.append(doc.strip())

        return docs

    def split_text(self, text: str) -> List[str]:
        """Split text into chunks using recursive separator hierarchy."""
        return self._split_text(text, self.separators)


class ChunkingService:
    """Service handling text normalization and page-aware recursive text splitting."""

    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None) -> None:
        """Initialize ChunkingService with configurable boundaries and strict validation."""
        self.chunk_size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP

        # Instantiate RecursiveCharacterTextSplitter with validation
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def split_pages_into_chunks(
        self, pages: List[Dict[str, Any]], doc_id: str, filename: str
    ) -> List[Dict[str, Any]]:
        """Split text into semantic chunks while maintaining metadata and 1-indexed page numbers.
        
        Args:
            pages: List of page dicts [{"page_number": 1, "text": "..."}, ...]
            doc_id: Unique UUID string of parent document
            filename: Source PDF document filename
            
        Returns:
            List of chunk dictionaries:
            [
                {
                    "chunk_id": "...",
                    "document_id": "...",
                    "source_filename": "...",
                    "page_number": 1,
                    "chunk_index": 0,
                    "text": "..."
                },
                ...
            ]
        """
        chunks: List[Dict[str, Any]] = []
        chunk_counter = 0

        for page in pages:
            page_number = page.get("page_number", 1)
            raw_page_text = page.get("text", "")

            if not raw_page_text or not raw_page_text.strip():
                continue

            # Split single page text recursively
            raw_chunks = self.text_splitter.split_text(raw_page_text)

            for raw_chunk in raw_chunks:
                clean_chunk_text = raw_chunk.strip()
                
                # Filter out empty or whitespace-only chunks
                if not clean_chunk_text:
                    continue

                chunk_id = str(uuid.uuid4())
                chunk_record = {
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "source_filename": filename,
                    "page_number": page_number,
                    "chunk_index": chunk_counter,
                    "text": clean_chunk_text
                }

                chunks.append(chunk_record)
                chunk_counter += 1

        logger.info(
            f"Chunked document '{filename}' (ID: {doc_id}): Generated {len(chunks)} chunks "
            f"across {len(pages)} pages using chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}."
        )

        return chunks
