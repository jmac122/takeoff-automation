# Phase 2A: Page Classification
## AI-Powered Page Type Identification

> **Duration**: Weeks 6-9
> **Prerequisites**: Phases 1A and 1B complete (documents uploaded, OCR working)
> **Outcome**: Automatic classification of plan pages by type (structural, site, mechanical, etc.)

---

## Context for LLM Assistant

You are implementing AI-powered page classification for a construction takeoff platform. This phase uses vision-language models to:
- Classify pages by discipline (Architectural, Structural, Civil, etc.)
- Identify page types (Plan, Elevation, Section, Detail, Schedule)
- Detect which pages contain concrete scope
- Enable filtering and navigation by page type

### Multi-Provider LLM Support

The platform supports **four LLM providers** for AI operations:
- **Anthropic** (Claude 3.5 Sonnet) - Recommended primary
- **OpenAI** (GPT-4o)
- **Google** (Gemini 2.5 Flash)
- **xAI** (Grok Vision)

This allows benchmarking across providers and configuring the best provider per task.

### Why Classification Matters
A typical construction plan set has 50-200+ pages across many disciplines. Estimators need to quickly find:
- **Foundation Plans** (concrete footings)
- **Structural Plans** (concrete slabs, columns, beams)
- **Site Plans** (concrete paving, curbs)
- **Detail Sheets** (concrete specifications)

Classification helps users navigate directly to relevant pages.

### Classification Categories

**Disciplines:**
- Architectural (A)
- Structural (S)
- Civil/Site (C)
- Mechanical (M)
- Electrical (E)
- Plumbing (P)
- Landscape (L)
- General/Cover (G)

**Page Types:**
- Plan View
- Elevation
- Section
- Detail
- Schedule
- Notes/Legend
- Cover Sheet
- Title Sheet

**Concrete Relevance:**
- `high` - Page primarily shows concrete work
- `medium` - Page contains some concrete elements
- `low` - Page has minimal/no concrete
- `none` - Definitely no concrete

---

## Task List

### Task 4.1: Multi-Provider LLM Client Service

Create `backend/app/services/llm_client.py`:

```python
"""Multi-provider LLM client service for AI operations.

Supports:
- Anthropic (Claude 3.5 Sonnet)
- OpenAI (GPT-4o)
- Google (Gemini 2.5 Flash)
- xAI (Grok Vision)
"""

import base64
import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import anthropic
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


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
    LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    LLMProvider.OPENAI: "gpt-4o",
    LLMProvider.GOOGLE: "gemini-1.5-pro",
    LLMProvider.XAI: "grok-vision-beta",
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
            self._clients[provider] = openai.OpenAI(
                api_key=settings.openai_api_key
            )
        
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
                api_key=settings.xai_api_key,
                base_url="https://api.x.ai/v1"
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
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIConnectionError)),
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
            result = self._analyze_anthropic(image_bytes, prompt, system_prompt, max_tokens)
        elif provider == LLMProvider.OPENAI:
            result = self._analyze_openai(image_bytes, prompt, system_prompt, max_tokens, provider)
        elif provider == LLMProvider.GOOGLE:
            result = self._analyze_google(image_bytes, prompt, system_prompt, max_tokens)
        elif provider == LLMProvider.XAI:
            # xAI uses OpenAI-compatible API
            result = self._analyze_openai(image_bytes, prompt, system_prompt, max_tokens, provider)
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
        
        image_data = base64.b64encode(image_bytes).decode("utf-8")
        media_type = self._detect_media_type(image_bytes)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({
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
        })
        
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
            generation_config={"max_output_tokens": max_tokens},
        )
        
        # Gemini doesn't provide token counts directly in all cases
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata'):
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
        
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
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif image_bytes[:2] == b'\xff\xd8':
            return "image/jpeg"
        elif image_bytes[:4] == b'GIF8':
            return "image/gif"
        elif image_bytes[:4] in (b'II*\x00', b'MM\x00*'):
            return "image/tiff"
        else:
            return "image/png"  # Default
    
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
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if json_match:
                return json.loads(json_match.group(1)), response
            
            # Try to find JSON object
            json_match = re.search(r'\{[\s\S]*\}', content)
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
```

---

### Task 4.2: Page Classification Service

Create `backend/app/services/page_classifier.py`:

