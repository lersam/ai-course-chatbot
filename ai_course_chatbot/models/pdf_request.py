from pydantic import BaseModel

class PDFRequest(BaseModel):
    url: str
