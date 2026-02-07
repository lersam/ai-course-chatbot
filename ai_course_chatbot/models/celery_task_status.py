from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CeleryTaskStatus(BaseModel):
    task_id: str
    status: str
    date_done: Optional[datetime] = None
    traceback: Optional[str] = None
