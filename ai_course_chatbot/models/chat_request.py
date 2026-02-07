from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    show_sources: bool = True

class ChatResponse(BaseModel):
    response: str
    sources: list = []
