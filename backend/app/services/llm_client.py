"""Multi-provider LLM client service for AI operations.

Supports:
- Anthropic (Claude 3.5 Sonnet)
- OpenAI (GPT-4o)
- Google (Gemini 2.5 Flash)
- xAI (Grok Vision)
"""

import base64
import io
import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import anthropic
import structlog
from PIL import Image
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Claude has a 5MB image limit
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class LLMProvider(str, Enum):
    """Available LLM providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    XAI = "xai"


@dataclass
class LLMResponse:
    """Standardized response from LLM providers."""

    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": self.latency_ms,
        }


# Model configurations for each provider
PROVIDER_MODELS = {
    LLMProvider.ANTHROPIC: "claude-sonnet-4-20250514",
    LLMProvider.OPENAI: "gpt-4o",
    LLMProvider.GOOGLE: "gemini-2.5-flash",
    LLMProvider.XAI: "grok-2-vision-latest",
}


class LLMClient:
    """Client for interacting with vision-language models.

    Supports multiple providers with automatic fallback and consistent interface.
    """

    def __init__(
        self,
        provider: LLMProvider | str = LLMProvider.ANTHROPIC,
        fallback_providers: list[LLMProvider | str] | None = None,
    ):
        """Initialize the LLM client.

        Args:
            provider: Primary LLM provider to use
            fallback_providers: List of providers to try if primary fails
        """
        if isinstance(provider, str):
            provider = LLMProvider(provider)

        self.provider = provider
        self.fallback_providers = []

        if fallback_providers:
            for fp in fallback_providers:
                if isinstance(fp, str):
                    fp = LLMProvider(fp)
                self.fallback_providers.append(fp)

        self._clients: dict[LLMProvider, Any] = {}
        self._init_client(self.provider)

    @property
    def model_name(self) -> str:
        """Get the current model name."""
        return PROVIDER_MODELS.get(self.provider, "unknown")

    def _init_client(self, provider: LLMProvider) -> None:
        """Initialize client for a specific provider."""
        if provider in self._clients:
            return

        if provider == LLMProvider.ANTHROPIC:
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self._clients[provider] = anthropic.Anthropic(
                api_key=settings.anthropic_api_key
            )

        elif provider == LLMProvider.OPENAI:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            import openai

            self._clients[provider] = openai.OpenAI(api_key=settings.openai_api_key)

        elif provider == LLMProvider.GOOGLE:
            if not settings.google_ai_api_key:
                raise ValueError("GOOGLE_AI_API_KEY not configured")
            import google.generativeai as genai

            genai.configure(api_key=settings.google_ai_api_key)
            self._clients[provider] = genai

        elif provider == LLMProvider.XAI:
            if not settings.xai_api_key:
                raise ValueError("XAI_API_KEY not configured")
            import openai

            # xAI uses OpenAI-compatible API
            self._clients[provider] = openai.OpenAI(
                api_key=settings.xai_api_key, base_url="https://api.x.ai/v1"
            )

    def _ensure_fallback_clients(self) -> None:
        """Initialize fallback provider clients."""
        for provider in self.fallback_providers:
            try:
                self._init_client(provider)
            except ValueError as e:
                logger.warning(
                    "Could not initialize fallback provider",
                    provider=provider.value,
                    error=str(e),
                )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(
            (anthropic.RateLimitError, anthropic.APIConnectionError)
        ),
    )
    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 1024,
        provider: LLMProvider | None = None,
    ) -> LLMResponse:
        """Analyze an image with a text prompt.

        Args:
            image_bytes: Image file contents (PNG or JPEG)
            prompt: User prompt for analysis
            system_prompt: Optional system instructions
            max_tokens: Maximum response tokens
            provider: Override provider for this call

        Returns:
            LLMResponse with model output and metadata
        """
        target_provider = provider or self.provider

        # Try primary provider
        try:
            return self._analyze_with_provider(
                target_provider, image_bytes, prompt, system_prompt, max_tokens
            )
        except Exception as e:
            logger.warning(
                "Primary provider failed",
                provider=target_provider.value,
                error=str(e),
            )

            # Try fallback providers
            self._ensure_fallback_clients()
            for fallback in self.fallback_providers:
                try:
                    logger.info("Trying fallback provider", provider=fallback.value)
                    return self._analyze_with_provider(
                        fallback, image_bytes, prompt, system_prompt, max_tokens
                    )
                except Exception as fe:
                    logger.warning(
                        "Fallback provider failed",
                        provider=fallback.value,
                        error=str(fe),
                    )

            # All providers failed
            raise RuntimeError(f"All LLM providers failed. Last error: {e}")

    def _analyze_with_provider(
        self,
        provider: LLMProvider,
        image_bytes: bytes,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
    ) -> LLMResponse:
        """Analyze image with a specific provider."""
        self._init_client(provider)

        start_time = time.time()

        if provider == LLMProvider.ANTHROPIC:
            result = self._analyze_anthropic(
                image_bytes, prompt, system_prompt, max_tokens
            )
        elif provider == LLMProvider.OPENAI:
            result = self._analyze_openai(
                image_bytes, prompt, system_prompt, max_tokens, provider
            )
        elif provider == LLMProvider.GOOGLE:
            result = self._analyze_google(
                image_bytes, prompt, system_prompt, max_tokens
            )
        elif provider == LLMProvider.XAI:
            # xAI uses OpenAI-compatible API
            result = self._analyze_openai(
                image_bytes, prompt, system_prompt, max_tokens, provider
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

        latency_ms = (time.time() - start_time) * 1000
        result.latency_ms = latency_ms

        logger.info(
            "LLM analysis complete",
            provider=provider.value,
            model=result.model,
            latency_ms=round(latency_ms, 2),
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )

        return result

    def _analyze_anthropic(
        self,
        image_bytes: bytes,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
    ) -> LLMResponse:
        """Analyze using Anthropic Claude."""
        client = self._clients[LLMProvider.ANTHROPIC]
        model = PROVIDER_MODELS[LLMProvider.ANTHROPIC]

        # Compress image if needed (Claude has 5MB limit)
        image_bytes = self._compress_image_if_needed(image_bytes)

        image_data = base64.b64encode(image_bytes).decode("utf-8")
        media_type = self._detect_media_type(image_bytes)

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ]

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=messages,
        )

        return LLMResponse(
            content=response.content[0].text,
            provider="anthropic",
            model=model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=0,  # Set by caller
        )

    def _analyze_openai(
        self,
        image_bytes: bytes,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
        provider: LLMProvider,
    ) -> LLMResponse:
        """Analyze using OpenAI GPT-4V or xAI Grok (OpenAI-compatible)."""
        client = self._clients[provider]
        model = PROVIDER_MODELS[provider]

        # Compress image if needed
        image_bytes = self._compress_image_if_needed(image_bytes)

        image_data = base64.b64encode(image_bytes).decode("utf-8")
        media_type = self._detect_media_type(image_bytes)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}",
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        )

        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            provider=provider.value,
            model=model,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            latency_ms=0,
        )

    def _analyze_google(
        self,
        image_bytes: bytes,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
    ) -> LLMResponse:
        """Analyze using Google Gemini."""
        import PIL.Image
        import io

        genai = self._clients[LLMProvider.GOOGLE]
        model_name = PROVIDER_MODELS[LLMProvider.GOOGLE]

        image = PIL.Image.open(io.BytesIO(image_bytes))
        model = genai.GenerativeModel(model_name)

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = model.generate_content(
            [full_prompt, image],
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": 0.1,  # Lower temperature for more deterministic JSON
            },
        )

        # Log response details for debugging
        logger.debug(
            "Gemini response details",
            candidates_count=len(response.candidates) if response.candidates else 0,
            finish_reason=response.candidates[0].finish_reason
            if response.candidates
            else None,
            text_length=len(response.text) if response.text else 0,
        )

        # Check if response was truncated or blocked
        if response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "finish_reason"):
                finish_reason = str(candidate.finish_reason)
                if "SAFETY" in finish_reason or "BLOCKED" in finish_reason:
                    logger.warning(
                        "Gemini response blocked or filtered",
                        finish_reason=finish_reason,
                    )
                elif "MAX_TOKENS" in finish_reason:
                    logger.warning(
                        "Gemini response truncated due to max tokens",
                        finish_reason=finish_reason,
                    )

        # Gemini doesn't provide token counts directly in all cases
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, "usage_metadata"):
            input_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
            output_tokens = getattr(
                response.usage_metadata, "candidates_token_count", 0
            )

        return LLMResponse(
            content=response.text,
            provider="google",
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=0,
        )

    def _detect_media_type(self, image_bytes: bytes) -> str:
        """Detect image media type from bytes."""
        if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        elif image_bytes[:2] == b"\xff\xd8":
            return "image/jpeg"
        elif image_bytes[:4] == b"GIF8":
            return "image/gif"
        elif image_bytes[:4] in (b"II*\x00", b"MM\x00*"):
            return "image/tiff"
        else:
            return "image/png"  # Default

    def _compress_image_if_needed(self, image_bytes: bytes) -> bytes:
        """Compress image if it exceeds size limits.

        Args:
            image_bytes: Original image bytes

        Returns:
            Compressed image bytes (or original if already small enough)
        """
        if len(image_bytes) <= MAX_IMAGE_SIZE_BYTES:
            return image_bytes

        logger.info(
            "Image exceeds size limit, compressing",
            original_size_mb=round(len(image_bytes) / (1024 * 1024), 2),
            limit_mb=5,
        )

        try:
            # Open image
            img = Image.open(io.BytesIO(image_bytes))

            # Convert RGBA to RGB if needed (for JPEG compatibility)
            if img.mode == "RGBA":
                # Create white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = background
            elif img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            # Try progressive quality reduction
            for quality in [85, 75, 65, 55, 45]:
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=quality, optimize=True)
                compressed_bytes = output.getvalue()

                if len(compressed_bytes) <= MAX_IMAGE_SIZE_BYTES:
                    logger.info(
                        "Image compressed successfully",
                        final_size_mb=round(len(compressed_bytes) / (1024 * 1024), 2),
                        quality=quality,
                        compression_ratio=round(
                            len(image_bytes) / len(compressed_bytes), 2
                        ),
                    )
                    return compressed_bytes

            # If still too large, resize the image
            logger.warning("Quality reduction insufficient, resizing image")
            scale_factor = 0.8
            while len(compressed_bytes) > MAX_IMAGE_SIZE_BYTES and scale_factor > 0.3:
                new_size = (
                    int(img.width * scale_factor),
                    int(img.height * scale_factor),
                )
                resized_img = img.resize(new_size, Image.Resampling.LANCZOS)

                output = io.BytesIO()
                resized_img.save(output, format="JPEG", quality=75, optimize=True)
                compressed_bytes = output.getvalue()

                if len(compressed_bytes) <= MAX_IMAGE_SIZE_BYTES:
                    logger.info(
                        "Image resized and compressed",
                        final_size_mb=round(len(compressed_bytes) / (1024 * 1024), 2),
                        scale_factor=scale_factor,
                        new_dimensions=f"{new_size[0]}x{new_size[1]}",
                    )
                    return compressed_bytes

                scale_factor -= 0.1

            # Return best effort
            logger.warning(
                "Could not compress below limit, using best effort",
                final_size_mb=round(len(compressed_bytes) / (1024 * 1024), 2),
            )
            return compressed_bytes

        except Exception as e:
            logger.error("Image compression failed, using original", error=str(e))
            return image_bytes

    def analyze_image_json(
        self,
        image_bytes: bytes,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 1024,
        provider: LLMProvider | None = None,
    ) -> tuple[dict[str, Any], LLMResponse]:
        """Analyze an image and parse JSON response.

        Args:
            image_bytes: Image file contents
            prompt: User prompt (should request JSON output)
            system_prompt: Optional system instructions
            max_tokens: Maximum response tokens
            provider: Override provider for this call

        Returns:
            Tuple of (parsed_json, llm_response)
        """
        response = self.analyze_image(
            image_bytes, prompt, system_prompt, max_tokens, provider
        )

        # Extract JSON from response
        content = response.content
        try:
            # Try to parse directly
            return json.loads(content), response
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re

            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
            if json_match:
                return json.loads(json_match.group(1)), response

            # Try to find JSON object
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                return json.loads(json_match.group(0)), response

            raise ValueError(f"Could not parse JSON from response: {content[:200]}")


# ============================================================================
# Factory functions for getting LLM clients
# ============================================================================

_default_client: LLMClient | None = None


def get_llm_client(
    provider: LLMProvider | str | None = None,
    task: str | None = None,
) -> LLMClient:
    """Get an LLM client instance.

    Args:
        provider: Specific provider to use (overrides task-based selection)
        task: Task name for task-based provider selection
              ('page_classification', 'scale_detection', 'element_detection', 'measurement')

    Returns:
        Configured LLMClient instance
    """
    # Determine provider
    if provider:
        if isinstance(provider, str):
            provider = LLMProvider(provider)
        target_provider = provider
    elif task:
        provider_name = settings.get_provider_for_task(task)
        target_provider = LLMProvider(provider_name)
    else:
        target_provider = LLMProvider(settings.default_llm_provider)

    # Get fallback providers
    fallbacks = [LLMProvider(p) for p in settings.fallback_providers_list]

    return LLMClient(
        provider=target_provider,
        fallback_providers=fallbacks,
    )


def get_default_llm_client() -> LLMClient:
    """Get the default LLM client (cached singleton)."""
    global _default_client
    if _default_client is None:
        _default_client = get_llm_client()
    return _default_client
