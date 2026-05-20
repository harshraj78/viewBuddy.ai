from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Interview Copilot"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:8501",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:4173",
            "http://127.0.0.1:8501",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:4173",
        ]
    )

    database_url: str = (
        "postgresql+psycopg://postgres:change_me@localhost:5432/ai_interview_copilot"
    )

    jwt_secret_key: str = "replace_with_long_random_secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    upload_dir: str = "./data/uploads"
    max_resume_file_mb: int = 10

    llm_provider: str = "openai"
    interview_llm_provider: str = "fallback"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    local_llm_base_url: str = "http://localhost:8001/v1"
    local_llm_api_key: str = "EMPTY"
    local_llm_model: str = "interview-llm"
    ai_evaluation_mode: str = "fallback"
    llm_request_timeout_seconds: int = 60
    llm_max_retries: int = 3

    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
