#!/usr/bin/env python3
"""
Main Application
Entry point for the AI RAG Chatbot application.
"""
import argparse

from ai_course_chatbot.ai_modules import VectorStore, PDFLoader

def setup_vector_store(pdf_paths: list[str]) -> VectorStore | None:
    """
    Load PDF files into a new VectorStore and return it.

    This function only handles loading the provided PDF files into a VectorStore.
    It does not try to detect or load an existing vector store on disk.

    Args:
        pdf_paths: List of PDF paths to load (required)

    Returns:
        VectorStore instance populated with the documents, or None if no documents were loaded.
    """
    if not pdf_paths:
        raise ValueError("At least one PDF path must be provided to load into the VectorStore.")

    # Create a new vector store (uses default persist_directory unless overridden by VectorStore)
    vector_store = VectorStore()

    # Load PDFs
    print("Loading PDF files...")
    pdf_loader = PDFLoader()
    documents = pdf_loader.load_multiple_pdfs(pdf_paths)

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
    parser.add_argument("--model", default="llama2", help="Ollama model to use (default: llama2)")
    parser.add_argument("--embedding-model", default="nomic-embed-text",
                        help="Ollama embedding model to use (default: nomic-embed-text)")
    parser.add_argument("--reload", action="store_true", help="Force reload PDFs even if vector store exists")

    args = parser.parse_args()

    print("=" * 60)
    print("AI RAG Chatbot - PDF Document Q&A")
    print("=" * 60)


    setup_vector_store(args.pdf)
    print("Vector store populated successfully.")


if __name__ == "__main__":
    main()
