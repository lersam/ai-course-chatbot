"""
PDF Loader Module
Loads PDF files and splits them into chunks for vector storage.
"""

import logging
import os
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ai_course_chatbot.config import get_settings

logger = logging.getLogger(__name__)


class PDFLoader:
    """Handles loading and processing PDF files."""

    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        settings = get_settings()
        self.chunk_size = chunk_size if chunk_size is not None else settings.chunk_size
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )

    def load_pdf(self, pdf_path: str) -> List:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)

        logger.info("Loaded %d pages from %s", len(documents), pdf_path)
        logger.info("Split into %d chunks", len(chunks))

        return chunks

    def load_and_chunk_pdfs(self, pdf_paths: List[str]) -> List:
        all_chunks = []
        for pdf_path in pdf_paths:
            try:
                chunks = self.load_pdf(pdf_path)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error("Error loading %s: %s", pdf_path, e)

        return all_chunks
