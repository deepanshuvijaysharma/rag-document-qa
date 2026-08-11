"""Application Configuration Management."""

import os
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    
    class Settings(BaseSettings):
        """Application settings loaded from environment variables."""
        
        PROJECT_NAME: str = "RAG Document Q&A"
        VERSION: str = "0.1.0"
        API_V1_STR: str = "/api/v1"
        
        # CORS Security Configuration
        # In production, set CORS_ORIGINS to specific trusted domains via environment variables.
        CORS_ORIGINS: List[str] = [
            "http://localhost:5173",  # Default Vite Dev Server
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ]
        
        # Vector Store Configuration
        CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
        CHROMA_COLLECTION_NAME: str = "rag_documents"
        
        # Embedding Model Configuration
        EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
        
        # Chunking Configuration
        CHUNK_SIZE: int = 1000
        CHUNK_OVERLAP: int = 200
        
        # LLM Provider Settings
        LLM_PROVIDER: str = "openai"  # Options: openai, ollama, groq, anthropic
        OPENAI_API_KEY: Optional[str] = None
        GROQ_API_KEY: Optional[str] = None
        ANTHROPIC_API_KEY: Optional[str] = None
        OLLAMA_BASE_URL: str = "http://localhost:11434"
        DEFAULT_MODEL_NAME: str = "gpt-4o-mini"
        
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
            case_sensitive=True,
        )

except ImportError:
    # Fallback definition when pydantic_settings package is not installed yet
    class Settings:  # type: ignore
        """Fallback settings class prior to dependency installation."""
        
        PROJECT_NAME: str = "RAG Document Q&A"
        VERSION: str = "0.1.0"
        API_V1_STR: str = "/api/v1"
        CORS_ORIGINS: List[str] = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ]
        CHROMA_PERSIST_DIR: str = "./data/chroma"
        CHROMA_COLLECTION_NAME: str = "rag_documents"
        EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
        CHUNK_SIZE: int = 1000
        CHUNK_OVERLAP: int = 200
        LLM_PROVIDER: str = "openai"
        OPENAI_API_KEY: Optional[str] = None
        GROQ_API_KEY: Optional[str] = None
        ANTHROPIC_API_KEY: Optional[str] = None
        OLLAMA_BASE_URL: str = "http://localhost:11434"
        DEFAULT_MODEL_NAME: str = "gpt-4o-mini"


settings = Settings()
