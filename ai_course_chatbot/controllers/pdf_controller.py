import os
import asyncio
import urllib.request
from typing import List
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

from ai_course_chatbot.config import DOWNLOAD_DIR
from ai_course_chatbot.utils import validate_url_safety


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


async def scrape_pdf_links(url: str) -> List[str]:
    """Scrape all PDF links from a given URL."""
    def _sync_scrape():
        try:
            # Validate URL to prevent SSRF attacks
            validate_url_safety(url)
            
            # Disable redirects to prevent bypass of SSRF protection
            response = requests.get(url, timeout=30, allow_redirects=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all anchor tags with href
            pdf_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Check if the link points to a PDF
                if href.lower().endswith('.pdf'):
                    # Convert relative URLs to absolute URLs
                    absolute_url = urljoin(url, href)
                    pdf_links.append(absolute_url)
            
            return pdf_links
        except Exception as e:
            raise Exception(f"Failed to scrape PDF links from {url}: {str(e)}")
    
    return await asyncio.to_thread(_sync_scrape)
