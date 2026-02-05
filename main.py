#!/usr/bin/env python3
"""
Main Application
Entry point for the AI RAG Chatbot application.
"""

import os
import sys
import argparse
from pdf_loader import PDFLoader
from vector_store import VectorStore
from rag_chatbot import RAGChatbot


def setup_vector_store(pdf_paths, force_reload=False):
    """
    Setup or load the vector store.
    
    Args:
        pdf_paths: List of PDF paths to load
        force_reload: Whether to force reload PDFs even if vector store exists
        
    Returns:
        VectorStore instance
    """
    vector_store = VectorStore()

    # Check if vector store already exists
    if not force_reload and os.path.exists(vector_store.persist_directory):
        print("Loading existing vector store...")
        if vector_store.load_existing():
            return vector_store

    # Load PDFs if provided or if forcing reload
    if pdf_paths:
        print("\nLoading PDF files...")
        pdf_loader = PDFLoader()
        documents = pdf_loader.load_multiple_pdfs(pdf_paths)

        if documents:
            print("\nCreating vector store...")
            vector_store.add_documents(documents)
            print("Vector store created successfully!")
        else:
            print("No documents loaded. Cannot create vector store.")
            sys.exit(1)
    else:
        print("No PDF files provided and no existing vector store found.")
        print("Please provide PDF files using --pdf argument.")
        sys.exit(1)

    return vector_store


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="AI RAG Chatbot - Chat with your PDF documents using Ollama"
    )
    parser.add_argument(
        "--pdf",
        nargs="+",
        help="Path(s) to PDF file(s) to load"
    )
    parser.add_argument(
        "--model",
        default="llama2",
        help="Ollama model to use (default: llama2)"
    )
    parser.add_argument(
        "--embedding-model",
        default="nomic-embed-text",
        help="Ollama embedding model to use (default: nomic-embed-text)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Force reload PDFs even if vector store exists"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("AI RAG Chatbot - PDF Document Q&A")
    print("=" * 60)

    # Setup vector store
    vector_store = setup_vector_store(args.pdf, args.reload)

    # Initialize chatbot
    print(f"\nInitializing chatbot with model: {args.model}")
    chatbot = RAGChatbot(vector_store, model_name=args.model)

    # Start interactive chat
    chatbot.chat()


if __name__ == "__main__":
    main()
