from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()


def _env_number(name, default, cast):

    value = os.getenv(name)

    if value is None:
        return cast(default)

    # Allow readable values such as ``10485760 # 10 MB`` in .env files.
    value = value.split("#", 1)[0].strip()

    return cast(value)


class Settings:

    def __init__(self):

        self.GOOGLE_API_KEY = os.getenv(
            "GOOGLE_API_KEY"
        )

        self.UPLOAD_DIRECTORY = Path(
            os.getenv(
                "UPLOAD_DIRECTORY",
                "uploads"
            )
        )

        self.CHROMA_DIRECTORY = Path(
            os.getenv(
                "CHROMA_DIRECTORY",
                os.getenv("CHROMA_PATH", "chroma_db")
            )
        )

        self.CHROMA_COLLECTION = os.getenv(
            "CHROMA_COLLECTION",
            "documents"
        )

        self.CHAT_MODEL = os.getenv(
            "CHAT_MODEL",
            "gemini-2.5-flash"
        )

        self.CHUNK_SIZE = _env_number(
            "CHUNK_SIZE",
            800,
            int
        )

        self.CHUNK_OVERLAP = _env_number(
            "CHUNK_OVERLAP",
            150,
            int
        )

        self.TOP_K = _env_number(
            "TOP_K",
            30,
            int
        )

        self.MAX_CONTEXT_CHUNKS = _env_number(
            "MAX_CONTEXT_CHUNKS",
            10,
            int
        )

        self.MAX_CONTEXT_PAGES = _env_number(
            "MAX_CONTEXT_PAGES",
            3,
            int
        )

        self.MAX_CONTEXT_CHARACTERS = _env_number(
            "MAX_CONTEXT_CHARACTERS",
            24000,
            int
        )

        self.DISTANCE_THRESHOLD = _env_number(
            "DISTANCE_THRESHOLD",
            0.50,
            float
        )

        self.MAX_FILE_SIZE = _env_number(
            "MAX_FILE_SIZE",
            10 * 1024 * 1024,
            int
        )

        self.UPLOAD_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True
        )

        self.CHROMA_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True
        )


settings = Settings()
