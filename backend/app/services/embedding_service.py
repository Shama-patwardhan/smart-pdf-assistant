"""Service for generating vector embeddings using Sentence Transformers.

Loads the configured embedding model once and exposes methods for generating
individual text embeddings or batch processing document chunks.
"""

import logging
from typing import Optional
from sentence_transformers import SentenceTransformer
from backend.app.config import settings

# Set up module-level logger
logger = logging.getLogger(__name__)

# Global singleton container for the model to ensure it is loaded only once
_model: Optional[SentenceTransformer] = None


def _get_model() -> SentenceTransformer:
    """Helper to lazily load and retrieve the SentenceTransformer model singleton.

    Returns:
        SentenceTransformer: The loaded embedding model instance.

    Raises:
        RuntimeError: If model loading fails.
    """
    global _model
    if _model is None:
        try:
            logger.info(f"Loading SentenceTransformer model: '{settings.EMBEDDING_MODEL}'...")
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model '{settings.EMBEDDING_MODEL}': {e}")
            raise RuntimeError(f"Could not initialize embedding model: {str(e)}")
    return _model


def generate_embedding(text: str) -> list[float]:
    """Generates a dense vector embedding for a single text string.

    Args:
        text: The input text to embed.

    Returns:
        list[float]: The generated vector embedding as a list of floats.

    Raises:
        ValueError: If input text is empty or invalid.
        RuntimeError: If model inference fails.
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text.")

    try:
        model = _get_model()
        # Perform embedding generation
        embedding_vector = model.encode(text.strip(), convert_to_numpy=True)
        return embedding_vector.tolist()
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise RuntimeError(f"Embedding generation failed: {str(e)}")


def generate_embeddings(chunks: list[dict]) -> list[dict]:
    """Processes a list of chunks and inserts their vector embeddings.

    Each chunk dictionary is updated inline with an 'embedding' key. Empty 
    chunks or chunks missing text are skipped.

    Args:
        chunks: A list of dictionaries representing document chunks.
            Example: [{"chunk_id": 1, "filename": "doc.pdf", "chunk_text": "text..."}]

    Returns:
        list[dict]: The list of processed chunks containing the 'embedding' key.

    Raises:
        ValueError: If input structure is invalid.
        RuntimeError: If model inference fails.
    """
    if not isinstance(chunks, list):
        raise ValueError("Input 'chunks' must be a list of dictionaries.")

    logger.info(f"Preparing to generate embeddings for {len(chunks)} chunks.")

    try:
        model = _get_model()
        valid_chunks = []
        texts_to_embed = []

        # 1. Filter out empty chunks and prepare batch texts
        for index, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                raise ValueError(f"Chunk at index {index} is not a dictionary.")

            chunk_text = chunk.get("chunk_text")
            if not chunk_text or not chunk_text.strip():
                logger.warning(f"Skipping empty or missing text in chunk at index {index}.")
                continue

            valid_chunks.append(chunk)
            texts_to_embed.append(chunk_text.strip())

        if not texts_to_embed:
            logger.warning("No valid text chunks found to embed.")
            return []

        # 2. Batch encode the texts for optimal performance
        logger.info(f"Encoding batch of {len(texts_to_embed)} texts...")
        embeddings = model.encode(
            texts_to_embed,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        logger.info("Batch encoding completed successfully.")

        # 3. Map embeddings back to their respective chunks
        for chunk, emb in zip(valid_chunks, embeddings):
            chunk["embedding"] = emb.tolist()

        return valid_chunks

    except Exception as e:
        logger.error(f"Failed to generate batch embeddings: {e}")
        raise RuntimeError(f"Batch embedding generation failed: {str(e)}")
