"""
PDF Loader Module
Loads PDF files and splits them into chunks for vector storage.
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
import os


class PDFLoader:
    """Handles loading and processing PDF files."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the PDF loader.
        
        Args:
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def load_pdf(self, pdf_path: str) -> List:
        """
        Load a PDF file and split it into chunks.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of document chunks
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        print(f"Loaded {len(documents)} pages from {pdf_path}")
        print(f"Split into {len(chunks)} chunks")
        
        return chunks
    
    def load_multiple_pdfs(self, pdf_paths: List[str]) -> List:
        """
        Load multiple PDF files.
        
        Args:
            pdf_paths: List of paths to PDF files
            
        Returns:
            Combined list of document chunks from all PDFs
        """
        all_chunks = []
        for pdf_path in pdf_paths:
            try:
                chunks = self.load_pdf(pdf_path)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"Error loading {pdf_path}: {e}")
        
        return all_chunks
