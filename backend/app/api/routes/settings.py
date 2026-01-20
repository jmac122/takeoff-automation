"""Settings API routes for LLM provider configuration."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter()
settings = get_settings()


class LLMProviderInfo(BaseModel):
    """Information about an LLM provider."""

    name: str
    display_name: str
    model: str
    available: bool
    is_default: bool


class LLMSettingsResponse(BaseModel):
    """Response with LLM settings."""

    available_providers: list[LLMProviderInfo]
    default_provider: str
    fallback_providers: list[str]
    task_overrides: dict[str, str]


class LLMTaskConfigRequest(BaseModel):
    """Request to update task-specific provider."""

    task: str
    provider: str


PROVIDER_INFO = {
    "anthropic": {
        "display_name": "Anthropic (Claude)",
        "model": "claude-3-5-sonnet-20241022",
    },
    "openai": {
        "display_name": "OpenAI (GPT-4o)",
        "model": "gpt-4o",
    },
    "google": {
        "display_name": "Google (Gemini 1.5 Pro)",
        "model": "gemini-1.5-pro",
    },
    "xai": {
        "display_name": "xAI (Grok)",
        "model": "grok-vision-beta",
    },
}


@router.get("/llm", response_model=LLMSettingsResponse)
async def get_llm_settings() -> LLMSettingsResponse:
    """Get current LLM provider settings."""
    providers = []
    for name, info in PROVIDER_INFO.items():
        providers.append(
            LLMProviderInfo(
                name=name,
                display_name=info["display_name"],
                model=info["model"],
                available=name in settings.available_providers,
                is_default=name == settings.default_llm_provider,
            )
        )

    task_overrides = {
        "page_classification": settings.llm_provider_page_classification
        or settings.default_llm_provider,
        "scale_detection": settings.llm_provider_scale_detection
        or settings.default_llm_provider,
        "element_detection": settings.llm_provider_element_detection
        or settings.default_llm_provider,
        "measurement": settings.llm_provider_measurement
        or settings.default_llm_provider,
    }

    return LLMSettingsResponse(
        available_providers=providers,
        default_provider=settings.default_llm_provider,
        fallback_providers=settings.fallback_providers_list,
        task_overrides=task_overrides,
    )


@router.get("/llm/providers")
async def list_available_providers() -> dict:
    """List available LLM providers with their status and details.

    Returns providers dict with name, display_name, model, strengths, cost_tier, available, is_default.
    """
    providers_dict = {}

    for name, info in PROVIDER_INFO.items():
        # Determine cost tier
        cost_tier = "medium"
        if name == "anthropic":
            cost_tier = "medium-high"
        elif name == "openai":
            cost_tier = "high"
        elif name == "google":
            cost_tier = "low"
        elif name == "xai":
            cost_tier = "medium"

        # Determine strengths
        strengths = ""
        if name == "anthropic":
            strengths = "Best accuracy, excellent for technical documents"
        elif name == "openai":
            strengths = "Fast, reliable, good general performance"
        elif name == "google":
            strengths = "Cost-effective, good for batch processing"
        elif name == "xai":
            strengths = "Fast responses, competitive pricing"

        providers_dict[name] = {
            "name": name,
            "display_name": info["display_name"],
            "model": info["model"],
            "strengths": strengths,
            "cost_tier": cost_tier,
            "available": name in settings.available_providers,
            "is_default": name == settings.default_llm_provider,
        }

    return {
        "providers": providers_dict,
    }
