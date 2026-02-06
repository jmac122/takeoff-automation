# Phase 4A: AI Takeoff Generation
## Automated Element Detection and Measurement

> **Duration**: Weeks 16-22
> **Prerequisites**: Measurement engine and conditions working (Phases 3A, 3B)
> **Outcome**: AI-powered automatic detection and measurement of concrete elements

---

## Context for LLM Assistant

You are implementing the AI-powered takeoff generation system. This is the core value proposition—using vision-language models to automatically detect and measure concrete elements on construction plans.

### Multi-Provider LLM Support

The platform supports **four LLM providers** that can be configured per-task:

| Provider | Model | Strengths |
|----------|-------|-----------|
| Anthropic | Claude 3.5 Sonnet | Best document understanding |
| OpenAI | GPT-4o | Good spatial reasoning |
| Google | Gemini 2.5 Flash | Cost-effective |
| xAI | Grok Vision | Alternative option |

Different providers may excel at different tasks. The system supports:
- Default provider for all tasks
- Per-task provider overrides (based on benchmarking)
- Runtime provider selection for A/B testing
- Automatic fallback on provider failure

### AI Takeoff Workflow

```
1. User selects a page
2. User chooses condition type (e.g., "4" Slab", "Foundation")
3. System determines which LLM provider to use for this task
4. AI analyzes the page image
5. AI identifies relevant elements
6. AI generates measurements (polygons, lines, counts)
7. User reviews and refines
```

### Detection Strategies

| Element Type | Detection Method | Output | Best Provider* |
|--------------|------------------|--------|----------------|
| Slab areas | Polygon detection via LLM | Area polygons | TBD via benchmark |
| Foundation walls | Line detection | Polylines | TBD via benchmark |
| Footings | Pattern recognition | Lines or polygons | TBD via benchmark |
| Columns/Piers | Point detection | Count markers | TBD via benchmark |
| Openings | Exclusion zones | Negative areas | TBD via benchmark |

*Best provider determined by running accuracy benchmarks (see Phase 5B)

### AI Takeoff vs Auto Count

This phase (AI Takeoff) and Auto Count (`14-AUTO-COUNT.md`) serve different purposes:

| Feature | AI Takeoff (This Phase) | Auto Count (Phase 4B) |
|---------|-------------------------|----------------------|
| **Use Case** | First-pass detection of areas, lines, elements | Counting repetitive identical elements |
| **Method** | LLM vision analysis | Template matching + LLM similarity |
| **Best For** | Slab outlines, foundation walls, footings | Piers, columns, bolts, fixtures |
| **User Action** | Select condition → AI detects all instances | Select ONE instance → find all similar |
| **Output** | Polygons, polylines, points | Count with locations |

**When to use which:**
- Use **AI Takeoff** for unique or varied elements that need boundary detection
- Use **Auto Count** when you have many identical items to count quickly

### Accuracy Targets

- **75% accuracy** for initial detection
- Human review for refinement
- Track AI confidence scores
- Track accuracy per provider for optimization
- Learn from corrections (future enhancement)

---

## Task List

### Task 8.1: AI Takeoff Service with Provider Selection

Create `backend/app/services/ai_takeoff.py`:

