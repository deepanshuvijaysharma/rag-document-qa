"""Application Configuration Management using Pydantic Settings."""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application Settings
    APP_ENV: str = "development"
    APP_NAME: str = "RAG Document Q&A"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"

    # CORS Security Configuration
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # File Ingestion & Security Thresholds
    MAX_UPLOAD_SIZE_MB: int = 25
    MAX_DOCUMENT_PAGES: int = 500

    # Retrieval & Context Boundaries
    TOP_K: int = 4
    MAX_CONTEXT_CHUNKS: int = 10

    # Vector Store Configuration
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    CHROMA_COLLECTION_NAME: str = "rag_documents"

    # Embedding & Chunking Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # LLM Provider Configuration
    LLM_PROVIDER: str = "openai"  # Options: openai, ollama, groq, anthropic
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
