"""Main application script for the AI Course Chatbot."""

import os
import sys
import argparse
from pathlib import Path
from src.pdf_loader import PDFLoader
from src.vector_store import VectorStore
from src.chatbot import RAGChatbot


def load_pdfs(pdf_paths: list, vector_store: VectorStore, embedding_model: str):
    """Load PDF files and add them to the vector store.
    
    Args:
        pdf_paths: List of paths to PDF files
        vector_store: VectorStore instance
        embedding_model: Ollama embedding model to use
    """
    print("Loading PDF files...")
    
    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"Warning: File not found: {pdf_path}")
            continue
        
        print(f"Processing: {pdf_path}")
        loader = PDFLoader(pdf_path)
        documents = loader.load()
        print(f"  Extracted {len(documents)} pages")
        
        vector_store.add_documents(documents, model=embedding_model)
        print(f"  Added to vector store")
    
    print("All PDFs loaded successfully!\n")


def chat_loop(chatbot: RAGChatbot):
    """Run the interactive chat loop.
    
    Args:
        chatbot: RAGChatbot instance
    """
    print("=" * 60)
    print("AI Course Chatbot - Interactive Mode")
    print("=" * 60)
    print("Ask questions about your documents. Type 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            question = input("You: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            print("\nThinking...\n")
            result = chatbot.chat(question)
            
            print(f"Bot: {result['answer']}\n")
            
            # Optionally show sources
            if result['sources']:
                print("Sources:")
                for source in result['sources']:
                    print(f"  - {source.get('source', 'Unknown')}, Page {source.get('page', 'Unknown')}")
                print()
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}\n")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="AI Course Chatbot - RAG chatbot with PDF support"
    )
    parser.add_argument(
        '--pdfs',
        nargs='+',
        help='Paths to PDF files to load'
    )
    parser.add_argument(
        '--data-dir',
        default='./data',
        help='Directory containing PDF files (default: ./data)'
    )
    parser.add_argument(
        '--model',
        default='llama2',
        help='Ollama model for chat (default: llama2)'
    )
    parser.add_argument(
        '--embedding-model',
        default='nomic-embed-text',
        help='Ollama model for embeddings (default: nomic-embed-text)'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear the vector store before loading new documents'
    )
    
    args = parser.parse_args()
    
    # Initialize vector store
    print("Initializing vector store...")
    vector_store = VectorStore(collection_name="course_documents")
    
    if args.clear:
        print("Clearing existing vector store...")
        vector_store.clear()
    
    # Collect PDF files
    pdf_files = []
    
    if args.pdfs:
        pdf_files.extend(args.pdfs)
    
    # Also check data directory
    data_dir = Path(args.data_dir)
    if data_dir.exists():
        pdf_files.extend([str(p) for p in data_dir.glob("*.pdf")])
    
    # Load PDFs if any are found
    if pdf_files:
        try:
            load_pdfs(pdf_files, vector_store, args.embedding_model)
        except Exception as e:
            print(f"Error loading PDFs: {str(e)}")
            sys.exit(1)
    else:
        print("No PDF files found. Please specify PDFs with --pdfs or place them in the data directory.")
        print("You can still chat if documents were previously loaded.\n")
    
    # Initialize chatbot
    print("Initializing chatbot...")
    chatbot = RAGChatbot(
        vector_store=vector_store,
        model=args.model,
        embedding_model=args.embedding_model
    )
    
    # Start chat loop
    chat_loop(chatbot)


if __name__ == "__main__":
    main()
