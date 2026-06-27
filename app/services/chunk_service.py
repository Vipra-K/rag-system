import re
import uuid

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from app.core.config import settings
from app.models.chunk import Chunk


class ChunkService:

    def __init__(self):

        self.text_splitter = RecursiveCharacterTextSplitter(

            chunk_size=settings.CHUNK_SIZE,

            chunk_overlap=settings.CHUNK_OVERLAP,

            separators=[

                "\n\n",

                "\n",

                ". ",

                "? ",

                "! ",

                "; ",

                ", ",

                " ",

                ""

            ]

        )

    def create_chunks(

        self,

        document_id: str,

        page_contents: list[dict]

    ) -> list[Chunk]:

        chunks = []

        for page in page_contents:

            page_number = page["page_number"]

            text = self._clean_text(

                page["text"]

            )

            if len(text) < 30:
                continue

            split_chunks = self.text_splitter.split_text(

                text

            )

            for chunk_text in split_chunks:

                chunk_text = chunk_text.strip()

                if len(chunk_text) < 40:
                    continue

                chunks.append(

                    Chunk(

                        chunk_id=str(uuid.uuid4()),

                        document_id=document_id,

                        page_number=page_number,

                        text=chunk_text

                    )

                )

        return chunks

    def _clean_text(

        self,

        text: str

    ) -> str:

        text = text.replace(

            "\u00a0",

            " "

        )

        text = text.replace(

            "\t",

            " "

        )

        text = text.replace(

            "\r",

            "\n"

        )

        text = re.sub(

            r"[ ]{2,}",

            " ",

            text

        )

        text = re.sub(

            r"\n{3,}",

            "\n\n",

            text

        )

        text = re.sub(

            r" +\n",

            "\n",

            text

        )

        return text.strip()