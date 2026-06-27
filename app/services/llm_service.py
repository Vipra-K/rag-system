from google import genai

from app.core.config import settings


class LLMService:

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GOOGLE_API_KEY
        )

        self.model = settings.CHAT_MODEL

    def build_prompt(
        self,
        question: str,
        context: str
    ) -> str:

        return f"""
You are an expert AI assistant for Retrieval-Augmented Generation (RAG).

You are given context extracted from one or more uploaded PDF documents.

Your job is to answer ONLY from the provided context.

Rules:

1. Use ONLY the provided context.
2. Never invent or assume information.
3. If the context does not contain enough information, respond exactly:
   "I couldn't find enough information in the uploaded document."
4. When possible, provide a complete answer instead of only repeating a heading.
5. If the context contains lists, learning objectives or steps, preserve them using bullet points.
6. Keep answers well structured and easy to read.
7. Do not mention that you are using context or documents.
8. Ignore duplicate information if it appears multiple times.

-------------------------
Context
-------------------------

{context}

-------------------------
Question
-------------------------

{question}

-------------------------
Answer
-------------------------
"""

    def generate_answer(
        self,
        question: str,
        context: str
    ) -> str:

        prompt = self.build_prompt(

            question=question,

            context=context

        )

        response = self.client.models.generate_content(

            model=self.model,

            contents=prompt

        )

        if response.text:

            return response.text.strip()

        return "I couldn't generate an answer."