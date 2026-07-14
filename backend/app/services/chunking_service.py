"""Service for chunking parsed PDF documents into smaller text segments.

Utilizes LangChain's RecursiveCharacterTextSplitter to split text page by page
while keeping track of the page numbers and generating unique sequential chunk IDs.
"""

import logging
from backend.app.config import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Set up module-level logger
logger = logging.getLogger(__name__)


def chunk_document(pages: list[dict], filename: str) -> list[dict]:
    """Splits a document's page-by-page text into semantic overlapping chunks.

    Preserves the original page number of each text block and assigns a sequential 
    chunk ID across the entire document.

    Args:
        pages: A list of dictionaries representing pages with keys 'page_number' and 'text'.
            Example: [{"page_number": 1, "text": "page content..."}]
        filename: The filename of the PDF document being chunked.

    Returns:
        list[dict]: A list of chunks with metadata and sequential IDs.
            Example:
            [
                {
                    "chunk_id": 1,
                    "filename": "sample.pdf",
                    "page_number": 1,
                    "chunk_text": "chunk text content..."
                }
            ]

    Raises:
        ValueError: If input format is invalid or chunking fails.
    """
    logger.info(
        f"Starting chunking for '{filename}' "
        f"with chunk_size={settings.CHUNK_SIZE}, chunk_overlap={settings.CHUNK_OVERLAP}"
    )

    if not isinstance(pages, list):
        raise ValueError("Input 'pages' must be a list of dictionaries.")

    try:
        # Initialize LangChain's RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        chunked_data = []
        chunk_id_counter = 1

        for page in pages:
            if not isinstance(page, dict) or "page_number" not in page or "text" not in page:
                raise ValueError("Each page item must be a dictionary containing 'page_number' and 'text'.")

            page_num = page["page_number"]
            page_text = page["text"]

            if not page_text or not page_text.strip():
                continue

            # Split text of the current page
            split_texts = text_splitter.split_text(page_text)

            for text in split_texts:
                cleaned_chunk_text = text.strip()
                if not cleaned_chunk_text:
                    continue

                chunked_data.append({
                    "chunk_id": chunk_id_counter,
                    "filename": filename,
                    "page_number": page_num,
                    "chunk_text": cleaned_chunk_text,
                })
                chunk_id_counter += 1

        total_chunks = len(chunked_data)
        logger.info(f"Successfully chunked '{filename}': created {total_chunks} chunks.")
        return chunked_data

    except Exception as e:
        logger.error(f"Chunking failed for document '{filename}': {e}")
        raise ValueError(f"Failed to chunk document '{filename}': {str(e)}")
