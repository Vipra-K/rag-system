from typing import List

from sentence_transformers import SentenceTransformer

from app.exceptions.embedding_exception import (
    EmbeddingGenerationException,
)


class EmbeddingService:

    def __init__(self):

        self.model = SentenceTransformer(
            "BAAI/bge-small-en-v1.5"
        )

    def generate_embedding(
        self,
        text: str
    ) -> List[float]:

        try:

            embedding = self.model.encode(

                text,

                normalize_embeddings=True

            )

            return embedding.tolist()

        except Exception as exception:

            raise EmbeddingGenerationException(
                f"Failed to generate embedding: {exception}"
            )

    def generate_embeddings(
        self,
        texts: List[str]
    ) -> List[List[float]]:

        if not texts:
            return []

        try:

            embeddings = self.model.encode(

                texts,

                batch_size=64,

                normalize_embeddings=True,

                show_progress_bar=True

            )

            return embeddings.tolist()

        except Exception as exception:

            raise EmbeddingGenerationException(
                f"Failed to generate embeddings: {exception}"
            )