```python
"""AI-powered takeoff generation service with multi-provider support."""

import json
import re
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.services.llm_client import get_llm_client, LLMProvider, LLMResponse
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class DetectedElement:
    """An element detected by AI."""
    
    element_type: str  # slab, footing, wall, column, etc.
    geometry_type: str  # polygon, polyline, line, point
    geometry_data: dict[str, Any]
    confidence: float
    description: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "element_type": self.element_type,
            "geometry_type": self.geometry_type,
            "geometry_data": self.geometry_data,
            "confidence": self.confidence,
            "description": self.description,
        }


@dataclass
class AITakeoffResult:
    """Result of AI takeoff analysis."""
    
    elements: list[DetectedElement]
    page_description: str
    analysis_notes: str
    # LLM metadata for tracking and benchmarking
    llm_provider: str = ""
    llm_model: str = ""
    llm_latency_ms: float = 0.0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "elements": [e.to_dict() for e in self.elements],
            "page_description": self.page_description,
            "analysis_notes": self.analysis_notes,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_latency_ms": self.llm_latency_ms,
            "llm_input_tokens": self.llm_input_tokens,
            "llm_output_tokens": self.llm_output_tokens,
        }


TAKEOFF_SYSTEM_PROMPT = """You are an expert construction estimator analyzing construction plan drawings to identify and measure concrete elements.

Your task is to identify specific concrete elements on the drawing and provide their locations as geometric shapes that can be used for quantity takeoff.

CRITICAL: You must provide coordinates as pixel positions on the image. The image dimensions will be provided.

When identifying elements:
1. Look for hatching patterns that indicate concrete (diagonal lines, dots)
2. Look for labels like "CONC.", "CONCRETE", "SOG" (slab on grade)
3. Identify foundation walls, footings, slabs, columns, and piers
4. Note any dimensions shown on the drawing
5. Exclude openings, equipment pads, and non-concrete areas

Respond with valid JSON only."""


AREA_DETECTION_PROMPT = """Analyze this construction plan image ({width}x{height} pixels) and identify all {element_type} areas.

For each {element_type} area found, provide:
1. A polygon (list of points) that outlines the area
2. Your confidence level (0.0-1.0)
3. A brief description

Points should be in pixel coordinates where (0,0) is top-left.

The page scale is approximately {scale_description}.

Respond with JSON in this exact format:
{{
    "page_description": "Brief description of what this page shows",
    "elements": [
        {{
            "geometry_type": "polygon",
            "points": [{{"x": 100, "y": 200}}, {{"x": 300, "y": 200}}, {{"x": 300, "y": 400}}, {{"x": 100, "y": 400}}],
            "confidence": 0.85,
            "description": "Main slab area - approximately 50'x30'"
        }}
    ],
    "analysis_notes": "Notes about the analysis"
}}

Focus specifically on: {element_type}
Additional context: {context}"""


LINEAR_DETECTION_PROMPT = """Analyze this construction plan image ({width}x{height} pixels) and identify all {element_type} elements.

For each {element_type} found, provide:
1. A polyline (list of points) that traces the centerline
2. Your confidence level (0.0-1.0)
3. A brief description

Points should be in pixel coordinates where (0,0) is top-left.

The page scale is approximately {scale_description}.

Respond with JSON in this exact format:
{{
    "page_description": "Brief description of what this page shows",
    "elements": [
        {{
            "geometry_type": "polyline",
            "points": [{{"x": 100, "y": 200}}, {{"x": 300, "y": 200}}, {{"x": 300, "y": 400}}],
            "confidence": 0.85,
            "description": "Foundation wall - north side"
        }}
    ],
    "analysis_notes": "Notes about the analysis"
}}

Focus specifically on: {element_type}
Additional context: {context}"""


COUNT_DETECTION_PROMPT = """Analyze this construction plan image ({width}x{height} pixels) and identify all {element_type} locations.

For each {element_type} found, provide:
1. A point (x, y) marking its center location
2. Your confidence level (0.0-1.0)
3. A brief description

Points should be in pixel coordinates where (0,0) is top-left.

The page scale is approximately {scale_description}.

Respond with JSON in this exact format:
{{
    "page_description": "Brief description of what this page shows",
    "elements": [
        {{
            "geometry_type": "point",
            "x": 150,
            "y": 250,
            "confidence": 0.9,
            "description": "Column C1 - 12x12"
        }}
    ],
    "analysis_notes": "Notes about the analysis"
}}

Focus specifically on: {element_type}
Additional context: {context}"""


class AITakeoffService:
    """Service for AI-powered takeoff generation with multi-provider support."""
    
    ELEMENT_PROMPTS = {
        "area": AREA_DETECTION_PROMPT,
        "linear": LINEAR_DETECTION_PROMPT,
        "count": COUNT_DETECTION_PROMPT,
    }
    
    def __init__(self, provider: str | None = None):
        """Initialize the service.
        
        Args:
            provider: Override LLM provider (default: use task-based config)
        """
        self.provider_override = provider

    def analyze_page(
        self,
        image_bytes: bytes,
        width: int,
        height: int,
        element_type: str,
        measurement_type: str,
        scale_text: str | None = None,
        ocr_text: str | None = None,
        provider: str | None = None,
    ) -> AITakeoffResult:
        """Analyze a page and detect elements for takeoff.
        
        Args:
            image_bytes: Page image
            width: Image width in pixels
            height: Image height in pixels
            element_type: Type of element to detect (e.g., "concrete slab", "foundation wall")
            measurement_type: "area", "linear", or "count"
            scale_text: Page scale (e.g., "1/4\" = 1'-0\"")
            ocr_text: OCR text from page (for context)
            provider: Override LLM provider for this call
            
        Returns:
            AITakeoffResult with detected elements
        """
        # Determine task-based provider
        task_map = {
            "area": "element_detection",
            "linear": "element_detection",
            "count": "element_detection",
        }
        task = task_map.get(measurement_type, "element_detection")
        
        # Get LLM client with appropriate provider
        llm = get_llm_client(
            provider=provider or self.provider_override,
            task=task,
        )
        
        # Select appropriate prompt template
        prompt_template = self.ELEMENT_PROMPTS.get(measurement_type, AREA_DETECTION_PROMPT)
        
        # Build context
        scale_description = scale_text or "unknown - use visual cues for relative sizing"
        context = ""
        if ocr_text:
            context = f"Text found on page (truncated): {ocr_text[:500]}"
        
        # Build prompt
        prompt = prompt_template.format(
            width=width,
            height=height,
            element_type=element_type,
            scale_description=scale_description,
            context=context,
        )
        
        # Call LLM
        try:
            data, response = llm.analyze_image_json(
                image_bytes=image_bytes,
                prompt=prompt,
                system_prompt=TAKEOFF_SYSTEM_PROMPT,
                max_tokens=2048,
            )
            
            # Parse detected elements
            elements = []
            for elem in data.get("elements", []):
                geometry_type = elem.get("geometry_type", "polygon")
                
                if geometry_type == "point":
                    geometry_data = {"x": elem.get("x", 0), "y": elem.get("y", 0)}
                else:
                    geometry_data = {"points": elem.get("points", [])}
                
                elements.append(DetectedElement(
                    element_type=element_type,
                    geometry_type=geometry_type,
                    geometry_data=geometry_data,
                    confidence=float(elem.get("confidence", 0.5)),
                    description=elem.get("description", ""),
                ))
            
            # Validate geometries are within bounds
            elements = self._filter_valid_geometries(elements, width, height)
            
            logger.info(
                "AI takeoff analysis complete",
                element_type=element_type,
                measurement_type=measurement_type,
                elements_detected=len(elements),
                provider=response.provider,
                model=response.model,
                latency_ms=response.latency_ms,
            )
            
            return AITakeoffResult(
                elements=elements,
                page_description=data.get("page_description", ""),
                analysis_notes=data.get("analysis_notes", ""),
                llm_provider=response.provider,
                llm_model=response.model,
                llm_latency_ms=response.latency_ms,
                llm_input_tokens=response.input_tokens,
                llm_output_tokens=response.output_tokens,
            )
            
        except Exception as e:
            logger.error(
                "AI takeoff analysis failed",
                element_type=element_type,
                error=str(e),
            )
            raise
    
    def _filter_valid_geometries(
        self,
        elements: list[DetectedElement],
        width: int,
        height: int,
    ) -> list[DetectedElement]:
        """Filter out elements with invalid geometries."""
        valid = []
        
        for elem in elements:
            if elem.geometry_type == "point":
                x = elem.geometry_data.get("x", 0)
                y = elem.geometry_data.get("y", 0)
                if 0 <= x <= width and 0 <= y <= height:
                    valid.append(elem)
            else:
                points = elem.geometry_data.get("points", [])
                if all(
                    0 <= p.get("x", -1) <= width and 0 <= p.get("y", -1) <= height
                    for p in points
                ):
                    valid.append(elem)
        
        return valid
    
    def analyze_page_multi_provider(
        self,
        image_bytes: bytes,
        width: int,
        height: int,
        element_type: str,
        measurement_type: str,
        scale_text: str | None = None,
        ocr_text: str | None = None,
        providers: list[str] | None = None,
    ) -> dict[str, AITakeoffResult]:
        """Analyze a page with multiple providers for comparison.
        
        Useful for benchmarking and A/B testing.
        
        Args:
            providers: List of providers to use (default: all available)
            ... other args same as analyze_page
            
        Returns:
            Dict mapping provider name to results
        """
        if providers is None:
            providers = settings.available_providers
        
        results = {}
        for provider in providers:
            try:
                result = self.analyze_page(
                    image_bytes=image_bytes,
                    width=width,
                    height=height,
                    element_type=element_type,
                    measurement_type=measurement_type,
                    scale_text=scale_text,
                    ocr_text=ocr_text,
                    provider=provider,
                )
                results[provider] = result
            except Exception as e:
                logger.warning(
                    "Provider failed in multi-provider analysis",
                    provider=provider,
                    error=str(e),
                )
        
        return results


# Convenience function
def get_ai_takeoff_service(provider: str | None = None) -> AITakeoffService:
    """Get an AI takeoff service instance.
    
    Args:
        provider: Override LLM provider
        
    Returns:
        Configured AITakeoffService
    """
    return AITakeoffService(provider=provider)
```