```python
"""Page classification service using vision LLM."""

from dataclasses import dataclass
from typing import Any

import structlog

from app.services.llm_client import get_llm_client, LLMResponse

logger = structlog.get_logger()


@dataclass
class ClassificationResult:
    """Result of page classification."""
    
    discipline: str
    discipline_confidence: float
    page_type: str
    page_type_confidence: float
    concrete_relevance: str
    concrete_elements: list[str]
    description: str
    # LLM metadata for tracking
    llm_provider: str
    llm_model: str
    llm_latency_ms: float
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "discipline": self.discipline,
            "discipline_confidence": self.discipline_confidence,
            "page_type": self.page_type,
            "page_type_confidence": self.page_type_confidence,
            "concrete_relevance": self.concrete_relevance,
            "concrete_elements": self.concrete_elements,
            "description": self.description,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_latency_ms": self.llm_latency_ms,
        }


CLASSIFICATION_SYSTEM_PROMPT = """You are an expert construction document analyst specializing in reading and classifying construction plans and drawings.

You will analyze construction plan images and classify them according to:
1. Discipline (Architectural, Structural, Civil, etc.)
2. Page type (Plan, Elevation, Section, Detail, Schedule, etc.)
3. Concrete relevance for takeoff purposes

Be precise and confident in your classifications. Use the sheet number prefix if visible (A=Architectural, S=Structural, C=Civil, etc.) to help with discipline classification."""


CLASSIFICATION_PROMPT = """Analyze this construction plan page and classify it.

Look for:
- Sheet number/prefix (e.g., S1.01 = Structural, A2.01 = Architectural)
- Drawing types visible (plans, elevations, sections, details)
- Concrete elements (foundations, slabs, columns, walls, paving)
- Title block information

Respond with JSON in this exact format:
{
    "discipline": "Structural|Architectural|Civil|Mechanical|Electrical|Plumbing|Landscape|General",
    "discipline_confidence": 0.95,
    "page_type": "Plan|Elevation|Section|Detail|Schedule|Notes|Cover|Title",
    "page_type_confidence": 0.90,
    "concrete_relevance": "high|medium|low|none",
    "concrete_elements": ["slab", "foundation wall", "footing"],
    "description": "Foundation plan showing footings and grade beams"
}

Only respond with valid JSON."""


class PageClassifier:
    """Service for classifying construction plan pages using LLM vision."""
    
    def __init__(self, provider: str | None = None):
        """Initialize the classifier.
        
        Args:
            provider: Override LLM provider (default: use task-based config)
        """
        self.provider_override = provider
    
    def classify_page(
        self,
        image_bytes: bytes,
        ocr_text: str | None = None,
    ) -> ClassificationResult:
        """Classify a construction plan page.
        
        Args:
            image_bytes: Page image as bytes (PNG or JPEG)
            ocr_text: Optional OCR text from page for additional context
            
        Returns:
            ClassificationResult with discipline, page type, and concrete relevance
        """
        # Get LLM client for page classification task
        llm = get_llm_client(
            provider=self.provider_override,
            task="page_classification",
        )
        
        # Build prompt with optional OCR context
        prompt = CLASSIFICATION_PROMPT
        if ocr_text:
            prompt += f"\n\nOCR text found on page (for context):\n{ocr_text[:1000]}"
        
        # Analyze image
        try:
            data, response = llm.analyze_image_json(
                image_bytes=image_bytes,
                prompt=prompt,
                system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
                max_tokens=512,
            )
            
            return ClassificationResult(
                discipline=data.get("discipline", "Unknown"),
                discipline_confidence=float(data.get("discipline_confidence", 0.0)),
                page_type=data.get("page_type", "Unknown"),
                page_type_confidence=float(data.get("page_type_confidence", 0.0)),
                concrete_relevance=data.get("concrete_relevance", "none"),
                concrete_elements=data.get("concrete_elements", []),
                description=data.get("description", ""),
                llm_provider=response.provider,
                llm_model=response.model,
                llm_latency_ms=response.latency_ms,
            )
            
        except Exception as e:
            logger.error("Page classification failed", error=str(e))
            raise


# Convenience function
def classify_page(
    image_bytes: bytes,
    ocr_text: str | None = None,
    provider: str | None = None,
) -> ClassificationResult:
    """Classify a construction plan page.
    
    Args:
        image_bytes: Page image as bytes
        ocr_text: Optional OCR text for context
        provider: Override LLM provider
        
    Returns:
        ClassificationResult
    """
    classifier = PageClassifier(provider=provider)
    return classifier.classify_page(image_bytes, ocr_text)
```

---

### Task 4.3: Classification Worker Task

Create `backend/app/workers/tasks/classify.py`:

