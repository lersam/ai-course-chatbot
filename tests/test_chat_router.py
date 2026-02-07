"""
Tests for the chat router
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from ai_course_chatbot.routers import chat_router
from ai_course_chatbot.ai_modules import VectorStore, RAGChatbot


app = FastAPI()
app.include_router(chat_router.router)
client = TestClient(app)


def test_chat_status_not_ready():
    """Test status endpoint when vector store is not initialized"""
    # Reset the chatbot instance
    chat_router._chatbot_instance = None
    
    with patch.object(VectorStore, 'load_existing', return_value=False):
        response = client.get("/chat/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"


def test_chat_status_ready():
    """Test status endpoint when chatbot is ready"""
    # Mock chatbot
    mock_vector_store = Mock(spec=VectorStore)
    mock_vector_store.load_existing.return_value = True
    mock_vector_store.get_retriever.return_value = Mock()
    
    with patch.object(VectorStore, '__init__', return_value=None):
        with patch.object(VectorStore, 'load_existing', return_value=True):
            with patch('ai_course_chatbot.routers.chat_router.RAGChatbot') as mock_chatbot_class:
                mock_chatbot = Mock()
                mock_chatbot.model_name = "test-model"
                mock_chatbot_class.return_value = mock_chatbot
                
                # Reset and set instance
                chat_router._chatbot_instance = mock_chatbot
                
                response = client.get("/chat/status")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "ready"
                assert data["model"] == "test-model"
    
    # Clean up
    chat_router._chatbot_instance = None


def test_chat_empty_message():
    """Test chat with empty message"""
    response = client.post("/chat/", json={"message": ""})
    assert response.status_code == 400


def test_chat_successful_response():
    """Test successful chat interaction"""
    # Mock the chatbot
    mock_chatbot = Mock(spec=RAGChatbot)
    mock_chatbot.model_name = "test-model"
    mock_chatbot.ask.return_value = "This is a test response.\n\nSources:\n1. test.pdf (Page 1)"
    
    chat_router._chatbot_instance = mock_chatbot
    
    response = client.post("/chat/", json={
        "message": "What is this about?",
        "show_sources": True
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "This is a test response."
    assert "sources" in data
    assert len(data["sources"]) > 0
    
    # Clean up
    chat_router._chatbot_instance = None


def test_chat_without_sources():
    """Test chat with sources disabled"""
    mock_chatbot = Mock(spec=RAGChatbot)
    mock_chatbot.model_name = "test-model"
    mock_chatbot.ask.return_value = "This is a test response."
    
    chat_router._chatbot_instance = mock_chatbot
    
    response = client.post("/chat/", json={
        "message": "What is this about?",
        "show_sources": False
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "This is a test response."
    
    # Clean up
    chat_router._chatbot_instance = None
