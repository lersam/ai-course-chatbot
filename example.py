#!/usr/bin/env python3
"""
Example usage script for the AI RAG Chatbot.
This script demonstrates how to use the chatbot programmatically.
"""

from ai_course_chatbot.ai_modules import PDFLoader, VectorStore, RAGChatbot


def example_usage():
    """Example of using the chatbot programmatically."""

    # Initialize components
    print("Initializing RAG Chatbot components...")

    # 1. Load PDFs
    pdf_loader = PDFLoader(chunk_size=1000, chunk_overlap=200)
    pdf_files = ["example.pdf"]  # Add your PDF files here

    # Note: For this example, we'll demonstrate with the API
    # In practice, you would provide actual PDF files

    # 2. Setup vector store
    vector_store = VectorStore(
        collection_name="example_collection",
        persist_directory="./example_chroma_db"
    )

    # 3. Ingest PDFs into the vector store
    print("Loading PDFs...")
    documents = pdf_loader.load_and_chunk_pdfs(pdf_files)
    if documents:
        vector_store.add_documents(documents)
    else:
        print("No documents produced by loader; vector store left unchanged.")

    # 4. Initialize chatbot
    chatbot = RAGChatbot(
        vector_store=vector_store,
        model_name="llama2",
        temperature=0.7
    )

    # 5. Ask questions programmatically
    questions = [
        "What is the main topic of the document?",
        "Can you summarize the key points?",
        "What are the conclusions?"
    ]

    for question in questions:
        print(f"\nQuestion: {question}")
        answer = chatbot.ask(question, show_sources=True)
        print(f"Answer: {answer}")
        print("-" * 60)


if __name__ == "__main__":
    # For interactive mode, use main.py instead
    print("This is an example script showing programmatic usage.")
    print("For interactive chat, run: python main.py --pdf your_file.pdf")
    print("\nExample API usage:")
    print("-" * 60)

    # Uncomment to run example (requires actual PDF files)
    # example_usage()
