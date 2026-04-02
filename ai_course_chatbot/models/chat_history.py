"""Pydantic models for chat history persistence."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatHistoryEntry(BaseModel):
    """A single chat exchange (user question + bot response)."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_message: str
    bot_response: str
    sources: List[str] = []
    show_sources: bool = True


class ChatHistory(BaseModel):
    """Full conversation history."""

    entries: List[ChatHistoryEntry] = []
