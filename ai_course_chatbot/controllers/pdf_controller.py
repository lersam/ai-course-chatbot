import os
import tempfile
import asyncio
import urllib.request
import tempfile

# Use the system default temporary directory
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "ai-course-chatbot", "downloads")


async def download_file(url: str, dest_path: str):
    """Download a file using urllib in a thread to avoid blocking the event loop."""
    def _sync_download():
        urllib.request.urlretrieve(url, dest_path)
    await asyncio.to_thread(_sync_download)


async def save_upload_file_bytes(data: bytes, dest_path: str):
    """Write bytes to disk in a thread to avoid blocking."""
    def _sync_write(d, p):
        with open(p, "wb") as f:
            f.write(d)
    await asyncio.to_thread(_sync_write, data, dest_path)
