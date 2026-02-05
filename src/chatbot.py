"""RAG Chatbot module for question-answering over documents."""

import ollama
from typing import List, Dict
from src.vector_store import VectorStore


class RAGChatbot:
    """RAG-based chatbot for answering questions using document context."""
    
    def __init__(
        self, 
        vector_store: VectorStore,
        model: str = "llama2",
        embedding_model: str = "nomic-embed-text"
    ):
        """Initialize the RAG chatbot.
        
        Args:
            vector_store: VectorStore instance for retrieving context
            model: Ollama model to use for chat
            embedding_model: Ollama model to use for embeddings
        """
        self.vector_store = vector_store
        self.model = model
        self.embedding_model = embedding_model
    
    def _format_context(self, documents: List[Dict]) -> str:
        """Format retrieved documents into context string.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        context_parts = []
        for doc in documents:
            metadata = doc.get('metadata', {})
            content = doc.get('content', '')
            source = metadata.get('source', 'Unknown')
            page = metadata.get('page', 'Unknown')
            
            context_parts.append(f"[Source: {source}, Page: {page}]\n{content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def chat(self, question: str, n_context: int = 3) -> Dict[str, str]:
        """Answer a question using RAG.
        
        Args:
            question: User question
            n_context: Number of context documents to retrieve
            
        Returns:
            Dictionary with 'answer' and 'context' keys
        """
        # Retrieve relevant documents
        relevant_docs = self.vector_store.query(
            query_text=question,
            n_results=n_context,
            model=self.embedding_model
        )
        
        # Format context
        context = self._format_context(relevant_docs)
        
        # Create prompt
        prompt = f"""You are a helpful assistant. Answer the question based on the context provided below. If you cannot answer the question based on the context, say so.

Context:
{context}

Question: {question}

Answer:"""
        
        # Generate response using Ollama
        try:
            response = ollama.generate(model=self.model, prompt=prompt)
            answer = response['response']
        except Exception as e:
            answer = f"Error generating response: {str(e)}"
        
        return {
            'answer': answer,
            'context': context,
            'sources': [doc.get('metadata', {}) for doc in relevant_docs]
        }