```python
"""Celery tasks for page classification."""

import structlog
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_sync_db
from app.models import Page
from app.services.page_classifier import classify_page
from app.services.storage import get_storage_client

logger = structlog.get_logger()


@shared_task(bind=True, max_retries=3)
def classify_page_task(
    self,
    page_id: str,
    provider: str | None = None,
) -> dict:
    """Classify a single page.
    
    Args:
        page_id: Page UUID
        provider: Optional LLM provider override
        
    Returns:
        Classification result dict
    """
    logger.info("Starting page classification", page_id=page_id, provider=provider)
    
    try:
        with get_sync_db() as db:
            # Get page
            page = db.execute(
                select(Page).where(Page.id == page_id)
            ).scalar_one_or_none()
            
            if not page:
                raise ValueError(f"Page not found: {page_id}")
            
            # Get page image from storage
            storage = get_storage_client()
            image_bytes = storage.get_object(page.image_storage_path)
            
            # Classify
            result = classify_page(
                image_bytes=image_bytes,
                ocr_text=page.ocr_text,
                provider=provider,
            )
            
            # Update page record
            page.classification = f"{result.discipline}:{result.page_type}"
            page.classification_confidence = min(
                result.discipline_confidence,
                result.page_type_confidence,
            )
            page.concrete_relevance = result.concrete_relevance
            page.classification_metadata = result.to_dict()
            
            db.commit()
            
            logger.info(
                "Page classification complete",
                page_id=page_id,
                discipline=result.discipline,
                page_type=result.page_type,
                concrete_relevance=result.concrete_relevance,
                provider=result.llm_provider,
                latency_ms=result.llm_latency_ms,
            )
            
            return result.to_dict()
            
    except Exception as e:
        logger.error("Page classification failed", page_id=page_id, error=str(e))
        raise self.retry(exc=e, countdown=60)


@shared_task
def classify_document_pages(
    document_id: str,
    provider: str | None = None,
) -> dict:
    """Classify all pages in a document.
    
    Args:
        document_id: Document UUID
        provider: Optional LLM provider override
        
    Returns:
        Summary of classification results
    """
    logger.info("Starting document classification", document_id=document_id)
    
    with get_sync_db() as db:
        pages = db.execute(
            select(Page).where(Page.document_id == document_id)
        ).scalars().all()
        
        task_ids = []
        for page in pages:
            task = classify_page_task.delay(str(page.id), provider=provider)
            task_ids.append(task.id)
        
        return {
            "document_id": document_id,
            "pages_queued": len(task_ids),
            "task_ids": task_ids,
        }
```

---

### Task 4.4: Classification API Endpoints

Create `backend/app/api/routes/classification.py`:

```python
"""API routes for page classification."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.config import get_settings
from app.workers.tasks.classify import classify_page_task, classify_document_pages

router = APIRouter()
settings = get_settings()


class ClassifyPageRequest(BaseModel):
    """Request to classify a single page."""
    provider: str | None = None  # Optional provider override


class ClassifyDocumentRequest(BaseModel):
    """Request to classify all pages in a document."""
    provider: str | None = None  # Optional provider override


class ClassificationTaskResponse(BaseModel):
    """Response with task ID for async classification."""
    task_id: str
    message: str


class DocumentClassificationResponse(BaseModel):
    """Response for document classification."""
    document_id: str
    pages_queued: int
    task_ids: list[str]


@router.post(
    "/pages/{page_id}/classify",
    response_model=ClassificationTaskResponse,
)
async def classify_page(
    page_id: str,
    request: ClassifyPageRequest | None = None,
) -> ClassificationTaskResponse:
    """Trigger classification for a single page.
    
    Optionally specify an LLM provider to use for this classification.
    Available providers: anthropic, openai, google, xai
    """
    provider = request.provider if request else None
    
    # Validate provider if specified
    if provider and provider not in settings.available_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' not available. "
                   f"Available: {settings.available_providers}"
        )
    
    task = classify_page_task.delay(page_id, provider=provider)
    
    return ClassificationTaskResponse(
        task_id=task.id,
        message=f"Classification started for page {page_id}"
            + (f" using {provider}" if provider else ""),
    )


@router.post(
    "/documents/{document_id}/classify",
    response_model=DocumentClassificationResponse,
)
async def classify_document(
    document_id: str,
    request: ClassifyDocumentRequest | None = None,
) -> DocumentClassificationResponse:
    """Trigger classification for all pages in a document.
    
    Optionally specify an LLM provider to use for classification.
    """
    provider = request.provider if request else None
    
    if provider and provider not in settings.available_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' not available. "
                   f"Available: {settings.available_providers}"
        )
    
    result = classify_document_pages.delay(document_id, provider=provider)
    
    # Wait briefly for task to start and get info
    try:
        info = result.get(timeout=5)
        return DocumentClassificationResponse(**info)
    except Exception:
        return DocumentClassificationResponse(
            document_id=document_id,
            pages_queued=0,
            task_ids=[result.id],
        )


@router.get("/pages/{page_id}/classification")
async def get_page_classification(page_id: str) -> dict:
    """Get classification results for a page."""
    from sqlalchemy import select
    from app.database import get_async_db
    from app.models import Page
    
    async with get_async_db() as db:
        page = await db.execute(
            select(Page).where(Page.id == page_id)
        )
        page = page.scalar_one_or_none()
        
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        return {
            "page_id": str(page.id),
            "classification": page.classification,
            "confidence": page.classification_confidence,
            "concrete_relevance": page.concrete_relevance,
            "metadata": page.classification_metadata,
        }
```

