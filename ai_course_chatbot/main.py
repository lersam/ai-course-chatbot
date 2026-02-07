from contextlib import asynccontextmanager
import os

import uvicorn

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette import status

from ai_course_chatbot.routers import pdf_router
from ai_course_chatbot.routers import monitoring
from ai_course_chatbot.routers import chat_router

@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(pdf_router.router)
app.include_router(monitoring.router)
app.include_router(chat_router.router)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the chat frontend."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/healthy", status_code=status.HTTP_200_OK, include_in_schema=False)
def health_check():
    return {'status': 'Healthy'}


if __name__ == "__main__":
    uvicorn.run("ai_course_chatbot.main:app", host="0.0.0.0", port=8000, reload=True)