"""Storage service for managing documents in Supabase Storage."""

import logging
from backend.app.services.supabase_client import supabase

logger = logging.getLogger(__name__)

BUCKET_NAME = "document"

def upload_pdf(filename: str, content: bytes) -> bool:
    """Uploads a PDF to the storage backend.
    
    Args:
        filename: The target filename in storage.
        content: The raw byte content of the PDF.
        
    Returns:
        True if successful.
    
    Raises:
        RuntimeError: If storage client is not available.
        Exception: If the upload operation fails.
    """
    if not supabase:
        raise RuntimeError("Supabase client not initialized.")
    
    try:
        # Uploading with upsert option is safer if it might exist
        supabase.storage.from_(BUCKET_NAME).upload(
            path=filename,
            file=content,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        logger.info(f"Successfully uploaded '{filename}' to Supabase.")
        return True
    except Exception as e:
        logger.error(f"Failed to upload file '{filename}' to Supabase: {e}")
        raise

def download_pdf(filename: str) -> bytes:
    """Downloads a PDF from the storage backend.
    
    Args:
        filename: The name of the file to download.
        
    Returns:
        bytes: The raw content of the downloaded file.
        
    Raises:
        RuntimeError: If storage client is not available.
        Exception: If the download fails.
    """
    if not supabase:
        raise RuntimeError("Supabase client not initialized.")
    
    try:
        res = supabase.storage.from_(BUCKET_NAME).download(filename)
        return res
    except Exception as e:
        logger.error(f"Failed to download file '{filename}' from Supabase: {e}")
        raise

def delete_pdf(filename: str) -> bool:
    """Deletes a PDF from the storage backend.
    
    Args:
        filename: The name of the file to delete.
        
    Returns:
        True if successful.
        
    Raises:
        RuntimeError: If storage client is not available.
        Exception: For unexpected storage errors.
    """
    if not supabase:
        raise RuntimeError("Supabase client not initialized.")
    
    try:
        res = supabase.storage.from_(BUCKET_NAME).remove([filename])
        if not res:
            logger.warning(f"File '{filename}' was already missing from Supabase.")
        else:
            logger.info(f"Successfully deleted '{filename}' from Supabase.")
        return True
    except Exception as e:
        # Supabase API might return exceptions for missing files, depending on the error message
        error_msg = str(e).lower()
        if "not found" in error_msg or "missing" in error_msg:
            logger.warning(f"File '{filename}' was already missing from Supabase. (Error: {e})")
            return True
        logger.error(f"Unexpected error deleting file '{filename}' from Supabase: {e}")
        raise
