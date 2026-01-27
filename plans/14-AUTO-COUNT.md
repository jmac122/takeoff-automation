# Phase 4C: Auto Count Feature
## Similarity-Based Object Detection and Counting

> **Duration**: Weeks 24-27
> **Prerequisites**: AI takeoff generation working (Phase 4A), Review interface working (Phase 4B)
> **Outcome**: Select one object, find and count all similar objects automatically

---

## Context for LLM Assistant

You are implementing the "Auto Count" feature—a powerful tool that lets users select one instance of a repeating element (like a pier, column, or symbol) and automatically find all similar instances on the page or document.

### What is Auto Count?

Auto Count solves one of the most tedious takeoff tasks: counting repetitive elements. Instead of manually clicking each pier, anchor bolt, or equipment pad, the estimator:

1. **Selects one example** (clicks on a single pier symbol)
2. **System finds all matches** (identifies every similar pier on the page)
3. **Generates count measurements** (creates a measurement for each detected instance)

### Real-World Use Cases

| Element | Traditional Method | Auto Count Method |
|---------|-------------------|-------------------|
| Concrete piers | Click each one (50+ clicks) | Select one, find 50 |
| Column grid intersections | Manual count | Select one, detect pattern |
| Anchor bolts | Count from schedule | Select one, verify count |
| Equipment pads | Measure each | Select one, find all |
| Catch basins | Manual count | Select one, find matches |
| Light pole bases | Click each | Select one, find all |
| Bollards | Manual count | Select one, detect all |

### Technical Approach

We'll implement a hybrid approach combining:

1. **Template Matching** (OpenCV) - Fast, works well for identical symbols
2. **Feature Embedding** (Vision LLM) - Handles variations, rotations, scale differences
3. **Clustering** - Groups similar detections, removes duplicates

```
User Flow:
1. User clicks on an element (pier symbol)
2. System extracts a template region around the click
3. Template matching finds exact/near matches
4. LLM embedding finds semantic matches (rotated, scaled)
5. Results are clustered to remove duplicates
6. User reviews and confirms matches
7. Count measurements created for confirmed matches
```

### Accuracy Targets

- **90%+ recall** - Find most instances (miss very few)
- **85%+ precision** - Most detections are correct (few false positives)
- **Sub-second latency** for template matching
- **<5 second latency** for LLM-enhanced detection

---

## Database Models

### Task 14.1: Auto Count Models

Create `backend/app/models/auto_count.py`:

```python
"""Auto count models for similarity-based detection."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import String, Float, Integer, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.page import Page
    from app.models.condition import Condition


class AutoCountSession(Base, UUIDMixin, TimestampMixin):
    """
    An auto count session for detecting similar objects.
    
    Stores the template, detection settings, and results for
    a single auto count operation.
    """

    __tablename__ = "auto_count_sessions"

    # Foreign keys
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
    )
    condition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conditions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Session info
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Template definition (the "example" the user selected)
    template_center_x: Mapped[float] = mapped_column(Float, nullable=False)
    template_center_y: Mapped[float] = mapped_column(Float, nullable=False)
    template_width: Mapped[float] = mapped_column(Float, nullable=False)
    template_height: Mapped[float] = mapped_column(Float, nullable=False)
    template_image_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # Base64
    
    # Detection settings
    detection_method: Mapped[str] = mapped_column(
        String(50),
        default="hybrid",
    )  # template_match, llm_embedding, hybrid
    
    similarity_threshold: Mapped[float] = mapped_column(Float, default=0.8)
    scale_tolerance: Mapped[float] = mapped_column(Float, default=0.2)  # ±20%
    rotation_tolerance: Mapped[float] = mapped_column(Float, default=15)  # ±15 degrees
    
    # Search scope
    search_scope: Mapped[str] = mapped_column(
        String(50),
        default="page",
    )  # page, document, selected_pages
    search_page_ids: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    
    # Results summary
    total_detections: Mapped[int] = mapped_column(Integer, default=0)
    confirmed_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    pending_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Processing status
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
    )  # pending, processing, completed, failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timing
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    page: Mapped["Page"] = relationship("Page")
    condition: Mapped["Condition | None"] = relationship("Condition")
    detections: Mapped[list["AutoCountDetection"]] = relationship(
        "AutoCountDetection",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class AutoCountDetection(Base, UUIDMixin, TimestampMixin):
    """
    A single detection from an auto count session.
    
    Each detection represents a potential match found by the
    similarity algorithm.
    """

    __tablename__ = "auto_count_detections"

    # Foreign keys
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auto_count_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # If confirmed, links to created measurement
    measurement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("measurements.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Detection location
    center_x: Mapped[float] = mapped_column(Float, nullable=False)
    center_y: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    rotation: Mapped[float] = mapped_column(Float, default=0)  # degrees
    
    # Bounding box (for display)
    bbox_x1: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_y1: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_x2: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_y2: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Confidence scores
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    template_match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    llm_embedding_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Detection method that found this
    detected_by: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # User review status
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
    )  # pending, confirmed, rejected
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Ranking (for display order)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    session: Mapped["AutoCountSession"] = relationship(
        "AutoCountSession",
        back_populates="detections",
    )
    page: Mapped["Page"] = relationship("Page")
```

Create migration:

```bash
alembic revision --autogenerate -m "add_auto_count_models"
alembic upgrade head
```

---

## Auto Count Service

### Task 14.2: Template Matching Service

Create `backend/app/services/template_matching.py`:

