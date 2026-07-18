"""API router for PDF upload and ingestion pipeline.

Saves uploaded PDF files, parses text, splits into chunks, computes vector 
embeddings, and writes records to the persistent database.
"""

import logging
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.config import settings
from backend.app.models.schemas import UploadResponse, ErrorResponse
from backend.app.services.pdf_service import validate_pdf, extract_text
from backend.app.services.chunking_service import chunk_document
from backend.app.services.embedding_service import generate_embeddings
from backend.app.services.vector_store import add_document, delete_document, document_exists, save_document_questions
from backend.app.services.groq_service import generate_suggested_questions
from backend.app.services.storage_service import upload_pdf as upload_pdf_to_storage
import tempfile
import os

# Set up module-level logger
logger = logging.getLogger(__name__)

# Initialize APIRouter
router = APIRouter(prefix="/upload", tags=["Upload"])

# Maximum file size constraint (20 MB limit)
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024


@router.post(
    "/",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file structure or parser failure"},
        413: {"model": ErrorResponse, "description": "Uploaded file exceeds size limits"},
        500: {"model": ErrorResponse, "description": "Pipeline execution error"},
    },
)
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    """Ingests, parses, chunks, embeds, and indexes an uploaded PDF document.

    If a document with the same filename already exists, it is automatically
    removed from the store and local disk to allow a clean overwrite.

    Args:
        file: The UploadFile payload containing the PDF.

    Returns:
        UploadResponse: Metadata detailing processed pages and chunks.

    Raises:
        HTTPException: For invalid formats, sizes, parsing, or indexing failures.
    """
    filename = file.filename or ""

    # 1. Basic Extension Check
    if not filename.lower().endswith(".pdf"):
        logger.warning(f"Rejected non-PDF upload attempt: '{filename}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents (.pdf) are supported.",
        )

    # 2. File Size Validation
    try:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
    except Exception as e:
        logger.error(f"Error checking file size for '{filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not check uploaded file size.",
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        logger.warning(f"Rejected '{filename}' upload: Size {file_size} exceeds limit.")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f} MB size limit.",
        )
    if file_size == 0:
        logger.warning(f"Rejected empty file upload: '{filename}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    # 3. Structure Integrity Check
    try:
        validate_pdf(file)
    except ValueError as e:
        logger.warning(f"Validation failed for '{filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF validation failed: {str(e)}",
        )

    # 4. Clean overwrite logic: delete old reference if exists
    try:
        if document_exists(filename):
            logger.info(f"Overwriting existing document: '{filename}'. Deleting old entries.")
            delete_document(filename)
    except Exception as e:
        logger.error(f"Failed to clear old index records for overwriting '{filename}': {e}")
        # Non-fatal error, log and continue

    # 5. Upload file to Supabase Storage
    content = await file.read()
    try:
        upload_pdf_to_storage(filename, content)
    except Exception as e:
        logger.error(f"Failed saving file '{filename}' to Supabase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed saving file upload to persistent storage.",
        )

    # 6. Execute RAG Ingestion Pipeline
    # Create a temporary file to run the parsing pipeline (extract_text expects a path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        # Extract page-by-page text
        pages = extract_text(temp_file_path)
        page_count = len(pages)
        if page_count == 0:
            raise ValueError("No readable text found in document pages.")

        # Text Chunking
        chunks = chunk_document(pages, filename)
        chunk_count = len(chunks)
        if chunk_count == 0:
            raise ValueError("Text split resulted in zero chunks.")

        # Embedding Generation
        embedded_chunks = generate_embeddings(chunks)

        # Index in Vector Database
        add_document(embedded_chunks)

        # Generate suggested questions based on document text context
        full_text = "\n".join([page.get("text", "") for page in pages])
        suggested_qs = generate_suggested_questions(full_text)

        # Persist suggested questions associated with the filename metadata
        save_document_questions(filename, suggested_qs)

        logger.info(
            f"Pipeline complete for '{filename}': "
            f"Ingested {page_count} pages, generated {chunk_count} vector chunks."
        )

        return UploadResponse(
            filename=filename,
            page_count=page_count,
            chunk_count=chunk_count,
            message="Document parsed, embedded, and indexed successfully.",
            suggested_questions=suggested_qs
        )

    except ValueError as e:
        logger.error(f"Process pipeline failed for '{filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process document: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected pipeline exception for '{filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal processing failure: {str(e)}",
        )
    finally:
        # 7. Cleanup the temporary file regardless of success or failure
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
        except Exception as cleanup_err:
            logger.error(f"Failed to clean up temporary file {temp_file_path}: {cleanup_err}")
