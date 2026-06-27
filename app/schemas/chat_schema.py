from pydantic import BaseModel


class ChatRequest(BaseModel):

    question: str


class Source(BaseModel):

    page_number: int

    document_id: str


class ChatResponse(BaseModel):

    answer: str

    sources: list[Source]