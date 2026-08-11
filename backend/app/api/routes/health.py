"""Health Check API Endpoints."""

from typing import Dict

try:
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/health", response_model=Dict[str, str], summary="System Health Status")
    async def get_health() -> Dict[str, str]:
        """Health check endpoint to verify backend operational status."""
        return {"status": "ok"}
except ImportError:
    router = None  # type: ignore
