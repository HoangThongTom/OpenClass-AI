from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://openclass:openclass@127.0.0.1:5434/openclass"
    ollama_url: str = "http://127.0.0.1:11434"
    default_ollama_model: str = "qwen2.5:3b"
    ollama_timeout_seconds: int = 600
    ollama_num_ctx: int = Field(default=4096, ge=4096, le=32768)
    ollama_source_char_limit: int = Field(default=2400, ge=500, le=8500)
    max_upload_mb: int = 15


@lru_cache

def get_settings() -> Settings:
    return Settings()
