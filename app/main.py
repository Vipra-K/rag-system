from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes.upload import (
    router as upload_router
)

from app.routes.chat import (
    router as chat_router
)

app = FastAPI(

    title="RAG System",

    version="1.0.0"

)

app.include_router(upload_router)

app.include_router(chat_router)

STATIC_DIRECTORY = Path(__file__).parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIRECTORY),
    name="static"
)


@app.get("/")
async def home():

    return FileResponse(STATIC_DIRECTORY / "index.html")


@app.get("/health")
async def health():

    return {

        "status": "healthy"

    }
