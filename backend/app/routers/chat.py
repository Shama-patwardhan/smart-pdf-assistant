"""API router for RAG chat operations.

Handles user question submissions, retrieves context chunks from the vector store, 
and generates grounded answers using the Groq LLM API.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from backend.app.models.schemas import QuestionRequest, QuestionResponse, SourceChunk, ErrorResponse
from backend.app.services.retrieval_service import retrieve_relevant_chunks
from backend.app.services.groq_service import generate_answer

# Set up module-level logger
logger = logging.getLogger(__name__)

# Initialize APIRouter
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Validation or service parameters mismatch"},
        500: {"model": ErrorResponse, "description": "Vector store or LLM invocation failure"},
    },
)
async def ask_question(request: QuestionRequest) -> QuestionResponse:
    """Accepts a query question, retrieves supporting documents context, and returns a grounded answer.

    Users can optionally filter context strictly to a single document via 'filename'.

    Args:
        request: The QuestionRequest payload.

    Returns:
        QuestionResponse: The answer, confidence score, and supporting sources.

    Raises:
        HTTPException: If query validation, context retrieval, or Groq API calls fail.
    """
    question = request.question.strip()
    filename_scope = request.filename

    logger.info(f"Received query request: '{question}' (Scoped document: {filename_scope or 'None'})")

    try:
        # 1. Retrieve relevant contextual chunks from ChromaDB
        retrieved_chunks = retrieve_relevant_chunks(question, filename_scope)
        logger.debug(f"Retrieved {len(retrieved_chunks)} relevant source blocks for LLM context.")

        # 2. Generate grounded answer via Groq LLM API
        completion = generate_answer(question, retrieved_chunks)
        
        # 3. Format supporting context list as SourceChunks
        source_objects = [
            SourceChunk(
                filename=chunk["filename"],
                page_number=chunk["page_number"],
                chunk_text=chunk["chunk_text"],
                similarity_score=chunk["similarity_score"]
            )
            for chunk in retrieved_chunks
        ]

        logger.info(
            f"Successfully resolved query response. Answer character count: {len(completion['answer'])}. "
            f"Confidence: {completion['confidence']:.4f}"
        )

        return QuestionResponse(
            answer=completion["answer"],
            confidence=completion["confidence"],
            sources=source_objects
        )

    except ValueError as e:
        logger.warning(f"Validation failure handling question request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to process chat query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while answering the query: {str(e)}",
        )
