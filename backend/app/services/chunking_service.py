"""Text Chunking Service Interface."""

from typing import List, Dict, Any


class ChunkingService:
    """Service handling text normalization and recursive character splitting."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        """Initialize ChunkingService with configurable boundaries."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_pages_into_chunks(self, pages: List[Dict[str, Any]], doc_id: str, filename: str) -> List[Dict[str, Any]]:
        """Split text into semantic chunks while maintaining metadata and page numbers.
        
        To be implemented in Phase 2 using LangChain RecursiveCharacterTextSplitter.
        """
        raise NotImplementedError("Text chunking will be implemented in Phase 2.")