---

### Task 8.2: Takeoff Worker Task with Provider Support

Create `backend/app/workers/tasks/takeoff.py`:

```python
"""Celery tasks for AI takeoff generation."""

import structlog
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_sync_db
from app.models import Page, Condition, Measurement
from app.services.ai_takeoff import get_ai_takeoff_service, AITakeoffResult
from app.services.storage import get_storage_client
from app.utils.geometry import MeasurementCalculator

logger = structlog.get_logger()


@shared_task(bind=True, max_retries=3)
def generate_ai_takeoff_task(
    self,
    page_id: str,
    condition_id: str,
    provider: str | None = None,
) -> dict:
    """Generate AI takeoff for a page and condition.
    
    Args:
        page_id: Page UUID
        condition_id: Condition UUID
        provider: Optional LLM provider override
        
    Returns:
        Result summary dict
    """
    logger.info(
        "Starting AI takeoff generation",
        page_id=page_id,
        condition_id=condition_id,
        provider=provider,
    )
    
    try:
        with get_sync_db() as db:
            # Get page and condition
            page = db.execute(
                select(Page).where(Page.id == page_id)
            ).scalar_one_or_none()
            
            condition = db.execute(
                select(Condition).where(Condition.id == condition_id)
            ).scalar_one_or_none()
            
            if not page:
                raise ValueError(f"Page not found: {page_id}")
            if not condition:
                raise ValueError(f"Condition not found: {condition_id}")
            
            # Verify page is calibrated
            if not page.scale_calibrated:
                raise ValueError("Page must be calibrated before AI takeoff")
            
            # Get page image
            storage = get_storage_client()
            image_bytes = storage.get_object(page.image_storage_path)
            
            # Get AI takeoff service
            ai_service = get_ai_takeoff_service(provider=provider)
            
            # Analyze page
            result = ai_service.analyze_page(
                image_bytes=image_bytes,
                width=page.width,
                height=page.height,
                element_type=condition.element_type or condition.name,
                measurement_type=condition.measurement_type,
                scale_text=page.scale_text,
                ocr_text=page.ocr_text,
            )
            
            # Create measurements from detected elements
            calculator = MeasurementCalculator(
                pixels_per_foot=page.pixels_per_foot or 24.0
            )
            
            measurements_created = 0
            for elem in result.elements:
                measurement = create_measurement_from_element(
                    db, page, condition, elem, calculator, result
                )
                if measurement:
                    db.add(measurement)
                    measurements_created += 1
            
            db.commit()
            
            logger.info(
                "AI takeoff complete",
                page_id=page_id,
                condition_id=condition_id,
                elements_detected=len(result.elements),
                measurements_created=measurements_created,
                provider=result.llm_provider,
                model=result.llm_model,
                latency_ms=result.llm_latency_ms,
            )
            
            return {
                "page_id": page_id,
                "condition_id": condition_id,
                "elements_detected": len(result.elements),
                "measurements_created": measurements_created,
                "page_description": result.page_description,
                "analysis_notes": result.analysis_notes,
                "llm_provider": result.llm_provider,
                "llm_model": result.llm_model,
                "llm_latency_ms": result.llm_latency_ms,
            }
            
    except Exception as e:
        logger.error(
            "AI takeoff failed",
            page_id=page_id,
            condition_id=condition_id,
            error=str(e),
        )
        raise self.retry(exc=e, countdown=60)


def create_measurement_from_element(
    db: Session,
    page: Page,
    condition: Condition,
    element: "DetectedElement",
    calculator: "MeasurementCalculator",
    result: AITakeoffResult,
) -> Measurement | None:
    """Create a Measurement record from a detected element."""
    from app.models import Measurement
    import uuid
    
    # Calculate quantity based on geometry type
    if element.geometry_type == "polygon":
        points = element.geometry_data.get("points", [])
        if len(points) < 3:
            return None
        quantity = calculator.calculate_polygon_area(
            [(p["x"], p["y"]) for p in points]
        )
        unit = "SF"
    
    elif element.geometry_type in ("line", "polyline"):
        points = element.geometry_data.get("points", [])
        if len(points) < 2:
            return None
        quantity = calculator.calculate_polyline_length(
            [(p["x"], p["y"]) for p in points]
        )
        unit = "LF"
    
    elif element.geometry_type == "point":
        quantity = 1
        unit = "EA"
    
    else:
        return None
    
    return Measurement(
        id=uuid.uuid4(),
        page_id=page.id,
        condition_id=condition.id,
        geometry_type=element.geometry_type,
        geometry_data=element.geometry_data,
        quantity=quantity,
        unit=unit,
        description=element.description,
        confidence=element.confidence,
        is_ai_generated=True,
        ai_provider=result.llm_provider,
        ai_model=result.llm_model,
    )


@shared_task
def compare_providers_task(
    page_id: str,
    condition_id: str,
    providers: list[str] | None = None,
) -> dict:
    """Run AI takeoff with multiple providers for comparison.
    
    Useful for benchmarking provider accuracy.
    
    Args:
        page_id: Page UUID
        condition_id: Condition UUID
        providers: List of providers to compare (default: all available)
        
    Returns:
        Comparison results
    """
    from app.config import get_settings
    settings = get_settings()
    
    if providers is None:
        providers = settings.available_providers
    
    logger.info(
        "Starting multi-provider comparison",
        page_id=page_id,
        condition_id=condition_id,
        providers=providers,
    )
    
    with get_sync_db() as db:
        page = db.execute(
            select(Page).where(Page.id == page_id)
        ).scalar_one_or_none()
        
        condition = db.execute(
            select(Condition).where(Condition.id == condition_id)
        ).scalar_one_or_none()
        
        if not page or not condition:
            raise ValueError("Page or condition not found")
        
        storage = get_storage_client()
        image_bytes = storage.get_object(page.image_storage_path)
        
        ai_service = get_ai_takeoff_service()
        
        results = ai_service.analyze_page_multi_provider(
            image_bytes=image_bytes,
            width=page.width,
            height=page.height,
            element_type=condition.element_type or condition.name,
            measurement_type=condition.measurement_type,
            scale_text=page.scale_text,
            ocr_text=page.ocr_text,
            providers=providers,
        )
        
        comparison = {}
        for provider, result in results.items():
            comparison[provider] = {
                "elements_detected": len(result.elements),
                "latency_ms": result.llm_latency_ms,
                "input_tokens": result.llm_input_tokens,
                "output_tokens": result.llm_output_tokens,
                "model": result.llm_model,
                "elements": [e.to_dict() for e in result.elements],
            }
        
        logger.info(
            "Multi-provider comparison complete",
            page_id=page_id,
            providers_compared=len(results),
        )
        
        return {
            "page_id": page_id,
            "condition_id": condition_id,
            "providers_compared": list(results.keys()),
            "results": comparison,
        }
```

