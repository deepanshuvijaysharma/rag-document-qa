"""Lightweight Persistent Document Metadata Store.

Stores document ingestion metadata in a thread-safe JSON file store, decoupled from ChromaDB vector indexes.
"""

import os
import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("rag_app.metadata_store")

# Default metadata storage file path
DEFAULT_METADATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "documents.json"
)


class MetadataStore:
    """Thread-safe persistent JSON metadata store for document lifecycle management."""

    _lock = threading.Lock()

    def __init__(self, file_path: Optional[str] = None) -> None:
        """Initialize MetadataStore with file persistence path.
        
        Args:
            file_path: Optional custom JSON file path for storage.
        """
        self.file_path = file_path or DEFAULT_METADATA_FILE
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create empty JSON object file if it does not exist."""
        if not os.path.exists(self.file_path):
            with self._lock:
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=2)

    def _read_data(self) -> Dict[str, Dict[str, Any]]:
        """Read metadata JSON file safely."""
        with self._lock:
            try:
                if not os.path.exists(self.file_path):
                    return {}
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as err:
                logger.error(f"Error reading metadata store '{self.file_path}': {err}")
                return {}

    def _write_data(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Write metadata JSON file atomically using a temporary file."""
        with self._lock:
            temp_path = f"{self.file_path}.tmp"
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                os.replace(temp_path, self.file_path)
            except Exception as err:
                logger.error(f"Error writing metadata store '{self.file_path}': {err}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

    def save_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update document metadata record."""
        doc_id = doc_data.get("document_id") or doc_data.get("id")
        if not doc_id:
            raise ValueError("Document metadata record must contain 'document_id' or 'id'.")

        data = self._read_data()
        
        # Format record
        now_iso = datetime.utcnow().isoformat()
        record = {
            "id": doc_id,
            "document_id": doc_id,
            "filename": doc_data["filename"],
            "file_size": doc_data.get("file_size", 0),
            "page_count": doc_data.get("page_count", 0),
            "chunk_count": doc_data.get("chunk_count", 0),
            "upload_timestamp": doc_data.get("upload_timestamp", now_iso),
            "status": doc_data.get("status", "processed"),
            "pages": doc_data.get("pages", []),
            "chunks": doc_data.get("chunks", [])
        }

        data[doc_id] = record
        self._write_data(data)
        logger.info(f"Saved document metadata for '{doc_data['filename']}' (ID: {doc_id}) to metadata store.")
        return record

    def list_documents(self) -> List[Dict[str, Any]]:
        """List summary metadata for all active documents, ordered by timestamp descending."""
        data = self._read_data()
        documents = []
        for record in data.values():
            documents.append({
                "id": record["id"],
                "filename": record["filename"],
                "file_size": record.get("file_size", 0),
                "page_count": record.get("page_count", 0),
                "chunk_count": record.get("chunk_count", 0),
                "upload_timestamp": record.get("upload_timestamp"),
                "status": record.get("status", "processed")
            })

        # Sort newest first
        documents.sort(key=lambda x: str(x.get("upload_timestamp", "")), reverse=True)
        return documents

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve complete document metadata record including pages and chunks."""
        data = self._read_data()
        return data.get(doc_id)

    def find_by_filename_and_size(self, filename: str, file_size: int) -> Optional[Dict[str, Any]]:
        """Check if a document with identical filename and file size was previously ingested."""
        data = self._read_data()
        for record in data.values():
            if record.get("filename") == filename and record.get("file_size") == file_size:
                return record
        return None

    def delete_document(self, doc_id: str) -> bool:
        """Delete document record from metadata store."""
        data = self._read_data()
        if doc_id in data:
            del data[doc_id]
            self._write_data(data)
            logger.info(f"Deleted document '{doc_id}' from metadata store.")
            return True
        return False

    def clear(self) -> None:
        """Clear all stored metadata records (primarily for tests/reset)."""
        self._write_data({})
