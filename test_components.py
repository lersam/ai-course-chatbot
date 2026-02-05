#!/usr/bin/env python3
"""Test script to verify RAG chatbot components."""

import sys
import os
from src.pdf_loader import PDFLoader
from src.vector_store import VectorStore


def test_pdf_loader():
    """Test PDF loading functionality."""
    print("=" * 60)
    print("Testing PDF Loader")
    print("=" * 60)
    
    try:
        loader = PDFLoader('data/sample_course.pdf')
        documents = loader.load()
        
        assert len(documents) > 0, "No documents loaded"
        assert 'content' in documents[0], "Document missing content"
        assert 'metadata' in documents[0], "Document missing metadata"
        
        print(f"✓ Loaded {len(documents)} pages successfully")
        print(f"✓ First page has {len(documents[0]['content'])} characters")
        print(f"✓ Metadata structure verified")
        
        return documents
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)


def test_vector_store():
    """Test vector store initialization."""
    print("\n" + "=" * 60)
    print("Testing Vector Store")
    print("=" * 60)
    
    try:
        # Initialize vector store
        vector_store = VectorStore(
            collection_name='test_collection',
            persist_directory='./test_chroma'
        )
        
        print("✓ Vector store initialized successfully")
        print(f"✓ Collection: {vector_store.collection_name}")
        print(f"✓ Persist directory: {vector_store.persist_directory}")
        
        # Clean up
        vector_store.clear()
        print("✓ Vector store cleared successfully")
        
        return True
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)


def test_integration():
    """Test basic integration without Ollama."""
    print("\n" + "=" * 60)
    print("Testing Integration (without Ollama)")
    print("=" * 60)
    
    try:
        # Load PDF
        loader = PDFLoader('data/sample_course.pdf')
        documents = loader.load()
        print(f"✓ Loaded {len(documents)} pages from PDF")
        
        # Initialize vector store
        vector_store = VectorStore(
            collection_name='test_integration',
            persist_directory='./test_chroma'
        )
        print("✓ Vector store initialized")
        
        # Note: Cannot test embedding/querying without Ollama running
        print("⚠ Skipping embedding tests (requires Ollama)")
        
        # Clean up
        vector_store.clear()
        print("✓ Integration test completed")
        
        return True
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)


def main():
    """Run all tests."""
    print("\nRAG Chatbot Component Tests")
    print("=" * 60)
    
    # Test individual components
    documents = test_pdf_loader()
    test_vector_store()
    test_integration()
    
    # Clean up test artifacts
    if os.path.exists('./test_chroma'):
        import shutil
        shutil.rmtree('./test_chroma')
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    print("\nNote: To fully test the chatbot, you need:")
    print("1. Ollama installed and running")
    print("2. Required models pulled:")
    print("   - ollama pull llama2")
    print("   - ollama pull nomic-embed-text")
    print("3. Run: python main.py")


if __name__ == "__main__":
    main()
