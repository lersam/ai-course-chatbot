from contextlib import asynccontextmanager

import uvicorn

from fastapi import FastAPI
from starlette import status

from ai_course_chatbot.routers import pdf_router
from ai_course_chatbot.routers import monitoring
@asynccontextmanager
async def lifespan(_app: FastAPI):
    _app.include_router(pdf_router.router)
    _app.include_router(monitoring.router)

    yield

app = FastAPI(lifespan=lifespan)


@app.get("/healthy", status_code=status.HTTP_200_OK, include_in_schema=False)
def health_check():
    return {'status': 'Healthy'}


if __name__ == "__main__":
    uvicorn.run("ai_course_chatbot.main:app", host="0.0.0.0", port=8000, reload=True)