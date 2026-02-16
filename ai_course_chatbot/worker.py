import os
import pathlib
import urllib.request


from celery import Celery

from ai_course_chatbot.setup_vector_store import setup_vector_store
from ai_course_chatbot.config import DOWNLOAD_DIR
from ai_course_chatbot.utils import validate_url_safety


# Ensure the Celery app has a stable project name and imports this module
# so tasks defined here are registered when the worker starts.
celery = Celery("ai_course_chatbot", include=["ai_course_chatbot.worker"])

# Use SQLAlchemy transport with SQLite by default. Install `kombu-sqlalchemy` and `SQLAlchemy`.
# Broker (kombu SQLAlchemy transport) example: sqla+sqlite:///./celerydb.sqlite
celery.conf.broker_url = os.environ.get(
	"CELERY_BROKER_URL", "sqla+sqlite:///./celerydb.sqlite"
)
# Use the DB result backend with SQLite by default
celery.conf.result_backend = os.environ.get(
	"CELERY_RESULT_BACKEND", "db+sqlite:///./celery_results.sqlite"
)

# Also explicitly import this module so tasks are registered when workers start.
celery.conf.imports = ["ai_course_chatbot.worker"]

@celery.task(bind=True)
def update_vector_store(self, pdf_paths: list[str]):
    print(f"Starting vector store update for {pdf_paths}...")
    # mark task as running so status endpoints and DB reflect it
    try:
        self.update_state(state="RUNNING", meta={"pdf_paths": pdf_paths})
    except Exception:
        # best-effort: if updating state fails, continue
        pass

    vector_store = setup_vector_store(pdf_paths)
    if vector_store is not None:
        print("Vector store updated successfully.")
        self.update_state(state="SUCCESS", meta={"pdf_paths": pdf_paths})
    else:
        print("Vector store update failed or no documents were loaded.")
        self.update_state(state="FAILURE", meta={"pdf_paths": pdf_paths})


@celery.task(bind=True)
def download_pdf_task(self, pdf_url: str):
    """Download a single PDF file from URL and update vector store."""
    print(f"Starting download for {pdf_url}...")
    
    try:
        self.update_state(state="RUNNING", meta={"pdf_url": pdf_url})
    except Exception:
        pass
    
    try:
        # Validate URL to prevent SSRF attacks
        validate_url_safety(pdf_url)
        
        # Ensure download directory exists
        pathlib.Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
        
        # Extract filename from URL
        from urllib.parse import urlparse
        parsed = urlparse(pdf_url)
        filename = os.path.basename(parsed.path)
        if not filename:
            filename = f"downloaded_{self.request.id}.pdf"
        
        dest_path = os.path.join(DOWNLOAD_DIR, filename)
        
        # Download the PDF using requests (respects SSRF protections, no redirects)
        import requests
        response = requests.get(pdf_url, timeout=30, allow_redirects=False)
        response.raise_for_status()
        
        # Write the content to file
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded PDF to {dest_path}")
        
        # Update vector store with the downloaded PDF
        vector_store = setup_vector_store([dest_path])
        
        if vector_store is not None:
            print(f"Vector store updated successfully with {dest_path}")
            self.update_state(state="SUCCESS", meta={"pdf_url": pdf_url, "dest_path": dest_path})
            return {"status": "success", "pdf_url": pdf_url, "dest_path": dest_path}
        else:
            print(f"Vector store update failed for {dest_path}")
            self.update_state(state="FAILURE", meta={"pdf_url": pdf_url, "error": "Vector store update failed"})
            return {"status": "failure", "pdf_url": pdf_url, "error": "Vector store update failed"}
            
    except Exception as e:
        error_msg = f"Failed to download PDF from {pdf_url}: {str(e)}"
        print(error_msg)
        self.update_state(state="FAILURE", meta={"pdf_url": pdf_url, "error": error_msg})
        return {"status": "failure", "pdf_url": pdf_url, "error": error_msg}