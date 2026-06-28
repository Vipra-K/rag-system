from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)
import uuid

from app.core.config import settings
from app.schemas.pdf_schema import (
    DocumentDeleteResponse,
    DocumentSummary,
    PDFUploadResponse
)

from app.services.pdf_service import PDFService
from app.services.chunk_service import ChunkService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService

from app.utils.file_validator import (
    validate_extension
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

pdf_service = PDFService()
chunk_service = ChunkService()
embedding_service = EmbeddingService()
vector_service = VectorService()


@router.get(
    "",
    response_model=list[DocumentSummary]
)
async def list_documents():

    return vector_service.list_documents()


@router.post(
    "/upload",
    response_model=PDFUploadResponse
)
async def upload_pdf(
    file: UploadFile = File(...)
):

    try:

        validate_extension(file.filename)

        document_id, file_path = pdf_service.save_pdf(file)

        extracted_data = pdf_service.extract_text(file_path)

        chunks = chunk_service.create_chunks(
            document_id=document_id,
            page_contents=extracted_data["page_contents"],
            filename=file.filename
        )

        embeddings = embedding_service.generate_embeddings(
            [chunk.text for chunk in chunks]
        )

        vector_service.store_chunks(
            chunks=chunks,
            embeddings=embeddings
        )

        return PDFUploadResponse(

            document_id=document_id,

            filename=file.filename,

            total_pages=extracted_data["pages"],

            character_count=extracted_data["characters"],

            total_chunks=len(chunks),

            message="PDF uploaded successfully"

        )

    except ValueError as exception:

        raise HTTPException(
            status_code=400,
            detail=str(exception)
        )

    except Exception as exception:

        raise HTTPException(
            status_code=500,
            detail=str(exception)
        )


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse
)
async def delete_document(document_id: str):

    try:
        uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID."
        )

    if not vector_service.document_exists(document_id):
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    vector_service.delete_document(document_id)
    file_path = settings.UPLOAD_DIRECTORY / f"{document_id}.pdf"

    if file_path.exists():
        file_path.unlink()

    return DocumentDeleteResponse(
        document_id=document_id,
        message="Document deleted successfully"
    )
