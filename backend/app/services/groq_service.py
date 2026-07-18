"""Service for generating grounded answers and suggested questions using the Groq LLM API.

Constructs prompts based on retrieved chunks, handles conversational history,
and generates suggested questions from document context.
"""

import logging
import json
import requests
from backend.app.config import settings

# Set up module-level logger
logger = logging.getLogger(__name__)


def generate_answer(question: str, chunks: list[dict], history: list[dict] = None) -> dict:
    """Generates an answer to the question using context from retrieved chunks and chat history.

    Sends requests to the Groq Chat Completions API. Prepend conversation history
    before the grounded query prompt to maintain conversational memory context.

    Args:
        question: The user's query question.
        chunks: List of retrieved context chunks (SourceChunk dictionaries).
        history: Optional list of recent message history items.

    Returns:
        dict: A dictionary containing the generated answer:
            {"answer": "..."}

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
        "Your goal is to provide accurate, confident, informative, and well-structured answers while remaining completely grounded in the retrieved context.\n"
        "Follow these rules:\n"
        "1. Answer the user's question directly. Do not begin with phrases like 'According to the provided context', 'The document appears to', or 'The context suggests'.\n"
        "2. Base every statement ONLY on the provided context. Never invent, assume or infer information that is not supported by the retrieved sources.\n"
        "3. If the provided context does not contain enough information to answer the question, respond with: 'I could not find enough information in the provided documents to answer this question.' Do not guess.\n"
        "4. Combine information from multiple sources into a single coherent answer whenever possible instead of discussing each source separately.\n"
        "5. Answer naturally in your own words. Avoid copying long passages from the retrieved context.\n"
        "6. For conceptual questions, begin with a clear explanation before discussing important details, applications, advantages, limitations or examples if available.\n"
        "7. For procedural questions, explain the steps in a logical sequence.\n"
        "8. Use headings, bullet points or numbered lists whenever they improve readability.\n"
        "9. Cite supporting evidence naturally using [Source 1], [Source 2], etc., immediately after the relevant statement rather than collecting all citations at the end.\n"
        "10. Keep the tone professional, confident, educational and concise.\n"
        "11. Do not mention the retrieval process, document context, vector search, similarity scores or how the information was obtained.\n"
    )

    user_prompt = (
        f"Context Sources:\n{context_str}\n\n"
        f"User Question: {question}\n\n"
        "Answer:"
    )

    # Prepend conversation history if provided
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for item in history:
            messages.append({
                "role": item.get("role", "user"),
                "content": item.get("content", "")
            })
    messages.append({"role": "user", "content": user_prompt})

    # 4. Invoke Groq Completions Endpoint via HTTP API
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
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
        return {
            "answer": answer
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request to Groq API failed: {e}")
        raise RuntimeError(f"Groq API communication error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in Groq service: {e}")
        raise RuntimeError(f"Failed to generate answer: {str(e)}")


def generate_suggested_questions(document_text: str) -> list[str]:
    """Generates 6-8 suggested questions based on the provided document text using Groq.

    Returns:
        list[str]: A list of generated question strings. Returns empty list on failure.
    """
    try:
        settings.validate_groq_key()
    except ValueError as e:
        logger.error(f"Configuration error checking key: {e}")
        return []

    if not document_text or not document_text.strip():
        logger.warning("Empty text context provided for suggested question generation.")
        return []

    system_prompt = (
        "You are an expert document analyst. Analyze the provided document text and generate 6-8 clear, useful questions that a reader might want to ask.\n"
        "The questions should cover various dimensions of the text, such as:\n"
        "- A summary of the document\n"
        "- Important concepts or ideas discussed\n"
        "- Key definitions or terminology\n"
        "- Specific processes, methodologies, or workflows described\n"
        "- Comparisons between items, options, or techniques\n"
        "- Real-world applications or use cases\n"
        "- Core conclusions or takeaways\n"
        "- Important formulas or equations, if present in the text\n\n"
        "CRITICAL: You must return ONLY a JSON object with a single key 'questions' containing the list of strings. Do not include markdown code block formatting (like ```json), intro text, or outro text. Just the raw JSON object, e.g., {\"questions\": [\"Question 1\", \"Question 2\"]}."
    )

    # Use first 10,000 characters of the document text as context
    user_prompt = f"Document Text:\n{document_text[:10000]}\n\nSuggested Questions JSON:"

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
        "temperature": 0.2,
        "max_tokens": 512,
        "response_format": {"type": "json_object"}
    }

    try:
        logger.info("Generating suggested questions using Groq...")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        response_json = response.json()
        raw_content = response_json["choices"][0]["message"]["content"].strip()
        
        # Clean the output in case the model used markdown code blocks
        if raw_content.startswith("```"):
            lines = raw_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_content = "\n".join(lines).strip()
            
        data = json.loads(raw_content)
        if isinstance(data, dict) and "questions" in data:
            return [str(q) for q in data["questions"] if isinstance(q, str)]
            
        return []
    except Exception as e:
        logger.error(f"Failed to generate suggested questions: {e}")
        # Return standard fallback questions on error
        return [
            "What is the summary of this document?",
            "What are the key methodologies or concepts presented?",
            "What are the main conclusions or takeaways of this text?"
        ]

def _generate_intermediate_study_notes(text_batch: str) -> str:
    """Helper to generate intermediate study notes for a batch of text."""
    system_prompt = (
        "You are an expert academic assistant. Analyze the provided text batch and extract key information "
        "to form a study sheet. Output your response directly in Markdown format (do NOT wrap in JSON).\n"
        "STRICT GROUNDING RULES:\n"
        "- Every extracted statement, formula, algorithm, definition, and concept MUST be explicitly present in the provided text.\n"
        "- NEVER supplement missing information using your prior knowledge.\n"
        "- NEVER generate common textbook examples, equations, or concepts if they are not explicitly written in the batch.\n"
        "- If no formulas exist in the batch, explicitly state 'No formulas are provided in this section.' Do not invent formulas.\n\n"
        "FORMATTING RULES:\n"
        "- Prioritize concise notes over long paragraphs. Use bullet points.\n"
        "- Extract comparisons, classifications, and algorithms into Markdown tables wherever it improves readability.\n"
        "- Use proper KaTeX block syntax ($$ ... $$) for block math and ($ ... $) for inline math.\n"
        "- Represent workflows as numbered steps or structured bullet hierarchies.\n"
        "Be concise and focus on high-yield study material."
    )
    user_prompt = f"Text Batch:\n{text_batch}\n\nGenerate intermediate study notes in Markdown:"

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
        "temperature": 0.2,
        "max_tokens": 2048,
    }

    response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    
    return response.json()["choices"][0]["message"]["content"].strip()


def _merge_study_notes(combined_notes: str) -> str:
    """Helper to merge multiple intermediate study notes into a final, cohesive study sheet."""
    system_prompt = (
        "You are an expert academic assistant. Synthesize the provided intermediate study notes into ONE final master Study Sheet.\n"
        "Output your response directly in Markdown format (do NOT wrap in JSON).\n\n"
        "STRICT GROUNDING RULES:\n"
        "- Every statement, formula, and concept MUST be directly supported by the provided notes.\n"
        "- NEVER supplement missing information using your prior knowledge.\n"
        "- NEVER generate common textbook examples or equations not present in the notes.\n\n"
        "ORGANIZATION & MERGE RULES:\n"
        "- Organize the information logically by revision value, rather than chronological order.\n"
        "- Use sections such as: Core Definitions, Important Concepts, Algorithms / Methods, Formulas, Comparisons, Tables, Workflows, Key Facts, Common Exam Points.\n"
        "- ONLY include sections that have supporting content.\n"
        "- Deduplicate repeated information. Merge similar sections into a single section. NEVER duplicate headings.\n"
        "- Ensure the final document reads as if generated in a single pass. Never expose batching artifacts (like 'Part 1', 'Intermediate Notes').\n\n"
        "FORMATTING RULES:\n"
        "- Prioritize concise, information-dense revision notes (bullet points, short explanations).\n"
        "- Preserve and enhance Markdown tables for comparisons and classifications.\n"
        "- Use proper KaTeX syntax ($$ ... $$ for blocks, $ ... $ for inline).\n"
        "- Workflows must remain structured (numbered steps or bullet hierarchies).\n\n"
        "FINAL REQUIREMENT:\n"
        "- At the very end of the document, add a 'Quick Revision' section: a concise checklist of only the highest-value facts for last-minute revision. Do not invent information."
    )
    user_prompt = f"Intermediate Notes:\n{combined_notes}\n\nGenerate final master Study Sheet in Markdown:"

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
        "temperature": 0.2,
        "max_tokens": 4096,
    }

    response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    
    return response.json()["choices"][0]["message"]["content"].strip()


def _incremental_merge_study_notes(existing_notes: str, new_notes: str) -> str:
    """Helper to incrementally merge new notes into an existing master study sheet."""
    system_prompt = (
        "You are an expert academic assistant. Synthesize the New Notes into the Existing Master Study Sheet.\n"
        "Output your response directly in Markdown format (do NOT wrap in JSON).\n\n"
        "STRICT GROUNDING RULES:\n"
        "- Every statement and formula MUST be directly supported by the provided text.\n"
        "- NEVER supplement missing information using your prior knowledge.\n\n"
        "ORGANIZATION & MERGE RULES:\n"
        "- Integrate new concepts seamlessly into the existing sections (Core Definitions, Important Concepts, Formulas, etc.).\n"
        "- Do NOT blindly append new notes to the end. Maintain a SINGLE logical Markdown hierarchy.\n"
        "- Deduplicate repeated definitions, algorithms, or concepts. NEVER duplicate headings.\n"
        "- Remove any batching artifacts (e.g., 'Part X', 'Intermediate Notes'). The document must read as a single unified guide.\n\n"
        "FORMATTING RULES:\n"
        "- Prioritize concise, information-dense revision notes (bullet points, short explanations).\n"
        "- Preserve Markdown tables and structured workflow hierarchies.\n"
        "- Use proper KaTeX syntax ($$ ... $$ for blocks, $ ... $ for inline).\n\n"
        "FINAL REQUIREMENT:\n"
        "- Ensure the 'Quick Revision' checklist at the end is updated with any new critical facts from the New Notes, but keep it concise and grounded."
    )
    
    # Cap strings to prevent context window overflow
    # Llama 3 has an 8192 token limit. prompt_tokens + max_tokens must be <= 8192.
    # If max_tokens is 3000, prompt can be max 5192 tokens (~20,000 chars).
    existing_capped = existing_notes[-12000:] if len(existing_notes) > 12000 else existing_notes
    new_capped = new_notes[-6000:] if len(new_notes) > 6000 else new_notes
    
    user_prompt = f"Existing Master Study Sheet (End):\n{existing_capped}\n\nNew Notes to Integrate:\n{new_capped}\n\nGenerate updated master Study Sheet in Markdown:"

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
        "temperature": 0.2,
        "max_tokens": 3000,
    }

    response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    
    # If we truncated existing notes, prepend the truncated part back to ensure we don't lose the start of the document
    prefix = existing_notes[:-12000] if len(existing_notes) > 12000 else ""
    merged_content = response.json()["choices"][0]["message"]["content"].strip()
    
    if prefix:
        return prefix + "\n\n" + merged_content
    return merged_content


def generate_study_sheet(document_text: str) -> str:
    """Generates a study sheet for a document, handling large texts via batching and incremental merging.
    
    Returns raw Markdown text.
    """
    try:
        settings.validate_groq_key()
    except ValueError as e:
        logger.error(f"Configuration error checking key: {e}")
        return "Error: API Key not configured."

    if not document_text or not document_text.strip():
        logger.warning("Empty text context provided for study sheet generation.")
        return "No text available to generate a study sheet."

    batch_size = 20000
    batches = [document_text[i:i + batch_size] for i in range(0, len(document_text), batch_size)]
    
    logger.info(f"Generating study sheet in {len(batches)} batches...")
    
    intermediate_results = []
    for i, batch in enumerate(batches):
        logger.info(f"Processing batch {i+1}/{len(batches)}...")
        try:
            notes = _generate_intermediate_study_notes(batch)
            intermediate_results.append(notes)
        except Exception as e:
            logger.error(f"Failed to process batch {i+1}: {e}")
            # we skip failed batches to at least return partial results if possible
    
    if not intermediate_results:
        return "Failed to generate study sheet due to API errors."

    if len(intermediate_results) == 1:
        logger.info("Formatting single batch into final study sheet...")
        try:
            return _merge_study_notes(intermediate_results[0])
        except Exception as e:
            logger.error(f"Failed to format study sheet: {e}")
            return intermediate_results[0]
            
    logger.info("Merging intermediate notes into final study sheet incrementally...")
    
    # Start with formatting the first batch properly
    try:
        final_sheet = _merge_study_notes(intermediate_results[0])
    except Exception as e:
        logger.error(f"Failed to format initial batch: {e}")
        final_sheet = intermediate_results[0]
        
    # Incrementally merge subsequent batches
    for i, next_notes in enumerate(intermediate_results[1:]):
        logger.info(f"Merging batch {i+2}/{len(intermediate_results)}...")
        try:
            final_sheet = _incremental_merge_study_notes(final_sheet, next_notes)
        except Exception as e:
            logger.error(f"Failed to merge batch {i+2}: {e}")
            # Fallback: roughly append if merge fails so data isn't lost, without exposing artifacts
            final_sheet += f"\n\n---\n\n{next_notes}"
            
    return final_sheet
