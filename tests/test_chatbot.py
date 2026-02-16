"""
Simple tests for the AI RAG Chatbot components.
Note: These are basic smoke tests. Full testing requires actual PDFs and Ollama running.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from ai_course_chatbot.ai_modules import PDFLoader, VectorStore, RAGChatbot

class TestPDFLoader(unittest.TestCase):
    """Test PDF loader functionality."""
    
    def test_pdf_loader_initialization(self):
        """Test that PDF loader initializes correctly."""

        loader = PDFLoader(chunk_size=500, chunk_overlap=50)
        self.assertEqual(loader.chunk_size, 500)
        self.assertEqual(loader.chunk_overlap, 50)
        self.assertIsNotNone(loader.text_splitter)
    
    def test_pdf_loader_file_not_found(self):
        """Test that PDF loader raises error for non-existent file."""

        loader = PDFLoader()
        with self.assertRaises(FileNotFoundError):
            loader.load_pdf("nonexistent_file.pdf")


class TestVectorStore(unittest.TestCase):
    """Test vector store functionality."""
    
    def test_vector_store_initialization(self):
        """Test that vector store initializes correctly."""

        with tempfile.TemporaryDirectory() as temp_dir:
            store = VectorStore(
                collection_name="test_collection",
                persist_directory=temp_dir
            )
            self.assertEqual(store.collection_name, "test_collection")
            self.assertEqual(store.persist_directory, temp_dir)
            self.assertTrue(os.path.exists(temp_dir))
    
    def test_vector_store_empty_documents(self):
        """Test adding empty documents list."""

        with tempfile.TemporaryDirectory() as temp_dir:
            store = VectorStore(persist_directory=temp_dir)
            # Should handle empty list gracefully
            store.add_documents([])


class TestRAGChatbot(unittest.TestCase):
    """Test RAG chatbot functionality."""
    
    @patch('ai_course_chatbot.ai_modules.rag_chatbot.Ollama')
    @patch('ai_course_chatbot.ai_modules.rag_chatbot.RetrievalQA')
    def test_chatbot_initialization(self, mock_qa, mock_ollama):
        """Test that chatbot initializes correctly."""

        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock vector store
            mock_vector_store = Mock(spec=VectorStore)
            mock_vector_store.get_retriever.return_value = Mock()
            
            # Initialize chatbot
            chatbot = RAGChatbot(
                vector_store=mock_vector_store,
                model_name="gemma3:4b"
            )
            
            self.assertEqual(chatbot.model_name, "gemma3:4b")
            self.assertIsNotNone(chatbot.prompt_template)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    print("Running AI RAG Chatbot Tests")
    print("=" * 60)
    print("Note: These are basic unit tests.")
    print("Full integration tests require Ollama running and actual PDF files.")
    print("=" * 60)
    run_tests()
