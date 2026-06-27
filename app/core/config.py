from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()


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
                "chroma_db"
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

        self.CHUNK_SIZE = int(
            os.getenv(
                "CHUNK_SIZE",
                500
            )
        )

        self.CHUNK_OVERLAP = int(
            os.getenv(
                "CHUNK_OVERLAP",
                100
            )
        )

        self.TOP_K = int(
            os.getenv(
                "TOP_K",
                15
            )
        )

        self.MAX_CONTEXT_CHUNKS = int(
            os.getenv(
                "MAX_CONTEXT_CHUNKS",
                8
            )
        )

        self.DISTANCE_THRESHOLD = float(
            os.getenv(
                "DISTANCE_THRESHOLD",
                0.60
            )
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