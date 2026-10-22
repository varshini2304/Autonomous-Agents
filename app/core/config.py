from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    xai_api_key: str | None = None
    xai_model: str = "grok-4.7"
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"
    output_dir: Path = Path("generated_documents")
    max_request_length: int = 12000
    max_plan_steps: int = 8
    llm_timeout_seconds: float = 20.0
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.xai_api_key or self.groq_api_key)

    @property
    def llm_provider_name(self) -> str | None:
        if self.xai_api_key:
            return "xai"
        if self.groq_api_key:
            return "groq"
        return None

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
