from fastapi import FastAPI
from fastapi.testclient import TestClient
import os
from pathlib import Path

from ai_course_chatbot.routers import pdf_router


app = FastAPI()
app.include_router(pdf_router.router)
client = TestClient(app)


def test_load_pdf_download_and_overwrite(tmp_path, monkeypatch):
    # Use a temp directory for downloads
    tmp_dir = tmp_path / "downloads"
    pdf_router.DOWNLOAD_DIR = str(tmp_dir)

    async def fake_download(url: str, dest_path: str):
        # Create file content to simulate a downloaded PDF
        Path(dest_path).write_bytes(b"%PDF-1.4\n%fakepdf")

    monkeypatch.setattr(pdf_router, "download_file", fake_download)

    url = "https://example.com/test.pdf"

    # First download -> should not be marked overwritten
    resp = client.post("/pdf/download", json={"url": url})
    assert resp.status_code == 200
    j = resp.json()
    assert "path" in j
    assert j.get("overwritten") is False
    assert os.path.exists(j["path"]) is True

    # Second download -> should be marked overwritten
    resp2 = client.post("/pdf/download", json={"url": url})
    assert resp2.status_code == 200
    j2 = resp2.json()
    assert j2.get("overwritten") is True
    assert os.path.exists(j2["path"]) is True


def test_upload_pdf_save_and_overwrite(tmp_path):
    # Use a temp directory for downloads
    tmp_dir = tmp_path / "downloads"
    pdf_router.DOWNLOAD_DIR = str(tmp_dir)

    filename = "upload_test.pdf"
    files = {
        "file": (filename, b"%PDF-1.4\n%uploaded", "application/pdf")
    }

    # First upload -> saved (not overwritten)
    resp = client.post("/pdf/upload", files=files)
    assert resp.status_code == 200
    j = resp.json()
    assert j.get("overwritten") is False
    assert os.path.exists(j["path"]) is True

    # Second upload with same name -> overwritten True
    resp2 = client.post("/pdf/upload", files=files)
    assert resp2.status_code == 200
    j2 = resp2.json()
    assert j2.get("overwritten") is True
    assert os.path.exists(j2["path"]) is True


def test_upload_pdf_reject_non_pdf(tmp_path):
    tmp_dir = tmp_path / "downloads"
    pdf_router.DOWNLOAD_DIR = str(tmp_dir)

    files = {"file": ("not_a_pdf.txt", b"hello", "text/plain")}
    resp = client.post("/pdf/upload", files=files)
    assert resp.status_code == 400


def test_load_pdf_local_path_echo():
    # Local path should be echoed
    resp = client.post("/pdf/download", json={"url": "/some/local/path/doc.pdf"})
    assert resp.status_code == 200
    j = resp.json()
    assert "loaded from /some/local/path/doc.pdf" in j.get("message", "")