```python
"""Template matching service using OpenCV."""

import io
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
from PIL import Image

import structlog

logger = structlog.get_logger()


@dataclass
class TemplateMatch:
    """A template match result."""
    
    center_x: float
    center_y: float
    width: float
    height: float
    score: float
    rotation: float = 0
    scale: float = 1.0
    
    @property
    def bbox(self) -> tuple[float, float, float, float]:
        """Get bounding box (x1, y1, x2, y2)."""
        half_w = self.width / 2
        half_h = self.height / 2
        return (
            self.center_x - half_w,
            self.center_y - half_h,
            self.center_x + half_w,
            self.center_y + half_h,
        )


class TemplateMatchingService:
    """
    Service for finding similar objects using template matching.
    
    Uses OpenCV's template matching with multi-scale and
    optional rotation support.
    """
    
    def __init__(
        self,
        default_threshold: float = 0.8,
        nms_threshold: float = 0.3,
    ):
        self.default_threshold = default_threshold
        self.nms_threshold = nms_threshold
    
    def find_matches(
        self,
        image_bytes: bytes,
        template_bytes: bytes,
        threshold: float | None = None,
        scale_range: tuple[float, float] = (0.8, 1.2),
        scale_steps: int = 5,
        rotation_range: tuple[float, float] | None = None,
        rotation_steps: int = 7,
        max_results: int = 500,
    ) -> list[TemplateMatch]:
        """
        Find all instances of a template in an image.
        
        Args:
            image_bytes: The source image as bytes
            template_bytes: The template to search for
            threshold: Minimum similarity score (0-1)
            scale_range: Min/max scale factors to try
            scale_steps: Number of scales to test
            rotation_range: Min/max rotation angles (degrees), None for no rotation
            rotation_steps: Number of rotations to test
            max_results: Maximum number of matches to return
            
        Returns:
            List of TemplateMatch objects
        """
        threshold = threshold or self.default_threshold
        
        # Load images
        image = self._load_image(image_bytes)
        template = self._load_image(template_bytes)
        
        if image is None or template is None:
            logger.error("Failed to load image or template")
            return []
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = image
            
        if len(template.shape) == 3:
            gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            gray_template = template
        
        all_matches: list[TemplateMatch] = []
        
        # Generate scales to test
        scales = np.linspace(scale_range[0], scale_range[1], scale_steps)
        
        # Generate rotations to test
        if rotation_range:
            rotations = np.linspace(rotation_range[0], rotation_range[1], rotation_steps)
        else:
            rotations = [0]
        
        template_h, template_w = gray_template.shape[:2]
        
        for scale in scales:
            for rotation in rotations:
                # Scale and rotate template
                scaled_template = self._scale_and_rotate(
                    gray_template, scale, rotation
                )
                
                if scaled_template is None:
                    continue
                
                scaled_h, scaled_w = scaled_template.shape[:2]
                
                # Skip if template is larger than image
                if scaled_w > gray_image.shape[1] or scaled_h > gray_image.shape[0]:
                    continue
                
                # Perform template matching
                result = cv2.matchTemplate(
                    gray_image,
                    scaled_template,
                    cv2.TM_CCOEFF_NORMED,
                )
                
                # Find locations above threshold
                locations = np.where(result >= threshold)
                
                for pt_y, pt_x in zip(*locations):
                    score = result[pt_y, pt_x]
                    
                    # Calculate center
                    center_x = pt_x + scaled_w / 2
                    center_y = pt_y + scaled_h / 2
                    
                    all_matches.append(TemplateMatch(
                        center_x=float(center_x),
                        center_y=float(center_y),
                        width=float(template_w * scale),
                        height=float(template_h * scale),
                        score=float(score),
                        rotation=float(rotation),
                        scale=float(scale),
                    ))
        
        # Apply non-maximum suppression
        matches = self._apply_nms(all_matches)
        
        # Sort by score and limit results
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:max_results]
    
    def extract_template(
        self,
        image_bytes: bytes,
        center_x: float,
        center_y: float,
        width: float,
        height: float,
        padding: float = 0.1,
    ) -> bytes | None:
        """
        Extract a template region from an image.
        
        Args:
            image_bytes: Source image
            center_x, center_y: Center of template region
            width, height: Size of template region
            padding: Extra padding around the region (percentage)
            
        Returns:
            Template image as bytes
        """
        image = self._load_image(image_bytes)
        if image is None:
            return None
        
        img_h, img_w = image.shape[:2]
        
        # Add padding
        width = width * (1 + padding)
        height = height * (1 + padding)
        
        # Calculate bounds
        x1 = max(0, int(center_x - width / 2))
        y1 = max(0, int(center_y - height / 2))
        x2 = min(img_w, int(center_x + width / 2))
        y2 = min(img_h, int(center_y + height / 2))
        
        # Extract region
        template = image[y1:y2, x1:x2]
        
        # Convert to bytes
        _, buffer = cv2.imencode('.png', template)
        return buffer.tobytes()
    
    def _load_image(self, image_bytes: bytes) -> np.ndarray | None:
        """Load image from bytes."""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            logger.error("Failed to load image", error=str(e))
            return None
    
    def _scale_and_rotate(
        self,
        image: np.ndarray,
        scale: float,
        rotation: float,
    ) -> np.ndarray | None:
        """Scale and rotate an image."""
        try:
            h, w = image.shape[:2]
            
            # Scale
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            if new_w < 10 or new_h < 10:
                return None
            
            scaled = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # Rotate if needed
            if abs(rotation) > 0.1:
                center = (new_w // 2, new_h // 2)
                matrix = cv2.getRotationMatrix2D(center, rotation, 1.0)
                rotated = cv2.warpAffine(
                    scaled, matrix, (new_w, new_h),
                    borderMode=cv2.BORDER_REPLICATE,
                )
                return rotated
            
            return scaled
            
        except Exception as e:
            logger.error("Scale/rotate failed", error=str(e))
            return None
    
    def _apply_nms(
        self,
        matches: list[TemplateMatch],
    ) -> list[TemplateMatch]:
        """Apply non-maximum suppression to remove overlapping detections."""
        if not matches:
            return []
        
        # Convert to numpy arrays for NMS
        boxes = np.array([[m.bbox[0], m.bbox[1], m.bbox[2], m.bbox[3]] for m in matches])
        scores = np.array([m.score for m in matches])
        
        # Apply NMS
        indices = cv2.dnn.NMSBoxes(
            boxes.tolist(),
            scores.tolist(),
            score_threshold=0.0,
            nms_threshold=self.nms_threshold,
        )
        
        # Handle different OpenCV versions
        if len(indices) > 0:
            if isinstance(indices, np.ndarray):
                indices = indices.flatten()
            else:
                indices = [i[0] if isinstance(i, (list, tuple)) else i for i in indices]
        
        return [matches[i] for i in indices]


# Singleton
_service: TemplateMatchingService | None = None

def get_template_matching_service() -> TemplateMatchingService:
    """Get the template matching service singleton."""
    global _service
    if _service is None:
        _service = TemplateMatchingService()
    return _service
```

---

### Task 14.3: LLM Similarity Service

Create `backend/app/services/llm_similarity.py`:

