"""Configuration module for the Smart PDF Assistant.

This module defines the Settings class which loads and validates configuration 
parameters from environment variables and an optional .env file.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define project root directory (three levels up from backend/app/config.py)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Explicitly load .env file from root directory if it exists
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings(BaseSettings):
    """Application settings and configuration manager.
    
    Loads configuration parameters from environment variables or a .env file,
    performs validations, and converts string paths to resolved pathlib.Path objects.
    """

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Groq Configuration ---
    GROQ_API_KEY: str = Field(
        default="",
        description=(
            "The API key for accessing Groq Cloud services. Required for "
            "LLM-based generation and chat completions."
        ),
    )
    GROQ_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description=(
            "The specific Groq LLM model to use for generating answers to user "
            "queries (e.g., llama-3.3-70b-versatile)."
        ),
    )

    # --- Storage Configuration ---
    UPLOAD_FOLDER: Path = Field(
        default=ROOT_DIR / "data" / "uploads",
        description="Directory path where uploaded PDF documents are stored.",
    )
    CHROMA_DB_PATH: Path = Field(
        default=ROOT_DIR / "data" / "chroma_db",
        description="Directory path where the Chroma vector database stores its index files.",
    )

    # --- Embeddings Configuration ---
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description=(
            "The name/identifier of the pre-trained embedding model used to "
            "vectorize document chunks (e.g., HuggingFace model hub ID)."
        ),
    )

    # --- Chunking Configuration ---
    CHUNK_SIZE: int = Field(
        default=500,
        description=(
            "The target character length for each text chunk when splitting "
            "parsed PDF documents."
        ),
    )
    CHUNK_OVERLAP: int = Field(
        default=50,
        description=(
            "The number of overlapping characters between consecutive chunks to "
            "maintain context across splits."
        ),
    )

    # --- Retrieval Configuration ---
    TOP_K_RESULTS: int = Field(
        default=5,
        description=(
            "The maximum number of relevant document chunks to retrieve from the "
            "vector store for a given user query."
        ),
    )
    SIMILARITY_THRESHOLD: float = Field(
        default=0.35,
        description=(
            "The minimum similarity score threshold (0.0 to 1.0) required for a "
            "retrieved chunk to be considered relevant."
        ),
    )

    # --- Logging Configuration ---
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Minimum severity level for log messages (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    LOG_FILE_PATH: Path = Field(
        default=ROOT_DIR / "backend" / "app" / "logs" / "app.log",
        description="Path to the output log file.",
    )

    @field_validator("UPLOAD_FOLDER", "CHROMA_DB_PATH", "LOG_FILE_PATH", mode="before")
    @classmethod
    def resolve_relative_paths(cls, v: str | Path) -> Path:
        """Resolves relative paths to absolute paths against the project root.
        
        Args:
            v: The path value (string or Path object).
            
        Returns:
            An absolute Path object resolved against the root directory.
        """
        path = Path(v)
        if not path.is_absolute():
            path = (ROOT_DIR / path).resolve()
        return path

    @model_validator(mode="after")
    def create_directories_and_validate(self) -> "Settings":
        """Post-initialization validation and directory setup.
        
        - Ensures UPLOAD_FOLDER and CHROMA_DB_PATH directories are created.
        - Warns if GROQ_API_KEY is not defined.
        
        Returns:
            The initialized settings instance.
        """
        # Create storage directories automatically
        self.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        self.CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
        self.LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Warn at load time if Groq API Key is not set
        if not self.GROQ_API_KEY or self.GROQ_API_KEY.strip() == "":
            print(
                "WARNING: GROQ_API_KEY is not set. Groq LLM integration will be disabled "
                "until this key is provided.",
                file=sys.stderr,
            )

        return self

    def validate_groq_key(self) -> None:
        """Validates that the GROQ_API_KEY is present and not empty.
        
        Raises:
            ValueError: If GROQ_API_KEY is not defined or is empty.
        """
        if not self.GROQ_API_KEY or self.GROQ_API_KEY.strip() == "":
            raise ValueError(
                "GROQ_API_KEY environment variable is missing or empty. "
                "Please configure it in your .env file or environment variables."
            )


# Instantiate settings as a singleton
settings = Settings()
