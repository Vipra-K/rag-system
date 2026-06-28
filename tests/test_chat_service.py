import unittest

from app.services.chat_service import ChatService


class FakeEmbeddingService:

    def generate_query_embedding(self, question):
        assert question
        return [0.1, 0.2]


class FakeVectorService:

    def __init__(self, matches):
        self.matches = matches

    def hybrid_search(
        self,
        query,
        query_embedding,
        top_k,
        document_ids=None
    ):
        return self.matches

    def get_page_chunks(self, document_id, page_number):
        return [
            {
                "document": "Module overview and introduction.",
                "chunk_index": 0
            },
            {
                "document": "The program duration is seven weeks.",
                "chunk_index": 1
            }
        ]


class FakeLLMService:

    def __init__(self):
        self.context = None

    def generate_answer(self, question, context):
        self.context = context
        return "The program lasts seven weeks."


class ChatServiceTests(unittest.TestCase):

    def test_ask_uses_page_context_and_returns_source(self):
        match = {
            "chunk_id": "chunk-1",
            "document": "The program duration is seven weeks.",
            "document_id": "document-1",
            "page_number": 5,
            "distance": 0.70,
            "lexical_score": 0.5,
            "retrieval_score": 1.0
        }
        llm = FakeLLMService()
        service = ChatService(
            embedding_service=FakeEmbeddingService(),
            vector_service=FakeVectorService([match]),
            llm_service=llm
        )

        response = service.ask("How long is the program?")

        self.assertEqual(response.answer, "The program lasts seven weeks.")
        self.assertEqual(response.sources[0].document_id, "document-1")
        self.assertEqual(response.sources[0].page_number, 5)
        self.assertIn("Module overview", llm.context)
        self.assertIn("Page 5", llm.context)

    def test_ask_does_not_call_llm_without_relevant_evidence(self):
        match = {
            "chunk_id": "chunk-1",
            "document": "Unrelated text.",
            "document_id": "document-1",
            "page_number": 1,
            "distance": 1.1,
            "lexical_score": 0.0,
            "retrieval_score": 1.0
        }
        llm = FakeLLMService()
        service = ChatService(
            embedding_service=FakeEmbeddingService(),
            vector_service=FakeVectorService([match]),
            llm_service=llm
        )

        response = service.ask("What is the capital of France?")

        self.assertEqual(response.answer, service.NO_ANSWER)
        self.assertEqual(response.sources, [])
        self.assertIsNone(llm.context)


if __name__ == "__main__":
    unittest.main()
