"""FastAPI Application Main Entrypoint."""

import logging
from app.config import settings

# Configure basic logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rag_app")

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from app.api.routes import api_router

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )

    # CORS Security Configuration
    # Whitelists configured origins (e.g. Vite frontend on port 5173).
    # In production, restrict CORS_ORIGINS to trusted deployment domains.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Include aggregated API v1 routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/health", tags=["Health"])
    async def root_health():
        """Root level health check endpoint."""
        return {"status": "ok"}

except ImportError:
    logger.warning("FastAPI framework not installed yet. Skeleton modules defined.")
    app = None  # type: ignore


if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("Uvicorn not installed. Please install dependencies in requirements.txt")
