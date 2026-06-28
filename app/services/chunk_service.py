import re
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.models.chunk import Chunk


class ChunkService:

    MODULE_PATTERN = re.compile(
        r"(?im)^\s*Module\s+(\d+)\s*[-–—]\s*([^\n]+)"
    )

    def __init__(self):

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=[
                "\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""
            ]
        )

    def create_chunks(
        self,
        document_id: str,
        page_contents: list[dict],
        filename: str = ""
    ) -> list[Chunk]:

        chunks = []
        module_headings = []
        current_module_number = 0
        current_module_title = ""

        for page in page_contents:
            page_number = page["page_number"]
            text = self._clean_text(page["text"])

            if len(text) < 30:
                continue

            matches = list(self.MODULE_PATTERN.finditer(text))
            sections = []

            if matches and matches[0].start() > 0:
                sections.append((
                    text[:matches[0].start()],
                    current_module_number,
                    current_module_title
                ))

            for index, match in enumerate(matches):
                end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
                current_module_number = int(match.group(1))
                current_module_title = self._clean_title(match.group(2))
                module_headings.append({
                    "number": current_module_number,
                    "title": current_module_title,
                    "page_number": page_number
                })
                sections.append((
                    text[match.start():end],
                    current_module_number,
                    current_module_title
                ))

            if not matches:
                sections.append((
                    text,
                    current_module_number,
                    current_module_title
                ))

            page_chunk_index = 0

            for section_text, module_number, module_title in sections:
                section_text = section_text.strip()

                if len(section_text) < 40:
                    continue

                for chunk_text in self.text_splitter.split_text(section_text):
                    chunk_text = chunk_text.strip()

                    if len(chunk_text) < 40:
                        continue

                    chunks.append(Chunk(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        page_number=page_number,
                        text=chunk_text,
                        chunk_index=page_chunk_index,
                        filename=filename,
                        module_number=module_number,
                        module_title=module_title,
                        content_type="module_content" if module_number else "content"
                    ))
                    page_chunk_index += 1

        if module_headings:
            chunks.append(self._create_module_index(
                document_id=document_id,
                filename=filename,
                headings=module_headings
            ))

        return chunks

    def _create_module_index(
        self,
        document_id: str,
        filename: str,
        headings: list[dict]
    ) -> Chunk:

        unique_numbers = sorted({heading["number"] for heading in headings})
        lines = [
            "Document module index.",
            (
                f"This document contains {len(unique_numbers)} numbered modules, "
                f"numbered {unique_numbers[0]} through {unique_numbers[-1]}."
            )
        ]
        seen_numbers = set()

        for heading in headings:
            qualifier = ""

            if heading["number"] in seen_numbers:
                qualifier = " (duplicate module number in the source PDF)"

            seen_numbers.add(heading["number"])
            lines.append(
                f"Module {heading['number']}: {heading['title']} "
                f"(starts on page {heading['page_number']}){qualifier}."
            )

        return Chunk(
            chunk_id=str(uuid.uuid4()),
            document_id=document_id,
            page_number=headings[0]["page_number"],
            text="\n".join(lines),
            chunk_index=-1,
            filename=filename,
            content_type="module_index"
        )

    @staticmethod
    def _clean_title(title: str) -> str:

        return re.sub(r"\s+", " ", title).strip(" -–—")

    @staticmethod
    def _clean_text(text: str) -> str:

        text = text.replace("\u00a0", " ").replace("\t", " ").replace("\r", "\n")
        text = re.sub(r"[ ]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" +\n", "\n", text)
        return text.strip()