```python
"""LLM-based similarity detection using vision embeddings."""

import base64
import io
from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image

import structlog

from app.services.llm_client import get_llm_client, LLMProvider
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class SimilarityMatch:
    """A similarity match from LLM analysis."""
    
    center_x: float
    center_y: float
    width: float
    height: float
    similarity_score: float
    description: str = ""
    confidence: float = 0.0


class LLMSimilarityService:
    """
    Service for finding similar objects using LLM vision capabilities.
    
    Uses vision LLMs to understand semantic similarity, handling
    variations in rotation, scale, and style that template matching misses.
    """
    
    SIMILARITY_PROMPT = """Analyze this construction plan image and find all instances similar to the highlighted template region.

The template (highlighted in the overlay) shows: {template_description}

Image dimensions: {width}x{height} pixels
Template region: center ({template_x}, {template_y}), size {template_w}x{template_h}

Find ALL instances of similar objects on this page. For each instance found, provide:
1. Center coordinates (x, y) in pixels
2. Approximate size (width, height)
3. Confidence score (0.0-1.0)
4. Brief description

Consider objects similar if they:
- Have the same general shape/symbol
- Serve the same purpose (e.g., all pier symbols, all column marks)
- May be rotated, scaled, or slightly different in appearance

Respond with JSON only:
{{
  "template_interpretation": "description of what the template shows",
  "matches": [
    {{
      "center_x": 150,
      "center_y": 200,
      "width": 30,
      "height": 30,
      "confidence": 0.95,
      "description": "Pier symbol P1"
    }}
  ],
  "total_count": 5,
  "notes": "any relevant observations"
}}"""

    def __init__(self):
        self.client = get_llm_client()
    
    async def find_similar(
        self,
        image_bytes: bytes,
        template_center_x: float,
        template_center_y: float,
        template_width: float,
        template_height: float,
        template_description: str = "construction element",
        provider: LLMProvider | None = None,
        max_results: int = 200,
    ) -> list[SimilarityMatch]:
        """
        Find similar objects using LLM vision analysis.
        
        Args:
            image_bytes: The source image
            template_center_x, template_center_y: Template location
            template_width, template_height: Template size
            template_description: What the template represents
            provider: LLM provider to use
            max_results: Maximum matches to return
            
        Returns:
            List of SimilarityMatch objects
        """
        # Get image dimensions
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size
        
        # Create overlay image highlighting the template
        overlay_bytes = self._create_template_overlay(
            image_bytes,
            template_center_x,
            template_center_y,
            template_width,
            template_height,
        )
        
        # Build prompt
        prompt = self.SIMILARITY_PROMPT.format(
            template_description=template_description,
            width=width,
            height=height,
            template_x=int(template_center_x),
            template_y=int(template_center_y),
            template_w=int(template_width),
            template_h=int(template_height),
        )
        
        try:
            # Call LLM
            response = await self.client.analyze_image(
                image_bytes=overlay_bytes,
                prompt=prompt,
                provider=provider,
            )
            
            # Parse response
            matches = self._parse_response(response.content)
            
            # Limit results
            return matches[:max_results]
            
        except Exception as e:
            logger.error(
                "LLM similarity detection failed",
                error=str(e),
            )
            return []
    
    def _create_template_overlay(
        self,
        image_bytes: bytes,
        center_x: float,
        center_y: float,
        width: float,
        height: float,
    ) -> bytes:
        """Create an image with the template region highlighted."""
        import cv2
        import numpy as np
        
        # Load image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Calculate bounds
        x1 = int(center_x - width / 2)
        y1 = int(center_y - height / 2)
        x2 = int(center_x + width / 2)
        y2 = int(center_y + height / 2)
        
        # Draw rectangle highlight
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
        
        # Add label
        cv2.putText(
            image,
            "TEMPLATE",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        
        # Add crosshairs at center
        cv2.drawMarker(
            image,
            (int(center_x), int(center_y)),
            (0, 255, 0),
            cv2.MARKER_CROSS,
            20,
            2,
        )
        
        # Convert back to bytes
        _, buffer = cv2.imencode('.png', image)
        return buffer.tobytes()
    
    def _parse_response(self, content: str) -> list[SimilarityMatch]:
        """Parse LLM response into SimilarityMatch objects."""
        import json
        import re
        
        # Extract JSON from response
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
            else:
                logger.warning("No JSON found in LLM response")
                return []
            
            matches = []
            for item in data.get("matches", []):
                match = SimilarityMatch(
                    center_x=float(item.get("center_x", 0)),
                    center_y=float(item.get("center_y", 0)),
                    width=float(item.get("width", 20)),
                    height=float(item.get("height", 20)),
                    similarity_score=float(item.get("confidence", 0.5)),
                    description=item.get("description", ""),
                    confidence=float(item.get("confidence", 0.5)),
                )
                matches.append(match)
            
            return matches
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response", error=str(e))
            return []


# Singleton
_service: LLMSimilarityService | None = None

def get_llm_similarity_service() -> LLMSimilarityService:
    """Get the LLM similarity service singleton."""
    global _service
    if _service is None:
        _service = LLMSimilarityService()
    return _service
```

---

### Task 14.4: Auto Count Service

Create `backend/app/services/auto_count_service.py`:

