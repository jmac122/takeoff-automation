# Phase 3A: Measurement Engine
## Core Geometry Tools and Measurement Calculations

> **Duration**: Weeks 10-16
> **Prerequisites**: Scale detection working (Phase 2B)
> **Outcome**: Full measurement toolkit for linear, area, volume, and count takeoffs

---

## Context for LLM Assistant

You are implementing the measurement engine for a construction takeoff platform. This is the core calculation system that:
- Handles multiple geometry types (lines, polylines, polygons, rectangles, circles)
- Converts pixel measurements to real-world units using page scale
- Calculates linear feet, square footage, cubic yards, and counts
- Supports depth/thickness modifiers for volume calculations
- Provides undo/redo functionality
- Handles multi-page measurements

### Measurement Types for Concrete Takeoff

| Type | Use Case | Output |
|------|----------|--------|
| **Linear** | Footings, curbs, edge forms | Linear feet |
| **Area** | Slabs, paving, walls | Square feet |
| **Volume** | Concrete pours | Cubic yards |
| **Count** | Piers, columns, anchors | Each |

### Geometry Types

| Geometry | Description | Calculations |
|----------|-------------|--------------|
| **Line** | Two-point measurement | Length |
| **Polyline** | Multi-segment line | Total length, segment lengths |
| **Polygon** | Closed shape | Area, perimeter |
| **Rectangle** | Axis-aligned box | Area, perimeter, dimensions |
| **Circle** | Center + radius | Area, circumference, diameter |
| **Point** | Single location | Count (1) |

---

## Database Models

### Task 6.1: Measurement and Condition Models

Create `backend/app/models/condition.py`:

```python
"""Condition model for takeoff line items."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Float, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.measurement import Measurement


class Condition(Base, UUIDMixin, TimestampMixin):
    """Takeoff condition (line item) that groups measurements."""

    __tablename__ = "conditions"

    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Condition info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Scope/category
    scope: Mapped[str] = mapped_column(String(100), default="concrete")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Measurement type
    measurement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # linear, area, volume, count
    
    # Display
    color: Mapped[str] = mapped_column(String(20), default="#3B82F6")  # Hex color
    line_width: Mapped[int] = mapped_column(Integer, default=2)
    fill_opacity: Mapped[float] = mapped_column(Float, default=0.3)
    
    # Unit and modifiers
    unit: Mapped[str] = mapped_column(String(50), default="LF")  # LF, SF, CY, EA
    depth: Mapped[float | None] = mapped_column(Float, nullable=True)  # For volume calc
    thickness: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Calculated totals (denormalized for performance)
    total_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    measurement_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Sort order
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="conditions")
    measurements: Mapped[list["Measurement"]] = relationship(
        "Measurement",
        back_populates="condition",
        cascade="all, delete-orphan",
    )
```

Create `backend/app/models/measurement.py`:

```python
"""Measurement model for geometric shapes on pages."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import String, Float, Integer, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.condition import Condition
    from app.models.page import Page


class Measurement(Base, UUIDMixin, TimestampMixin):
    """Individual measurement (geometric shape) on a page."""

    __tablename__ = "measurements"

    # Foreign keys
    condition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conditions.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Geometry
    geometry_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # line, polyline, polygon, rectangle, circle, point
    
    geometry_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    # Structure varies by type:
    # line: {start: {x, y}, end: {x, y}}
    # polyline: {points: [{x, y}, ...]}
    # polygon: {points: [{x, y}, ...]}
    # rectangle: {x, y, width, height, rotation?}
    # circle: {center: {x, y}, radius}
    # point: {x, y}
    
    # Calculated values (in real-world units)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Pixel values (for reference)
    pixel_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    pixel_area: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # AI generation tracking
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # User modifications
    is_modified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    condition: Mapped["Condition"] = relationship("Condition", back_populates="measurements")
    page: Mapped["Page"] = relationship("Page", back_populates="measurements")
```

Run migration:

```bash
alembic revision --autogenerate -m "add_conditions_and_measurements"
alembic upgrade head
```

---

### Task 6.2: Geometry Utilities

Create `backend/app/utils/geometry.py`:

