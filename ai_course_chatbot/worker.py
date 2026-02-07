import os


from celery import Celery

from ai_course_chatbot.setup_vector_store import setup_vector_store


# Ensure the Celery app has a stable project name and imports this module
# so tasks defined here are registered when the worker starts.
celery = Celery("ai_course_chatbot", include=["ai_course_chatbot.worker"])

# Use SQLAlchemy transport with SQLite by default. Install `kombu-sqlalchemy` and `SQLAlchemy`.
# Broker (kombu SQLAlchemy transport) example: sqla+sqlite:///./celerydb.sqlite
celery.conf.broker_url = os.environ.get(
	"CELERY_BROKER_URL", "sqla+sqlite:///./celerydb.sqlite"
)
# Use the DB result backend with SQLite by default
celery.conf.result_backend = os.environ.get(
	"CELERY_RESULT_BACKEND", "db+sqlite:///./celery_results.sqlite"
)

# Also explicitly import this module so tasks are registered when workers start.
celery.conf.imports = ["ai_course_chatbot.worker"]

@celery.task(bind=True)
def update_vector_store(self, pdf_paths: list[str]):
    print(f"Starting vector store update for {pdf_paths}...")
    # mark task as running so status endpoints and DB reflect it
    try:
        self.update_state(state="RUNNING", meta={"pdf_paths": pdf_paths})
    except Exception:
        # best-effort: if updating state fails, continue
        pass

    vector_store = setup_vector_store(pdf_paths)
    if vector_store is not None:
        print("Vector store updated successfully.")
        self.update_state(state="SUCCESS", meta={"pdf_paths": pdf_paths})
    else:
        print("Vector store update failed or no documents were loaded.")
        self.update_state(state="FAILURE", meta={"pdf_paths": pdf_paths})