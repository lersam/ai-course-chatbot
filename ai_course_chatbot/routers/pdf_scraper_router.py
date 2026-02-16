from fastapi import APIRouter, HTTPException
from starlette import status
from pydantic import BaseModel

from ai_course_chatbot.controllers import scrape_pdf_links
from ai_course_chatbot.worker import download_pdf_task

router = APIRouter(
    prefix="/pdf",
    tags=["PDF Management"]
)


class ScrapeRequest(BaseModel):
    url: str


@router.post("/scrape-and-download", 
             summary="Scrape and download PDFs", 
             description="Scrape all PDF links from a given URL and download each in a separate Celery task.",
             status_code=status.HTTP_200_OK)
async def scrape_and_download_pdfs(request: ScrapeRequest):
    """
    Scrape all PDF links from the provided URL and start a Celery task for each PDF download.
    
    The request must be a JSON object like: {"url": "https://example.com/page-with-pdfs"}.
    This endpoint will:
    1. Scrape the page for PDF links
    2. Start a separate Celery task for each PDF to download and update the vector store
    3. Return the list of PDF URLs found and their corresponding task IDs
    """
    url = request.url
    
    if not url:
        raise HTTPException(status_code=400, detail="A JSON body with a non-empty 'url' field is required")
    
    try:
        # Scrape PDF links from the URL
        pdf_links = await scrape_pdf_links(url)
        
        if not pdf_links:
            return {
                "message": f"No PDF links found at {url}",
                "pdf_count": 0,
                "pdf_links": [],
                "tasks": []
            }
        
        # Start a Celery task for each PDF
        tasks = []
        for pdf_url in pdf_links:
            task = download_pdf_task.delay(pdf_url)
            tasks.append({
                "pdf_url": pdf_url,
                "task_id": task.id
            })
        
        return {
            "message": f"Found {len(pdf_links)} PDF(s) at {url}. Started download tasks.",
            "pdf_count": len(pdf_links),
            "pdf_links": pdf_links,
            "tasks": tasks
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scrape and download PDFs from {url}: {str(e)}"
        )
