import logging
import os
import pathlib
from urllib.parse import urlparse

import requests
from celery import Celery

from ai_course_chatbot.config import get_settings, DOWNLOAD_DIR
from ai_course_chatbot.setup_vector_store import setup_vector_store
from ai_course_chatbot.utils import validate_url_safety

logger = logging.getLogger(__name__)

settings = get_settings()

# Ensure the Celery app has a stable project name and imports this module
# so tasks defined here are registered when the worker starts.
celery = Celery("ai_course_chatbot", include=["ai_course_chatbot.worker"])

celery.conf.broker_url = settings.celery_broker_url
celery.conf.result_backend = settings.celery_result_backend
celery.conf.imports = ["ai_course_chatbot.worker"]


@celery.task(bind=True)
def update_vector_store(self, pdf_paths: list[str]):
    logger.info("Starting vector store update for %s", pdf_paths)
    try:
        self.update_state(state="RUNNING", meta={"pdf_paths": pdf_paths})
    except Exception:
        pass

    vector_store = setup_vector_store(pdf_paths)
    if vector_store is not None:
        logger.info("Vector store updated successfully.")
        self.update_state(state="SUCCESS", meta={"pdf_paths": pdf_paths})
    else:
        logger.warning("Vector store update failed or no documents were loaded.")
        self.update_state(state="FAILURE", meta={"pdf_paths": pdf_paths})


@celery.task(bind=True)
def download_pdf_task(self, pdf_url: str):
    """Download a single PDF file from URL and update vector store."""
    logger.info("Starting download for %s", pdf_url)

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
        parsed = urlparse(pdf_url)
        filename = os.path.basename(parsed.path)
        if not filename:
            filename = f"downloaded_{self.request.id}.pdf"

        dest_path = os.path.join(DOWNLOAD_DIR, filename)

        # Download the PDF with streaming to avoid loading entire file into memory
        response = requests.get(pdf_url, timeout=30, allow_redirects=False, stream=True)
        response.raise_for_status()

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info("Downloaded PDF to %s", dest_path)

        # Update vector store with the downloaded PDF
        vector_store = setup_vector_store([dest_path])

        if vector_store is not None:
            logger.info("Vector store updated successfully with %s", dest_path)
            self.update_state(state="SUCCESS", meta={"pdf_url": pdf_url, "dest_path": dest_path})
            return {"status": "success", "pdf_url": pdf_url, "dest_path": dest_path}
        else:
            logger.warning("Vector store update failed for %s", dest_path)
            self.update_state(state="FAILURE", meta={"pdf_url": pdf_url, "error": "Vector store update failed"})
            return {"status": "failure", "pdf_url": pdf_url, "error": "Vector store update failed"}

    except Exception as e:
        error_msg = f"Failed to download PDF from {pdf_url}: {str(e)}"
        logger.error(error_msg)
        self.update_state(state="FAILURE", meta={"pdf_url": pdf_url, "error": error_msg})
        return {"status": "failure", "pdf_url": pdf_url, "error": error_msg}
