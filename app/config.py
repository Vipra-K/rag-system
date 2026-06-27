from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()


class Settings:

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    CHROMA_DIRECTORY = Path(
        os.getenv("CHROMA_DIRECTORY", "chroma_db")
    )

    UPLOAD_DIRECTORY = Path(
        os.getenv("UPLOAD_DIRECTORY", "uploads")
    )


settings = Settings()