```python
"""Geometry calculation utilities."""

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class Point:
    """2D point."""
    x: float
    y: float
    
    def distance_to(self, other: "Point") -> float:
        """Calculate distance to another point."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "Point":
        return cls(x=data["x"], y=data["y"])


def calculate_line_length(start: Point, end: Point) -> float:
    """Calculate length of a line segment."""
    return start.distance_to(end)


def calculate_polyline_length(points: list[Point]) -> float:
    """Calculate total length of a polyline."""
    if len(points) < 2:
        return 0.0
    
    total = 0.0
    for i in range(len(points) - 1):
        total += points[i].distance_to(points[i + 1])
    
    return total


def calculate_polygon_area(points: list[Point]) -> float:
    """Calculate area of a polygon using the shoelace formula."""
    if len(points) < 3:
        return 0.0
    
    n = len(points)
    area = 0.0
    
    for i in range(n):
        j = (i + 1) % n
        area += points[i].x * points[j].y
        area -= points[j].x * points[i].y
    
    return abs(area) / 2.0


def calculate_polygon_perimeter(points: list[Point]) -> float:
    """Calculate perimeter of a polygon."""
    if len(points) < 2:
        return 0.0
    
    perimeter = calculate_polyline_length(points)
    # Close the polygon
    perimeter += points[-1].distance_to(points[0])
    
    return perimeter


def calculate_rectangle_area(width: float, height: float) -> float:
    """Calculate area of a rectangle."""
    return width * height


def calculate_rectangle_perimeter(width: float, height: float) -> float:
    """Calculate perimeter of a rectangle."""
    return 2 * (width + height)


def calculate_circle_area(radius: float) -> float:
    """Calculate area of a circle."""
    return math.pi * radius ** 2


def calculate_circle_circumference(radius: float) -> float:
    """Calculate circumference of a circle."""
    return 2 * math.pi * radius


class MeasurementCalculator:
    """Calculator for converting measurements to real-world units."""
    
    def __init__(self, pixels_per_foot: float):
        """
        Args:
            pixels_per_foot: Scale factor (pixels per real foot)
        """
        self.pixels_per_foot = pixels_per_foot
    
    def pixels_to_feet(self, pixels: float) -> float:
        """Convert pixel distance to feet."""
        return pixels / self.pixels_per_foot
    
    def pixels_to_square_feet(self, pixel_area: float) -> float:
        """Convert pixel area to square feet."""
        return pixel_area / (self.pixels_per_foot ** 2)
    
    def square_feet_to_cubic_yards(
        self,
        square_feet: float,
        depth_inches: float,
    ) -> float:
        """Convert square feet to cubic yards given depth.
        
        Args:
            square_feet: Area in square feet
            depth_inches: Depth/thickness in inches
            
        Returns:
            Volume in cubic yards
        """
        depth_feet = depth_inches / 12
        cubic_feet = square_feet * depth_feet
        cubic_yards = cubic_feet / 27
        return cubic_yards
    
    def calculate_line(
        self,
        start: dict[str, float],
        end: dict[str, float],
    ) -> dict[str, float]:
        """Calculate line measurement.
        
        Returns:
            Dict with pixel_length and length_feet
        """
        p1 = Point.from_dict(start)
        p2 = Point.from_dict(end)
        
        pixel_length = calculate_line_length(p1, p2)
        length_feet = self.pixels_to_feet(pixel_length)
        
        return {
            "pixel_length": pixel_length,
            "length_feet": length_feet,
        }
    
    def calculate_polyline(
        self,
        points: list[dict[str, float]],
    ) -> dict[str, float]:
        """Calculate polyline measurement.
        
        Returns:
            Dict with pixel_length, length_feet, and segment_lengths
        """
        pts = [Point.from_dict(p) for p in points]
        
        pixel_length = calculate_polyline_length(pts)
        length_feet = self.pixels_to_feet(pixel_length)
        
        # Calculate individual segments
        segment_lengths = []
        for i in range(len(pts) - 1):
            seg_pixels = pts[i].distance_to(pts[i + 1])
            segment_lengths.append({
                "pixel_length": seg_pixels,
                "length_feet": self.pixels_to_feet(seg_pixels),
            })
        
        return {
            "pixel_length": pixel_length,
            "length_feet": length_feet,
            "segment_count": len(segment_lengths),
            "segment_lengths": segment_lengths,
        }
    
    def calculate_polygon(
        self,
        points: list[dict[str, float]],
        depth_inches: float | None = None,
    ) -> dict[str, float]:
        """Calculate polygon measurement.
        
        Returns:
            Dict with area, perimeter, and optionally volume
        """
        pts = [Point.from_dict(p) for p in points]
        
        pixel_area = calculate_polygon_area(pts)
        pixel_perimeter = calculate_polygon_perimeter(pts)
        
        area_sf = self.pixels_to_square_feet(pixel_area)
        perimeter_lf = self.pixels_to_feet(pixel_perimeter)
        
        result = {
            "pixel_area": pixel_area,
            "pixel_perimeter": pixel_perimeter,
            "area_sf": area_sf,
            "perimeter_lf": perimeter_lf,
        }
        
        if depth_inches:
            result["volume_cy"] = self.square_feet_to_cubic_yards(
                area_sf, depth_inches
            )
            result["depth_inches"] = depth_inches
        
        return result
    
    def calculate_rectangle(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        depth_inches: float | None = None,
    ) -> dict[str, float]:
        """Calculate rectangle measurement.
        
        Returns:
            Dict with dimensions, area, perimeter, and optionally volume
        """
        pixel_area = calculate_rectangle_area(width, height)
        pixel_perimeter = calculate_rectangle_perimeter(width, height)
        
        width_feet = self.pixels_to_feet(width)
        height_feet = self.pixels_to_feet(height)
        area_sf = self.pixels_to_square_feet(pixel_area)
        perimeter_lf = self.pixels_to_feet(pixel_perimeter)
        
        result = {
            "pixel_width": width,
            "pixel_height": height,
            "pixel_area": pixel_area,
            "pixel_perimeter": pixel_perimeter,
            "width_feet": width_feet,
            "height_feet": height_feet,
            "area_sf": area_sf,
            "perimeter_lf": perimeter_lf,
        }
        
        if depth_inches:
            result["volume_cy"] = self.square_feet_to_cubic_yards(
                area_sf, depth_inches
            )
            result["depth_inches"] = depth_inches
        
        return result
    
    def calculate_circle(
        self,
        center: dict[str, float],
        radius: float,
        depth_inches: float | None = None,
    ) -> dict[str, float]:
        """Calculate circle measurement.
        
        Returns:
            Dict with radius, diameter, area, circumference, and optionally volume
        """
        pixel_area = calculate_circle_area(radius)
        pixel_circumference = calculate_circle_circumference(radius)
        
        radius_feet = self.pixels_to_feet(radius)
        diameter_feet = radius_feet * 2
        area_sf = self.pixels_to_square_feet(pixel_area)
        circumference_lf = self.pixels_to_feet(pixel_circumference)
        
        result = {
            "pixel_radius": radius,
            "pixel_area": pixel_area,
            "pixel_circumference": pixel_circumference,
            "radius_feet": radius_feet,
            "diameter_feet": diameter_feet,
            "area_sf": area_sf,
            "circumference_lf": circumference_lf,
        }
        
        if depth_inches:
            result["volume_cy"] = self.square_feet_to_cubic_yards(
                area_sf, depth_inches
            )
            result["depth_inches"] = depth_inches
        
        return result
    
    def calculate_count(self, x: float, y: float) -> dict[str, Any]:
        """Calculate count measurement (just returns 1).
        
        Returns:
            Dict with count and position
        """
        return {
            "count": 1,
            "position": {"x": x, "y": y},
        }
```

