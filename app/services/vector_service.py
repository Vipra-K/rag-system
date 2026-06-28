from collections import Counter
import math
import re

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import settings
from app.models.chunk import Chunk


class VectorService:

    STOP_WORDS = {
        "a", "about", "an", "and", "are", "as", "at", "be", "by",
        "covered", "do", "document", "does", "explain", "for", "from",
        "handbook", "how", "i", "in", "is", "it", "me", "mentioned",
        "of", "on", "or", "pdf", "tell", "teach", "that", "the", "this",
        "to", "was", "what", "when", "where", "which", "who", "why",
        "with"
    }

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
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "filename": chunk.filename or f"{chunk.document_id}.pdf",
                    "module_number": chunk.module_number,
                    "module_title": chunk.module_title or "",
                    "content_type": chunk.content_type
                }
                for chunk in chunks
            ]

        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 15,
        document_ids: list[str] | None = None
    ) -> list[dict]:

        collection_size = self.collection.count()

        if collection_size == 0:
            return []

        query_options = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, collection_size),
            "include": [
                "documents",
                "metadatas",
                "distances"
            ]
        }

        where = self._document_filter(document_ids)

        if where:
            query_options["where"] = where

        results = self.collection.query(**query_options)

        ids = results.get(
            "ids",
            [[]]
        )[0]

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

        for chunk_id, document, metadata, distance in zip(

            ids,

            documents,

            metadatas,

            distances

        ):

            if metadata is None:
                continue

            retrieved_chunks.append(

                {

                    "chunk_id": chunk_id,

                    "document": document,

                    "document_id": metadata.get(
                        "document_id"
                    ),

                    "page_number": metadata.get(
                        "page_number"
                    ),

                    "module_number": metadata.get("module_number", 0),

                    "module_title": metadata.get("module_title", ""),

                    "content_type": metadata.get("content_type", "content"),

                    "distance": distance,

                    "lexical_score": 0.0

                }

            )

        retrieved_chunks.sort(

            key=lambda chunk: chunk["distance"]

        )

        return retrieved_chunks

    def lexical_search(
        self,
        query: str,
        top_k: int = 15,
        document_ids: list[str] | None = None
    ) -> list[dict]:

        query_tokens = self._tokens(query)

        if not query_tokens:
            return []

        get_options = {
            "include": ["documents", "metadatas"]
        }

        where = self._document_filter(document_ids)

        if where:
            get_options["where"] = where

        results = self.collection.get(**get_options)

        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []
        ids = results.get("ids") or []

        tokenized_documents = [
            self._tokens(document or "")
            for document in documents
        ]

        document_frequencies = Counter()

        for tokens in tokenized_documents:
            document_frequencies.update(set(tokens))

        total_documents = max(len(documents), 1)
        query_terms = set(query_tokens)
        query_weight = sum(
            self._idf(term, document_frequencies, total_documents)
            for term in query_terms
        ) or 1.0

        matches = []

        for chunk_id, document, metadata, tokens in zip(
            ids,
            documents,
            metadatas,
            tokenized_documents
        ):

            overlap = query_terms.intersection(tokens)

            if not overlap or metadata is None:
                continue

            overlap_weight = sum(
                self._idf(term, document_frequencies, total_documents)
                for term in overlap
            )

            frequency_weight = sum(
                self._idf(term, document_frequencies, total_documents) *
                math.log1p(tokens.count(term))
                for term in overlap
            )

            lexical_score = (
                overlap_weight / query_weight +
                0.10 * frequency_weight / query_weight
            )

            matches.append({
                "chunk_id": chunk_id,
                "document": document,
                "document_id": metadata.get("document_id"),
                "page_number": metadata.get("page_number"),
                "module_number": metadata.get("module_number", 0),
                "module_title": metadata.get("module_title", ""),
                "content_type": metadata.get("content_type", "content"),
                "distance": None,
                "lexical_score": lexical_score
            })

        matches.sort(
            key=lambda chunk: chunk["lexical_score"],
            reverse=True
        )

        return matches[:top_k]

    def hybrid_search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int = 30,
        document_ids: list[str] | None = None
    ) -> list[dict]:

        vector_matches = self.search(
            query_embedding,
            top_k,
            document_ids=document_ids
        )
        lexical_matches = self.lexical_search(
            query,
            top_k,
            document_ids=document_ids
        )
        combined = {}

        # Reciprocal-rank fusion is robust even though vector distance and
        # lexical coverage use different scales.
        for rank, chunk in enumerate(vector_matches, start=1):
            item = dict(chunk)
            item["retrieval_score"] = 1.0 / (60 + rank)
            combined[item["chunk_id"]] = item

        for rank, chunk in enumerate(lexical_matches, start=1):
            rank_score = 1.25 / (60 + rank)
            existing = combined.get(chunk["chunk_id"])

            if existing:
                existing["retrieval_score"] += rank_score
                existing["lexical_score"] = chunk["lexical_score"]
            else:
                item = dict(chunk)
                item["retrieval_score"] = rank_score
                combined[item["chunk_id"]] = item

        ranked = sorted(
            combined.values(),
            key=lambda chunk: chunk["retrieval_score"],
            reverse=True
        )

        return ranked[:top_k]

    def get_page_chunks(
        self,
        document_id: str,
        page_number: int
    ) -> list[dict]:

        results = self.collection.get(
            where={
                "$and": [
                    {"document_id": document_id},
                    {"page_number": page_number}
                ]
            },
            include=["documents", "metadatas"]
        )

        chunks = []

        for chunk_id, document, metadata in zip(
            results.get("ids") or [],
            results.get("documents") or [],
            results.get("metadatas") or []
        ):
            chunks.append({
                "chunk_id": chunk_id,
                "document": document,
                "chunk_index": (metadata or {}).get("chunk_index", 0)
            })

        chunks.sort(key=lambda chunk: chunk["chunk_index"])

        return chunks

    def get_module_chunks(
        self,
        module_numbers: list[int],
        document_ids: list[str] | None = None,
        limit: int = 20
    ) -> list[dict]:

        if not module_numbers:
            return []

        module_filter = (
            {"module_number": module_numbers[0]}
            if len(module_numbers) == 1
            else {"module_number": {"$in": module_numbers}}
        )
        where = self._combine_filters(
            self._document_filter(document_ids),
            module_filter
        )
        results = self.collection.get(
            where=where,
            limit=limit,
            include=["documents", "metadatas"]
        )

        return self._structural_results(results)

    def get_module_indexes(
        self,
        document_ids: list[str] | None = None
    ) -> list[dict]:

        where = self._combine_filters(
            self._document_filter(document_ids),
            {"content_type": "module_index"}
        )
        results = self.collection.get(
            where=where,
            include=["documents", "metadatas"]
        )

        return self._structural_results(results)

    @staticmethod
    def _structural_results(results) -> list[dict]:

        chunks = []

        for chunk_id, document, metadata in zip(
            results.get("ids") or [],
            results.get("documents") or [],
            results.get("metadatas") or []
        ):
            metadata = metadata or {}
            chunks.append({
                "chunk_id": chunk_id,
                "document": document,
                "document_id": metadata.get("document_id"),
                "page_number": metadata.get("page_number"),
                "module_number": metadata.get("module_number", 0),
                "module_title": metadata.get("module_title", ""),
                "content_type": metadata.get("content_type", "content"),
                "distance": 0.0,
                "lexical_score": 1.0,
                "retrieval_score": 1.0
            })

        chunks.sort(key=lambda chunk: (
            chunk["module_number"],
            chunk["page_number"] or 0
        ))
        return chunks

    @classmethod
    def _tokens(cls, text: str) -> list[str]:

        tokens = re.findall(r"[a-z0-9][a-z0-9+#.-]*", text.lower())

        return [
            cls._normalize_token(token)
            for token in tokens
            if token not in cls.STOP_WORDS and (
                len(token) > 1 or token.isdigit()
            )
        ]

    @staticmethod
    def _normalize_token(token: str) -> str:

        if (
            token.isalpha() and
            token.endswith("s") and
            not token.endswith(("ss", "us", "js")) and
            len(token) > 4
        ):
            return token[:-1]

        return token

    @staticmethod
    def _idf(term: str, frequencies: Counter, total: int) -> float:

        return math.log((total + 1) / (frequencies[term] + 1)) + 1.0

    def delete_document(
        self,
        document_id: str
    ) -> None:

        self.collection.delete(

            where={
                "document_id": document_id
            }

        )

    def list_documents(self) -> list[dict]:

        results = self.collection.get(include=["metadatas"])
        documents = {}

        for metadata in results.get("metadatas") or []:
            if not metadata:
                continue

            document_id = metadata.get("document_id")

            if not document_id:
                continue

            item = documents.setdefault(
                document_id,
                {
                    "document_id": document_id,
                    "filename": metadata.get("filename") or (
                        f"Document {document_id[:8]}"
                    ),
                    "total_pages": 0,
                    "total_chunks": 0
                }
            )
            item["total_chunks"] += 1
            item["total_pages"] = max(
                item["total_pages"],
                int(metadata.get("page_number") or 0)
            )

        return sorted(
            documents.values(),
            key=lambda item: item["filename"].lower()
        )

    @staticmethod
    def _document_filter(document_ids: list[str] | None):

        if not document_ids:
            return None

        unique_ids = list(dict.fromkeys(document_ids))

        if len(unique_ids) == 1:
            return {"document_id": unique_ids[0]}

        return {"document_id": {"$in": unique_ids}}

    @staticmethod
    def _combine_filters(*filters):

        active = [item for item in filters if item]

        if len(active) == 1:
            return active[0]

        return {"$and": active}

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
