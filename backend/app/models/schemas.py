"""Pydantic schema definitions for the Smart PDF Assistant.

This module contains the request and response schemas used for data validation
in the FastAPI backend endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MessageHistoryItem(BaseModel):
    """Schema representing an item in conversation history."""

    role: str = Field(..., description="The role of the speaker, either 'user' or 'assistant'.", examples=["user"])
    content: str = Field(..., description="The text content of the message.", examples=["Tell me about the document."])


class UploadResponse(BaseModel):
    """Schema representing the successful PDF upload response."""

    filename: str = Field(
        ...,
        description="The name of the uploaded and processed PDF file.",
        examples=["sample_document.pdf"],
    )
    page_count: int = Field(
        ...,
        description="The total number of pages parsed from the PDF.",
        examples=[12],
    )
    chunk_count: int = Field(
        ...,
        description="The total number of text chunks generated and stored.",
        examples=[85],
    )
    message: str = Field(
        ...,
        description="A user-friendly status message describing the upload result.",
        examples=["PDF uploaded, parsed, and embedded successfully."],
    )
    suggested_questions: Optional[List[str]] = Field(
        default=None,
        description="Automatically generated suggested questions from the document context.",
        examples=[["What is the summary of the document?", "What is the key takeaway?"]],
    )


class QuestionRequest(BaseModel):
    """Schema representing a user's question query."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        strip_whitespace=True,
        description="The user's query or question about the PDF document(s).",
        examples=["What is the revenue for Q3 2023?"],
    )

    filename: Optional[str] = Field(
        default=None,
        description=(
            "Optional specific document filename to scope the query. "
            "If omitted, the search runs across all documents."
        ),
        examples=["financial_report.pdf"],
    )

    history: Optional[List[MessageHistoryItem]] = Field(
        default=None,
        description="The recent conversation history to provide conversational context.",
    )


class SourceChunk(BaseModel):
    """Schema representing a retrieved context source chunk from the vector database."""

    filename: str = Field(
        ...,
        description="The name of the source PDF document containing the chunk.",
        examples=["financial_report.pdf"],
    )
    page_number: int = Field(
        ...,
        description="The page number in the source PDF (1-indexed).",
        examples=[4],
    )
    chunk_text: str = Field(
        ...,
        description="The exact text snippet retrieved from the document.",
        examples=["Q3 2023 revenues grew by 15% year-over-year to $4.2B."],
    )
    similarity_score: float = Field(
        ...,
        description="The computed similarity score of the retrieved chunk.",
        examples=[0.82],
    )


class QuestionResponse(BaseModel):
    """Schema representing the assistant's answer and supporting sources."""

    answer: str = Field(
        ...,
        description="The generated answer from the language model.",
        examples=[
            "The revenue for Q3 2023 was $4.2B, showing a 15% year-over-year growth."
        ],
    )

    sources: List[SourceChunk] = Field(
        ...,
        description="The list of document text chunks used to answer the question.",
    )


class DocumentInfo(BaseModel):
    """Schema representing metadata info of a processed document."""

    filename: str = Field(
        ...,
        description="The filename of the processed document.",
        examples=["sample_document.pdf"],
    )
    page_count: int = Field(
        ...,
        description="The total number of pages in the document.",
        examples=[12],
    )
    chunk_count: int = Field(
        ...,
        description="The number of vector chunks stored for this document.",
        examples=[85],
    )


class ErrorResponse(BaseModel):
    """Schema representing an error response returned by the API."""

    error: str = Field(
        ...,
        description="A short error identifier or title.",
        examples=["NOT_FOUND"],
    )
    detail: str = Field(
        ...,
        description="A detailed description of the error cause or resolution.",
        examples=["The requested document sample.pdf does not exist."],
    )


class ChatMessage(BaseModel):
    """Schema representing a complete chat message for persistence."""

    id: str = Field(..., description="Unique identifier for the message.")
    role: str = Field(..., description="The role of the speaker, either 'user' or 'assistant'.")
    content: str = Field(..., description="The text content of the message.")
    timestamp: str = Field(..., description="The timestamp of the message.")
    sources: Optional[List[SourceChunk]] = Field(
        default=None,
        description="The list of document text chunks used to answer the question, if applicable.",
    )