---

### Task 6.3: Measurement Service

Create `backend/app/services/measurement_engine.py`:

```python
"""Measurement engine service."""

import uuid
from typing import Any

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.condition import Condition
from app.models.measurement import Measurement
from app.models.page import Page
from app.utils.geometry import MeasurementCalculator, Point

logger = structlog.get_logger()


class MeasurementEngine:
    """Service for creating and managing measurements."""
    
    GEOMETRY_TYPES = ["line", "polyline", "polygon", "rectangle", "circle", "point"]
    MEASUREMENT_TYPES = ["linear", "area", "volume", "count"]
    
    UNIT_MAP = {
        "linear": "LF",
        "area": "SF",
        "volume": "CY",
        "count": "EA",
    }

    async def create_measurement(
        self,
        session: AsyncSession,
        condition_id: uuid.UUID,
        page_id: uuid.UUID,
        geometry_type: str,
        geometry_data: dict[str, Any],
        is_ai_generated: bool = False,
        ai_confidence: float | None = None,
        notes: str | None = None,
    ) -> Measurement:
        """Create a new measurement.
        
        Args:
            session: Database session
            condition_id: Parent condition ID
            page_id: Page where measurement is drawn
            geometry_type: Type of geometry
            geometry_data: Geometry coordinates
            is_ai_generated: Whether created by AI
            ai_confidence: AI confidence score
            notes: Optional notes
            
        Returns:
            Created Measurement
        """
        # Validate geometry type
        if geometry_type not in self.GEOMETRY_TYPES:
            raise ValueError(f"Invalid geometry type: {geometry_type}")
        
        # Get condition and page
        condition = await session.get(Condition, condition_id)
        if not condition:
            raise ValueError(f"Condition not found: {condition_id}")
        
        page = await session.get(Page, page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        if not page.scale_calibrated or not page.scale_value:
            raise ValueError("Page scale not calibrated")
        
        # Calculate measurement
        calculator = MeasurementCalculator(page.scale_value)
        calculation = self._calculate_geometry(
            calculator,
            geometry_type,
            geometry_data,
            condition.depth,
        )
        
        # Determine quantity based on measurement type
        quantity = self._extract_quantity(
            calculation,
            condition.measurement_type,
        )
        
        # Create measurement
        measurement = Measurement(
            condition_id=condition_id,
            page_id=page_id,
            geometry_type=geometry_type,
            geometry_data=geometry_data,
            quantity=quantity,
            unit=condition.unit,
            pixel_length=calculation.get("pixel_length"),
            pixel_area=calculation.get("pixel_area"),
            is_ai_generated=is_ai_generated,
            ai_confidence=ai_confidence,
            notes=notes,
            metadata={"calculation": calculation},
        )
        
        session.add(measurement)
        
        # Update condition totals
        await self._update_condition_totals(session, condition)
        
        await session.commit()
        await session.refresh(measurement)
        
        return measurement

    async def update_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        geometry_data: dict[str, Any] | None = None,
        notes: str | None = None,
    ) -> Measurement:
        """Update an existing measurement.
        
        Args:
            session: Database session
            measurement_id: Measurement to update
            geometry_data: New geometry (optional)
            notes: New notes (optional)
            
        Returns:
            Updated Measurement
        """
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        if geometry_data:
            # Get page for scale
            page = await session.get(Page, measurement.page_id)
            condition = await session.get(Condition, measurement.condition_id)
            
            if not page.scale_value:
                raise ValueError("Page scale not calibrated")
            
            # Recalculate
            calculator = MeasurementCalculator(page.scale_value)
            calculation = self._calculate_geometry(
                calculator,
                measurement.geometry_type,
                geometry_data,
                condition.depth,
            )
            
            measurement.geometry_data = geometry_data
            measurement.quantity = self._extract_quantity(
                calculation,
                condition.measurement_type,
            )
            measurement.pixel_length = calculation.get("pixel_length")
            measurement.pixel_area = calculation.get("pixel_area")
            measurement.metadata = {"calculation": calculation}
            measurement.is_modified = True
        
        if notes is not None:
            measurement.notes = notes
        
        # Update condition totals
        condition = await session.get(Condition, measurement.condition_id)
        await self._update_condition_totals(session, condition)
        
        await session.commit()
        await session.refresh(measurement)
        
        return measurement

    async def delete_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
    ) -> None:
        """Delete a measurement."""
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        condition_id = measurement.condition_id
        
        await session.delete(measurement)
        
        # Update condition totals
        condition = await session.get(Condition, condition_id)
        if condition:
            await self._update_condition_totals(session, condition)
        
        await session.commit()

    async def recalculate_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
    ) -> Measurement:
        """Recalculate a measurement (e.g., after scale change)."""
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        page = await session.get(Page, measurement.page_id)
        condition = await session.get(Condition, measurement.condition_id)
        
        if not page.scale_value:
            raise ValueError("Page scale not calibrated")
        
        calculator = MeasurementCalculator(page.scale_value)
        calculation = self._calculate_geometry(
            calculator,
            measurement.geometry_type,
            measurement.geometry_data,
            condition.depth,
        )
        
        measurement.quantity = self._extract_quantity(
            calculation,
            condition.measurement_type,
        )
        measurement.pixel_length = calculation.get("pixel_length")
        measurement.pixel_area = calculation.get("pixel_area")
        measurement.metadata = {"calculation": calculation}
        
        await self._update_condition_totals(session, condition)
        
        await session.commit()
        await session.refresh(measurement)
        
        return measurement

    def _calculate_geometry(
        self,
        calculator: MeasurementCalculator,
        geometry_type: str,
        geometry_data: dict[str, Any],
        depth: float | None,
    ) -> dict[str, Any]:
        """Calculate measurements for a geometry."""
        if geometry_type == "line":
            return calculator.calculate_line(
                geometry_data["start"],
                geometry_data["end"],
            )
        elif geometry_type == "polyline":
            return calculator.calculate_polyline(geometry_data["points"])
        elif geometry_type == "polygon":
            return calculator.calculate_polygon(
                geometry_data["points"],
                depth,
            )
        elif geometry_type == "rectangle":
            return calculator.calculate_rectangle(
                geometry_data["x"],
                geometry_data["y"],
                geometry_data["width"],
                geometry_data["height"],
                depth,
            )
        elif geometry_type == "circle":
            return calculator.calculate_circle(
                geometry_data["center"],
                geometry_data["radius"],
                depth,
            )
        elif geometry_type == "point":
            return calculator.calculate_count(
                geometry_data["x"],
                geometry_data["y"],
            )
        else:
            raise ValueError(f"Unknown geometry type: {geometry_type}")

    def _extract_quantity(
        self,
        calculation: dict[str, Any],
        measurement_type: str,
    ) -> float:
        """Extract the relevant quantity from calculation results."""
        if measurement_type == "linear":
            return calculation.get("length_feet", calculation.get("perimeter_lf", 0))
        elif measurement_type == "area":
            return calculation.get("area_sf", 0)
        elif measurement_type == "volume":
            return calculation.get("volume_cy", 0)
        elif measurement_type == "count":
            return calculation.get("count", 1)
        else:
            raise ValueError(f"Unknown measurement type: {measurement_type}")

    async def _update_condition_totals(
        self,
        session: AsyncSession,
        condition: Condition,
    ) -> None:
        """Update condition's denormalized totals."""
        result = await session.execute(
            select(
                func.sum(Measurement.quantity),
                func.count(Measurement.id),
            ).where(Measurement.condition_id == condition.id)
        )
        row = result.one()
        
        condition.total_quantity = row[0] or 0.0
        condition.measurement_count = row[1] or 0


# Singleton
_engine: MeasurementEngine | None = None


def get_measurement_engine() -> MeasurementEngine:
    """Get the measurement engine singleton."""
    global _engine
    if _engine is None:
        _engine = MeasurementEngine()
    return _engine
```

