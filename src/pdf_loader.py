"""PDF loader module for extracting text from PDF files."""

from typing import List
from pypdf import PdfReader


class PDFLoader:
    """Load and extract text from PDF files."""
    
    def __init__(self, file_path: str):
        """Initialize the PDF loader.
        
        Args:
            file_path: Path to the PDF file
        """
        self.file_path = file_path
    
    def load(self) -> List[dict]:
        """Load and extract text from the PDF file.
        
        Returns:
            List of dictionaries containing page content and metadata
        """
        documents = []
        
        try:
            reader = PdfReader(self.file_path)
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                
                if text.strip():  # Only add pages with content
                    documents.append({
                        'content': text,
                        'metadata': {
                            'source': self.file_path,
                            'page': page_num + 1
                        }
                    })
            
            return documents
        
        except Exception as e:
            raise RuntimeError(f"Error loading PDF {self.file_path}: {str(e)}")
