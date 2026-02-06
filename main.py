#!/usr/bin/env python3
"""
Main Application
Entry point for the AI RAG Chatbot application.
"""
import argparse

from ai_course_chatbot.ai_modules import RAGChatbot, setup_vector_store


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

    # Setup vector store
    vector_store = setup_vector_store(args.pdf, args.reload)

    # Initialize chatbot
    print(f"\nInitializing chatbot with model: {args.model}")
    chatbot = RAGChatbot(vector_store, model_name=args.model)

    # Start interactive chat
    chatbot.chat()


if __name__ == "__main__":
    main()
