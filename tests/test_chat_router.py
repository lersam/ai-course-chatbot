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
    """Chat status reports not_ready when the collection is empty."""
    chat_router._chatbot_instance = None

    mock_vector_store = Mock(spec=VectorStore)
    mock_vector_store.has_documents.return_value = False

    with patch(
        "ai_course_chatbot.routers.chat_router.VectorStore",
        return_value=mock_vector_store
    ):
        response = client.get("/chat/status")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_ready"
    assert "Vector store is empty" in data["message"]


def test_chat_status_ready():
    """Chat status reports ready when chatbot initializes successfully."""
    chat_router._chatbot_instance = None

    mock_vector_store = Mock(spec=VectorStore)
    mock_vector_store.has_documents.return_value = True
    mock_chatbot = Mock(spec=RAGChatbot)
    mock_chatbot.model_name = "test-model"

    with patch(
        "ai_course_chatbot.routers.chat_router.VectorStore",
        return_value=mock_vector_store
    ):
        with patch(
            "ai_course_chatbot.routers.chat_router.RAGChatbot",
            return_value=mock_chatbot
        ):
            response = client.get("/chat/status")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["model"] == "test-model"

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
