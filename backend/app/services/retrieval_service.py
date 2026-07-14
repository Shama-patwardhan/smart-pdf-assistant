"""Service for retrieving relevant document chunks from the vector database.

Uses the embedding service to convert user queries into vectors and queries
the FAISS vector store, filtering by thresholds and optional file scope.
"""

import logging
from typing import Optional
from backend.app.config import settings
from backend.app.services.embedding_service import generate_embedding
from backend.app.services.vector_store import search

# Set up module-level logger
logger = logging.getLogger(__name__)


def retrieve_relevant_chunks(question: str, filename: Optional[str] = None) -> list[dict]:
    """Retrieves relevant document chunks from the vector store for a question.

    Generates an embedding of the question, searches the FAISS index, and
    filters the results by similarity threshold and optional filename scope.

    Args:
        question: The user query string.
        filename: Optional filename to scope the search context.

    Returns:
        list[dict]: A list of matched source chunk dictionaries, sorted by relevance:
            [
                {
                    "filename": "doc.pdf",
                    "page_number": 4,
                    "chunk_text": "extracted text...",
                    "similarity_score": 0.82
                }
            ]

    Raises:
        ValueError: If query string is invalid.
        RuntimeError: If vector search fails.
    """
    if not question or not question.strip():
        raise ValueError("Search question cannot be empty.")

    logger.info(f"Retrieving chunks for question: '{question}' (scope: {filename or 'global'})")

    try:
        # 1. Generate query embedding vector
        query_vector = generate_embedding(question)

        # 2. Search FAISS index with an over-sampling factor to prevent filter starvation
        search_limit = max(settings.TOP_K_RESULTS * 4, 20)
        raw_results = search(query_vector, top_k=search_limit)

        filtered_results = []
        for res in raw_results:
            # 3. Filter by similarity threshold
            similarity_score = res.get("similarity_score", 0.0)
            if similarity_score < settings.SIMILARITY_THRESHOLD:
                logger.debug(
                    f"Skipping chunk from '{res.get('filename')}' page {res.get('page_number')}: "
                    f"similarity score {similarity_score:.4f} below threshold {settings.SIMILARITY_THRESHOLD}"
                )
                continue

            # 4. Filter by filename if scope is provided
            if filename and res.get("filename") != filename:
                logger.debug(
                    f"Skipping chunk from '{res.get('filename')}': "
                    f"does not match search scope '{filename}'"
                )
                continue

            # Append the cleaned dictionary
            filtered_results.append({
                "filename": res.get("filename", "unknown"),
                "page_number": res.get("page_number", 0),
                "chunk_text": res.get("chunk_text", ""),
                "similarity_score": similarity_score
            })

        # 5. Sort by similarity score descending
        filtered_results.sort(key=lambda x: x["similarity_score"], reverse=True)

        # 6. Keep only the top settings.TOP_K_RESULTS results
        final_results = filtered_results[:settings.TOP_K_RESULTS]

        logger.info(f"Retrieval returned {len(final_results)} chunks matching criteria.")
        return final_results

    except Exception as e:
        logger.error(f"Retrieval operation failed: {e}")
        raise RuntimeError(f"Retrieval operation failed: {str(e)}")
