from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute paths make the app stable whether you run uvicorn from the project
# root, backend folder, VS Code, Docker, or a process manager.
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
STORAGE_DIR = BACKEND_DIR / "storage"
UPLOAD_DIR = BACKEND_DIR / "uploads"
CHROMA_DIR = BACKEND_DIR / "chroma_db"

for directory in (STORAGE_DIR, UPLOAD_DIR, CHROMA_DIR):
    directory.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    app_name: str = "Multi-Agent Enterprise RAG System"
    environment: str = "development"

    # Change this in backend/.env before production deployment, this is the default setting if .env is not available
    secret_key: str = "asdfsdafasdf12312312"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # SQL database: stores users, documents metadata, and chat history.
    database_url: str = f"sqlite:///{STORAGE_DIR / 'app.db'}"

    # LLM configuration.
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Embeddings configuration.
    # Use huggingface by default so document indexing can work without OpenAI embeddings.
    embedding_provider: str = "huggingface"
    huggingface_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Vector database configuration.
    vector_db_provider: str = "qdrant"
    chroma_persist_dir: str = str(CHROMA_DIR)
    chroma_collection: str = "enterprise_docs"

    pinecone_api_key: str | None = None
    pinecone_index_name: str | None = None

    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str = "enterprise_docs"

    upload_dir: str = str(UPLOAD_DIR)

    # Use .env first
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
