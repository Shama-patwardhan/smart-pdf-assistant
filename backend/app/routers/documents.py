"""API router for document management operations.

Allows listing processed document profiles and deleting documents (clearing disk
and vector database records).
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from backend.app.config import settings
from backend.app.models.schemas import DocumentInfo, ErrorResponse
from backend.app.services.vector_store import list_documents, delete_document, document_exists, get_document_questions, get_document_full_text
from backend.app.services.asset_store import delete_assets, get_asset, save_asset
from backend.app.services.groq_service import generate_study_sheet
from backend.app.services.storage_service import delete_pdf
from fastapi.responses import PlainTextResponse

# Set up module-level logger
logger = logging.getLogger(__name__)

# Initialize APIRouter
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get(
    "/",
    response_model=List[DocumentInfo],
    status_code=status.HTTP_200_OK,
    responses={
        500: {"model": ErrorResponse, "description": "Database query failure"},
    },
)
async def list_indexed_documents() -> List[DocumentInfo]:
    """Retrieves all indexed PDF files alongside page counts and chunk statistics.

    Returns:
        List[DocumentInfo]: List of processed document summaries.
    """
    logger.info("Request received to list all indexed documents.")
    try:
        docs = list_documents()
        # Parse list of dicts to list of DocumentInfo models
        return [
            DocumentInfo(
                filename=doc["filename"],
                page_count=doc["page_count"],
                chunk_count=doc["chunk_count"]
            )
            for doc in docs
        ]
    except Exception as e:
        logger.error(f"Failed to fetch indexed documents list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query index records: {str(e)}",
        )


@router.delete(
    "/{filename}",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found in database"},
        500: {"model": ErrorResponse, "description": "Deletion failed"},
    },
)
async def delete_indexed_document(filename: str) -> dict:
    """Removes a document completely from the system.

    Deletes the associated PDF file from disk and deletes all indexing records
    and vector embeddings from ChromaDB.

    Args:
        filename: Name of the PDF file to delete.

    Returns:
        dict: Status message confirming successful deletion.

    Raises:
        HTTPException: If document is not found or deletion operations fail.
    """
    logger.info(f"Request received to delete document '{filename}'.")

    # 1. Validate existence in the system
    exists_in_db = document_exists(filename)

    if not exists_in_db:
        logger.warning(f"Delete request failed: '{filename}' not found in database.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' was not found in the assistant system.",
        )

    # 2. Delete entries from vector store
    try:
        if exists_in_db:
            delete_document(filename)
            logger.info(f"Deleted database index references for '{filename}'.")
    except Exception as e:
        logger.error(f"Failed to delete vector database entries for '{filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove vector references: {str(e)}",
        )

    # 3. Delete file from Supabase Storage
    try:
        delete_pdf(filename)
    except Exception as e:
        logger.error(f"Failed to remove file '{filename}' from Supabase storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove file from Supabase storage: {str(e)}",
        )

    # 4. Delete document assets directory
    try:
        delete_assets(filename)
    except Exception as e:
        logger.error(f"Failed to remove assets directory for '{filename}': {e}")

    return {
        "message": f"Document '{filename}' successfully deleted from vector database and Supabase storage."
    }


@router.get(
    "/{filename}/questions",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found in database"},
        500: {"model": ErrorResponse, "description": "Database query failure"},
    },
)
async def get_document_suggested_questions(filename: str) -> List[str]:
    """Retrieves persisted suggested questions for a given document.

    Args:
        filename: Name of the PDF file.

    Returns:
        List[str]: List of suggested questions.
    """
    logger.info(f"Request received to get suggested questions for '{filename}'.")
    if not document_exists(filename):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' was not found in the assistant system.",
        )
    try:
        return get_document_questions(filename)
    except Exception as e:
        logger.error(f"Failed to fetch suggested questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query questions: {str(e)}",
        )

@router.get(
    "/{filename}/study_sheet",
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK,
)
async def get_study_sheet(filename: str):
    logger.info(f"Retrieving study sheet for '{filename}'.")
    if not document_exists(filename):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found.",
        )
    data = get_asset(filename, "study_sheet")
    if not data or "content" not in data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study sheet for '{filename}' not found.",
        )
    return PlainTextResponse(content=data["content"])

@router.post(
    "/{filename}/study_sheet",
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK,
)
async def create_study_sheet(filename: str, force_regenerate: bool = False):
    logger.info(f"Request to generate study sheet for '{filename}'. Force: {force_regenerate}")
    if not document_exists(filename):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found.",
        )
        
    if not force_regenerate:
        data = get_asset(filename, "study_sheet")
        if data and "content" in data:
            return PlainTextResponse(content=data["content"])
            
    try:
        text = get_document_full_text(filename)
        markdown_content = generate_study_sheet(text)
        save_asset(filename, "study_sheet", {"content": markdown_content})
        return PlainTextResponse(content=markdown_content)
    except Exception as e:
        logger.error(f"Failed to generate study sheet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate study sheet: {str(e)}",
        )
