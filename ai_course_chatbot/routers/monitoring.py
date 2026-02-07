from fastapi import APIRouter, HTTPException
from typing import List
from starlette import status

from ai_course_chatbot.controllers import get_celery_tasks_status, get_celery_task_status
from ai_course_chatbot.models.celery_task_status import CeleryTaskStatus
from ai_course_chatbot.worker import celery

router = APIRouter(
    prefix="/monitoring",
    tags=["PDF Management"]
)


@router.get("/", response_model=List[CeleryTaskStatus], status_code=status.HTTP_200_OK)
async def celery_status():
    """Return Celery tasks currently known to workers with their id and status.

    Aggregates `active`, `reserved`, and `scheduled` tasks using Celery inspect
    and returns a JSON object with a `tasks` list where each item contains
    `id`, `status`, `worker`, and `name`.
    """

    celery_tasks = await get_celery_tasks_status()
    if celery_tasks is None:
        raise HTTPException(status_code=500, detail="Unsupported Celery result_backend URL")
    return celery_tasks


@router.get("/celery-task", response_model=CeleryTaskStatus)
async def celery_task(celery_task: str = None):
    """Return currently running Celery tasks (filtered)."""
    if not celery_task:
        raise HTTPException(status_code=400, detail="Missing required query parameter: celery_task")
    
    celery_tasks = await get_celery_task_status(celery_task)
    if celery_tasks is None:
        raise HTTPException(status_code=404, detail="Celery task not found")


    return celery_tasks