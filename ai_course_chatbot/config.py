"""
Centralized configuration for the AI Course Chatbot.

All settings are loaded from environment variables or .env file.
"""
import os
import tempfile
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    ollama_model: str = "gemma3:4b-it-qat"
    ollama_base_url: str = "http://localhost:11434"
    llm_temperature: float = 0.15
    llm_num_ctx: int = 8192

    # Embeddings
    embedding_model: str = "nomic-embed-text"

    # ChromaDB
    chroma_collection: str = "pdf_documents"
    chroma_persist_dir: str = "./chroma_db"

    # Retrieval
    retriever_k: int = 2

    # Chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Celery
    celery_broker_url: str = "sqla+sqlite:///./celerydb.sqlite"
    celery_result_backend: str = "db+sqlite:///./celery_results.sqlite"

    # Server
    download_dir: str = os.path.join(
        tempfile.gettempdir(), "ai-course-chatbot", "downloads"
    )
    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"

    # Cache
    chat_cache_maxsize: int = 128
    chat_cache_ttl: int = 300  # seconds

    # Chat history
    chat_history_path: str = "./chat_history.json"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton)."""
    return Settings()


# Backwards-compatible alias so existing `from config import DOWNLOAD_DIR` still works.
DOWNLOAD_DIR = get_settings().download_dir