```python
"""Auto count service combining template matching and LLM detection."""

import uuid
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auto_count import AutoCountSession, AutoCountDetection
from app.models.page import Page
from app.models.measurement import Measurement
from app.models.condition import Condition
from app.services.template_matching import (
    TemplateMatchingService, TemplateMatch, get_template_matching_service
)
from app.services.llm_similarity import (
    LLMSimilarityService, SimilarityMatch, get_llm_similarity_service
)
from app.services.storage import get_storage_service
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class AutoCountService:
    """
    Service for automatic object counting using similarity detection.
    
    Combines template matching for fast initial detection with
    LLM-based analysis for semantic understanding and validation.
    """
    
    def __init__(self):
        self.template_service = get_template_matching_service()
        self.llm_service = get_llm_similarity_service()
        self.storage = get_storage_service()
    
    async def create_session(
        self,
        session: AsyncSession,
        page_id: uuid.UUID,
        center_x: float,
        center_y: float,
        width: float,
        height: float,
        condition_id: uuid.UUID | None = None,
        created_by: str | None = None,
        detection_method: str = "hybrid",
        similarity_threshold: float = 0.8,
        search_scope: str = "page",
    ) -> AutoCountSession:
        """
        Create a new auto count session.
        
        Args:
            session: Database session
            page_id: Page to search on
            center_x, center_y: Center of template region
            width, height: Size of template region
            condition_id: Optional condition to link results to
            created_by: User who created the session
            detection_method: 'template_match', 'llm_embedding', or 'hybrid'
            similarity_threshold: Minimum similarity score (0-1)
            search_scope: 'page', 'document', or 'selected_pages'
            
        Returns:
            Created AutoCountSession
        """
        # Get the page
        page = await session.get(Page, page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        # Create session
        count_session = AutoCountSession(
            page_id=page_id,
            condition_id=condition_id,
            created_by=created_by,
            template_center_x=center_x,
            template_center_y=center_y,
            template_width=width,
            template_height=height,
            detection_method=detection_method,
            similarity_threshold=similarity_threshold,
            search_scope=search_scope,
            status="pending",
        )
        
        session.add(count_session)
        await session.commit()
        await session.refresh(count_session)
        
        logger.info(
            "Auto count session created",
            session_id=str(count_session.id),
            page_id=str(page_id),
        )
        
        return count_session
    
    async def run_detection(
        self,
        session: AsyncSession,
        count_session_id: uuid.UUID,
    ) -> AutoCountSession:
        """
        Run detection for an auto count session.
        
        Args:
            session: Database session
            count_session_id: Session to run detection for
            
        Returns:
            Updated session with detections
        """
        # Load session
        result = await session.execute(
            select(AutoCountSession)
            .options(selectinload(AutoCountSession.page))
            .where(AutoCountSession.id == count_session_id)
        )
        count_session = result.scalar_one_or_none()
        
        if not count_session:
            raise ValueError(f"Session not found: {count_session_id}")
        
        # Update status
        count_session.status = "processing"
        count_session.started_at = datetime.utcnow()
        await session.commit()
        
        try:
            # Get page image
            page = count_session.page
            image_bytes = await self.storage.get_file(page.processed_image_path)
            
            # Extract template
            template_bytes = self.template_service.extract_template(
                image_bytes,
                count_session.template_center_x,
                count_session.template_center_y,
                count_session.template_width,
                count_session.template_height,
            )
            
            if not template_bytes:
                raise ValueError("Failed to extract template")
            
            # Store template image
            count_session.template_image_data = base64.b64encode(template_bytes).decode()
            
            # Run detection based on method
            detections: list[AutoCountDetection] = []
            
            if count_session.detection_method in ("template_match", "hybrid"):
                # Template matching
                template_matches = self.template_service.find_matches(
                    image_bytes,
                    template_bytes,
                    threshold=count_session.similarity_threshold,
                    scale_range=(
                        1 - count_session.scale_tolerance,
                        1 + count_session.scale_tolerance,
                    ),
                    rotation_range=(
                        -count_session.rotation_tolerance,
                        count_session.rotation_tolerance,
                    ) if count_session.rotation_tolerance > 0 else None,
                )
                
                for rank, match in enumerate(template_matches):
                    detection = AutoCountDetection(
                        session_id=count_session.id,
                        page_id=page.id,
                        center_x=match.center_x,
                        center_y=match.center_y,
                        width=match.width,
                        height=match.height,
                        rotation=match.rotation,
                        bbox_x1=match.bbox[0],
                        bbox_y1=match.bbox[1],
                        bbox_x2=match.bbox[2],
                        bbox_y2=match.bbox[3],
                        similarity_score=match.score,
                        template_match_score=match.score,
                        detected_by="template_match",
                        rank=rank,
                    )
                    detections.append(detection)
            
            if count_session.detection_method in ("llm_embedding", "hybrid"):
                # LLM similarity detection
                llm_matches = await self.llm_service.find_similar(
                    image_bytes,
                    count_session.template_center_x,
                    count_session.template_center_y,
                    count_session.template_width,
                    count_session.template_height,
                )
                
                for rank, match in enumerate(llm_matches):
                    # Check if this overlaps with existing detection
                    is_new = True
                    for existing in detections:
                        if self._detections_overlap(existing, match):
                            # Update existing with LLM score
                            existing.llm_embedding_score = match.similarity_score
                            # Use higher score
                            existing.similarity_score = max(
                                existing.similarity_score,
                                match.similarity_score,
                            )
                            is_new = False
                            break
                    
                    if is_new:
                        detection = AutoCountDetection(
                            session_id=count_session.id,
                            page_id=page.id,
                            center_x=match.center_x,
                            center_y=match.center_y,
                            width=match.width,
                            height=match.height,
                            rotation=0,
                            bbox_x1=match.center_x - match.width / 2,
                            bbox_y1=match.center_y - match.height / 2,
                            bbox_x2=match.center_x + match.width / 2,
                            bbox_y2=match.center_y + match.height / 2,
                            similarity_score=match.similarity_score,
                            llm_embedding_score=match.similarity_score,
                            detected_by="llm_embedding",
                            rank=len(detections) + rank,
                            metadata={"description": match.description},
                        )
                        detections.append(detection)
            
            # Save detections
            for detection in detections:
                session.add(detection)
            
            # Update session stats
            count_session.total_detections = len(detections)
            count_session.pending_count = len(detections)
            count_session.status = "completed"
            count_session.completed_at = datetime.utcnow()
            count_session.processing_time_ms = int(
                (count_session.completed_at - count_session.started_at).total_seconds() * 1000
            )
            
            await session.commit()
            await session.refresh(count_session)
            
            logger.info(
                "Auto count detection completed",
                session_id=str(count_session.id),
                total_detections=len(detections),
                processing_time_ms=count_session.processing_time_ms,
            )
            
            return count_session
            
        except Exception as e:
            count_session.status = "failed"
            count_session.error_message = str(e)
            await session.commit()
            
            logger.error(
                "Auto count detection failed",
                session_id=str(count_session_id),
                error=str(e),
            )
            raise
    
    def _detections_overlap(
        self,
        det1: AutoCountDetection,
        match: SimilarityMatch,
        iou_threshold: float = 0.5,
    ) -> bool:
        """Check if two detections overlap significantly."""
        # Calculate IoU (Intersection over Union)
        x1_1, y1_1 = det1.bbox_x1, det1.bbox_y1
        x2_1, y2_1 = det1.bbox_x2, det1.bbox_y2
        
        x1_2 = match.center_x - match.width / 2
        y1_2 = match.center_y - match.height / 2
        x2_2 = match.center_x + match.width / 2
        y2_2 = match.center_y + match.height / 2
        
        # Intersection
        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)
        
        if xi2 <= xi1 or yi2 <= yi1:
            return False
        
        intersection = (xi2 - xi1) * (yi2 - yi1)
        
        # Union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        iou = intersection / union if union > 0 else 0
        
        return iou >= iou_threshold
    
    async def confirm_detection(
        self,
        session: AsyncSession,
        detection_id: uuid.UUID,
        reviewer_name: str,
    ) -> AutoCountDetection:
        """Confirm a detection as valid."""
        detection = await session.get(AutoCountDetection, detection_id)
        if not detection:
            raise ValueError(f"Detection not found: {detection_id}")
        
        detection.status = "confirmed"
        detection.reviewed_by = reviewer_name
        detection.reviewed_at = datetime.utcnow()
        
        # Update session counts
        count_session = await session.get(AutoCountSession, detection.session_id)
        if count_session:
            count_session.confirmed_count += 1
            count_session.pending_count -= 1
        
        await session.commit()
        await session.refresh(detection)
        
        return detection
    
    async def reject_detection(
        self,
        session: AsyncSession,
        detection_id: uuid.UUID,
        reviewer_name: str,
    ) -> AutoCountDetection:
        """Reject a detection as false positive."""
        detection = await session.get(AutoCountDetection, detection_id)
        if not detection:
            raise ValueError(f"Detection not found: {detection_id}")
        
        detection.status = "rejected"
        detection.reviewed_by = reviewer_name
        detection.reviewed_at = datetime.utcnow()
        
        # Update session counts
        count_session = await session.get(AutoCountSession, detection.session_id)
        if count_session:
            count_session.rejected_count += 1
            count_session.pending_count -= 1
        
        await session.commit()
        await session.refresh(detection)
        
        return detection
    
    async def confirm_all_above_threshold(
        self,
        session: AsyncSession,
        count_session_id: uuid.UUID,
        threshold: float,
        reviewer_name: str,
    ) -> int:
        """Confirm all detections above a similarity threshold."""
        result = await session.execute(
            select(AutoCountDetection)
            .where(AutoCountDetection.session_id == count_session_id)
            .where(AutoCountDetection.status == "pending")
            .where(AutoCountDetection.similarity_score >= threshold)
        )
        detections = result.scalars().all()
        
        count = 0
        for detection in detections:
            detection.status = "confirmed"
            detection.reviewed_by = reviewer_name
            detection.reviewed_at = datetime.utcnow()
            count += 1
        
        # Update session
        count_session = await session.get(AutoCountSession, count_session_id)
        if count_session:
            count_session.confirmed_count += count
            count_session.pending_count -= count
        
        await session.commit()
        
        return count
    
    async def create_measurements_from_confirmed(
        self,
        session: AsyncSession,
        count_session_id: uuid.UUID,
        condition_id: uuid.UUID,
    ) -> list[Measurement]:
        """Create measurement records for all confirmed detections."""
        # Get confirmed detections
        result = await session.execute(
            select(AutoCountDetection)
            .where(AutoCountDetection.session_id == count_session_id)
            .where(AutoCountDetection.status == "confirmed")
            .where(AutoCountDetection.measurement_id == None)
        )
        detections = result.scalars().all()
        
        # Get condition
        condition = await session.get(Condition, condition_id)
        if not condition:
            raise ValueError(f"Condition not found: {condition_id}")
        
        measurements = []
        for detection in detections:
            measurement = Measurement(
                condition_id=condition_id,
                page_id=detection.page_id,
                geometry_type="point",
                geometry_data={
                    "x": detection.center_x,
                    "y": detection.center_y,
                    "width": detection.width,
                    "height": detection.height,
                },
                quantity=1,
                unit="EA",
                is_ai_generated=True,
                ai_confidence=detection.similarity_score,
                ai_model="auto_count",
                review_status="pending",
                metadata={
                    "auto_count_session_id": str(count_session_id),
                    "auto_count_detection_id": str(detection.id),
                    "detected_by": detection.detected_by,
                },
            )
            session.add(measurement)
            await session.flush()
            
            # Link detection to measurement
            detection.measurement_id = measurement.id
            
            measurements.append(measurement)
        
        # Update condition total
        condition.total_quantity = (condition.total_quantity or 0) + len(measurements)
        
        await session.commit()
        
        logger.info(
            "Created measurements from auto count",
            session_id=str(count_session_id),
            measurement_count=len(measurements),
        )
        
        return measurements


import base64

# Singleton
_service: AutoCountService | None = None

def get_auto_count_service() -> AutoCountService:
    """Get the auto count service singleton."""
    global _service
    if _service is None:
        _service = AutoCountService()
    return _service
```

