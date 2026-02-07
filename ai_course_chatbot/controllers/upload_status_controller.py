import aiosqlite

from typing import Optional

from ai_course_chatbot.worker import celery


def sqlite_path_from_backend(backend: str | None) -> Optional[str]:
    if not backend:
        return None
    s = str(backend)
    # Absolute path when there are 4 slashes after scheme (sqlite:////abs/path)
    for abs_prefix in ("db+sqlite:////", "sqlite:////"):
        if s.startswith(abs_prefix):
            return "/" + s[len(abs_prefix) :]

    # Relative or ./path when there are 3 slashes (sqlite:///./file or db+sqlite:///./file)
    for rel_prefix in ("db+sqlite:///", "sqlite:///"):
        if s.startswith(rel_prefix):
            return s[len(rel_prefix) :]

    return None

async def get_celery_tasks_status() -> list[dict[str, str]]:
    backend = getattr(celery.conf, "result_backend", None)
    db_path = sqlite_path_from_backend(backend)

    if not db_path:
        return None

    tasks = []
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT task_id, status, traceback, date_done FROM celery_taskmeta") as cursor:
            async for task_id, status, traceback, date_done in cursor:
                tasks.append({
                    "task_id": task_id,
                    "status": status,
                    "date_done": date_done,
                    "traceback": traceback
                })
        return tasks

async def get_celery_task_status(task_id: str) -> dict | None:
    backend = getattr(celery.conf, "result_backend", None)
    db_path = sqlite_path_from_backend(backend)

    if not db_path:
        return None
    
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT task_id, status, traceback, date_done FROM celery_taskmeta WHERE task_id = ?", (task_id,)) as cursor:
            sql_result = await cursor.fetchone()
            if sql_result is None:
                return None

            task_id, status, traceback, date_done = sql_result
            return {
                    "task_id": task_id,
                    "status": status,
                    "date_done": date_done,
                    "traceback": traceback
                }
