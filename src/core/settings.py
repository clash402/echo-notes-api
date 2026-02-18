from functools import lru_cache
import os
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = Field(
        default_factory=lambda: os.getenv("ECHO_NOTES_APP_NAME", "echo-notes-api")
    )
    app_env: str = Field(default_factory=lambda: os.getenv("ECHO_NOTES_APP_ENV", "dev"))
    database_path: Path = Field(
        default_factory=lambda: Path(os.getenv("ECHO_NOTES_DB_PATH", "data/echo_notes.db"))
    )
    llm_provider: str = Field(default_factory=lambda: os.getenv("ECHO_NOTES_LLM_PROVIDER", "auto"))
    llm_default_model: str = Field(
        default_factory=lambda: os.getenv("ECHO_NOTES_LLM_DEFAULT_MODEL", "echo-default-v1")
    )
    llm_cheap_model: str = Field(
        default_factory=lambda: os.getenv("ECHO_NOTES_LLM_CHEAP_MODEL", "echo-cheap-v1")
    )
    openai_api_key: str | None = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_base_url: str | None = Field(default_factory=lambda: os.getenv("OPENAI_BASE_URL"))
    llm_prompt_cost_per_1k: float = Field(
        default_factory=lambda: float(os.getenv("ECHO_NOTES_LLM_PROMPT_COST_PER_1K", "0.0"))
    )
    llm_completion_cost_per_1k: float = Field(
        default_factory=lambda: float(os.getenv("ECHO_NOTES_LLM_COMPLETION_COST_PER_1K", "0.0"))
    )
    embedding_provider: str = Field(
        default_factory=lambda: os.getenv("ECHO_NOTES_EMBEDDING_PROVIDER", "auto")
    )
    embedding_model: str = Field(
        default_factory=lambda: os.getenv("ECHO_NOTES_EMBEDDING_MODEL", "text-embedding-3-small")
    )
    embedding_cost_per_1k: float = Field(
        default_factory=lambda: float(os.getenv("ECHO_NOTES_EMBEDDING_COST_PER_1K", "0.0"))
    )
    transcription_provider: str = Field(
        default_factory=lambda: os.getenv("ECHO_NOTES_TRANSCRIPTION_PROVIDER", "auto")
    )
    whisper_local_model: str = Field(
        default_factory=lambda: os.getenv("ECHO_NOTES_WHISPER_LOCAL_MODEL", "base")
    )
    whisper_openai_model: str = Field(
        default_factory=lambda: os.getenv("ECHO_NOTES_WHISPER_OPENAI_MODEL", "whisper-1")
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
