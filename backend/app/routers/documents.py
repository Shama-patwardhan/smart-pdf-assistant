"""API router for document management operations.

Allows listing processed document profiles and deleting documents (clearing disk
and vector database records).
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from backend.app.config import settings
from backend.app.models.schemas import DocumentInfo, ErrorResponse
from backend.app.services.vector_store import list_documents, delete_document, document_exists

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
    file_path = settings.UPLOAD_FOLDER / filename
    exists_on_disk = file_path.exists()
    exists_in_db = document_exists(filename)

    if not exists_on_disk and not exists_in_db:
        logger.warning(f"Delete request failed: '{filename}' not found in uploads or database.")
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

    # 3. Delete file from local uploads folder
    try:
        if exists_on_disk:
            file_path.unlink()
            logger.info(f"Deleted local file from storage: '{file_path}'")
    except Exception as e:
        logger.error(f"Failed to remove file '{filename}' from local storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove local file from storage: {str(e)}",
        )

    return {
        "message": f"Document '{filename}' successfully deleted from vector database and local storage."
    }
