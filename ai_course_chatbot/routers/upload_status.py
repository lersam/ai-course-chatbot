from fastapi import APIRouter, HTTPException
from typing import List, Dict

from ai_course_chatbot.worker import celery

router = APIRouter(
    prefix="/aupload",
    tags=["PDF Management"]
)


@router.get("/status", response_model=Dict[str, List[Dict[str, str]]])
async def status():
    """Return Celery tasks currently known to workers with their id and status.

    Aggregates `active`, `reserved`, and `scheduled` tasks using Celery inspect
    and returns a JSON object with a `tasks` list where each item contains
    `id`, `status`, `worker`, and `name`.
    """
    try:
        insp = celery.control.inspect()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to contact Celery control API: {e}")

    tasks = []

    active = insp.active() or {}
    for worker, items in active.items():
        for item in items:
            tasks.append({
                "id": item.get("id"),
                "status": "active",
                "worker": worker,
                "name": item.get("name"),
            })

    reserved = insp.reserved() or {}
    for worker, items in reserved.items():
        for item in items:
            tasks.append({
                "id": item.get("id"),
                "status": "reserved",
                "worker": worker,
                "name": item.get("name"),
            })

    scheduled = insp.scheduled() or {}
    for worker, items in scheduled.items():
        for item in items:
            req = item.get("request") or item
            tasks.append({
                "id": req.get("id"),
                "status": "scheduled",
                "worker": worker,
                "name": req.get("name"),
            })

    return {"tasks": tasks}
