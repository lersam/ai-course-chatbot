import os

from vector_store import VectorStore
from .pdf_loader import PDFLoader

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
        print("Loading PDF files...")
        pdf_loader = PDFLoader()
        documents = pdf_loader.load_multiple_pdfs(pdf_paths)

        if documents:
            print("Creating vector store...")
            vector_store.add_documents(documents)
            print("Vector store created successfully!")
        else:
            print("No documents loaded. Cannot create vector store.")
            return None
    else:
        print("No PDF files provided and no existing vector store found.")
        print("Please provide PDF files using --pdf argument.")
        return None

    return vector_store
