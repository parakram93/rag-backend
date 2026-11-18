from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cohere_api_key: str
    llm_model: str = "command-a-03-2025"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    database_url: str = "sqlite:///app.db"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "documents"
    redis_host: str = "localhost"
    redis_port: int = 6379
    chat_ttl_seconds: int = 1800
    chat_max_messages: int = 10
    chunk_size: int = 500
    chunk_overlap: int = 50
    max_upload_bytes: int = 10 * 1024 * 1024
    retrieval_top_k: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()  