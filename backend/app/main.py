"""Main entry point for the Smart PDF Assistant FastAPI backend.

Configures the FastAPI application, registers middleware (CORS),
includes API routers, and defines root and health check endpoints.
"""

import logging
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Import configuration and logging utility
from backend.app.config import settings
from backend.app.utils import logger as app_logger  # Auto-configures logging on import

# Import routers
from backend.app.routers import chat, documents, upload

# Set up module-level logger
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Smart PDF Assistant API",
    description=(
        "Production-ready API backend for the Smart PDF Assistant, "
        "providing PDF ingestion, vector search, and RAG-based chat."
    ),
    version="1.0.0",
)

# Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Safely extract routers from modules, or fall back to default APIRouters 
# to prevent import/attribute errors on empty placeholder modules.
upload_router = getattr(upload, "router", None)
if upload_router is None:
    logger.warning("Router object not found in upload.py module. Initializing fallback APIRouter.")
    upload_router = APIRouter(prefix="/api/v1/upload", tags=["Upload"])

chat_router = getattr(chat, "router", None)
if chat_router is None:
    logger.warning("Router object not found in chat.py module. Initializing fallback APIRouter.")
    chat_router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

documents_router = getattr(documents, "router", None)
if documents_router is None:
    logger.warning("Router object not found in documents.py module. Initializing fallback APIRouter.")
    documents_router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

# Include the routers into the app
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(documents_router)


@app.get("/", tags=["General"])
async def read_root() -> dict:
    """Root endpoint returning API service information."""
    return {
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "status": "running",
    }


@app.get("/health", tags=["General"])
async def health_check() -> dict:
    """Health check endpoint to verify api availability."""
    return {
        "status": "healthy",
        "log_level": settings.LOG_LEVEL,
    }