---

### Task 14.5: Auto Count Celery Tasks

Create `backend/app/workers/auto_count_tasks.py`:

```python
"""Celery tasks for auto count operations."""

import uuid
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_sync_session
from app.models.auto_count import AutoCountSession
from app.services.auto_count_service import get_auto_count_service

import structlog

logger = structlog.get_logger()


@shared_task(
    name="run_auto_count_detection",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def run_auto_count_detection(self, session_id: str) -> dict:
    """
    Run auto count detection asynchronously.
    
    Args:
        session_id: Auto count session ID
        
    Returns:
        Detection results summary
    """
    import asyncio
    
    async def _run():
        from app.database import async_session_maker
        
        async with async_session_maker() as session:
            service = get_auto_count_service()
            
            count_session = await service.run_detection(
                session=session,
                count_session_id=uuid.UUID(session_id),
            )
            
            return {
                "session_id": str(count_session.id),
                "status": count_session.status,
                "total_detections": count_session.total_detections,
                "processing_time_ms": count_session.processing_time_ms,
            }
    
    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error(
            "Auto count detection task failed",
            session_id=session_id,
            error=str(e),
        )
        # Update session status to failed
        with get_sync_session() as session:
            count_session = session.get(AutoCountSession, uuid.UUID(session_id))
            if count_session:
                count_session.status = "failed"
                count_session.error_message = str(e)
                session.commit()
        raise


@shared_task(name="create_auto_count_measurements")
def create_auto_count_measurements(
    session_id: str,
    condition_id: str,
) -> dict:
    """
    Create measurements from confirmed auto count detections.
    
    Args:
        session_id: Auto count session ID
        condition_id: Condition to create measurements for
        
    Returns:
        Creation results
    """
    import asyncio
    
    async def _create():
        from app.database import async_session_maker
        
        async with async_session_maker() as session:
            service = get_auto_count_service()
            
            measurements = await service.create_measurements_from_confirmed(
                session=session,
                count_session_id=uuid.UUID(session_id),
                condition_id=uuid.UUID(condition_id),
            )
            
            return {
                "session_id": session_id,
                "condition_id": condition_id,
                "measurements_created": len(measurements),
            }
    
    return asyncio.run(_create())
```

---

### Task 14.6: Auto Count API Endpoints

Create `backend/app/api/routes/auto_count.py`:

