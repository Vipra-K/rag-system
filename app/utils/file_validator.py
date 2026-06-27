from pathlib import Path


ALLOWED_EXTENSIONS = {
    ".pdf"
}


def validate_extension(filename: str):

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Only PDF files are allowed."
        )