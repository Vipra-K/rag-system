from dataclasses import dataclass


@dataclass
class Chunk:

    chunk_id: str

    document_id: str

    page_number: int

    text: str