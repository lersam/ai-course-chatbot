import os
import time

from celery import Celery


celery = Celery(__name__)
# Use SQLAlchemy transport with SQLite by default. Install `kombu-sqlalchemy` and `SQLAlchemy`.
# Broker (kombu SQLAlchemy transport) example: sqla+sqlite:///./celerydb.sqlite
celery.conf.broker_url = os.environ.get(
	"CELERY_BROKER_URL", "sqla+sqlite:///./celerydb.sqlite"
)
# Use the DB result backend with SQLite by default
celery.conf.result_backend = os.environ.get(
	"CELERY_RESULT_BACKEND", "db+sqlite:///./celery_results.sqlite"
)

@celery.task
def long_running_task(duration):
    print(f"Starting long-running task for {duration} seconds...")
    time.sleep(duration)
    print("Task completed!")
    return f"Task completed after {duration} seconds"