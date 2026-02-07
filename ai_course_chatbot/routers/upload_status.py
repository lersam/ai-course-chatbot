from fastapi import APIRouter, HTTPException
from typing import List
from starlette import status

from ai_course_chatbot.controllers import get_celery_tasks_status
from ai_course_chatbot.models.celery_task_status import CeleryTaskStatus
from ai_course_chatbot.worker import celery

router = APIRouter(
    prefix="/aupload",
    tags=["PDF Management"]
)


@router.get("/status", response_model=List[CeleryTaskStatus], status_code=status.HTTP_200_OK)
async def status():
    """Return Celery tasks currently known to workers with their id and status.

    Aggregates `active`, `reserved`, and `scheduled` tasks using Celery inspect
    and returns a JSON object with a `tasks` list where each item contains
    `id`, `status`, `worker`, and `name`.
    """

    celery_tasks = await get_celery_tasks_status()
    if celery_tasks is None:
        raise HTTPException(status_code=500, detail="Unsupported Celery result_backend URL")
    return celery_tasks