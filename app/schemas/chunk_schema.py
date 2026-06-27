from pydantic import BaseModel


class Chunk(BaseModel):

    chunk_id: int

    document_id: str

    page_number: int

    text: str