---

### Task 8.3: Takeoff API with Provider Selection

Create `backend/app/api/routes/takeoff.py`:

```python
"""API routes for AI takeoff generation."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.config import get_settings
from app.workers.tasks.takeoff import (
    generate_ai_takeoff_task,
    compare_providers_task,
)

router = APIRouter()
settings = get_settings()


class GenerateTakeoffRequest(BaseModel):
    """Request to generate AI takeoff."""
    condition_id: str
    provider: str | None = None  # Optional provider override


class CompareProvidersRequest(BaseModel):
    """Request to compare providers."""
    condition_id: str
    providers: list[str] | None = None  # None = all available


class TakeoffTaskResponse(BaseModel):
    """Response with task ID."""
    task_id: str
    message: str


@router.post("/pages/{page_id}/ai-takeoff", response_model=TakeoffTaskResponse)
async def generate_ai_takeoff(
    page_id: str,
    request: GenerateTakeoffRequest,
) -> TakeoffTaskResponse:
    """Generate AI takeoff for a page.
    
    Optionally specify an LLM provider to use.
    Available providers: anthropic, openai, google, xai
    """
    provider = request.provider
    
    if provider and provider not in settings.available_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' not available. "
                   f"Available: {settings.available_providers}"
        )
    
    task = generate_ai_takeoff_task.delay(
        page_id,
        request.condition_id,
        provider=provider,
    )
    
    provider_msg = f" using {provider}" if provider else ""
    
    return TakeoffTaskResponse(
        task_id=task.id,
        message=f"AI takeoff started for page {page_id}{provider_msg}",
    )


@router.post("/pages/{page_id}/compare-providers", response_model=TakeoffTaskResponse)
async def compare_providers(
    page_id: str,
    request: CompareProvidersRequest,
) -> TakeoffTaskResponse:
    """Compare AI takeoff results across multiple providers.
    
    Useful for benchmarking which provider works best for specific content.
    """
    providers = request.providers
    
    if providers:
        invalid = set(providers) - set(settings.available_providers)
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Providers not available: {invalid}. "
                       f"Available: {settings.available_providers}"
            )
    
    task = compare_providers_task.delay(
        page_id,
        request.condition_id,
        providers=providers,
    )
    
    return TakeoffTaskResponse(
        task_id=task.id,
        message=f"Provider comparison started for page {page_id}",
    )


@router.get("/pages/{page_id}/ai-takeoff/providers")
async def get_available_providers() -> dict:
    """Get available LLM providers for AI takeoff."""
    return {
        "available": settings.available_providers,
        "default": settings.default_llm_provider,
        "task_config": {
            "element_detection": settings.get_provider_for_task("element_detection"),
            "measurement": settings.get_provider_for_task("measurement"),
        },
    }
```

