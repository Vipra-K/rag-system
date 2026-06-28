from dataclasses import dataclass


@dataclass
class Chunk:

    chunk_id: str

    document_id: str

    page_number: int

    text: str

    chunk_index: int = 0

    filename: str = ""

    module_number: int = 0

    module_title: str = ""

    content_type: str = "content"
