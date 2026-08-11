"""API Routes Package Aggregator."""

try:
    from fastapi import APIRouter
    from app.api.routes import health, documents, retrieval, chat

    api_router = APIRouter()
    api_router.include_router(health.router, tags=["Health"])
    api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
    api_router.include_router(retrieval.router, prefix="/retrieval", tags=["Retrieval"])
    api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
except ImportError:
    api_router = None  # type: ignore
