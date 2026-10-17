"""
Application configuration.

All configurable values are loaded from environment variables (via a .env file
in development). Nothing sensitive is ever hardcoded here.
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # -> server/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    APP_NAME: str = "AI Research Paper Summarizer"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # --- AI ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    # Optional: where fastembed caches the ONNX model. Empty = fastembed default (system temp dir).
    FASTEMBED_CACHE_DIR: str = ""
    GEMINI_TIMEOUT_SECONDS: int = 60

    # --- Storage ---
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    FAISS_INDEX_DIR: Path = BASE_DIR / "storage" / "faiss_index"
    SAMPLES_DIR: Path = BASE_DIR / "storage" / "samples"
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]

    # --- Database ---
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'storage' / 'app.db'}"

    # --- RAG ---
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    RETRIEVAL_TOP_K: int = 5

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    settings.SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "storage").mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
