"""
FastAPI Server - Browser Isolation API

Main API server for the Browser Isolation system.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.models import ErrorResponse
from api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/api.log")],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    logger.info("Browser Isolation API starting up...")

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    yield

    logger.info("Browser Isolation API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Browser Isolation API",
    description="Zero-Trust Remote DOM Renderer for Malware-Resistant Web Browsing",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Browser Isolation API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "render": "POST /api/v1/render",
            "check_url": "POST /api/v1/check-url",
            "audit": "GET /api/v1/audit",
            "policies": "GET /api/v1/policies",
            "health": "GET /api/v1/health",
        },
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}")
    error = ErrorResponse(error="Validation Error", detail=str(exc))
    return JSONResponse(status_code=422, content=jsonable_encoder(error))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    error = ErrorResponse(error="Internal Server Error", detail="An unexpected error occurred")
    return JSONResponse(status_code=500, content=jsonable_encoder(error))


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Start the API server.

    Args:
        host: Host to bind to
        port: Port to listen on
        reload: Enable auto-reload for development
    """
    logger.info(f"Starting Browser Isolation API on {host}:{port}")

    uvicorn.run("api.server:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    start_server(reload=True)
