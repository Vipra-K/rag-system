from app.schemas.chat_schema import (
    ChatResponse,
    Source
)

from app.services.embedding_service import (
    EmbeddingService
)

from app.services.llm_service import (
    LLMService
)

from app.services.vector_service import (
    VectorService
)


class ChatService:

    DISTANCE_THRESHOLD = 0.60

    MAX_CONTEXT_CHUNKS = 8

    def __init__(self):

        self.embedding_service = EmbeddingService()

        self.vector_service = VectorService()

        self.llm_service = LLMService()

    def ask(
        self,
        question: str
    ) -> ChatResponse:

        question_embedding = (

            self.embedding_service.generate_embedding(

                question

            )

        )

        retrieved_chunks = (

            self.vector_service.search(

                query_embedding=question_embedding,

                top_k=15

            )

        )

        filtered_chunks = []

        seen_chunks = set()

        for chunk in retrieved_chunks:

            if chunk["distance"] > self.DISTANCE_THRESHOLD:
                continue

            normalized_text = (

                chunk["document"]

                .strip()

                .lower()

            )

            if normalized_text in seen_chunks:
                continue

            seen_chunks.add(

                normalized_text

            )

            filtered_chunks.append(

                chunk

            )

        filtered_chunks = filtered_chunks[

            :self.MAX_CONTEXT_CHUNKS

        ]

        context = "\n\n".join(

            chunk["document"]

            for chunk in filtered_chunks

        )

        answer = self.llm_service.generate_answer(

            question=question,

            context=context

        )

        sources = []

        seen_sources = set()

        for chunk in filtered_chunks:

            key = (

                chunk["document_id"],

                chunk["page_number"]

            )

            if key in seen_sources:
                continue

            seen_sources.add(

                key

            )

            sources.append(

                Source(

                    document_id=chunk["document_id"],

                    page_number=chunk["page_number"]

                )

            )

        return ChatResponse(

            answer=answer,

            sources=sources

        )