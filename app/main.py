from fastapi import FastAPI

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


@app.get("/")
async def home():

    return {

        "message": "RAG System Running"

    }


@app.get("/health")
async def health():

    return {

        "status": "healthy"

    }