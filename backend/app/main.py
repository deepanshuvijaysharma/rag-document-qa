"""FastAPI Application Main Entrypoint."""

import os
import sys
import ctypes

# Windows DLL directory fix for PyTorch dynamic libraries
if sys.platform == "win32":
    try:
        torch_lib = os.path.join(sys.prefix, "Lib", "site-packages", "torch", "lib")
        if os.path.exists(torch_lib):
            os.add_dll_directory(torch_lib)
            for dll_name in ["libiomp5md.dll", "c10.dll", "torch_cpu.dll", "torch.dll"]:
                dll_path = os.path.join(torch_lib, dll_name)
                if os.path.exists(dll_path):
                    try:
                        ctypes.CDLL(dll_path)
                    except Exception:
                        pass
    except Exception:
        pass

try:
    import torch  # Pre-import PyTorch runtime cleanly before transformers
except Exception:
    pass

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import api_router
from app.core.exceptions import AppBaseException

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rag_app")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
)

# CORS Middleware Setup
allowed_origins = set(settings.CORS_ORIGINS)
if settings.FRONTEND_ORIGIN:
    allowed_origins.add(settings.FRONTEND_ORIGIN)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(AppBaseException)
async def custom_app_exception_handler(request: Request, exc: AppBaseException):
    """Global exception handler for application domain exceptions."""
    logger.warning(f"Domain exception on '{request.url.path}': {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    """Global exception handler to prevent internal tracebacks or secrets leakage."""
    logger.error(f"Unhandled exception on '{request.url.path}': {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing your request."}
    )


# Include API Router under /api/v1 and alias /api
app.include_router(api_router, prefix=settings.API_PREFIX)
app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["Health"])
async def root_health():
    """Root level health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