---

### Task 6.4: Measurement API Endpoints

Create/update `backend/app/api/routes/measurements.py`:

```python
"""Measurement endpoints."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.measurement import Measurement
from app.models.condition import Condition
from app.models.page import Page
from app.schemas.measurement import (
    MeasurementCreate,
    MeasurementUpdate,
    MeasurementResponse,
    MeasurementListResponse,
)
from app.services.measurement_engine import get_measurement_engine

router = APIRouter()


@router.get("/conditions/{condition_id}/measurements", response_model=MeasurementListResponse)
async def list_condition_measurements(
    condition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all measurements for a condition."""
    result = await db.execute(
        select(Measurement)
        .where(Measurement.condition_id == condition_id)
        .order_by(Measurement.created_at)
    )
    measurements = result.scalars().all()
    
    return MeasurementListResponse(
        measurements=[MeasurementResponse.model_validate(m) for m in measurements],
        total=len(measurements),
    )


@router.get("/pages/{page_id}/measurements", response_model=MeasurementListResponse)
async def list_page_measurements(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all measurements on a page."""
    result = await db.execute(
        select(Measurement)
        .options(selectinload(Measurement.condition))
        .where(Measurement.page_id == page_id)
    )
    measurements = result.scalars().all()
    
    return MeasurementListResponse(
        measurements=[MeasurementResponse.model_validate(m) for m in measurements],
        total=len(measurements),
    )


@router.post(
    "/conditions/{condition_id}/measurements",
    response_model=MeasurementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_measurement(
    condition_id: uuid.UUID,
    request: MeasurementCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new measurement."""
    engine = get_measurement_engine()
    
    try:
        measurement = await engine.create_measurement(
            session=db,
            condition_id=condition_id,
            page_id=request.page_id,
            geometry_type=request.geometry_type,
            geometry_data=request.geometry_data,
            notes=request.notes,
        )
        return MeasurementResponse.model_validate(measurement)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/measurements/{measurement_id}", response_model=MeasurementResponse)
async def get_measurement(
    measurement_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get measurement details."""
    result = await db.execute(
        select(Measurement).where(Measurement.id == measurement_id)
    )
    measurement = result.scalar_one_or_none()
    
    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Measurement not found",
        )
    
    return MeasurementResponse.model_validate(measurement)


@router.put("/measurements/{measurement_id}", response_model=MeasurementResponse)
async def update_measurement(
    measurement_id: uuid.UUID,
    request: MeasurementUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a measurement."""
    engine = get_measurement_engine()
    
    try:
        measurement = await engine.update_measurement(
            session=db,
            measurement_id=measurement_id,
            geometry_data=request.geometry_data,
            notes=request.notes,
        )
        return MeasurementResponse.model_validate(measurement)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/measurements/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_measurement(
    measurement_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a measurement."""
    engine = get_measurement_engine()
    
    try:
        await engine.delete_measurement(db, measurement_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/measurements/{measurement_id}/recalculate", response_model=MeasurementResponse)
async def recalculate_measurement(
    measurement_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Recalculate a measurement (e.g., after scale change)."""
    engine = get_measurement_engine()
    
    try:
        measurement = await engine.recalculate_measurement(db, measurement_id)
        return MeasurementResponse.model_validate(measurement)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/pages/{page_id}/recalculate-all")
async def recalculate_page_measurements(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Recalculate all measurements on a page (after scale change)."""
    result = await db.execute(
        select(Measurement.id).where(Measurement.page_id == page_id)
    )
    measurement_ids = [row[0] for row in result.all()]
    
    engine = get_measurement_engine()
    
    for mid in measurement_ids:
        try:
            await engine.recalculate_measurement(db, mid)
        except ValueError:
            pass  # Skip measurements that can't be recalculated
    
    return {
        "status": "success",
        "recalculated_count": len(measurement_ids),
    }
```

