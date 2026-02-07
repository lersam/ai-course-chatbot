import sqlite3

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

    conn = sqlite3.connect(db_path)

    try:
        tasks = []
        
        cur = conn.cursor()
        cur.execute("SELECT task_id, status, traceback, date_done FROM celery_taskmeta")
        rows = cur.fetchall()
        for task_id, status, traceback, date_done in rows:
            tasks.append({
                "task_id": task_id,
                "status": status,
                "date_done": date_done,
                "traceback": traceback
            })
        return tasks
    except Exception as e:
        print(f"Error accessing Celery result backend: {e}")
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass
