"""Vector store module for managing embeddings with ChromaDB."""

import chromadb
from chromadb.config import Settings
from typing import List, Dict
import ollama


class VectorStore:
    """Vector store for managing document embeddings."""
    
    def __init__(self, collection_name: str = "documents", persist_directory: str = "./chroma_db"):
        """Initialize the vector store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the database
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def _generate_embedding(self, text: str, model: str = "nomic-embed-text") -> List[float]:
        """Generate embedding for text using Ollama.
        
        Args:
            text: Text to embed
            model: Ollama model to use for embeddings
            
        Returns:
            List of embedding values
        """
        try:
            response = ollama.embeddings(model=model, prompt=text)
            return response['embedding']
        except Exception as e:
            raise RuntimeError(f"Error generating embedding: {str(e)}")
    
    def add_documents(self, documents: List[Dict], model: str = "nomic-embed-text"):
        """Add documents to the vector store.
        
        Args:
            documents: List of documents with 'content' and 'metadata' keys
            model: Ollama model to use for embeddings
        """
        for i, doc in enumerate(documents):
            content = doc['content']
            metadata = doc['metadata']
            
            # Generate embedding
            embedding = self._generate_embedding(content, model)
            
            # Add to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[f"doc_{i}_{metadata.get('page', 0)}"]
            )
    
    def query(self, query_text: str, n_results: int = 3, model: str = "nomic-embed-text") -> List[Dict]:
        """Query the vector store for similar documents.
        
        Args:
            query_text: Query text
            n_results: Number of results to return
            model: Ollama model to use for embeddings
            
        Returns:
            List of relevant documents with metadata
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query_text, model)
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        documents = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                documents.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
        
        return documents
    
    def clear(self):
        """Clear all documents from the collection."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
