"""
Tests for the PDF scraper router
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from ai_course_chatbot.routers import pdf_scraper_router


app = FastAPI()
app.include_router(pdf_scraper_router.router)
client = TestClient(app)


def test_scrape_and_download_empty_url():
    """Test scrape-and-download with empty URL"""
    response = client.post("/pdf/scrape-and-download", json={"url": ""})
    assert response.status_code == 400


def test_scrape_and_download_no_pdfs_found():
    """Test scrape-and-download when no PDFs are found"""
    with patch(
        "ai_course_chatbot.routers.pdf_scraper_router.scrape_pdf_links",
        new_callable=AsyncMock,
        return_value=[]
    ):
        response = client.post(
            "/pdf/scrape-and-download",
            json={"url": "https://example.com/page"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["pdf_count"] == 0
    assert len(data["pdf_links"]) == 0
    assert len(data["tasks"]) == 0


def test_scrape_and_download_success():
    """Test successful scrape-and-download with multiple PDFs"""
    mock_pdf_links = [
        "https://example.com/doc1.pdf",
        "https://example.com/doc2.pdf"
    ]
    
    mock_task = Mock()
    mock_task.id = "test-task-id-123"
    
    with patch(
        "ai_course_chatbot.routers.pdf_scraper_router.scrape_pdf_links",
        new_callable=AsyncMock,
        return_value=mock_pdf_links
    ):
        with patch(
            "ai_course_chatbot.routers.pdf_scraper_router.download_pdf_task.delay",
            return_value=mock_task
        ):
            response = client.post(
                "/pdf/scrape-and-download",
                json={"url": "https://example.com/page"}
            )
    
    assert response.status_code == 200
    data = response.json()
    assert data["pdf_count"] == 2
    assert len(data["pdf_links"]) == 2
    assert len(data["tasks"]) == 2
    assert all("task_id" in task for task in data["tasks"])
    assert all("pdf_url" in task for task in data["tasks"])


def test_scrape_and_download_scraping_error():
    """Test scrape-and-download when scraping fails"""
    with patch(
        "ai_course_chatbot.routers.pdf_scraper_router.scrape_pdf_links",
        new_callable=AsyncMock,
        side_effect=Exception("Failed to connect")
    ):
        response = client.post(
            "/pdf/scrape-and-download",
            json={"url": "https://example.com/page"}
        )
    
    assert response.status_code == 500
    assert "Failed to scrape" in response.json()["detail"]
