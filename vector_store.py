"""
Vector Store Module
Manages document embeddings and vector storage using ChromaDB.
"""

import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from typing import List, Optional
import os


class VectorStore:
    """Manages vector storage for document embeddings."""
    
    def __init__(self, collection_name: str = "pdf_documents", 
                 persist_directory: str = "./chroma_db",
                 embedding_model: str = "nomic-embed-text"):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the collection in ChromaDB
            persist_directory: Directory to persist the database
            embedding_model: Ollama embedding model to use
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        
        # Create persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize Ollama embeddings
        self.embeddings = OllamaEmbeddings(model=embedding_model)
        
        # Initialize ChromaDB vector store
        self.vectorstore = None
    
    def add_documents(self, documents: List) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document chunks to add
        """
        if not documents:
            print("Warning: Empty document list provided, no documents will be added")
            return
        
        if self.vectorstore is None:
            # Create new vector store
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=self.collection_name,
                persist_directory=self.persist_directory
            )
        else:
            # Add to existing vector store
            self.vectorstore.add_documents(documents)
        
        print(f"Added {len(documents)} documents to vector store")
    
    def load_existing(self) -> bool:
        """
        Load an existing vector store from disk.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            print("Loaded existing vector store")
            return True
        except Exception as e:
            print(f"Vector store does not exist yet or failed to load: {e}")
            return False
    
    def similarity_search(self, query: str, k: int = 4) -> List:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        if self.vectorstore is None:
            print("Warning: Vector store not initialized. Please load documents first.")
            return []
        
        results = self.vectorstore.similarity_search(query, k=k)
        return results
    
    def get_retriever(self, k: int = 4):
        """
        Get a retriever for the vector store.
        
        Args:
            k: Number of documents to retrieve
            
        Returns:
            Retriever object
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Please load documents first using add_documents() or load_existing().")
        
        return self.vectorstore.as_retriever(search_kwargs={"k": k})
