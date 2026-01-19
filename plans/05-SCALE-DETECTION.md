# Phase 2B: Scale Detection and Calibration
## Automatic Scale Detection and Manual Calibration System

> **Duration**: Weeks 8-11
> **Prerequisites**: Phases 1A, 1B, 2A complete (OCR and classification working)
> **Outcome**: Automatic scale detection with manual calibration fallback

---

## Context for LLM Assistant

You are implementing the scale detection and calibration system for a construction takeoff platform. This phase enables:
- Automatic detection of scale notations from OCR text
- Parsing of architectural and engineering scale formats
- Visual scale bar detection using computer vision
- Manual calibration tool for users
- Pixels-to-real-world-units conversion

### Why Scale is Critical
Without accurate scale, all measurements are meaningless. A line that's 500 pixels long could be:
- 10 feet (at 1/4" = 1'-0" on an 8.5x11 page)
- 50 feet (at 1" = 50' on a site plan)
- 2 inches (at full scale detail)

### Common Scale Formats

**Architectural Scales:**
- `1/4" = 1'-0"` (1:48) - Common for floor plans
- `1/8" = 1'-0"` (1:96) - Common for smaller buildings
- `3/16" = 1'-0"` (1:64)
- `1/2" = 1'-0"` (1:24) - Common for details
- `1" = 1'-0"` (1:12) - Large scale details
- `3" = 1'-0"` (1:4) - Full size details

**Engineering Scales:**
- `1" = 10'` (1:120)
- `1" = 20'` (1:240) - Common for site plans
- `1" = 30'` (1:360)
- `1" = 40'` (1:480)
- `1" = 50'` (1:600)
- `1" = 100'` (1:1200)

**Metric Scales:**
- `1:50`
- `1:100`
- `1:200`
- `1:500`

---

## Task List

### Task 5.1: Scale Parser Service

Create `backend/app/services/scale_detector.py`:

```python
"""Scale detection and parsing service."""

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import cv2
import numpy as np
import structlog

from app.services.llm_client import get_llm_client

logger = structlog.get_logger()


@dataclass
class ParsedScale:
    """Parsed scale information."""
    
    original_text: str
    scale_ratio: float  # e.g., 48 for 1/4" = 1'-0" (1:48)
    drawing_unit: str  # "inch" or "foot"
    real_unit: str  # "foot" or "inch"
    is_metric: bool
    confidence: float
    
    @property
    def pixels_per_foot(self) -> float | None:
        """Calculate pixels per foot given standard DPI assumptions.
        
        This is a rough estimate. Actual calibration should use
        known dimensions or manual calibration.
        """
        # Assuming 150 DPI rendering (common for plan images)
        # and the drawing was originally on paper at the stated scale
        if self.is_metric:
            return None  # Metric needs different handling
        
        # For architectural scale like 1/4" = 1'-0":
        # 1 foot on the real building = 1/4" on the drawing
        # At 150 DPI: 1/4" = 150/4 = 37.5 pixels
        # So 1 real foot = 37.5 pixels
        
        dpi = 150
        if self.drawing_unit == "inch":
            # drawing_inches = real_feet / scale_ratio
            # pixels = drawing_inches * dpi
            # pixels_per_foot = dpi / scale_ratio
            return dpi / self.scale_ratio
        
        return None


class ScaleParser:
    """Parser for construction scale notations."""
    
    # Architectural scale patterns
    ARCH_PATTERNS = [
        # 1/4" = 1'-0"
        (r'(\d+)/(\d+)["\']?\s*=\s*1[\'"]\s*-?\s*0["\']?', 'fractional_arch'),
        # 1/4" = 1'
        (r'(\d+)/(\d+)["\']?\s*=\s*1[\'"']', 'fractional_arch_simple'),
        # 1" = 1'-0"
        (r'(\d+)["\']?\s*=\s*1[\'"]\s*-?\s*0["\']?', 'whole_arch'),
        # 3/4" = 1'-0"
        (r'(\d+)/(\d+)["\']?\s*=\s*1[\'"]-0["\']?', 'fractional_arch'),
    ]
    
    # Engineering scale patterns
    ENG_PATTERNS = [
        # 1" = 20'
        (r'1["\']?\s*=\s*(\d+)[\'"']', 'engineering'),
        # 1" = 20'-0"
        (r'1["\']?\s*=\s*(\d+)[\'"]\s*-?\s*0["\']?', 'engineering'),
    ]
    
    # Ratio patterns
    RATIO_PATTERNS = [
        # 1:48, 1:100
        (r'1\s*:\s*(\d+)', 'ratio'),
        # SCALE 1:48
        (r'SCALE\s*1\s*:\s*(\d+)', 'ratio'),
    ]
    
    # Common architectural scale ratios
    ARCH_SCALE_MAP = {
        (3, 1): 4,      # 3" = 1'-0" (1:4)
        (1, 1): 12,     # 1" = 1'-0" (1:12)
        (3, 4): 16,     # 3/4" = 1'-0" (1:16)
        (1, 2): 24,     # 1/2" = 1'-0" (1:24)
        (3, 8): 32,     # 3/8" = 1'-0" (1:32)
        (1, 4): 48,     # 1/4" = 1'-0" (1:48)
        (3, 16): 64,    # 3/16" = 1'-0" (1:64)
        (1, 8): 96,     # 1/8" = 1'-0" (1:96)
        (1, 16): 192,   # 1/16" = 1'-0" (1:192)
    }

    def parse_scale_text(self, text: str) -> ParsedScale | None:
        """Parse a scale notation string.
        
        Args:
            text: Scale text like "1/4\" = 1'-0\"" or "1\" = 20'"
            
        Returns:
            ParsedScale or None if cannot parse
        """
        text = text.strip().upper()
        
        # Check for "NOT TO SCALE"
        if re.search(r'N\.?T\.?S\.?|NOT\s*TO\s*SCALE', text):
            return ParsedScale(
                original_text=text,
                scale_ratio=0,
                drawing_unit="inch",
                real_unit="foot",
                is_metric=False,
                confidence=1.0,
            )
        
        # Try architectural patterns
        for pattern, scale_type in self.ARCH_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_arch_scale(match, scale_type, text)
        
        # Try engineering patterns
        for pattern, scale_type in self.ENG_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_eng_scale(match, text)
        
        # Try ratio patterns
        for pattern, scale_type in self.RATIO_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_ratio_scale(match, text)
        
        return None
    
    def _parse_arch_scale(
        self,
        match: re.Match,
        scale_type: str,
        original: str,
    ) -> ParsedScale:
        """Parse architectural scale format."""
        if scale_type in ('fractional_arch', 'fractional_arch_simple'):
            numerator = int(match.group(1))
            denominator = int(match.group(2))
            
            # Look up in scale map
            key = (numerator, denominator)
            if key in self.ARCH_SCALE_MAP:
                ratio = self.ARCH_SCALE_MAP[key]
            else:
                # Calculate: if n/d inch = 1 foot, ratio = 12 * d / n
                ratio = 12 * denominator / numerator
        else:
            # Whole number like 1" = 1'-0" or 3" = 1'-0"
            inches = int(match.group(1))
            ratio = 12 / inches
        
        return ParsedScale(
            original_text=original,
            scale_ratio=ratio,
            drawing_unit="inch",
            real_unit="foot",
            is_metric=False,
            confidence=0.9,
        )
    
    def _parse_eng_scale(self, match: re.Match, original: str) -> ParsedScale:
        """Parse engineering scale format (1" = X')."""
        feet = int(match.group(1))
        ratio = feet * 12  # Convert to inches for consistency
        
        return ParsedScale(
            original_text=original,
            scale_ratio=ratio,
            drawing_unit="inch",
            real_unit="foot",
            is_metric=False,
            confidence=0.9,
        )
    
    def _parse_ratio_scale(self, match: re.Match, original: str) -> ParsedScale:
        """Parse ratio scale format (1:X)."""
        ratio = int(match.group(1))
        
        # Determine if metric or imperial based on ratio
        is_metric = ratio in (50, 100, 200, 500, 1000)
        
        return ParsedScale(
            original_text=original,
            scale_ratio=ratio,
            drawing_unit="unit",
            real_unit="unit",
            is_metric=is_metric,
            confidence=0.8,
        )


class ScaleBarDetector:
    """Detect graphical scale bars using computer vision."""
    
    def detect_scale_bar(
        self,
        image_bytes: bytes,
    ) -> list[dict[str, Any]]:
        """Detect scale bars in an image.
        
        Looks for horizontal lines with tick marks and numbers
        that indicate a graphical scale.
        
        Returns:
            List of detected scale bar candidates with positions
        """
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            return []
        
        # Edge detection
        edges = cv2.Canny(img, 50, 150)
        
        # Detect horizontal lines using HoughLinesP
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=100,
            minLineLength=100,
            maxLineGap=10,
        )
        
        if lines is None:
            return []
        
        scale_bar_candidates = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Check if line is roughly horizontal
            if abs(y2 - y1) < 5:
                length = abs(x2 - x1)
                
                # Scale bars are typically in a specific size range
                # and located near the bottom of the page
                if 100 < length < 500 and y1 > img.shape[0] * 0.6:
                    scale_bar_candidates.append({
                        "x1": int(x1),
                        "y1": int(y1),
                        "x2": int(x2),
                        "y2": int(y2),
                        "length_pixels": int(length),
                    })
        
        return scale_bar_candidates


class ScaleDetector:
    """Main scale detection service combining OCR and CV approaches."""
    
    def __init__(self):
        self.parser = ScaleParser()
        self.bar_detector = ScaleBarDetector()
        self.llm = get_llm_client()
    
    def detect_scale(
        self,
        image_bytes: bytes,
        ocr_text: str | None = None,
        detected_scale_texts: list[str] | None = None,
    ) -> dict[str, Any]:
        """Detect scale from a page image.
        
        Uses multiple strategies:
        1. Parse OCR-detected scale texts
        2. Use LLM to analyze scale notation in image
        3. Detect graphical scale bars
        
        Args:
            image_bytes: Page image
            ocr_text: Full OCR text from page
            detected_scale_texts: Pre-detected scale text candidates
            
        Returns:
            Detection results with parsed scale and confidence
        """
        results = {
            "parsed_scales": [],
            "scale_bars": [],
            "best_scale": None,
            "needs_calibration": True,
        }
        
        # Strategy 1: Parse pre-detected scale texts
        if detected_scale_texts:
            for text in detected_scale_texts:
                parsed = self.parser.parse_scale_text(text)
                if parsed and parsed.scale_ratio > 0:
                    results["parsed_scales"].append({
                        "text": text,
                        "ratio": parsed.scale_ratio,
                        "pixels_per_foot": parsed.pixels_per_foot,
                        "confidence": parsed.confidence,
                    })
        
        # Strategy 2: Search OCR text for scale patterns
        if ocr_text and not results["parsed_scales"]:
            # Look for scale patterns in full text
            scale_patterns = [
                r'SCALE[:\s]*([^\n]+)',
                r'(\d+/\d+["\']?\s*=\s*[^\n]+)',
                r'(1["\']?\s*=\s*\d+[\'"][^\n]*)',
            ]
            
            for pattern in scale_patterns:
                matches = re.findall(pattern, ocr_text, re.IGNORECASE)
                for match in matches:
                    parsed = self.parser.parse_scale_text(match)
                    if parsed and parsed.scale_ratio > 0:
                        results["parsed_scales"].append({
                            "text": match,
                            "ratio": parsed.scale_ratio,
                            "pixels_per_foot": parsed.pixels_per_foot,
                            "confidence": parsed.confidence * 0.8,  # Lower confidence
                        })
        
        # Strategy 3: Detect graphical scale bars
        results["scale_bars"] = self.bar_detector.detect_scale_bar(image_bytes)
        
        # Select best scale
        if results["parsed_scales"]:
            # Sort by confidence
            sorted_scales = sorted(
                results["parsed_scales"],
                key=lambda x: x["confidence"],
                reverse=True,
            )
            results["best_scale"] = sorted_scales[0]
            
            # High confidence means likely no calibration needed
            if sorted_scales[0]["confidence"] >= 0.85:
                results["needs_calibration"] = False
        
        return results
    
    def calculate_scale_from_calibration(
        self,
        pixel_distance: float,
        real_distance: float,
        real_unit: str = "foot",
    ) -> dict[str, Any]:
        """Calculate scale from a known distance.
        
        Args:
            pixel_distance: Distance in pixels
            real_distance: Real-world distance
            real_unit: Unit of real distance ("foot", "inch", "meter")
            
        Returns:
            Calculated scale information
        """
        if pixel_distance <= 0 or real_distance <= 0:
            raise ValueError("Distances must be positive")
        
        pixels_per_unit = pixel_distance / real_distance
        
        # Convert to pixels per foot for consistency
        if real_unit == "inch":
            pixels_per_foot = pixels_per_unit * 12
        elif real_unit == "meter":
            pixels_per_foot = pixels_per_unit / 3.28084
        else:
            pixels_per_foot = pixels_per_unit
        
        # Estimate scale ratio (assuming 150 DPI original)
        estimated_ratio = 150 / pixels_per_foot
        
        return {
            "pixels_per_foot": pixels_per_foot,
            "pixels_per_unit": pixels_per_unit,
            "unit": real_unit,
            "estimated_ratio": estimated_ratio,
            "method": "manual_calibration",
        }


# Singleton instance
_scale_detector: ScaleDetector | None = None


def get_scale_detector() -> ScaleDetector:
    """Get the scale detector singleton."""
    global _scale_detector
    if _scale_detector is None:
        _scale_detector = ScaleDetector()
    return _scale_detector
```

---

### Task 5.2: Scale Detection Celery Task

Create `backend/app/workers/scale_tasks.py`:

```python
"""Scale detection Celery tasks."""

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.page import Page
from app.services.scale_detector import get_scale_detector
from app.utils.storage import get_storage_service
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()

engine = create_async_engine(str(settings.database_url))
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def run_async(coro):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=2)
def detect_page_scale_task(self, page_id: str) -> dict:
    """Detect scale for a single page.
    
    Args:
        page_id: Page UUID as string
        
    Returns:
        Scale detection result
    """
    logger.info("Starting scale detection", page_id=page_id)
    
    try:
        result = run_async(_detect_page_scale(page_id))
        return result
    except Exception as e:
        logger.error("Scale detection failed", page_id=page_id, error=str(e))
        raise self.retry(exc=e, countdown=30)


async def _detect_page_scale(page_id: str) -> dict:
    """Detect scale for a page."""
    page_uuid = uuid.UUID(page_id)
    
    detector = get_scale_detector()
    storage = get_storage_service()
    
    async with async_session() as session:
        result = await session.execute(
            select(Page).where(Page.id == page_uuid)
        )
        page = result.scalar_one_or_none()
        
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        # Download image
        image_bytes = storage.download_file(page.image_key)
        
        # Get pre-detected scale texts from OCR
        detected_scales = []
        if page.ocr_blocks and "detected_scales" in page.ocr_blocks:
            detected_scales = page.ocr_blocks["detected_scales"]
        
        # Detect scale
        detection = detector.detect_scale(
            image_bytes,
            ocr_text=page.ocr_text,
            detected_scale_texts=detected_scales,
        )
        
        # Update page with scale info
        if detection["best_scale"]:
            best = detection["best_scale"]
            page.scale_text = best["text"]
            page.scale_value = best.get("pixels_per_foot")
            
            if best["confidence"] >= 0.85 and page.scale_value:
                page.scale_calibrated = True
        
        # Store full detection data
        page.scale_calibration_data = detection
        
        await session.commit()
        
        logger.info(
            "Scale detection complete",
            page_id=page_id,
            scale_text=page.scale_text,
            scale_value=page.scale_value,
            calibrated=page.scale_calibrated,
        )
        
        return {
            "status": "success",
            "page_id": page_id,
            "scale_text": page.scale_text,
            "scale_value": page.scale_value,
            "calibrated": page.scale_calibrated,
            "detection": detection,
        }
```

Update celery_app.py to include scale tasks:

```python
include=[
    "app.workers.document_tasks",
    "app.workers.ocr_tasks",
    "app.workers.classification_tasks",
    "app.workers.scale_tasks",  # Add this
],
```

---

### Task 5.3: Scale Calibration API Endpoints

Add to `backend/app/api/routes/pages.py`:

```python
from app.services.scale_detector import get_scale_detector
from app.workers.scale_tasks import detect_page_scale_task


@router.put("/pages/{page_id}/scale")
async def update_page_scale(
    page_id: uuid.UUID,
    request: ScaleUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Manually set or update page scale."""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )
    
    page.scale_value = request.scale_value
    page.scale_unit = request.scale_unit
    page.scale_calibrated = True
    
    if request.scale_text:
        page.scale_text = request.scale_text
    
    # Store calibration source
    if not page.scale_calibration_data:
        page.scale_calibration_data = {}
    page.scale_calibration_data["manual_calibration"] = {
        "scale_value": request.scale_value,
        "scale_unit": request.scale_unit,
        "scale_text": request.scale_text,
    }
    
    await db.commit()
    
    return {
        "status": "success",
        "page_id": str(page_id),
        "scale_value": page.scale_value,
        "scale_unit": page.scale_unit,
        "scale_calibrated": page.scale_calibrated,
    }


@router.post("/pages/{page_id}/calibrate")
async def calibrate_page_scale(
    page_id: uuid.UUID,
    pixel_distance: float,
    real_distance: float,
    real_unit: str = "foot",
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Calibrate page scale using a known distance.
    
    The user draws a line on the page and specifies the real-world distance.
    """
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )
    
    detector = get_scale_detector()
    
    try:
        calibration = detector.calculate_scale_from_calibration(
            pixel_distance=pixel_distance,
            real_distance=real_distance,
            real_unit=real_unit,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Update page
    page.scale_value = calibration["pixels_per_foot"]
    page.scale_unit = "foot"
    page.scale_calibrated = True
    
    # Store calibration data
    if not page.scale_calibration_data:
        page.scale_calibration_data = {}
    page.scale_calibration_data["calibration"] = calibration
    page.scale_calibration_data["calibration_input"] = {
        "pixel_distance": pixel_distance,
        "real_distance": real_distance,
        "real_unit": real_unit,
    }
    
    await db.commit()
    
    return {
        "status": "success",
        "page_id": str(page_id),
        "pixels_per_foot": calibration["pixels_per_foot"],
        "estimated_scale_ratio": calibration["estimated_ratio"],
    }


@router.post("/pages/{page_id}/detect-scale", status_code=status.HTTP_202_ACCEPTED)
async def detect_page_scale(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Trigger automatic scale detection for a page."""
    result = await db.execute(select(Page.id).where(Page.id == page_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )
    
    detect_page_scale_task.delay(str(page_id))
    
    return {"status": "queued", "page_id": str(page_id)}


@router.post("/pages/{page_id}/copy-scale-from/{source_page_id}")
async def copy_scale_from_page(
    page_id: uuid.UUID,
    source_page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Copy scale settings from another page."""
    # Get source page
    result = await db.execute(select(Page).where(Page.id == source_page_id))
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source page not found",
        )
    
    if not source.scale_calibrated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source page is not calibrated",
        )
    
    # Get target page
    result = await db.execute(select(Page).where(Page.id == page_id))
    target = result.scalar_one_or_none()
    
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target page not found",
        )
    
    # Copy scale
    target.scale_value = source.scale_value
    target.scale_unit = source.scale_unit
    target.scale_text = source.scale_text
    target.scale_calibrated = True
    
    if not target.scale_calibration_data:
        target.scale_calibration_data = {}
    target.scale_calibration_data["copied_from"] = str(source_page_id)
    
    await db.commit()
    
    return {
        "status": "success",
        "page_id": str(page_id),
        "scale_value": target.scale_value,
        "copied_from": str(source_page_id),
    }
```

Add to schemas:

```python
# In backend/app/schemas/page.py

class ScaleUpdateRequest(BaseModel):
    """Request to update page scale."""
    
    scale_value: float  # pixels per foot
    scale_unit: str = "foot"
    scale_text: str | None = None


class CalibrationRequest(BaseModel):
    """Request to calibrate scale from known distance."""
    
    pixel_distance: float
    real_distance: float
    real_unit: str = "foot"
```

---

### Task 5.4: Frontend Scale Calibration Component

Create `frontend/src/components/viewer/ScaleCalibration.tsx`:

```tsx
import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Ruler, Check, X, Copy } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { apiClient } from '@/api/client';

interface ScaleCalibrationProps {
  pageId: string;
  currentScale: number | null;
  scaleText: string | null;
  isCalibrated: boolean;
  onCalibrationStart: () => void;
  onCalibrationEnd: () => void;
  calibrationLine: { start: { x: number; y: number }; end: { x: number; y: number } } | null;
}

export function ScaleCalibration({
  pageId,
  currentScale,
  scaleText,
  isCalibrated,
  onCalibrationStart,
  onCalibrationEnd,
  calibrationLine,
}: ScaleCalibrationProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [realDistance, setRealDistance] = useState('');
  const [unit, setUnit] = useState('foot');
  const queryClient = useQueryClient();

  const calibrateMutation = useMutation({
    mutationFn: async (data: {
      pixelDistance: number;
      realDistance: number;
      realUnit: string;
    }) => {
      const response = await apiClient.post(`/pages/${pageId}/calibrate`, null, {
        params: {
          pixel_distance: data.pixelDistance,
          real_distance: data.realDistance,
          real_unit: data.realUnit,
        },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['page', pageId] });
      setIsDialogOpen(false);
      onCalibrationEnd();
    },
  });

  const handleStartCalibration = () => {
    onCalibrationStart();
  };

  const handleCalibrationComplete = () => {
    if (calibrationLine) {
      const dx = calibrationLine.end.x - calibrationLine.start.x;
      const dy = calibrationLine.end.y - calibrationLine.start.y;
      const pixelDistance = Math.sqrt(dx * dx + dy * dy);

      if (pixelDistance > 10) {
        setIsDialogOpen(true);
      }
    }
  };

  const handleSubmitCalibration = () => {
    if (!calibrationLine || !realDistance) return;

    const dx = calibrationLine.end.x - calibrationLine.start.x;
    const dy = calibrationLine.end.y - calibrationLine.start.y;
    const pixelDistance = Math.sqrt(dx * dx + dy * dy);

    calibrateMutation.mutate({
      pixelDistance,
      realDistance: parseFloat(realDistance),
      realUnit: unit,
    });
  };

  const handleCancel = () => {
    setIsDialogOpen(false);
    onCalibrationEnd();
  };

  return (
    <div className="flex items-center gap-2">
      {/* Current scale display */}
      <div className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-md">
        <Ruler className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm">
          {isCalibrated ? (
            <>
              <span className="font-medium">{scaleText || 'Calibrated'}</span>
              {currentScale && (
                <span className="text-muted-foreground ml-1">
                  ({currentScale.toFixed(1)} px/ft)
                </span>
              )}
            </>
          ) : (
            <span className="text-amber-600">Not calibrated</span>
          )}
        </span>
        {isCalibrated && (
          <Check className="h-4 w-4 text-green-600" />
        )}
      </div>

      {/* Calibration button */}
      <Button
        variant="outline"
        size="sm"
        onClick={handleStartCalibration}
      >
        <Ruler className="h-4 w-4 mr-1" />
        {isCalibrated ? 'Recalibrate' : 'Calibrate'}
      </Button>

      {/* Show "Done" button when in calibration mode with a line drawn */}
      {calibrationLine && (
        <Button
          variant="default"
          size="sm"
          onClick={handleCalibrationComplete}
        >
          <Check className="h-4 w-4 mr-1" />
          Done
        </Button>
      )}

      {/* Calibration dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Calibrate Scale</DialogTitle>
            <DialogDescription>
              Enter the real-world distance of the line you drew.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="flex items-end gap-2">
              <div className="flex-1">
                <Label htmlFor="distance">Distance</Label>
                <Input
                  id="distance"
                  type="number"
                  step="0.1"
                  min="0"
                  value={realDistance}
                  onChange={(e) => setRealDistance(e.target.value)}
                  placeholder="e.g., 10"
                />
              </div>
              <div className="w-32">
                <Label htmlFor="unit">Unit</Label>
                <Select value={unit} onValueChange={setUnit}>
                  <SelectTrigger id="unit">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="foot">Feet</SelectItem>
                    <SelectItem value="inch">Inches</SelectItem>
                    <SelectItem value="meter">Meters</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <p className="text-sm text-muted-foreground">
              Tip: Use a dimension line or a known wall length for best accuracy.
            </p>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmitCalibration}
              disabled={!realDistance || calibrateMutation.isPending}
            >
              {calibrateMutation.isPending ? 'Calibrating...' : 'Apply'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Component for copying scale from another page
export function CopyScaleButton({
  pageId,
  pages,
}: {
  pageId: string;
  pages: Array<{ id: string; page_number: number; scale_calibrated: boolean; scale_text: string | null }>;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const queryClient = useQueryClient();

  const copyMutation = useMutation({
    mutationFn: async (sourcePageId: string) => {
      const response = await apiClient.post(
        `/pages/${pageId}/copy-scale-from/${sourcePageId}`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['page', pageId] });
      setIsOpen(false);
    },
  });

  const calibratedPages = pages.filter(
    (p) => p.scale_calibrated && p.id !== pageId
  );

  if (calibratedPages.length === 0) return null;

  return (
    <>
      <Button variant="ghost" size="sm" onClick={() => setIsOpen(true)}>
        <Copy className="h-4 w-4 mr-1" />
        Copy from...
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Copy Scale From Page</DialogTitle>
            <DialogDescription>
              Select a calibrated page to copy its scale settings.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 py-4 max-h-64 overflow-auto">
            {calibratedPages.map((page) => (
              <button
                key={page.id}
                onClick={() => copyMutation.mutate(page.id)}
                disabled={copyMutation.isPending}
                className="w-full flex items-center justify-between p-3 rounded-lg border hover:bg-muted transition-colors"
              >
                <span>Page {page.page_number}</span>
                <span className="text-sm text-muted-foreground">
                  {page.scale_text || 'Calibrated'}
                </span>
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] Scale parser correctly parses "1/4\" = 1'-0\""
- [ ] Scale parser correctly parses "1\" = 20'"
- [ ] Scale parser correctly parses "1:100"
- [ ] Scale parser handles "NOT TO SCALE"
- [ ] Automatic scale detection runs on pages
- [ ] Detected scale stored in database
- [ ] Manual calibration calculates correct pixels/foot
- [ ] Scale can be copied between pages
- [ ] Frontend calibration tool works (draw line, enter distance)
- [ ] Scale indicator shows calibrated/uncalibrated status
- [ ] High-confidence auto-detection marks page as calibrated

### Test Cases

1. Upload a page with "1/4\" = 1'-0\"" visible → auto-detects scale
2. Upload a page with "SCALE: 1\" = 20'" → auto-detects as engineering scale
3. Upload a page with no scale → shows "not calibrated"
4. Manually calibrate a page → scale persists
5. Copy scale from one page to another → both have same scale
6. Draw a 100-pixel line, say it's 10 feet → should get 10 px/ft

---

## Next Phase

Once verified, proceed to **`06-MEASUREMENT-ENGINE.md`** for implementing the core measurement tools and geometry calculations.