---

### Task 4.5: Frontend Provider Selector Component

Create `frontend/src/components/LLMProviderSelector.tsx`:

```tsx
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Bot, Zap, DollarSign } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Provider {
  name: string;
  display_name: string;
  model: string;
  strengths: string;
  cost_tier: string;
  available: boolean;
  is_default: boolean;
}

interface LLMProviderSelectorProps {
  value?: string;
  onChange: (provider: string | undefined) => void;
  showDefault?: boolean;
  label?: string;
}

const COST_COLORS = {
  low: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  'medium-high': 'bg-orange-100 text-orange-700',
  high: 'bg-red-100 text-red-700',
};

export function LLMProviderSelector({
  value,
  onChange,
  showDefault = true,
  label = 'AI Provider',
}: LLMProviderSelectorProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['llm-providers'],
    queryFn: async () => {
      const response = await apiClient.get<{ providers: Record<string, Provider> }>(
        '/settings/llm/providers'
      );
      return response.data;
    },
  });

  const providers = data?.providers || {};
  const availableProviders = Object.values(providers).filter(p => p.available);

  if (isLoading) {
    return <div className="h-10 w-48 bg-muted animate-pulse rounded-md" />;
  }

  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium">{label}</label>}
      <Select value={value || 'default'} onValueChange={(v) => onChange(v === 'default' ? undefined : v)}>
        <SelectTrigger className="w-[220px]">
          <SelectValue placeholder="Select provider" />
        </SelectTrigger>
        <SelectContent>
          {showDefault && (
            <SelectItem value="default">
              <div className="flex items-center gap-2">
                <Bot className="h-4 w-4" />
                <span>Default (Auto)</span>
              </div>
            </SelectItem>
          )}
          {availableProviders.map((provider) => (
            <SelectItem key={provider.name} value={provider.name}>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4" />
                      <span>{provider.display_name}</span>
                      {provider.is_default && (
                        <Badge variant="secondary" className="text-xs">Default</Badge>
                      )}
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="right" className="max-w-xs">
                    <div className="space-y-1">
                      <p className="font-medium">{provider.model}</p>
                      <p className="text-xs text-muted-foreground">{provider.strengths}</p>
                      <Badge className={COST_COLORS[provider.cost_tier as keyof typeof COST_COLORS]}>
                        <DollarSign className="h-3 w-3 mr-1" />
                        {provider.cost_tier}
                      </Badge>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
```

---

### Task 4.6: Page Browser with Classification Filters

[... PageBrowser component code remains largely unchanged, 
just ensure it uses the classification data ...]

---

## Verification Checklist

After completing all tasks, verify:

- [ ] LLM client connects to all configured providers
- [ ] Provider fallback works when primary fails
- [ ] Page classification returns valid discipline and page type
- [ ] Concrete relevance accurately identifies concrete-heavy pages
- [ ] Classification runs automatically or on-demand
- [ ] Classification data stored in database with LLM metadata
- [ ] Frontend can select provider for classification
- [ ] Frontend filter by discipline works
- [ ] Frontend filter by concrete relevance works
- [ ] High-concrete pages highlighted visually
- [ ] Classification confidence stored
- [ ] Errors handled gracefully with fallback

### Test Cases

1. Upload a Foundation Plan → should classify as "Structural:Plan" with high concrete relevance
2. Upload an Electrical Plan → should classify as "Electrical:Plan" with low/none concrete relevance
3. Upload a Site Plan with paving → should show medium-high concrete relevance
4. Filter to "Structural" pages only → only S-prefixed sheets shown
5. Filter to "high concrete" → only concrete-relevant pages shown
6. Test with different providers → results should be similar across providers
7. Disable primary provider API key → should fallback to secondary provider

---

## Next Phase

Once verified, proceed to **`05-SCALE-DETECTION.md`** for implementing automatic scale detection and calibration.
