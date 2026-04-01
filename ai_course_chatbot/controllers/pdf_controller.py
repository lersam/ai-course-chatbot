"""Controllers for PDF download, upload, and link scraping."""
import logging
from typing import List
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ai_course_chatbot.utils import validate_url_safety

logger = logging.getLogger(__name__)

# Reusable timeout for external HTTP requests.
_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def download_file(url: str, dest_path: str) -> None:
    """Download a file using httpx async streaming."""
    async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=False) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
    logger.info("Downloaded %s → %s", url, dest_path)


async def save_upload_file_bytes(data: bytes, dest_path: str) -> None:
    """Write raw bytes to disk in a background thread."""
    import asyncio

    def _sync_write(d: bytes, p: str) -> None:
        with open(p, "wb") as f:
            f.write(d)

    await asyncio.to_thread(_sync_write, data, dest_path)


async def scrape_pdf_links(url: str) -> List[str]:
    """Scrape all PDF links from a given URL."""
    validate_url_safety(url)

    async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=False) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    pdf_links: list[str] = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.lower().endswith(".pdf"):
            pdf_links.append(urljoin(url, href))

    logger.info("Found %d PDF links on %s", len(pdf_links), url)
    return pdf_links
