from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf"}


def is_pdf(filename: str) -> bool:
    extension = Path(filename).suffix.lower()
    return extension in ALLOWED_EXTENSIONS