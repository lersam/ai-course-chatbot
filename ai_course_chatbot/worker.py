import os


from celery import Celery

from ai_course_chatbot import setup_vector_store


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
def update_vector_store(pdf_paths: list[str]):
    print(f"Starting vector store update for {pdf_paths}...")
    vector_store = setup_vector_store(pdf_paths)
    if vector_store is not None:
        print("Vector store updated successfully.")
    else:
        print("Vector store update failed or no documents were loaded.")