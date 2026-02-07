import os
import pathlib

from fastapi import APIRouter, HTTPException, UploadFile, File
from urllib.parse import urlparse

from ai_course_chatbot.models.pdf_request import PDFRequest
from ai_course_chatbot.worker import update_vector_store
from ai_course_chatbot.controllers import download_file, save_upload_file_bytes, DOWNLOAD_DIR

router = APIRouter(
    prefix="/pdf",
    tags=["PDF Management"]
)


@router.post("/load", summary="Download PDF document", description="Download a PDF from a URL and save it into the temp downloads directory.")
async def load_pdf(request: PDFRequest):
    """Load a PDF from a local path or download it from a URL into the downloads directory.

    The request must be a JSON object like: {"url": "https://example.com/file.pdf"}.
    If the `url` is an http(s) URL, the PDF will be saved into the system temp directory under
    `.../ai-course-chatbot/downloads/`. The endpoint ensures the download directory exists
    and returns the saved path. For non-HTTP paths, the endpoint currently just echoes the path (no file validation).
    """
    url = request.url

    if not url:
        raise HTTPException(status_code=400, detail="A JSON body with a non-empty 'url' field is required")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        # Non-HTTP input: assume local path or other scheme
        return {"message": f"PDF loaded from {url}"}

    # Ensure download directory exists
    pathlib.Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # Derive a filename from the URL path
    filename = os.path.basename(parsed.path)
    if not filename:
        raise HTTPException(status_code=400, detail="URL must have a valid filename in the path")

    # Overwrite existing files if present (user requested behavior)
    dest_path = os.path.join(DOWNLOAD_DIR, filename)
    existed = os.path.exists(dest_path)

    try:
        await download_file(url, dest_path)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to download file: {e}")

    task = update_vector_store.delay([dest_path])
    return {
        "message": ("PDF downloaded and overwritten at" if existed else "PDF downloaded and saved to") + f" {dest_path}", 
        "path": dest_path,
        "overwritten": existed,
        "vector_store_update_task_id": task.id
        }


@router.post("/upload", summary="Upload a PDF file", description="Upload a PDF via multipart/form-data and save it into the temp downloads directory.")
async def upload_pdf(file: UploadFile = File(...)):
    """Accept a multipart file upload and save it into the system temp downloads directory.

    Returns the path where the file was saved. The endpoint does minimal validation: it prefers
    files with a .pdf extension or content type 'application/pdf'.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Optionally check content type or filename extension
    filename = file.filename
    content_type = file.content_type or ""
    if not (filename.lower().endswith(".pdf") or content_type == "application/pdf"):
        # accept but warn; alternatively we could reject non-pdf
        # For now, reject to be strict
        raise HTTPException(status_code=400, detail="Uploaded file does not appear to be a PDF")

    # Ensure download directory exists
    pathlib.Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # Overwrite existing files if present (user requested behavior)
    dest_path = os.path.join(DOWNLOAD_DIR, filename)
    existed = os.path.exists(dest_path)

    try:
        data = await file.read()
        await save_upload_file_bytes(data, dest_path)
        await file.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    task = update_vector_store.delay([dest_path])
    return {
        "message": 
            ("Uploaded PDF overwritten at" if existed else "Uploaded PDF saved to") + f" {dest_path}",
            "path": dest_path,
            "overwritten": existed,
            "vector_store_update_task_id": task.id
            }
