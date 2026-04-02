#!/usr/bin/env python3
"""
Main Application
Entry point for the AI RAG Chatbot application.
"""
import argparse
import logging
import os

from ai_course_chatbot.ai_modules import VectorStore, PDFLoader
from ai_course_chatbot.config import get_settings

logger = logging.getLogger(__name__)


def setup_vector_store(
    pdf_paths: list[str],
    *,
    embedding_model: str = "nomic-embed-text",
    ollama_model: str | None = None,
    rebuild: bool = False,
    normalize_lower: bool = False,
    default_lang: str = "en",
) -> VectorStore | None:
    if not pdf_paths:
        raise ValueError("At least one PDF path must be provided to load into the VectorStore.")

    logger.info("Using embedding model: %s", embedding_model)
    if ollama_model:
        logger.info("Target chat model (for reference): %s", ollama_model)

    vector_store = VectorStore(embedding_model=embedding_model,
                               normalize_lower=normalize_lower,
                               default_lang=default_lang)

    logger.info("Loading PDF files...")
    pdf_loader = PDFLoader()
    documents = pdf_loader.load_and_chunk_pdfs(pdf_paths)

    if not documents:
        logger.warning("No documents were loaded from the provided PDF paths.")
        return None

    logger.info("Adding documents to vector store...")
    vector_store.add_documents(documents)
    logger.info("Vector store populated successfully.")

    return vector_store


def main():
    settings = get_settings()
    parser = argparse.ArgumentParser(description="AI RAG Chatbot - Chat with your PDF documents using Ollama")
    parser.add_argument("--pdf", nargs="+", help="Path(s) to PDF file(s) to load")
    parser.add_argument("--model", default=settings.ollama_model, help="Ollama model to use for chat")
    parser.add_argument("--embedding-model", default=settings.embedding_model, help="Embedding model")
    parser.add_argument("--embedding-lower", action="store_true", help="Lowercase text before embedding")
    parser.add_argument("--lang", default="en", help="Default language tag")
    parser.add_argument("--rebuild", action="store_true", help="Clear collection before loading")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    logger.info("=" * 60)
    logger.info("AI RAG Chatbot - PDF Document Q&A")
    logger.info("=" * 60)

    if args.model:
        os.environ["OLLAMA_MODEL"] = args.model
        logger.info("Configured OLLAMA_MODEL=%s", args.model)

    setup_vector_store(
        args.pdf,
        embedding_model=args.embedding_model,
        ollama_model=args.model,
        rebuild=args.rebuild,
        normalize_lower=args.embedding_lower,
        default_lang=args.lang,
    )


if __name__ == "__main__":
    main()
