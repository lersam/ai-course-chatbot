"""FastAPI application entry point for the AI Course Chatbot."""
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette import status

from ai_course_chatbot.config import get_settings
from ai_course_chatbot.routers import pdf_router, monitoring, chat_router, pdf_scraper_router

logger = logging.getLogger(__name__)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def _configure_logging() -> None:
    """Set up root logging based on the configured log level."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _configure_logging()
    logger.info("Initializing chatbot...")
    try:
        chat_router.get_chatbot()
        logger.info("Chatbot initialized successfully")
    except Exception as e:
        logger.warning("Could not pre-initialize chatbot: %s", e)
        logger.info("Chatbot will be initialized on first request")
    yield


app = FastAPI(lifespan=lifespan)

# ── CORS ───────────────────────────────────────────────────────────────────
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ──────────────────────────────────────────────
@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(pdf_router.router)
app.include_router(pdf_scraper_router.router)
app.include_router(monitoring.router)
app.include_router(chat_router.router)

# ── Static files ───────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the chat frontend."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/healthy", status_code=status.HTTP_200_OK, include_in_schema=False)
def health_check():
    return {"status": "Healthy"}


if __name__ == "__main__":
    uvicorn.run("ai_course_chatbot.main:app", host="0.0.0.0", port=8000, reload=True)
