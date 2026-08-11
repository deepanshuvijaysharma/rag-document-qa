"""Dedicated Vector Embedding Service using Sentence Transformers."""

import os
import sys
import ctypes
import logging
from typing import List, Dict, Optional

# Windows DLL directory fix for PyTorch dynamic libraries
if sys.platform == "win32":
    try:
        torch_lib = os.path.join(sys.prefix, "Lib", "site-packages", "torch", "lib")
        if os.path.exists(torch_lib):
            os.add_dll_directory(torch_lib)
            iomp = os.path.join(torch_lib, "libiomp5md.dll")
            if os.path.exists(iomp):
                try:
                    ctypes.CDLL(iomp)
                except Exception:
                    pass
    except Exception:
        pass

from sentence_transformers import SentenceTransformer

from app.config import settings
from app.core.exceptions import EmbeddingError

logger = logging.getLogger("rag_app.embedding_service")


class EmbeddingService:
    """Service handling text embedding generation using Sentence Transformers.
    
    Uses singleton model instance caching to prevent redundant model reloads.
    """

    # Class-level model cache to reuse loaded SentenceTransformer instances
    _model_cache: Dict[str, SentenceTransformer] = {}

    def __init__(self, model_name: Optional[str] = None) -> None:
        """Initialize EmbeddingService with configurable model name.
        
        Args:
            model_name: Optional embedding model name. Defaults to settings.EMBEDDING_MODEL.
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL

    def _get_model(self) -> SentenceTransformer:
        """Retrieve cached SentenceTransformer instance or initialize new instance lazily."""
        if self.model_name not in self._model_cache:
            logger.info(f"Loading SentenceTransformer model '{self.model_name}' into memory...")
            try:
                model_instance = SentenceTransformer(self.model_name)
                self._model_cache[self.model_name] = model_instance
                logger.info(f"Successfully loaded and cached model '{self.model_name}'.")
            except Exception as err:
                logger.error(f"Failed to load SentenceTransformer model '{self.model_name}': {err}")
                raise EmbeddingError(f"Unable to initialize embedding model '{self.model_name}': {err}")

        return self._model_cache[self.model_name]

    @property
    def dimension(self) -> int:
        """Return the vector embedding dimension produced by the current model (e.g., 384)."""
        model = self._get_model()
        dim = model.get_sentence_embedding_dimension()
        return int(dim) if dim is not None else 384

    def embed_query(self, text: str) -> List[float]:
        """Generate dense vector embedding for a single user search query or question."""
        if not text or not text.strip():
            logger.warning("Query embedding rejected: text is empty or whitespace-only.")
            raise ValueError("Query text for embedding cannot be empty or whitespace-only.")

        clean_text = text.strip()
        model = self._get_model()

        try:
            embedding = model.encode(clean_text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as err:
            logger.error(f"Error generating query vector for model '{self.model_name}': {err}")
            raise EmbeddingError(f"Error computing query vector embedding: {err}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings in batches for a list of document chunks."""
        if not texts:
            return []

        cleaned_texts: List[str] = []
        for idx, t in enumerate(texts):
            if not t or not t.strip():
                logger.warning(f"Batch document embedding rejected: item at index {idx} is empty.")
                raise ValueError(f"Document text at index {idx} cannot be empty or whitespace-only.")
            cleaned_texts.append(t.strip())

        model = self._get_model()

        try:
            embeddings = model.encode(cleaned_texts, batch_size=32, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as err:
            logger.error(f"Error generating batch document vectors for model '{self.model_name}': {err}")
            raise EmbeddingError(f"Error computing batch document vector embeddings: {err}")
