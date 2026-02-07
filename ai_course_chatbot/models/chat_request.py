from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    message: str
    show_sources: bool = True

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []
