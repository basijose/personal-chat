from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Personal Chat", alias="APP_NAME")
    database_url: str = Field(
        default="sqlite:///./personal_chat.db",
        alias="DATABASE_URL",
    )
    jwt_secret: str = Field(default="change-me-in-development-use-a-long-secret", alias="JWT_SECRET")
    jwt_access_token_expire_minutes: int = Field(default=480, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    backend_cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="BACKEND_CORS_ORIGINS",
    )
    frontend_api_base_url: str = Field(default="http://127.0.0.1:8000", alias="FRONTEND_API_BASE_URL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    demo_seed_password: str = Field(default="Demo1234!", alias="DEMO_SEED_PASSWORD")
    n8n_sample_webhook_url: str | None = Field(default=None, alias="N8N_SAMPLE_WEBHOOK_URL")
    external_agent_rest_url: str | None = Field(default=None, alias="EXTERNAL_AGENT_REST_URL")
    external_agent_rest_api_key: str | None = Field(default=None, alias="EXTERNAL_AGENT_REST_API_KEY")
    external_agent_mcp_url: str | None = Field(default=None, alias="EXTERNAL_AGENT_MCP_URL")
    external_agent_mcp_api_key: str | None = Field(default=None, alias="EXTERNAL_AGENT_MCP_API_KEY")
    external_agent_timeout_seconds: float = Field(default=20, alias="EXTERNAL_AGENT_TIMEOUT_SECONDS")
    cors_allow_credentials: bool = True

    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    def model_dump_safe(self) -> dict[str, Any]:
        data = self.model_dump()
        data.pop("jwt_secret", None)
        data.pop("openai_api_key", None)
        return data


@lru_cache
def get_settings() -> Settings:
    return Settings()
