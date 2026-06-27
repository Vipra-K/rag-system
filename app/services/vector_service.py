import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import settings
from app.models.chunk import Chunk


class VectorService:

    def __init__(self):

        self.client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DIRECTORY)
        )

        self.collection: Collection = (
            self.client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION,
                metadata={
                    "hnsw:space": "cosine"
                }
            )
        )

    def store_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]]
    ) -> None:

        if not chunks:
            return

        self.collection.add(

            ids=[
                chunk.chunk_id
                for chunk in chunks
            ],

            documents=[
                chunk.text
                for chunk in chunks
            ],

            embeddings=embeddings,

            metadatas=[
                {
                    "document_id": chunk.document_id,
                    "page_number": chunk.page_number
                }
                for chunk in chunks
            ]

        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 15
    ) -> list[dict]:

        results = self.collection.query(

            query_embeddings=[query_embedding],

            n_results=top_k,

            include=[
                "documents",
                "metadatas",
                "distances"
            ]

        )

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        distances = results.get(
            "distances",
            [[]]
        )[0]

        retrieved_chunks = []

        for document, metadata, distance in zip(

            documents,

            metadatas,

            distances

        ):

            if metadata is None:
                continue

            retrieved_chunks.append(

                {

                    "document": document,

                    "document_id": metadata.get(
                        "document_id"
                    ),

                    "page_number": metadata.get(
                        "page_number"
                    ),

                    "distance": distance

                }

            )

        retrieved_chunks.sort(

            key=lambda chunk: chunk["distance"]

        )

        return retrieved_chunks

    def delete_document(
        self,
        document_id: str
    ) -> None:

        self.collection.delete(

            where={
                "document_id": document_id
            }

        )

    def document_exists(
        self,
        document_id: str
    ) -> bool:

        results = self.collection.get(

            where={
                "document_id": document_id
            },

            limit=1

        )

        return len(results["ids"]) > 0