```python
"""Auto count API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.auto_count import AutoCountSession, AutoCountDetection
from app.schemas.auto_count import (
    AutoCountSessionCreate,
    AutoCountSessionResponse,
    AutoCountSessionDetailResponse,
    AutoCountDetectionResponse,
    ConfirmDetectionRequest,
    BulkConfirmRequest,
    CreateMeasurementsRequest,
)
from app.services.auto_count_service import get_auto_count_service
from app.workers.auto_count_tasks import run_auto_count_detection, create_auto_count_measurements

router = APIRouter()


@router.post(
    "/pages/{page_id}/auto-count",
    response_model=AutoCountSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_auto_count_session(
    page_id: uuid.UUID,
    request: AutoCountSessionCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create an auto count session and start detection.
    
    The user selects a template region, and the system finds
    all similar objects on the page.
    """
    service = get_auto_count_service()
    
    try:
        count_session = await service.create_session(
            session=db,
            page_id=page_id,
            center_x=request.center_x,
            center_y=request.center_y,
            width=request.width,
            height=request.height,
            condition_id=request.condition_id,
            created_by=request.created_by,
            detection_method=request.detection_method,
            similarity_threshold=request.similarity_threshold,
            search_scope=request.search_scope,
        )
        
        # Start detection in background
        run_auto_count_detection.delay(str(count_session.id))
        
        return AutoCountSessionResponse.model_validate(count_session)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/auto-count/{session_id}",
    response_model=AutoCountSessionDetailResponse,
)
async def get_auto_count_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get auto count session with all detections."""
    result = await db.execute(
        select(AutoCountSession)
        .options(selectinload(AutoCountSession.detections))
        .where(AutoCountSession.id == session_id)
    )
    count_session = result.scalar_one_or_none()
    
    if not count_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    return AutoCountSessionDetailResponse.model_validate(count_session)


@router.get(
    "/auto-count/{session_id}/detections",
    response_model=list[AutoCountDetectionResponse],
)
async def list_detections(
    session_id: uuid.UUID,
    status_filter: str | None = Query(None, alias="status"),
    min_score: float | None = Query(None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """List detections for an auto count session."""
    query = select(AutoCountDetection).where(
        AutoCountDetection.session_id == session_id
    )
    
    if status_filter:
        query = query.where(AutoCountDetection.status == status_filter)
    if min_score is not None:
        query = query.where(AutoCountDetection.similarity_score >= min_score)
    
    query = query.order_by(
        AutoCountDetection.similarity_score.desc(),
        AutoCountDetection.rank,
    )
    
    result = await db.execute(query)
    detections = result.scalars().all()
    
    return [AutoCountDetectionResponse.model_validate(d) for d in detections]


@router.post("/auto-count/detections/{detection_id}/confirm")
async def confirm_detection(
    detection_id: uuid.UUID,
    request: ConfirmDetectionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Confirm a single detection as valid."""
    service = get_auto_count_service()
    
    try:
        detection = await service.confirm_detection(
            session=db,
            detection_id=detection_id,
            reviewer_name=request.reviewer_name,
        )
        return {
            "status": "confirmed",
            "detection_id": str(detection_id),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/auto-count/detections/{detection_id}/reject")
async def reject_detection(
    detection_id: uuid.UUID,
    request: ConfirmDetectionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reject a detection as a false positive."""
    service = get_auto_count_service()
    
    try:
        detection = await service.reject_detection(
            session=db,
            detection_id=detection_id,
            reviewer_name=request.reviewer_name,
        )
        return {
            "status": "rejected",
            "detection_id": str(detection_id),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/auto-count/{session_id}/bulk-confirm")
async def bulk_confirm_detections(
    session_id: uuid.UUID,
    request: BulkConfirmRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Confirm all detections above a threshold."""
    service = get_auto_count_service()
    
    count = await service.confirm_all_above_threshold(
        session=db,
        count_session_id=session_id,
        threshold=request.threshold,
        reviewer_name=request.reviewer_name,
    )
    
    return {
        "confirmed_count": count,
        "threshold": request.threshold,
    }


@router.post("/auto-count/{session_id}/create-measurements")
async def create_measurements_from_session(
    session_id: uuid.UUID,
    request: CreateMeasurementsRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create measurement records from confirmed detections."""
    # Queue task
    task = create_auto_count_measurements.delay(
        str(session_id),
        str(request.condition_id),
    )
    
    return {
        "task_id": task.id,
        "session_id": str(session_id),
        "condition_id": str(request.condition_id),
    }


@router.delete("/auto-count/{session_id}")
async def delete_auto_count_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an auto count session and all detections."""
    count_session = await db.get(AutoCountSession, session_id)
    if not count_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    await db.delete(count_session)
    await db.commit()
    
    return {"status": "deleted"}
```

---

### Task 14.7: Auto Count Schemas

Create `backend/app/schemas/auto_count.py`:

```python
"""Auto count schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AutoCountSessionCreate(BaseModel):
    """Request to create an auto count session."""
    
    center_x: float = Field(..., description="Template center X coordinate")
    center_y: float = Field(..., description="Template center Y coordinate")
    width: float = Field(..., gt=0, description="Template width")
    height: float = Field(..., gt=0, description="Template height")
    condition_id: uuid.UUID | None = None
    created_by: str | None = None
    detection_method: str = Field(default="hybrid")
    similarity_threshold: float = Field(default=0.8, ge=0, le=1)
    search_scope: str = Field(default="page")


class AutoCountDetectionResponse(BaseModel):
    """Auto count detection response."""
    
    id: uuid.UUID
    session_id: uuid.UUID
    page_id: uuid.UUID
    measurement_id: uuid.UUID | None
    center_x: float
    center_y: float
    width: float
    height: float
    rotation: float
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    similarity_score: float
    template_match_score: float | None
    llm_embedding_score: float | None
    detected_by: str
    status: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    rank: int
    
    model_config = {"from_attributes": True}


class AutoCountSessionResponse(BaseModel):
    """Auto count session response."""
    
    id: uuid.UUID
    page_id: uuid.UUID
    condition_id: uuid.UUID | None
    name: str | None
    created_by: str | None
    template_center_x: float
    template_center_y: float
    template_width: float
    template_height: float
    detection_method: str
    similarity_threshold: float
    search_scope: str
    total_detections: int
    confirmed_count: int
    rejected_count: int
    pending_count: int
    status: str
    error_message: str | None
    processing_time_ms: int | None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class AutoCountSessionDetailResponse(AutoCountSessionResponse):
    """Auto count session with detections."""
    
    detections: list[AutoCountDetectionResponse] = []
    template_image_data: str | None = None


class ConfirmDetectionRequest(BaseModel):
    """Request to confirm/reject a detection."""
    
    reviewer_name: str = Field(..., min_length=1)


class BulkConfirmRequest(BaseModel):
    """Request for bulk confirmation."""
    
    threshold: float = Field(..., ge=0, le=1)
    reviewer_name: str = Field(..., min_length=1)


class CreateMeasurementsRequest(BaseModel):
    """Request to create measurements from confirmed detections."""
    
    condition_id: uuid.UUID
```

