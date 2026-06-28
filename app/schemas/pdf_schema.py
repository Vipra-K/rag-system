from pydantic import BaseModel


class PDFUploadResponse(BaseModel):

    document_id: str
    filename: str
    total_pages: int
    character_count: int
    total_chunks: int
    message: str


class DocumentSummary(BaseModel):

    document_id: str
    filename: str
    total_pages: int
    total_chunks: int


class DocumentDeleteResponse(BaseModel):

    document_id: str
    message: str
