from pydantic import BaseModel
from typing import Optional
from ai_course_chatbot.models.support import Topics


class PDFRequest(BaseModel):
    url: str
    topics: Optional[Topics] = None