---

### Task 14.8: Frontend Auto Count Components

Create `frontend/src/components/auto-count/AutoCountTool.tsx`:

```tsx
import { useState, useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Target,
  Loader2,
  Check,
  X,
  AlertCircle,
  Zap,
  MousePointer2,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { apiClient } from '@/api/client';
import { cn } from '@/lib/utils';

interface AutoCountToolProps {
  pageId: string;
  conditionId?: string;
  onTemplateSelect: (callback: (x: number, y: number, w: number, h: number) => void) => void;
  onDetectionsReceived: (detections: Detection[]) => void;
}

interface Detection {
  id: string;
  center_x: number;
  center_y: number;
  width: number;
  height: number;
  similarity_score: number;
  status: 'pending' | 'confirmed' | 'rejected';
}

interface Session {
  id: string;
  status: string;
  total_detections: number;
  confirmed_count: number;
  rejected_count: number;
  pending_count: number;
  processing_time_ms: number | null;
  detections: Detection[];
}

export function AutoCountTool({
  pageId,
  conditionId,
  onTemplateSelect,
  onDetectionsReceived,
}: AutoCountToolProps) {
  const [isSelecting, setIsSelecting] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [threshold, setThreshold] = useState(0.8);
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  
  const queryClient = useQueryClient();

  // Fetch session data
  const { data: session, isLoading: isLoadingSession } = useQuery({
    queryKey: ['auto-count-session', sessionId],
    queryFn: async () => {
      if (!sessionId) return null;
      const response = await apiClient.get<Session>(`/auto-count/${sessionId}`);
      return response.data;
    },
    enabled: !!sessionId,
    refetchInterval: (data) => {
      // Poll while processing
      if (data?.status === 'processing') return 1000;
      return false;
    },
  });

  // Update parent when detections change
  useEffect(() => {
    if (session?.detections) {
      onDetectionsReceived(session.detections);
    }
  }, [session?.detections, onDetectionsReceived]);

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: async (template: {
      center_x: number;
      center_y: number;
      width: number;
      height: number;
    }) => {
      const response = await apiClient.post<{ id: string }>(
        `/pages/${pageId}/auto-count`,
        {
          ...template,
          condition_id: conditionId,
          similarity_threshold: threshold,
          detection_method: 'hybrid',
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      setSessionId(data.id);
      setIsSelecting(false);
    },
  });

  // Confirm detection mutation
  const confirmMutation = useMutation({
    mutationFn: async (detectionId: string) => {
      await apiClient.post(`/auto-count/detections/${detectionId}/confirm`, {
        reviewer_name: 'Estimator', // TODO: Get from auth
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auto-count-session', sessionId] });
    },
  });

  // Reject detection mutation
  const rejectMutation = useMutation({
    mutationFn: async (detectionId: string) => {
      await apiClient.post(`/auto-count/detections/${detectionId}/reject`, {
        reviewer_name: 'Estimator',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auto-count-session', sessionId] });
    },
  });

  // Bulk confirm mutation
  const bulkConfirmMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post(`/auto-count/${sessionId}/bulk-confirm`, {
        threshold,
        reviewer_name: 'Estimator',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auto-count-session', sessionId] });
    },
  });

  // Create measurements mutation
  const createMeasurementsMutation = useMutation({
    mutationFn: async () => {
      if (!conditionId) throw new Error('No condition selected');
      await apiClient.post(`/auto-count/${sessionId}/create-measurements`, {
        condition_id: conditionId,
      });
    },
    onSuccess: () => {
      setShowReviewDialog(false);
      setSessionId(null);
      queryClient.invalidateQueries({ queryKey: ['measurements'] });
    },
  });

  const handleStartSelection = () => {
    setIsSelecting(true);
    onTemplateSelect((x, y, w, h) => {
      createSessionMutation.mutate({
        center_x: x,
        center_y: y,
        width: w,
        height: h,
      });
    });
  };

  const pendingDetections = session?.detections.filter(d => d.status === 'pending') || [];
  const confirmedDetections = session?.detections.filter(d => d.status === 'confirmed') || [];
  const highConfidenceCount = pendingDetections.filter(d => d.similarity_score >= threshold).length;

  return (
    <div className="space-y-4">
      {/* Tool Header */}
      <div className="flex items-center gap-2">
        <Target className="h-5 w-5 text-primary" />
        <h3 className="font-medium">Auto Count</h3>
      </div>

      {/* Instructions */}
      {!session && !isSelecting && (
        <div className="text-sm text-muted-foreground">
          Select one instance of a repeating element to find all similar objects.
        </div>
      )}

      {/* Threshold Slider */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          Similarity Threshold: {Math.round(threshold * 100)}%
        </label>
        <Slider
          value={[threshold]}
          onValueChange={([v]) => setThreshold(v)}
          min={0.5}
          max={0.95}
          step={0.05}
          disabled={!!session}
        />
      </div>

      {/* Action Buttons */}
      {!session ? (
        <Button
          onClick={handleStartSelection}
          disabled={isSelecting || createSessionMutation.isPending}
          className="w-full"
        >
          {isSelecting ? (
            <>
              <MousePointer2 className="h-4 w-4 mr-2 animate-pulse" />
              Click on template...
            </>
          ) : createSessionMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Starting...
            </>
          ) : (
            <>
              <Target className="h-4 w-4 mr-2" />
              Select Template
            </>
          )}
        </Button>
      ) : (
        <div className="space-y-3">
          {/* Status */}
          {session.status === 'processing' && (
            <div className="flex items-center gap-2 text-sm">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Detecting similar objects...</span>
            </div>
          )}

          {session.status === 'completed' && (
            <>
              {/* Results Summary */}
              <div className="bg-muted rounded-lg p-3 space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Total Found:</span>
                  <Badge variant="secondary">{session.total_detections}</Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Confirmed:</span>
                  <Badge variant="default" className="bg-green-600">
                    {session.confirmed_count}
                  </Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Pending Review:</span>
                  <Badge variant="outline">{session.pending_count}</Badge>
                </div>
                {session.processing_time_ms && (
                  <div className="text-xs text-muted-foreground">
                    Processed in {(session.processing_time_ms / 1000).toFixed(1)}s
                  </div>
                )}
              </div>

              {/* Quick Actions */}
              {pendingDetections.length > 0 && (
                <div className="space-y-2">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => bulkConfirmMutation.mutate()}
                    disabled={bulkConfirmMutation.isPending}
                  >
                    <Zap className="h-4 w-4 mr-2" />
                    Confirm {highConfidenceCount} High-Confidence
                  </Button>
                  
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => setShowReviewDialog(true)}
                  >
                    Review All ({pendingDetections.length})
                  </Button>
                </div>
              )}

              {/* Create Measurements */}
              {confirmedDetections.length > 0 && conditionId && (
                <Button
                  className="w-full"
                  onClick={() => createMeasurementsMutation.mutate()}
                  disabled={createMeasurementsMutation.isPending}
                >
                  <Check className="h-4 w-4 mr-2" />
                  Create {confirmedDetections.length} Measurements
                </Button>
              )}

              {/* Reset */}
              <Button
                variant="ghost"
                className="w-full"
                onClick={() => setSessionId(null)}
              >
                Start Over
              </Button>
            </>
          )}

          {session.status === 'failed' && (
            <div className="text-sm text-destructive flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              {session.error_message || 'Detection failed'}
            </div>
          )}
        </div>
      )}

      {/* Review Dialog */}
      <Dialog open={showReviewDialog} onOpenChange={setShowReviewDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Review Detections</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 overflow-auto max-h-[60vh]">
            {pendingDetections
              .sort((a, b) => b.similarity_score - a.similarity_score)
              .map((detection) => (
                <div
                  key={detection.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        'w-3 h-3 rounded-full',
                        detection.similarity_score >= 0.9
                          ? 'bg-green-500'
                          : detection.similarity_score >= 0.8
                          ? 'bg-yellow-500'
                          : 'bg-orange-500'
                      )}
                    />
                    <div>
                      <div className="font-medium">
                        {Math.round(detection.similarity_score * 100)}% match
                      </div>
                      <div className="text-xs text-muted-foreground">
                        ({Math.round(detection.center_x)}, {Math.round(detection.center_y)})
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => confirmMutation.mutate(detection.id)}
                      disabled={confirmMutation.isPending}
                    >
                      <Check className="h-4 w-4 text-green-600" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => rejectMutation.mutate(detection.id)}
                      disabled={rejectMutation.isPending}
                    >
                      <X className="h-4 w-4 text-red-600" />
                    </Button>
                  </div>
                </div>
              ))}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowReviewDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Need to import useEffect
import { useEffect } from 'react';
```

