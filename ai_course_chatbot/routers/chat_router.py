"""
Chat router for AI RAG Chatbot
Provides endpoints for chatting with the chatbot using RAGChatbot and VectorStore
"""
import os
from fastapi import APIRouter, HTTPException
from starlette import status

from ai_course_chatbot.models.chat_request import ChatRequest, ChatResponse
from ai_course_chatbot.ai_modules import VectorStore, RAGChatbot

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

# Global chatbot instance (will be initialized on first request)
_chatbot_instance = None


def get_chatbot() -> RAGChatbot:
    """
    Get or create the chatbot instance.
    Uses the existing vector store if available.
    """
    global _chatbot_instance
    
    if _chatbot_instance is None:
        # Initialize vector store
        vector_store = VectorStore(
            collection_name="pdf_documents",
            persist_directory="./chroma_db",
            embedding_model="nomic-embed-text"
        )

        # Verify that the vector store is actually populated / available.
        # If we can determine that it has zero documents, treat the chatbot as not ready.
        try:
            doc_count = None

            # Prefer an explicit helper if VectorStore provides one
            if hasattr(vector_store, "get_document_count"):
                doc_count = vector_store.get_document_count()  # type: ignore[attr-defined]
            # Fallback: inspect an underlying collection with a count() method
            elif hasattr(vector_store, "collection") and hasattr(vector_store.collection, "count"):
                doc_count = vector_store.collection.count()  # type: ignore[union-attr]

            if doc_count is not None and doc_count == 0:
                raise HTTPException(
                    status_code=503,
                    detail="Vector store is empty. Please ingest PDF documents before using the chatbot.",
                )
        except HTTPException:
            # Propagate readiness failures as-is so callers can distinguish 503 status.
            raise
        except Exception:
            # If we cannot verify readiness due to an unexpected error, also treat as not ready.
            raise HTTPException(
                status_code=503,
                detail="Unable to verify vector store readiness. Please ensure PDF documents have been ingested.",
            )
        if not vector_store.has_documents():
            raise HTTPException(
                status_code=503,
                detail="Vector store is empty. Run setup_vector_store.py with your PDFs before chatting."
            )

        # Initialize chatbot
        _chatbot_instance = RAGChatbot(
            vector_store=vector_store,
            model_name=os.getenv("OLLAMA_MODEL", "gemma3:4b"),
            temperature=0.7
        )
    
    return _chatbot_instance


@router.post("/", 
             summary="Send a chat message",
             description="Send a message to the AI chatbot and receive a response based on the loaded documents.",
             status_code=status.HTTP_200_OK,
             response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the chatbot and get a response.
    
    Args:
        request: ChatRequest containing the message and optional show_sources flag
        
    Returns:
        ChatResponse with the answer and optional sources
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        chatbot = get_chatbot()
        
        # Get response from chatbot
        answer = chatbot.ask(request.message, show_sources=request.show_sources)
        
        # Parse sources from answer if present
        sources = []
        response_text = answer
        
        if request.show_sources and "\n\nSources:" in answer:
            parts = answer.split("\n\nSources:")
            response_text = parts[0]
            if len(parts) > 1:
                source_lines = parts[1].strip().split("\n")
                sources = [line.strip() for line in source_lines if line.strip()]
        
        return ChatResponse(response=response_text, sources=sources)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.get("/status",
            summary="Check chatbot status",
            description="Check if the chatbot is ready to receive messages.",
            status_code=status.HTTP_200_OK)
async def check_status():
    """
    Check if the chatbot is initialized and ready.
    
    Returns:
        Status information about the chatbot
    """
    try:
        chatbot = get_chatbot()
        return {
            "status": "ready",
            "model": chatbot.model_name,
            "message": "Chatbot is initialized and ready to chat"
        }
    except HTTPException as e:
        return {
            "status": "not_ready",
            "message": e.detail
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking chatbot status: {str(e)}"
        }