---

### Task 8.4: Frontend AI Takeoff Button with Provider Selection

Update `frontend/src/components/AITakeoffButton.tsx`:

```tsx
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Sparkles, Loader2, Check, AlertCircle, FlaskConical } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { LLMProviderSelector } from './LLMProviderSelector';

interface AITakeoffButtonProps {
  pageId: string;
  conditionId: string;
  conditionName: string;
  isPageCalibrated: boolean;
  onComplete?: (result: any) => void;
}

type TaskStatus = 'idle' | 'pending' | 'processing' | 'success' | 'error';

export function AITakeoffButton({
  pageId,
  conditionId,
  conditionName,
  isPageCalibrated,
  onComplete,
}: AITakeoffButtonProps) {
  const [showDialog, setShowDialog] = useState(false);
  const [taskStatus, setTaskStatus] = useState<TaskStatus>('idle');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string | undefined>(undefined);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const queryClient = useQueryClient();

  const generateMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(
        `/pages/${pageId}/ai-takeoff`,
        {
          condition_id: conditionId,
          provider: selectedProvider,
        }
      );
      return response.data;
    },
    onSuccess: async (data) => {
      setTaskStatus('processing');
      
      // Poll for task completion
      const taskId = data.task_id;
      let attempts = 0;
      const maxAttempts = 60; // 5 minutes max
      
      const poll = async () => {
        try {
          const statusResponse = await apiClient.get(`/tasks/${taskId}/status`);
          const status = statusResponse.data;
          
          if (status.status === 'SUCCESS') {
            setTaskStatus('success');
            setResult(status.result);
            queryClient.invalidateQueries({ queryKey: ['measurements', pageId] });
            queryClient.invalidateQueries({ queryKey: ['conditions'] });
            onComplete?.(status.result);
          } else if (status.status === 'FAILURE') {
            setTaskStatus('error');
            setError(status.error || 'Generation failed');
          } else if (attempts < maxAttempts) {
            attempts++;
            setTimeout(poll, 5000);
          } else {
            setTaskStatus('error');
            setError('Generation timed out');
          }
        } catch (e) {
          setTaskStatus('error');
          setError('Failed to check status');
        }
      };
      
      setTimeout(poll, 2000);
    },
    onError: (error: any) => {
      setTaskStatus('error');
      setError(error.response?.data?.detail || 'Failed to start generation');
    },
  });

  const handleStart = () => {
    setTaskStatus('pending');
    setResult(null);
    setError(null);
    setShowDialog(true);
    generateMutation.mutate();
  };

  const handleClose = () => {
    setShowDialog(false);
    setTaskStatus('idle');
  };

  if (!isPageCalibrated) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <span>
              <Button variant="outline" size="sm" disabled>
                <Sparkles className="h-4 w-4 mr-1" />
                AI Takeoff
              </Button>
            </span>
          </TooltipTrigger>
          <TooltipContent>
            <p>Calibrate page scale first</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={handleStart}>
          <Sparkles className="h-4 w-4 mr-1" />
          AI Takeoff
        </Button>
        
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                <FlaskConical className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Advanced: Select AI provider</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {showAdvanced && (
        <div className="mt-2">
          <LLMProviderSelector
            value={selectedProvider}
            onChange={setSelectedProvider}
            label="AI Provider"
          />
        </div>
      )}

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>AI Takeoff Generation</DialogTitle>
            <DialogDescription>
              Detecting {conditionName} elements on this page
              {selectedProvider && ` using ${selectedProvider}`}
            </DialogDescription>
          </DialogHeader>

          <div className="py-6">
            {taskStatus === 'pending' && (
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                <span>Starting analysis...</span>
              </div>
            )}

            {taskStatus === 'processing' && (
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                <div>
                  <p>Analyzing page...</p>
                  <p className="text-sm text-muted-foreground">
                    This may take 30-60 seconds
                  </p>
                </div>
              </div>
            )}

            {taskStatus === 'success' && result && (
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-green-600">
                  <Check className="h-5 w-5" />
                  <span>Analysis complete!</span>
                </div>
                <div className="bg-muted p-3 rounded-lg space-y-1 text-sm">
                  <p>
                    <strong>Elements detected:</strong> {result.elements_detected}
                  </p>
                  <p>
                    <strong>Measurements created:</strong> {result.measurements_created}
                  </p>
                  <p>
                    <strong>Provider:</strong> {result.llm_provider} ({result.llm_model})
                  </p>
                  <p>
                    <strong>Processing time:</strong> {Math.round(result.llm_latency_ms)}ms
                  </p>
                  {result.page_description && (
                    <p className="text-muted-foreground">
                      {result.page_description}
                    </p>
                  )}
                </div>
                {result.analysis_notes && (
                  <p className="text-sm text-muted-foreground">
                    {result.analysis_notes}
                  </p>
                )}
              </div>
            )}

            {taskStatus === 'error' && (
              <div className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-5 w-5" />
                <span>{error || 'An error occurred'}</span>
              </div>
            )}
          </div>

          <DialogFooter>
            {taskStatus === 'success' || taskStatus === 'error' ? (
              <Button onClick={handleClose}>Close</Button>
            ) : (
              <Button variant="outline" onClick={handleClose} disabled>
                Cancel
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
```

