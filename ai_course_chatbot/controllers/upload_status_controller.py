import logging
import aiosqlite

from typing import Optional

from ai_course_chatbot.worker import celery

logger = logging.getLogger(__name__)

_db_connection: Optional[aiosqlite.Connection] = None


async def _get_db_connection(db_path: str) -> aiosqlite.Connection:
    global _db_connection
    if _db_connection is None:
        logger.debug("Opening new aiosqlite connection to %s", db_path)
        _db_connection = await aiosqlite.connect(db_path)
    return _db_connection


def sqlite_path_from_backend(backend: str | None) -> Optional[str]:
    if not backend:
        return None
    s = str(backend)
    for abs_prefix in ("db+sqlite:////", "sqlite:////"):
        if s.startswith(abs_prefix):
            return "/" + s[len(abs_prefix):]

    for rel_prefix in ("db+sqlite:///", "sqlite:///"):
        if s.startswith(rel_prefix):
            return s[len(rel_prefix):]

    return None


async def get_celery_tasks_status() -> list[dict[str, str]]:
    backend = getattr(celery.conf, "result_backend", None)
    db_path = sqlite_path_from_backend(backend)

    if not db_path:
        logger.warning("No valid SQLite backend path found (get_celery_tasks_status)")
        return None

    tasks = []
    try:
        db = await _get_db_connection(db_path)
        async with db.execute("SELECT task_id, status, traceback, date_done FROM celery_taskmeta") as cursor:
            async for task_id, status, traceback, date_done in cursor:
                tasks.append({
                    "task_id": task_id,
                    "status": status,
                    "date_done": date_done,
                    "traceback": traceback,
                })
    except Exception:
        logger.warning("Failed to query celery task statuses", exc_info=True)
        return None
    return tasks


async def get_celery_task_status(task_id: str) -> dict | None:
    backend = getattr(celery.conf, "result_backend", None)
    db_path = sqlite_path_from_backend(backend)

    if not db_path:
        logger.warning("No valid SQLite backend path found (get_celery_task_status)")
        return None

    try:
        db = await _get_db_connection(db_path)
        async with db.execute(
            "SELECT task_id, status, traceback, date_done FROM celery_taskmeta WHERE task_id = ?",
            (task_id,),
        ) as cursor:
            sql_result = await cursor.fetchone()
            if sql_result is None:
                return None

            task_id, status, traceback, date_done = sql_result
            return {
                "task_id": task_id,
                "status": status,
                "date_done": date_done,
                "traceback": traceback,
            }
    except Exception:
        logger.warning("Failed to query celery task status for task_id=%s", task_id, exc_info=True)
        return None
