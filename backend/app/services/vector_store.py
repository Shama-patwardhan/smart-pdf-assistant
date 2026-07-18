"""Service for interacting with FAISS vector store.

Handles persistent vector store operations including adding documents, checking
existence, listing processed files, deleting documents, and searching using FAISS.
It also persists generated suggested questions metadata.
"""

import logging
import pickle
from pathlib import Path

import faiss
import numpy as np

from backend.app.config import settings

# Set up module-level logger
logger = logging.getLogger(__name__)

# Paths for persisting the FAISS index and metadata
FAISS_DIR = settings.UPLOAD_FOLDER.parent / "faiss"
INDEX_FILE = FAISS_DIR / "index.faiss"
META_FILE = FAISS_DIR / "metadata.pkl"
QUESTIONS_FILE = FAISS_DIR / "questions.pkl"
EMBEDDING_DIM = 384  # Dimension for sentence-transformers/all-MiniLM-L6-v2

# Global state
index: faiss.IndexFlatL2 | None = None
metadata_store: list[dict] = []
questions_store: dict[str, list[str]] = {}


def load_store() -> None:
    """Loads the FAISS index, metadata, and questions from disk on startup."""
    global index, metadata_store, questions_store
    
    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    
    if INDEX_FILE.exists() and META_FILE.exists():
        try:
            logger.info(f"Loading existing FAISS index from {INDEX_FILE}...")
            index = faiss.read_index(str(INDEX_FILE))
            with open(META_FILE, "rb") as f:
                metadata_store = pickle.load(f)
            logger.info(f"Loaded FAISS index and metadata. Total chunks: {len(metadata_store)}")
        except Exception as e:
            logger.error(f"Failed to load FAISS store, creating a new empty index: {e}")
            index = faiss.IndexFlatL2(EMBEDDING_DIM)
            metadata_store = []
    else:
        logger.info("FAISS store not found. Creating a new empty index.")
        index = faiss.IndexFlatL2(EMBEDDING_DIM)
        metadata_store = []

    # Load persisted questions
    if QUESTIONS_FILE.exists():
        try:
            with open(QUESTIONS_FILE, "rb") as f:
                questions_store = pickle.load(f)
            logger.info(f"Loaded suggested questions for {len(questions_store)} documents.")
        except Exception as e:
            logger.error(f"Failed to load suggested questions: {e}")
            questions_store = {}
    else:
        questions_store = {}


def save_store() -> None:
    """Saves the FAISS index and metadata to disk."""
    global index, metadata_store
    try:
        FAISS_DIR.mkdir(parents=True, exist_ok=True)
        if index is not None:
            faiss.write_index(index, str(INDEX_FILE))
        with open(META_FILE, "wb") as f:
            pickle.dump(metadata_store, f)
        logger.info("FAISS index and metadata successfully saved to disk.")
    except Exception as e:
        logger.error(f"Failed to save FAISS store: {e}")
        raise RuntimeError(f"Failed to save vector store: {str(e)}")


def save_questions() -> None:
    """Saves the suggested questions store to disk."""
    global questions_store
    try:
        FAISS_DIR.mkdir(parents=True, exist_ok=True)
        with open(QUESTIONS_FILE, "wb") as f:
            pickle.dump(questions_store, f)
        logger.info("Suggested questions metadata successfully saved to disk.")
    except Exception as e:
        logger.error(f"Failed to save suggested questions: {e}")
        raise RuntimeError(f"Failed to save suggested questions metadata: {str(e)}")


def save_document_questions(filename: str, questions: list[str]) -> None:
    """Associates and persists suggested questions with a document."""
    global questions_store
    questions_store[filename] = questions
    save_questions()


def get_document_questions(filename: str) -> list[str]:
    """Retrieves suggested questions for a document."""
    return questions_store.get(filename, [])


def add_document(chunks: list[dict]) -> None:
    """Adds a document's text chunks and embeddings to FAISS.

    Args:
        chunks: List of dictionaries representing chunks with embeddings.

    Raises:
        ValueError: If chunks list is empty or format is invalid.
        RuntimeError: If FAISS insert operation fails.
    """
    if not chunks:
        raise ValueError("Cannot add empty chunk list to vector store.")

    filename = chunks[0].get("filename", "unknown_document")
    logger.info(f"Adding {len(chunks)} chunks for document '{filename}' to FAISS...")

    try:
        new_metadata = []
        vectors = []
        
        for idx, chunk in enumerate(chunks):
            chunk_id = chunk.get("chunk_id")
            chunk_text = chunk.get("chunk_text")
            embedding = chunk.get("embedding")
            page_number = chunk.get("page_number", 0)

            if chunk_text is None or embedding is None or chunk_id is None:
                raise ValueError(f"Chunk at index {idx} is missing required data fields.")

            vectors.append(embedding)
            
            # Metadata for each chunk
            new_metadata.append({
                "filename": filename,
                "page_number": page_number,
                "chunk_id": chunk_id,
                "chunk_text": chunk_text
            })

        vectors_np = np.array(vectors, dtype=np.float32)
        
        global index
        if index is None:
            dim = vectors_np.shape[1]
            index = faiss.IndexFlatL2(dim)
            
        index.add(vectors_np)
        metadata_store.extend(new_metadata)
        
        # Save after every add operation
        save_store()
        logger.info(f"Successfully added document '{filename}' with {len(chunks)} chunks to FAISS.")

    except Exception as e:
        logger.error(f"Failed to add document '{filename}' to FAISS: {e}")
        raise RuntimeError(f"FAISS vector store insert failed: {str(e)}")


