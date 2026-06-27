from pathlib import Path
import re
import shutil
import uuid

import fitz

from app.core.config import settings


class PDFService:

    def save_pdf(
        self,
        uploaded_file
    ):

        document_id = str(uuid.uuid4())

        file_path = (
            settings.UPLOAD_DIRECTORY /
            f"{document_id}.pdf"
        )

        with open(file_path, "wb") as file:

            shutil.copyfileobj(

                uploaded_file.file,

                file

            )

        return document_id, file_path

    def extract_text(
        self,
        file_path: Path
    ):

        document = fitz.open(file_path)

        extracted_pages = []

        full_text = []

        for page_number, page in enumerate(
            document,
            start=1
        ):

            text = page.get_text(
                "text"
            )

            text = self._clean_text(
                text
            )

            extracted_pages.append(

                {

                    "page_number": page_number,

                    "text": text

                }

            )

            full_text.append(
                text
            )

        document.close()

        return {

            "pages": len(extracted_pages),

            "characters": len(
                "\n".join(full_text)
            ),

            "text": "\n".join(
                full_text
            ),

            "page_contents": extracted_pages

        }

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