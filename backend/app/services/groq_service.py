"""Service for generating grounded answers using the Groq LLM API.

Constructs prompts based on retrieved chunks and validates answers against
provided contexts.
"""

import logging
import requests
from backend.app.config import settings

# Set up module-level logger
logger = logging.getLogger(__name__)


def generate_answer(question: str, chunks: list[dict]) -> dict:
    """Generates an answer to the question using context from retrieved chunks.

    Sends requests to the Groq Chat Completions API. If context is missing
    or insufficient, returns a standard answer indicating context is not found.

    Args:
        question: The user's query question.
        chunks: List of retrieved context chunks (SourceChunk dictionaries).

    Returns:
        dict: A dictionary containing the answer and confidence score:
            {"answer": "...", "confidence": 0.85}

    Raises:
        ValueError: If question is invalid.
        RuntimeError: If the Groq API call fails.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    # 1. Handle Empty Context immediately
    if not chunks:
        logger.info("Empty context provided. Returning 'not found' response directly.")
        return {
            "answer": "I could not find the answer in the provided documents as there is no relevant context available.",
            "confidence": 0.0
        }

    # 2. Validate Groq Configuration
    try:
        settings.validate_groq_key()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise RuntimeError(f"Groq service unavailable: {str(e)}")

    # 3. Construct Prompt Context
    context_text_blocks = []
    for idx, chunk in enumerate(chunks):
        filename = chunk.get("filename", "Unknown")
        page_num = chunk.get("page_number", 0)
        chunk_text = chunk.get("chunk_text", "")
        context_text_blocks.append(
            f"[Source {idx + 1}] Document: {filename}, Page: {page_num}\n"
            f"Content: {chunk_text}\n"
        )
    context_str = "\n---\n".join(context_text_blocks)

    system_prompt = (
    "You are Smart PDF Assistant, an AI assistant that answers questions using ONLY the provided document context.\n"
    "Your task is to provide accurate, informative, and well-structured answers based strictly on the retrieved context.\n"
    "Follow these strict rules:\n"
    "1. Base every answer ONLY on the provided context sources. Never invent or assume information.\n"
    "2. If the answer is not fully available in the provided context, clearly state: "
    "'I could not find enough information in the provided context to answer this question.'\n"
    "3. Combine information from multiple context sources whenever they discuss the same topic instead of describing each source separately.\n"
    "4. Answer in your own words. Do not copy long passages from the context unless absolutely necessary.\n"
    "5. For broad or conceptual questions, begin with a clear definition or overview, then explain the concept in a logical and educational manner.\n"
    "6. For 'How' questions, explain the process step by step.\n"
    "7. For 'Why' questions, explain the reasoning before providing supporting details.\n"
    "8. Use bullet points or numbered lists whenever they improve readability.\n"
    "9. Refer to supporting context using citations such as [Source 1], [Source 2], etc., wherever appropriate.\n"
    "10. Keep the response professional, clear, and easy to understand while remaining concise.\n"
)

    user_prompt = (
        f"Context Sources:\n{context_str}\n\n"
        f"User Question: {question}\n\n"
        "Answer:"
    )

    # 4. Invoke Groq Completions Endpoint via HTTP API
    # Zero external dependency ensures maximum stability
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 1024
    }

    logger.info(f"Sending generation request to Groq using model '{settings.GROQ_MODEL}'...")
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        response_json = response.json()
        answer = response_json["choices"][0]["message"]["content"].strip()
        logger.info("Successfully received answer from Groq API.")

        # 5. Compute Confidence Score
        # Confidence is based on retrieval quality rather than only the top similarity.
        similarities = [chunk.get("similarity_score", 0.0) for chunk in chunks]
        average_similarity = sum(similarities) / len(similarities)
        chunk_count_score = min(len(chunks), settings.TOP_K_RESULTS) / settings.TOP_K_RESULTS
        consistency_score = 1.0 - (
            (max(similarities) - min(similarities))
            if len(similarities) > 1 else 0
        )
        lowercase_answer = answer.lower()
        if (
            "could not find the answer" in lowercase_answer
            or "not found in the provided context" in lowercase_answer
            or "no relevant context" in lowercase_answer
        ):
            confidence = 0.0
        else:
            confidence = (
                average_similarity * 0.60 +
                chunk_count_score * 0.20 +
                consistency_score * 0.20
            )
        confidence = round(max(0.0, min(confidence, 1.0)), 4)

        return {
            "answer": answer,
            "confidence": confidence
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request to Groq API failed: {e}")
        raise RuntimeError(f"Groq API communication error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in Groq service: {e}")
        raise RuntimeError(f"Failed to generate answer: {str(e)}")
