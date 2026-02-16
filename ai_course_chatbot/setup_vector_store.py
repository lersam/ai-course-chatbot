#!/usr/bin/env python3
"""
Main Application
Entry point for the AI RAG Chatbot application.
"""
import argparse
import os

from ai_course_chatbot.ai_modules import VectorStore, PDFLoader

def setup_vector_store(
    pdf_paths: list[str],
    *,
    embedding_model: str = "nomic-embed-text",
    ollama_model: str | None = None,
    rebuild: bool = False,
) -> VectorStore | None:
    """
    Load PDF files into a VectorStore and return it.

    By default, this function appends new documents to the existing collection
    with deduplication. Use rebuild=True to clear the collection first.

    Args:
        pdf_paths: List of PDF paths to load (required)
        embedding_model: Ollama embedding model used to generate vector representations
        ollama_model: Optional chat model name (logged for reference)
        rebuild: If True, clear the collection before loading documents

    Returns:
        VectorStore instance populated with the documents, or None if no documents were loaded.
    """
    if not pdf_paths:
        raise ValueError("At least one PDF path must be provided to load into the VectorStore.")

    print(f"Using embedding model: {embedding_model}")
    if ollama_model:
        print(f"Target chat model (for reference): {ollama_model}")

    # Create a new vector store (uses default persist_directory unless overridden by VectorStore)
    vector_store = VectorStore(embedding_model=embedding_model)

    # Load PDFs
    print("Loading PDF files...")
    pdf_loader = PDFLoader()
    documents = pdf_loader.load_and_chunk_pdfs(pdf_paths)

    if not documents:
        print("No documents were loaded from the provided PDF paths.")
        return None

    print("Adding documents to vector store...")
    vector_store.add_documents(documents)
    print("Vector store populated successfully.")

    return vector_store


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="AI RAG Chatbot - Chat with your PDF documents using Ollama")
    parser.add_argument("--pdf", nargs="+", help="Path(s) to PDF file(s) to load")
    parser.add_argument("--model", default="gemma3:4b-it-qat", help="Ollama model to use for chat (default: gemma3:4b-it-qat)")
    parser.add_argument("--embedding-model", default="nomic-embed-text",
                        help="Embedding model to use for vectorization (default: nomic-embed-text)")


    args = parser.parse_args()

    print("=" * 60)
    print("AI RAG Chatbot - PDF Document Q&A")
    print("=" * 60)


    if args.model:
        os.environ["OLLAMA_MODEL"] = args.model
        print(f"Configured OLLAMA_MODEL={args.model} for downstream chat sessions.")

    setup_vector_store(
        args.pdf,
        embedding_model=args.embedding_model,
        ollama_model=args.model,
        rebuild=args.rebuild,
    )


if __name__ == "__main__":
    main()