---

### Task 8.5: Provider Comparison UI Component

Create `frontend/src/components/ProviderComparison.tsx`:

```tsx
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, FlaskConical, Clock, Hash, DollarSign } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface ProviderComparisonProps {
  pageId: string;
  conditionId: string;
  conditionName: string;
}

interface ProviderResult {
  elements_detected: number;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  model: string;
}

export function ProviderComparison({
  pageId,
  conditionId,
  conditionName,
}: ProviderComparisonProps) {
  const [results, setResults] = useState<Record<string, ProviderResult> | null>(null);

  const compareMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/pages/${pageId}/compare-providers`, {
        condition_id: conditionId,
      });
      
      // Poll for results
      const taskId = response.data.task_id;
      let attempts = 0;
      
      while (attempts < 120) { // 10 minutes max
        await new Promise(resolve => setTimeout(resolve, 5000));
        const statusResponse = await apiClient.get(`/tasks/${taskId}/status`);
        
        if (statusResponse.data.status === 'SUCCESS') {
          return statusResponse.data.result;
        } else if (statusResponse.data.status === 'FAILURE') {
          throw new Error(statusResponse.data.error || 'Comparison failed');
        }
        attempts++;
      }
      
      throw new Error('Comparison timed out');
    },
    onSuccess: (data) => {
      setResults(data.results);
    },
  });

  const estimateCost = (result: ProviderResult, provider: string): string => {
    // Rough cost estimates per 1M tokens
    const costs: Record<string, { input: number; output: number }> = {
      anthropic: { input: 3, output: 15 },
      openai: { input: 2.5, output: 10 },
      google: { input: 1.25, output: 5 },
      xai: { input: 5, output: 15 },
    };
    
    const rate = costs[provider] || { input: 3, output: 15 };
    const cost = (result.input_tokens * rate.input + result.output_tokens * rate.output) / 1_000_000;
    return `$${cost.toFixed(4)}`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FlaskConical className="h-5 w-5" />
          Provider Comparison
        </CardTitle>
        <CardDescription>
          Compare AI takeoff results across different providers for {conditionName}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!results && (
          <Button
            onClick={() => compareMutation.mutate()}
            disabled={compareMutation.isPending}
          >
            {compareMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Running comparison...
              </>
            ) : (
              <>
                <FlaskConical className="h-4 w-4 mr-2" />
                Compare All Providers
              </>
            )}
          </Button>
        )}

        {results && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(results).map(([provider, result]) => (
                <Card key={provider}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg capitalize">{provider}</CardTitle>
                    <CardDescription className="text-xs">{result.model}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground flex items-center gap-1">
                        <Hash className="h-3 w-3" />
                        Elements
                      </span>
                      <Badge variant="secondary">{result.elements_detected}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Latency
                      </span>
                      <Badge variant="outline">{Math.round(result.latency_ms)}ms</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground flex items-center gap-1">
                        <DollarSign className="h-3 w-3" />
                        Est. Cost
                      </span>
                      <Badge variant="outline">{estimateCost(result, provider)}</Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Button variant="outline" onClick={() => setResults(null)}>
              Run Again
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] AI service connects to all configured providers
- [ ] Provider fallback works when primary fails
- [ ] Polygon detection works for slab areas
- [ ] Polyline detection works for linear elements
- [ ] Point detection works for count elements
- [ ] Detected geometries are within page bounds
- [ ] Measurements created with correct quantities
- [ ] AI confidence scores stored
- [ ] Provider and model tracked with each measurement
- [ ] is_ai_generated flag set correctly
- [ ] Task polling works correctly
- [ ] Frontend shows provider selection option
- [ ] Frontend shows provider used in results
- [ ] Provider comparison tool works
- [ ] Uncalibrated pages blocked from AI takeoff
- [ ] Errors handled gracefully with fallback

### Test Cases

1. Run AI takeoff on a foundation plan with clear slab area → detects polygon
2. Run AI takeoff on a plan with foundation walls → detects polylines
3. Run AI takeoff with column locations → detects points
4. Verify measurements have correct quantities based on scale
5. Check that low-confidence detections are still created but flagged
6. Run with each provider individually → all produce results
7. Run provider comparison → shows results from all providers
8. Disable primary provider → falls back to secondary

### Accuracy Testing
## Next Phase

Once verified, proceed to **`14-AUTO-COUNT.md`** for implementing the Auto Count feature.

Auto Count enables rapid counting of repetitive elements:
- **Template Matching**: Use OpenCV to find visually similar elements
- **LLM Similarity**: Use vision models to find semantically similar elements
- **Hybrid Detection**: Combine both methods for best results
- **Bulk Creation**: Create measurements from all confirmed detections

This is especially useful for:
- Counting piers and columns on foundation plans
- Counting fixtures, anchors, or bolts
- Any repetitive element where you want to "select one, find all"

After Auto Count, continue to **`09-REVIEW-INTERFACE-ENHANCED.md`** for the human review and refinement interface with keyboard shortcuts and auto-accept features.