def document_exists(filename: str) -> bool:
    """Checks if a document is already indexed in FAISS metadata.

    Args:
        filename: Name of the PDF file.

    Returns:
        bool: True if at least one chunk exists for this filename.
    """
    exists = any(meta.get("filename") == filename for meta in metadata_store)
    logger.debug(f"Document existence check for '{filename}': {exists}")
    return exists


def list_documents() -> list[dict]:
    """Retrieves all indexed documents with page and chunk metrics.

    Returns:
        list[dict]: A list of DocumentInfo structures as dictionaries:
            [{"filename": "doc.pdf", "page_count": 5, "chunk_count": 23}]
    """
    logger.info("Retrieving indexed documents list from metadata store...")
    
    doc_stats = {}
    for meta in metadata_store:
        fname = meta.get("filename", "unknown")
        page_num = meta.get("page_number", 1)
        
        if fname not in doc_stats:
            doc_stats[fname] = {
                "filename": fname,
                "pages": set(),
                "chunk_count": 0
            }
        
        doc_stats[fname]["pages"].add(page_num)
        doc_stats[fname]["chunk_count"] += 1
        
    documents_list = []
    for stats in doc_stats.values():
        documents_list.append({
            "filename": stats["filename"],
            "page_count": len(stats["pages"]),
            "chunk_count": stats["chunk_count"]
        })
        
    logger.info(f"Found {len(documents_list)} unique documents in vector store.")
    return documents_list


def delete_document(filename: str) -> None:
    """Removes all indexed chunks associated with a document from FAISS and metadata."""
    logger.info(f"Deleting document '{filename}' from FAISS vector store...")
    global index, metadata_store, questions_store
    
    try:
        if not document_exists(filename):
            logger.warning(f"Attempted to delete non-existent document '{filename}'")
            return

        # Boolean mask: True if we want to keep the chunk
        keep_mask = [meta.get("filename") != filename for meta in metadata_store]
        
        new_metadata = [meta for meta, keep in zip(metadata_store, keep_mask) if keep]
        
        if len(new_metadata) == 0:
            # Everything deleted, create empty index
            dim = index.d if index else EMBEDDING_DIM
            index = faiss.IndexFlatL2(dim)
            metadata_store = []
        else:
            # Reconstruct index with kept vectors
            keep_mask_np = np.array(keep_mask, dtype=bool)
            all_vectors = index.reconstruct_n(0, index.ntotal)
            new_vectors = all_vectors[keep_mask_np]
            
            dim = index.d
            new_index = faiss.IndexFlatL2(dim)
            new_index.add(new_vectors)
            
            index = new_index
            metadata_store = new_metadata
            
        # Save FAISS index
        save_store()

        # Delete document questions if present
        if filename in questions_store:
            del questions_store[filename]
            save_questions()

        logger.info(f"Successfully deleted all vector and questions records for '{filename}'.")
        
    except Exception as e:
        logger.error(f"Failed to delete document '{filename}' from FAISS: {e}")
        raise RuntimeError(f"Failed to delete document: {str(e)}")


def search(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """Searches the FAISS index for the most similar chunks to the query."""
    if index is None or index.ntotal == 0:
        logger.debug("Index is empty, returning no results.")
        return []
        
    q_vec = np.array([query_embedding], dtype=np.float32)
    # Search returns squared L2 distances and indices
    distances, indices = index.search(q_vec, top_k)
    
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
            
        meta = metadata_store[idx]
        
        # Convert L2 distance to a similarity score (higher is more similar)
        similarity_score = 1.0 / (1.0 + float(dist))
        
        results.append({
            "filename": meta.get("filename", "unknown"),
            "page_number": meta.get("page_number", 0),
            "chunk_id": meta.get("chunk_id", 0),
            "chunk_text": meta.get("chunk_text", ""),
            "similarity_score": round(similarity_score, 4)
        })
        
    logger.debug(f"Search found {len(results)} matches.")
    return results

def get_document_full_text(filename: str) -> str:
    """Retrieves all text chunks for a document, concatenated into a single string.
    
    Args:
        filename: Name of the PDF file.
        
    Returns:
        str: The full text of the document.
    """
    chunks = [meta for meta in metadata_store if meta.get("filename") == filename]
    # Sort chunks by page_number, then chunk_id to maintain order
    chunks.sort(key=lambda x: (x.get("page_number", 0), x.get("chunk_id", 0)))
    return "\n\n".join(chunk.get("chunk_text", "") for chunk in chunks)

# Initialize on module load
load_store()
