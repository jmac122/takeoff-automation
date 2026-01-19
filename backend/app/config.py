"""Application configuration with multi-LLM provider support."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)

    # Database
    database_url: PostgresDsn
    database_pool_size: int = 20

    # Redis
    redis_url: RedisDsn
    celery_broker_url: RedisDsn
    celery_result_backend: RedisDsn

    # Storage
    storage_endpoint: str
    storage_access_key: str
    storage_secret_key: str
    storage_bucket: str = "takeoff-documents"
    storage_use_ssl: bool = False

    # ==========================================================================
    # LLM API Keys - Multi-Provider Support
    # ==========================================================================
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_ai_api_key: str | None = None
    xai_api_key: str | None = None  # Grok

    # ==========================================================================
    # LLM Provider Configuration
    # ==========================================================================
    default_llm_provider: Literal["anthropic", "openai", "google", "xai"] = "anthropic"
    llm_fallback_providers: str = ""  # Comma-separated list

    # Per-task provider overrides (empty = use default)
    llm_provider_page_classification: str = ""
    llm_provider_scale_detection: str = ""
    llm_provider_element_detection: str = ""
    llm_provider_measurement: str = ""

    # Google Cloud Vision (OCR - separate from Gemini)
    google_application_credentials: str | None = None

    @field_validator("llm_fallback_providers", mode="before")
    @classmethod
    def parse_fallback_providers(cls, v: str) -> str:
        """Validate fallback providers."""
        if not v:
            return ""
        valid_providers = {"anthropic", "openai", "google", "xai"}
        providers = [p.strip().lower() for p in v.split(",") if p.strip()]
        invalid = set(providers) - valid_providers
        if invalid:
            raise ValueError(f"Invalid LLM providers: {invalid}")
        return ",".join(providers)

    @property
    def fallback_providers_list(self) -> list[str]:
        """Get fallback providers as a list."""
        if not self.llm_fallback_providers:
            return []
        return [p.strip() for p in self.llm_fallback_providers.split(",")]

    @property
    def available_providers(self) -> list[str]:
        """Get list of providers with configured API keys."""
        providers = []
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.openai_api_key:
            providers.append("openai")
        if self.google_ai_api_key:
            providers.append("google")
        if self.xai_api_key:
            providers.append("xai")
        return providers

    def get_provider_for_task(self, task: str) -> str:
        """Get the LLM provider to use for a specific task.

        Args:
            task: One of 'page_classification', 'scale_detection',
                  'element_detection', 'measurement'

        Returns:
            Provider name to use for this task
        """
        task_overrides = {
            "page_classification": self.llm_provider_page_classification,
            "scale_detection": self.llm_provider_scale_detection,
            "element_detection": self.llm_provider_element_detection,
            "measurement": self.llm_provider_measurement,
        }

        override = task_overrides.get(task, "")
        if override and override in self.available_providers:
            return override

        # Use default if available, otherwise first available
        if self.default_llm_provider in self.available_providers:
            return self.default_llm_provider

        if self.available_providers:
            return self.available_providers[0]

        raise ValueError("No LLM providers configured. Set at least one API key.")

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
