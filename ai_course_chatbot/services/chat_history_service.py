"""Service for persisting chat history to a JSON file."""
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import List

from ai_course_chatbot.config import get_settings
from ai_course_chatbot.models.chat_history import ChatHistory, ChatHistoryEntry

logger = logging.getLogger(__name__)

_lock = threading.Lock()


def _history_path() -> Path:
    """Return the resolved path to the chat history JSON file."""
    settings = get_settings()
    return Path(settings.chat_history_path)


def load_history() -> ChatHistory:
    """Load chat history from disk. Returns empty history if file missing."""
    path = _history_path()
    if not path.exists():
        return ChatHistory()
    try:
        with _lock:
            data = json.loads(path.read_text(encoding="utf-8"))
        return ChatHistory.model_validate(data)
    except Exception:
        logger.warning("Failed to load chat history from %s, starting fresh", path, exc_info=True)
        return ChatHistory()


def save_entry(
    user_message: str,
    bot_response: str,
    sources: List[str] | None = None,
    show_sources: bool = True,
) -> ChatHistoryEntry:
    """Append a single exchange to the persisted history and return it."""
    entry = ChatHistoryEntry(
        timestamp=datetime.utcnow(),
        user_message=user_message,
        bot_response=bot_response,
        sources=sources or [],
        show_sources=show_sources,
    )

    history = load_history()
    history.entries.append(entry)

    path = _history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        path.write_text(
            history.model_dump_json(indent=2),
            encoding="utf-8",
        )

    logger.debug("Saved chat entry (%d total)", len(history.entries))
    return entry


def clear_history() -> None:
    """Delete the history file."""
    path = _history_path()
    with _lock:
        if path.exists():
            path.unlink()
    logger.info("Chat history cleared")
