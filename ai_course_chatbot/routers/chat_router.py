"""
Chat router for AI RAG Chatbot.
Provides endpoints for chatting with the chatbot using RAGChatbot and VectorStore.
"""
import asyncio
import logging
import threading

from cachetools import TTLCache
from fastapi import APIRouter, HTTPException
from starlette import status

from fastapi.responses import StreamingResponse

from ai_course_chatbot.config import get_settings
from ai_course_chatbot.models.chat_request import ChatRequest, ChatResponse
from ai_course_chatbot.models.chat_history import ChatHistory
from ai_course_chatbot.ai_modules import VectorStore, RAGChatbot
from ai_course_chatbot.services import chat_history_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

# ── Thread-safe chatbot singleton ──────────────────────────────────────────
_chatbot_instance: RAGChatbot | None = None
_chatbot_lock = threading.Lock()

# ── Response cache ─────────────────────────────────────────────────────────
_settings = get_settings()
_response_cache: TTLCache = TTLCache(
    maxsize=_settings.chat_cache_maxsize,
    ttl=_settings.chat_cache_ttl,
)
_cache_lock = threading.Lock()


def get_chatbot() -> RAGChatbot:
    """
    Get or create the chatbot instance (double-checked locking).
    """
    global _chatbot_instance

    if _chatbot_instance is not None:
        return _chatbot_instance

    with _chatbot_lock:
        # Re-check after acquiring the lock
        if _chatbot_instance is not None:
            return _chatbot_instance

        settings = get_settings()

        vector_store = VectorStore(
            collection_name=settings.chroma_collection,
            persist_directory=settings.chroma_persist_dir,
            embedding_model=settings.embedding_model,
        )

        if not vector_store.has_documents():
            raise HTTPException(
                status_code=503,
                detail="Vector store is empty. Run setup_vector_store.py with your PDFs before chatting.",
            )

        _chatbot_instance = RAGChatbot(
            vector_store=vector_store,
            model_name=settings.ollama_model,
            num_ctx=settings.llm_num_ctx,
            temperature=settings.llm_temperature,
        )
        logger.info("Chatbot initialized successfully")

    return _chatbot_instance


def _cache_key(message: str, show_sources: bool) -> str:
    """Normalise a question into a stable cache key."""
    return f"{message.strip().lower()}|{show_sources}"


def _parse_sources(answer: str, show_sources: bool):
    """Split the raw answer into response text and a list of source strings."""
    sources: list[str] = []
    response_text = answer

    if show_sources and "\n\nSources:" in answer:
        parts = answer.split("\n\nSources:")
        response_text = parts[0]
        if len(parts) > 1:
            source_lines = parts[1].strip().split("\n")
            sources = [line.strip() for line in source_lines if line.strip()]

    return response_text, sources


@router.post(
    "/",
    summary="Send a chat message",
    description="Send a message to the AI chatbot and receive a response based on the loaded documents.",
    status_code=status.HTTP_200_OK,
    response_model=ChatResponse,
)
async def chat(request: ChatRequest):
    """Send a message to the chatbot and get a response."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        chatbot = get_chatbot()

        # ── Check cache ────────────────────────────────────────────────
        key = _cache_key(request.message, request.show_sources)
        with _cache_lock:
            cached = _response_cache.get(key)
        if cached is not None:
            logger.debug("Cache hit for: %s", key)
            return cached

        # ── Run LLM off the event loop ────────────────────────────────
        answer = await asyncio.to_thread(
            chatbot.ask, request.message, show_sources=request.show_sources
        )

        response_text, sources = _parse_sources(answer, request.show_sources)
        result = ChatResponse(response=response_text, sources=sources)

        # ── Store in cache ─────────────────────────────────────────────
        with _cache_lock:
            _response_cache[key] = result

        # ── Persist to chat history ────────────────────────────────────
        chat_history_service.save_entry(
            user_message=request.message,
            bot_response=response_text,
            sources=sources,
            show_sources=request.show_sources,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing chat request")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}",
        )


@router.post(
    "/stream",
    summary="Stream a chat response (SSE)",
    description="Send a message and receive the response as a Server-Sent Events stream.",
)
async def chat_stream(request: ChatRequest):
    """Stream tokens from the chatbot as Server-Sent Events."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    chatbot = get_chatbot()

    async def _event_generator():
        full_response = []
        try:
            async for token in chatbot.ask_stream(
                request.message, show_sources=request.show_sources
            ):
                full_response.append(token)
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"

            # Persist streamed response to chat history
            full_text = "".join(full_response)
            response_text, sources = _parse_sources(full_text, request.show_sources)
            chat_history_service.save_entry(
                user_message=request.message,
                bot_response=response_text,
                sources=sources,
                show_sources=request.show_sources,
            )
        except Exception as e:
            logger.exception("Error during streaming")
            yield f"data: [ERROR] {e}\n\n"

    return StreamingResponse(_event_generator(), media_type="text/event-stream")


@router.get(
    "/history",
    summary="Get chat history",
    description="Retrieve the full saved chat conversation history.",
    status_code=status.HTTP_200_OK,
    response_model=ChatHistory,
)
async def get_history():
    """Return the persisted chat history."""
    return chat_history_service.load_history()


@router.delete(
    "/history",
    summary="Clear chat history",
    description="Delete all saved chat history.",
    status_code=status.HTTP_200_OK,
)
async def delete_history():
    """Clear the persisted chat history."""
    chat_history_service.clear_history()
    with _cache_lock:
        _response_cache.clear()
    return {"message": "Chat history cleared"}


@router.get(
    "/status",
    summary="Check chatbot status",
    description="Check if the chatbot is ready to receive messages.",
    status_code=status.HTTP_200_OK,
)
async def check_status():
    """Check if the chatbot is initialized and ready."""
    try:
        get_chatbot()
        return {
            "status": "ready",
            "message": "Chatbot is initialized and ready to receive messages",
        }
    except HTTPException as e:
        return {
            "status": "not_ready",
            "message": e.detail,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking chatbot status: {str(e)}",
        }
