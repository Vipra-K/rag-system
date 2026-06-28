from app.core.config import settings
from app.schemas.chat_schema import ChatResponse, Source
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.vector_service import VectorService


class ChatService:

    NO_ANSWER = "I couldn't find enough information in the uploaded document."

    def __init__(
        self,
        embedding_service=None,
        vector_service=None,
        llm_service=None
    ):

        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_service = vector_service or VectorService()
        self.llm_service = llm_service or LLMService()

    def ask(
        self,
        question: str,
        document_ids: list[str] | None = None
    ) -> ChatResponse:

        question = question.strip()
        question_embedding = (
            self.embedding_service.generate_query_embedding(question)
        )

        retrieved_chunks = self.vector_service.hybrid_search(
            query=question,
            query_embedding=question_embedding,
            top_k=settings.TOP_K,
            document_ids=document_ids
        )

        filtered_chunks = []
        seen_chunks = set()

        for chunk in retrieved_chunks:
            distance = chunk.get("distance")
            lexical_score = chunk.get("lexical_score", 0.0)
            has_semantic_match = (
                distance is not None and
                distance <= settings.DISTANCE_THRESHOLD
            )
            has_lexical_match = lexical_score >= 0.15

            if not has_semantic_match and not has_lexical_match:
                continue

            normalized_text = chunk["document"].strip().lower()

            if normalized_text in seen_chunks:
                continue

            seen_chunks.add(normalized_text)
            filtered_chunks.append(chunk)

        filtered_chunks = filtered_chunks[:settings.MAX_CONTEXT_CHUNKS]

        if not filtered_chunks:
            return ChatResponse(answer=self.NO_ANSWER, sources=[])

        context, source_data = self._build_context(filtered_chunks)

        if not context:
            return ChatResponse(answer=self.NO_ANSWER, sources=[])

        answer = self.llm_service.generate_answer(
            question=question,
            context=context
        )

        sources = [
            Source(document_id=document_id, page_number=page_number)
            for document_id, page_number in source_data
        ]

        return ChatResponse(answer=answer, sources=sources)

    def _build_context(
        self,
        chunks: list[dict]
    ) -> tuple[str, list[tuple[str, int]]]:

        sections = []
        sources = []
        seen_pages = set()
        character_count = 0

        for chunk in chunks:
            page_key = (chunk["document_id"], chunk["page_number"])

            if page_key in seen_pages:
                continue

            if len(seen_pages) >= settings.MAX_CONTEXT_PAGES:
                break

            page_chunks = self.vector_service.get_page_chunks(
                document_id=chunk["document_id"],
                page_number=chunk["page_number"]
            )

            page_text_parts = []
            seen_text = set()

            for page_chunk in page_chunks:
                text = (page_chunk.get("document") or "").strip()
                normalized = text.lower()

                if text and normalized not in seen_text:
                    seen_text.add(normalized)
                    page_text_parts.append(text)

            if not page_text_parts:
                page_text_parts = [chunk["document"].strip()]

            page_text = "\n".join(page_text_parts)
            header = (
                f"[Document {chunk['document_id']} | "
                f"Page {chunk['page_number']}]"
            )
            section = f"{header}\n{page_text}"
            remaining = settings.MAX_CONTEXT_CHARACTERS - character_count

            if remaining <= len(header) + 20:
                break

            if len(section) > remaining:
                section = section[:remaining]

            sections.append(section)
            sources.append(page_key)
            seen_pages.add(page_key)
            character_count += len(section)

        return "\n\n".join(sections), sources
