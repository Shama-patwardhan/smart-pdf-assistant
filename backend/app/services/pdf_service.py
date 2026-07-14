"""Service for PDF validation and text extraction using PyMuPDF (fitz).

Handles parsing, checking integrity, and extracting raw page text from 
uploaded PDF documents.
"""

import logging
import re
from fastapi import UploadFile
import fitz  # PyMuPDF

# Set up module-level logger
logger = logging.getLogger(__name__)


def validate_pdf(file: UploadFile) -> bool:
    """Validates the structure and readability of an uploaded PDF file.

    Checks if the file is empty, encrypted (password-protected), or corrupted.

    Args:
        file: The UploadFile object to validate.

    Returns:
        bool: True if the PDF is valid.

    Raises:
        ValueError: If the file is not a valid PDF, is encrypted, or corrupted.
    """
    try:
        # Read the file content from the upload stream
        content = file.file.read()
        # Reset the stream cursor back to the beginning
        file.file.seek(0)

        if not content:
            raise ValueError("The uploaded file is empty.")

        # Attempt to open the PDF from memory stream
        doc = fitz.open(stream=content, filetype="pdf")

        # Check for encryption/password-protection
        if doc.is_encrypted:
            doc.close()
            raise ValueError("The PDF is password-protected or encrypted.")

        # Check if the PDF has pages
        if len(doc) == 0:
            doc.close()
            raise ValueError("The PDF contains no pages.")

        # Ensure we can open/read the first page metadata
        _ = doc[0]
        doc.close()
        return True

    except fitz.FileDataError as e:
        logger.error(f"Corrupted or invalid PDF data structure: {e}")
        raise ValueError("The PDF file structure appears corrupted or invalid.")
    except Exception as e:
        if isinstance(e, ValueError):
            raise e
        logger.error(f"Unexpected error validating PDF: {e}")
        raise ValueError(f"Failed to validate PDF: {str(e)}")


def extract_text(file_path: str) -> list[dict]:
    """Opens a PDF from the filesystem and extracts text page by page.

    Cleans up excessive whitespace, preserves page numbers, skips empty pages,
    and raises exceptions for password-protected, corrupted, or image-only PDFs.

    Args:
        file_path: The absolute or relative string path to the PDF file.

    Returns:
        list[dict]: A list of dictionaries containing page number and text, e.g.:
            [{"page_number": 1, "text": "..."}]

    Raises:
        ValueError: If the PDF is password-protected, corrupted, or contains no extractable text.
        FileNotFoundError: If the file does not exist at the specified path.
    """
    try:
        # Open PDF from local path
        doc = fitz.open(file_path)

        if doc.is_encrypted:
            doc.close()
            raise ValueError("The PDF is password-protected.")

        if len(doc) == 0:
            doc.close()
            raise ValueError("The PDF contains no pages.")

        pages_data = []
        total_characters_extracted = 0

        # Loop through pages and extract text
        for page_idx, page in enumerate(doc):
            page_number = page_idx + 1
            raw_text = page.get_text()

            # Clean excessive whitespace: collapse multiple whitespace characters into a single space
            cleaned_text = re.sub(r"\s+", " ", raw_text).strip()

            # Skip empty pages
            if not cleaned_text:
                continue

            total_characters_extracted += len(cleaned_text)
            pages_data.append({"page_number": page_number, "text": cleaned_text})

        doc.close()

        # Check if any text was extracted at all (handling scan/image-only PDFs)
        if total_characters_extracted == 0:
            raise ValueError(
                "The PDF contains no extractable text. It may be scanned or image-only."
            )

        logger.info(
            f"Successfully extracted text from '{file_path}': "
            f"{len(pages_data)} active pages, {total_characters_extracted} characters."
        )
        return pages_data

    except fitz.FileDataError as e:
        logger.error(f"Failed opening corrupted PDF at '{file_path}': {e}")
        raise ValueError("The PDF file is corrupted and cannot be read.")
    except FileNotFoundError as e:
        logger.error(f"PDF file not found at '{file_path}': {e}")
        raise FileNotFoundError(f"PDF file not found at path: {file_path}")
    except Exception as e:
        if isinstance(e, ValueError):
            raise e
        logger.error(f"Unexpected error extracting PDF text from '{file_path}': {e}")
        raise ValueError(f"Failed to extract PDF text: {str(e)}")
