"""Page classification service using vision LLM."""

from dataclasses import dataclass
from typing import Any

import structlog

from app.services.llm_client import get_llm_client

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
                max_tokens=1024,  # Increased for Gemini which may need more tokens
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
