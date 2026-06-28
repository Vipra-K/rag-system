from fastapi import (
    APIRouter,
    HTTPException
)

from app.schemas.chat_schema import (
    ChatRequest,
    ChatResponse
)

from app.services.chat_service import (
    ChatService
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

chat_service = ChatService()


@router.post(
    "",
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest
):

    try:

        return chat_service.ask(
            question=request.question,
            document_ids=request.document_ids
        )

    except Exception as exception:

        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(exception)
        )
