from typing import List

from app.exceptions.embedding_exception import (
    EmbeddingGenerationException,
)


class EmbeddingService:

    _model = None

    QUERY_INSTRUCTION = (
        "Represent this sentence for searching relevant passages: "
    )

    def __init__(self):

        pass

    @classmethod
    def _get_model(cls):

        if cls._model is None:

            from sentence_transformers import SentenceTransformer

            cls._model = SentenceTransformer(
                "BAAI/bge-small-en-v1.5"
            )

        return cls._model

    def generate_embedding(
        self,
        text: str
    ) -> List[float]:

        try:

            embedding = self._get_model().encode(

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

            embeddings = self._get_model().encode(

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

    def generate_query_embedding(
        self,
        question: str
    ) -> List[float]:

        query = f"{self.QUERY_INSTRUCTION}{question.strip()}"

        return self.generate_embedding(query)