---

### Task 6.5: Measurement Schemas

Create `backend/app/schemas/measurement.py`:

```python
"""Measurement schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class MeasurementCreate(BaseModel):
    """Request to create a measurement."""
    
    page_id: uuid.UUID
    geometry_type: str
    geometry_data: dict[str, Any]
    notes: str | None = None


class MeasurementUpdate(BaseModel):
    """Request to update a measurement."""
    
    geometry_data: dict[str, Any] | None = None
    notes: str | None = None


class MeasurementResponse(BaseModel):
    """Measurement response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    condition_id: uuid.UUID
    page_id: uuid.UUID
    geometry_type: str
    geometry_data: dict[str, Any]
    quantity: float
    unit: str
    pixel_length: float | None = None
    pixel_area: float | None = None
    is_ai_generated: bool
    ai_confidence: float | None = None
    is_modified: bool
    is_verified: bool
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class MeasurementListResponse(BaseModel):
    """Response for listing measurements."""
    
    measurements: list[MeasurementResponse]
    total: int
```

---

### Task 6.6: Frontend Measurement Layer

Create `frontend/src/components/viewer/MeasurementLayer.tsx`:

```tsx
import { useCallback, useState } from 'react';
import { Layer, Line, Rect, Circle, Group, Text } from 'react-konva';
import type { KonvaEventObject } from 'konva/lib/Node';

import type { Measurement, Condition } from '@/types';

interface MeasurementLayerProps {
  measurements: Measurement[];
  conditions: Map<string, Condition>;
  selectedMeasurementId: string | null;
  onMeasurementSelect: (id: string | null) => void;
  onMeasurementUpdate: (id: string, geometryData: any) => void;
  isEditing: boolean;
  scale: number; // Viewer zoom scale
}

export function MeasurementLayer({
  measurements,
  conditions,
  selectedMeasurementId,
  onMeasurementSelect,
  onMeasurementUpdate,
  isEditing,
  scale,
}: MeasurementLayerProps) {
  return (
    <Layer>
      {measurements.map((measurement) => {
        const condition = conditions.get(measurement.condition_id);
        if (!condition) return null;

        const isSelected = measurement.id === selectedMeasurementId;

        return (
          <MeasurementShape
            key={measurement.id}
            measurement={measurement}
            condition={condition}
            isSelected={isSelected}
            isEditing={isEditing && isSelected}
            scale={scale}
            onClick={() => onMeasurementSelect(measurement.id)}
            onUpdate={(geometryData) =>
              onMeasurementUpdate(measurement.id, geometryData)
            }
          />
        );
      })}
    </Layer>
  );
}

interface MeasurementShapeProps {
  measurement: Measurement;
  condition: Condition;
  isSelected: boolean;
  isEditing: boolean;
  scale: number;
  onClick: () => void;
  onUpdate: (geometryData: any) => void;
}

function MeasurementShape({
  measurement,
  condition,
  isSelected,
  isEditing,
  scale,
  onClick,
  onUpdate,
}: MeasurementShapeProps) {
  const { geometry_type, geometry_data } = measurement;
  const color = condition.color;
  const strokeWidth = (condition.line_width || 2) / scale;
  const fillOpacity = condition.fill_opacity || 0.3;

  const commonProps = {
    stroke: color,
    strokeWidth: isSelected ? strokeWidth * 1.5 : strokeWidth,
    onClick,
    onTap: onClick,
  };

  switch (geometry_type) {
    case 'line':
      return (
        <LineShape
          start={geometry_data.start}
          end={geometry_data.end}
          {...commonProps}
          quantity={measurement.quantity}
          unit={measurement.unit}
          scale={scale}
        />
      );

    case 'polyline':
      return (
        <PolylineShape
          points={geometry_data.points}
          {...commonProps}
          quantity={measurement.quantity}
          unit={measurement.unit}
          scale={scale}
        />
      );

    case 'polygon':
      return (
        <PolygonShape
          points={geometry_data.points}
          fill={color}
          fillOpacity={fillOpacity}
          {...commonProps}
          quantity={measurement.quantity}
          unit={measurement.unit}
          scale={scale}
        />
      );

    case 'rectangle':
      return (
        <RectangleShape
          x={geometry_data.x}
          y={geometry_data.y}
          width={geometry_data.width}
          height={geometry_data.height}
          fill={color}
          fillOpacity={fillOpacity}
          {...commonProps}
          quantity={measurement.quantity}
          unit={measurement.unit}
          scale={scale}
        />
      );

    case 'circle':
      return (
        <CircleShape
          center={geometry_data.center}
          radius={geometry_data.radius}
          fill={color}
          fillOpacity={fillOpacity}
          {...commonProps}
          quantity={measurement.quantity}
          unit={measurement.unit}
          scale={scale}
        />
      );

    case 'point':
      return (
        <PointShape
          x={geometry_data.x}
          y={geometry_data.y}
          color={color}
          {...commonProps}
          scale={scale}
        />
      );

    default:
      return null;
  }
}

// Individual shape components
function LineShape({
  start,
  end,
  stroke,
  strokeWidth,
  onClick,
  onTap,
  quantity,
  unit,
  scale,
}: any) {
  const midX = (start.x + end.x) / 2;
  const midY = (start.y + end.y) / 2;

  return (
    <Group>
      <Line
        points={[start.x, start.y, end.x, end.y]}
        stroke={stroke}
        strokeWidth={strokeWidth}
        onClick={onClick}
        onTap={onTap}
        hitStrokeWidth={20}
      />
      <Text
        x={midX}
        y={midY - 10 / scale}
        text={`${quantity.toFixed(1)} ${unit}`}
        fontSize={12 / scale}
        fill={stroke}
        offsetX={20}
      />
    </Group>
  );
}

function PolylineShape({
  points,
  stroke,
  strokeWidth,
  onClick,
  onTap,
  quantity,
  unit,
  scale,
}: any) {
  const flatPoints = points.flatMap((p: any) => [p.x, p.y]);
  const firstPoint = points[0];

  return (
    <Group>
      <Line
        points={flatPoints}
        stroke={stroke}
        strokeWidth={strokeWidth}
        onClick={onClick}
        onTap={onTap}
        hitStrokeWidth={20}
      />
      <Text
        x={firstPoint.x}
        y={firstPoint.y - 15 / scale}
        text={`${quantity.toFixed(1)} ${unit}`}
        fontSize={12 / scale}
        fill={stroke}
      />
    </Group>
  );
}

function PolygonShape({
  points,
  stroke,
  strokeWidth,
  fill,
  fillOpacity,
  onClick,
  onTap,
  quantity,
  unit,
  scale,
}: any) {
  const flatPoints = points.flatMap((p: any) => [p.x, p.y]);
  
  // Calculate centroid for label
  const centroidX = points.reduce((sum: number, p: any) => sum + p.x, 0) / points.length;
  const centroidY = points.reduce((sum: number, p: any) => sum + p.y, 0) / points.length;

  return (
    <Group>
      <Line
        points={flatPoints}
        stroke={stroke}
        strokeWidth={strokeWidth}
        fill={fill}
        opacity={fillOpacity}
        closed={true}
        onClick={onClick}
        onTap={onTap}
      />
      <Text
        x={centroidX}
        y={centroidY}
        text={`${quantity.toFixed(1)} ${unit}`}
        fontSize={14 / scale}
        fill={stroke}
        align="center"
        offsetX={30}
        offsetY={7}
      />
    </Group>
  );
}

function RectangleShape({
  x,
  y,
  width,
  height,
  stroke,
  strokeWidth,
  fill,
  fillOpacity,
  onClick,
  onTap,
  quantity,
  unit,
  scale,
}: any) {
  return (
    <Group>
      <Rect
        x={x}
        y={y}
        width={width}
        height={height}
        stroke={stroke}
        strokeWidth={strokeWidth}
        fill={fill}
        opacity={fillOpacity}
        onClick={onClick}
        onTap={onTap}
      />
      <Text
        x={x + width / 2}
        y={y + height / 2}
        text={`${quantity.toFixed(1)} ${unit}`}
        fontSize={14 / scale}
        fill={stroke}
        align="center"
        offsetX={30}
        offsetY={7}
      />
    </Group>
  );
}

function CircleShape({
  center,
  radius,
  stroke,
  strokeWidth,
  fill,
  fillOpacity,
  onClick,
  onTap,
  quantity,
  unit,
  scale,
}: any) {
  return (
    <Group>
      <Circle
        x={center.x}
        y={center.y}
        radius={radius}
        stroke={stroke}
        strokeWidth={strokeWidth}
        fill={fill}
        opacity={fillOpacity}
        onClick={onClick}
        onTap={onTap}
      />
      <Text
        x={center.x}
        y={center.y}
        text={`${quantity.toFixed(1)} ${unit}`}
        fontSize={14 / scale}
        fill={stroke}
        align="center"
        offsetX={30}
        offsetY={7}
      />
    </Group>
  );
}

function PointShape({
  x,
  y,
  color,
  onClick,
  onTap,
  scale,
}: any) {
  const markerSize = 8 / scale;

  return (
    <Group onClick={onClick} onTap={onTap}>
      {/* X marker */}
      <Line
        points={[
          x - markerSize, y - markerSize,
          x + markerSize, y + markerSize,
        ]}
        stroke={color}
        strokeWidth={2 / scale}
      />
      <Line
        points={[
          x + markerSize, y - markerSize,
          x - markerSize, y + markerSize,
        ]}
        stroke={color}
        strokeWidth={2 / scale}
      />
      <Circle
        x={x}
        y={y}
        radius={markerSize * 1.5}
        stroke={color}
        strokeWidth={1 / scale}
      />
    </Group>
  );
}
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] Line measurement calculates correct length in feet
- [ ] Polyline measurement sums all segments
- [ ] Polygon measurement calculates area in SF
- [ ] Rectangle measurement works correctly
- [ ] Circle measurement calculates area correctly
- [ ] Volume calculation with depth works (SF → CY)
- [ ] Count measurements return 1 each
- [ ] Measurements update condition totals
- [ ] Measurements display on canvas with labels
- [ ] Measurements can be selected and edited
- [ ] Scale changes trigger recalculation
- [ ] API CRUD operations work correctly

### Test Cases

1. Draw a 100-pixel line on a page with scale 10 px/ft → should show 10 LF
2. Draw a 100x100 pixel rectangle → should show 100 SF at 10 px/ft scale
3. Add 4" depth to an area condition → verify CY calculation
4. Delete a measurement → condition total updates
5. Change page scale → all measurements recalculate

---

## Next Phase

Once verified, proceed to **`07-CONDITION-MANAGEMENT.md`** for implementing the condition (takeoff line item) management system and UI.
