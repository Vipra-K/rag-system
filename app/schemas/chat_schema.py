from pydantic import BaseModel, Field


class ChatRequest(BaseModel):

    question: str = Field(min_length=2, max_length=2000)

    document_ids: list[str] | None = None


class Source(BaseModel):

    page_number: int

    document_id: str


class ChatResponse(BaseModel):

    answer: str

    sources: list[Source]