Create `frontend/src/components/auto-count/AutoCountOverlay.tsx`:

```tsx
import { useMemo } from 'react';
import { Group, Rect, Circle, Text } from 'react-konva';

interface Detection {
  id: string;
  center_x: number;
  center_y: number;
  width: number;
  height: number;
  similarity_score: number;
  status: 'pending' | 'confirmed' | 'rejected';
}

interface AutoCountOverlayProps {
  detections: Detection[];
  selectedId?: string;
  onSelect?: (id: string) => void;
  showLabels?: boolean;
}

const STATUS_COLORS = {
  pending: '#FFA500',  // Orange
  confirmed: '#22C55E',  // Green
  rejected: '#EF4444',  // Red
};

export function AutoCountOverlay({
  detections,
  selectedId,
  onSelect,
  showLabels = true,
}: AutoCountOverlayProps) {
  // Filter out rejected detections
  const visibleDetections = useMemo(
    () => detections.filter(d => d.status !== 'rejected'),
    [detections]
  );

  return (
    <Group>
      {visibleDetections.map((detection, index) => {
        const isSelected = detection.id === selectedId;
        const color = STATUS_COLORS[detection.status];
        
        return (
          <Group
            key={detection.id}
            x={detection.center_x - detection.width / 2}
            y={detection.center_y - detection.height / 2}
            onClick={() => onSelect?.(detection.id)}
            onTap={() => onSelect?.(detection.id)}
          >
            {/* Bounding box */}
            <Rect
              width={detection.width}
              height={detection.height}
              stroke={color}
              strokeWidth={isSelected ? 3 : 2}
              fill={`${color}20`}
              cornerRadius={2}
            />
            
            {/* Center marker */}
            <Circle
              x={detection.width / 2}
              y={detection.height / 2}
              radius={4}
              fill={color}
            />
            
            {/* Label */}
            {showLabels && (
              <Group y={-20}>
                <Rect
                  width={40}
                  height={18}
                  fill={color}
                  cornerRadius={2}
                />
                <Text
                  text={`${Math.round(detection.similarity_score * 100)}%`}
                  width={40}
                  height={18}
                  fontSize={11}
                  fill="white"
                  align="center"
                  verticalAlign="middle"
                />
              </Group>
            )}
            
            {/* Index number */}
            <Group x={detection.width - 20} y={-20}>
              <Circle
                radius={10}
                fill={color}
              />
              <Text
                x={-6}
                y={-6}
                text={String(index + 1)}
                fontSize={10}
                fill="white"
                fontStyle="bold"
              />
            </Group>
          </Group>
        );
      })}
    </Group>
  );
}
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] Auto count session created with template info
- [ ] Template matching finds similar objects
- [ ] LLM similarity detection works
- [ ] Hybrid mode combines both methods
- [ ] Non-maximum suppression removes duplicates
- [ ] Detection confidence scores calculated
- [ ] User can confirm/reject detections
- [ ] Bulk confirm above threshold works
- [ ] Measurements created from confirmed detections
- [ ] Frontend shows detections on canvas
- [ ] Detection overlay updates in real-time
- [ ] Processing status polled correctly
- [ ] Errors handled gracefully

### Test Cases

1. Select a pier symbol → finds all piers on page
2. Select rotated symbol → rotation tolerance catches variations
3. Confirm detection → status updates, count increases
4. Reject detection → hidden from view
5. Bulk confirm at 90% → all high-confidence confirmed
6. Create measurements → count measurements created
7. Multiple scales → scale tolerance finds different sizes
8. No matches → graceful empty state

---

## Next Phase

Once verified, proceed to enhanced review features in **`09-REVIEW-INTERFACE-ENHANCED.md`**.
