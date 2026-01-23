# Measurement Engine Service Documentation

## Overview

The Measurement Engine service converts pixel-based geometry drawings on construction plans into real-world measurements (linear feet, square feet, cubic yards, counts) using page scale calibration. It provides comprehensive CRUD operations for measurements with automatic calculation and condition total updates.

**Location:** `backend/app/services/measurement_engine.py`

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│            Measurement Engine Service                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐      ┌──────────────────┐   │
│  │MeasurementEngine │      │MeasurementCalc   │   │
│  └────────┬─────────┘      └────────┬─────────┘   │
│           │                         │              │
│           ▼                         ▼              │
│  ┌──────────────────┐      ┌──────────────────┐   │
│  │  CRUD Operations │      │ Geometry Utils   │   │
│  │  - Create        │      │ - Point          │   │
│  │  - Update        │      │ - Calculations   │   │
│  │  - Delete        │      │ - Conversions    │   │
│  │  - Recalculate   │      └──────────────────┘   │
│  └──────────────────┘                              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Data Flow

```
Geometry Data + Condition + Page
    ↓
MeasurementEngine.create_measurement()
    ↓
Validate geometry type & page scale
    ↓
MeasurementCalculator converts pixels → real units
    ↓
Extract quantity based on measurement_type
    ↓
Create Measurement record
    ↓
Update Condition totals (denormalized)
    ↓
Return Measurement with calculated values
```

---

## Classes

### MeasurementEngine

Main service class for measurement operations.

#### Initialization

```python
from app.services.measurement_engine import get_measurement_engine

engine = get_measurement_engine()
# Returns singleton instance
```

**Requirements:**
- Page must have `scale_calibrated = true`
- Page must have `scale_value` set (pixels per foot)
- Condition must exist and belong to project

#### Constants

```python
GEOMETRY_TYPES = ["line", "polyline", "polygon", "rectangle", "circle", "point"]
MEASUREMENT_TYPES = ["linear", "area", "volume", "count"]

UNIT_MAP = {
    "linear": "LF",   # Linear Feet
    "area": "SF",     # Square Feet
    "volume": "CY",   # Cubic Yards
    "count": "EA",    # Each
}
```

---

### Methods

#### create_measurement()

Create a new measurement with automatic calculation.

```python
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
    """
    Create a new measurement.
    
    Args:
        session: Database session
        condition_id: Parent condition ID
        page_id: Page where measurement is drawn
        geometry_type: Type of geometry (line, polyline, polygon, rectangle, circle, point)
        geometry_data: Geometry coordinates (structure varies by type)
        is_ai_generated: Whether created by AI
        ai_confidence: AI confidence score (0-1)
        notes: Optional notes
        
    Returns:
        Created Measurement with calculated quantity
        
    Raises:
        ValueError: If geometry type invalid, page not calibrated, or condition/page not found
    """
```

**Example:**
```python
from app.services.measurement_engine import get_measurement_engine

engine = get_measurement_engine()

measurement = await engine.create_measurement(
    session=db,
    condition_id=condition_id,
    page_id=page_id,
    geometry_type="polygon",
    geometry_data={
        "points": [
            {"x": 100, "y": 100},
            {"x": 200, "y": 100},
            {"x": 200, "y": 200},
            {"x": 100, "y": 200}
        ]
    },
    notes="Main slab area"
)

print(f"Created measurement: {measurement.quantity} {measurement.unit}")
# Output: Created measurement: 100.0 SF
```

**Validation:**
- Geometry type must be in `GEOMETRY_TYPES`
- Page must have `scale_calibrated = true` and `scale_value` set
- Condition and page must exist
- Geometry data structure must match geometry type

**Automatic Updates:**
- Condition `total_quantity` is updated via SQL aggregation
- Condition `measurement_count` is incremented
- Measurement `quantity` is calculated based on condition's `measurement_type`

---

#### update_measurement()

Update an existing measurement's geometry or notes.

```python
async def update_measurement(
    self,
    session: AsyncSession,
    measurement_id: uuid.UUID,
    geometry_data: dict[str, Any] | None = None,
    notes: str | None = None,
) -> Measurement:
    """
    Update an existing measurement.
    
    Args:
        session: Database session
        measurement_id: Measurement to update
        geometry_data: New geometry (optional, triggers recalculation)
        notes: New notes (optional)
        
    Returns:
        Updated Measurement
        
    Raises:
        ValueError: If measurement not found or page not calibrated
    """
```

**Example:**
```python
measurement = await engine.update_measurement(
    session=db,
    measurement_id=measurement_id,
    geometry_data={
        "points": [
            {"x": 150, "y": 150},
            {"x": 250, "y": 150},
            {"x": 250, "y": 250},
            {"x": 150, "y": 250}
        ]
    },
    notes="Updated slab area"
)
```

**Behavior:**
- If `geometry_data` provided, measurement is recalculated
- `is_modified` flag is set to `True`
- Condition totals are automatically updated

---

#### delete_measurement()

Delete a measurement and update condition totals.

```python
async def delete_measurement(
    self,
    session: AsyncSession,
    measurement_id: uuid.UUID,
) -> None:
    """
    Delete a measurement.
    
    Args:
        session: Database session
        measurement_id: Measurement to delete
        
    Raises:
        ValueError: If measurement not found
    """
```

**Example:**
```python
await engine.delete_measurement(db, measurement_id)
# Condition totals automatically updated
```

**Cascade Behavior:**
- Measurement is deleted from database
- Condition `total_quantity` decreases by measurement's quantity
- Condition `measurement_count` decreases by 1

---

#### recalculate_measurement()

Recalculate a measurement (e.g., after page scale change).

```python
async def recalculate_measurement(
    self,
    session: AsyncSession,
    measurement_id: uuid.UUID,
) -> Measurement:
    """
    Recalculate a measurement using current page scale.
    
    Args:
        session: Database session
        measurement_id: Measurement to recalculate
        
    Returns:
        Recalculated Measurement
        
    Raises:
        ValueError: If measurement not found or page not calibrated
    """
```

**Example:**
```python
# After changing page scale
measurement = await engine.recalculate_measurement(db, measurement_id)
print(f"New quantity: {measurement.quantity} {measurement.unit}")
```

**Use Cases:**
- Page scale recalibration
- Scale detection updates
- Manual scale corrections

---

### MeasurementCalculator

Calculator for converting pixel measurements to real-world units.

**Location:** `backend/app/utils/geometry.py`

#### Initialization

```python
from app.utils.geometry import MeasurementCalculator

calculator = MeasurementCalculator(pixels_per_foot=10.0)
# 10 pixels = 1 real foot
```

#### Methods

##### pixels_to_feet()

Convert pixel distance to feet.

```python
def pixels_to_feet(self, pixels: float) -> float:
    """Convert pixel distance to feet."""
    return pixels / self.pixels_per_foot
```

**Example:**
```python
calculator = MeasurementCalculator(pixels_per_foot=10)
feet = calculator.pixels_to_feet(100)  # Returns 10.0
```

---

##### pixels_to_square_feet()

Convert pixel area to square feet.

```python
def pixels_to_square_feet(self, pixel_area: float) -> float:
    """Convert pixel area to square feet."""
    return pixel_area / (self.pixels_per_foot ** 2)
```

**Example:**
```python
calculator = MeasurementCalculator(pixels_per_foot=10)
sf = calculator.pixels_to_square_feet(10000)  # Returns 100.0
```

---

##### square_feet_to_cubic_yards()

Convert square feet to cubic yards given depth.

```python
def square_feet_to_cubic_yards(
    self,
    square_feet: float,
    depth_inches: float,
) -> float:
    """
    Convert square feet to cubic yards given depth.
    
    Formula: (SF × depth_inches / 12) / 27
    
    Args:
        square_feet: Area in square feet
        depth_inches: Depth/thickness in inches
        
    Returns:
        Volume in cubic yards
    """
```

**Example:**
```python
calculator = MeasurementCalculator(pixels_per_foot=10)
cy = calculator.square_feet_to_cubic_yards(100, 4)  # 100 SF × 4" = 1.23 CY
```

---

##### calculate_line()

Calculate line measurement (two points).

```python
def calculate_line(
    self,
    start: dict[str, float],
    end: dict[str, float],
) -> dict[str, float]:
    """
    Calculate line measurement.
    
    Args:
        start: {"x": float, "y": float}
        end: {"x": float, "y": float}
        
    Returns:
        {
            "pixel_length": float,
            "length_feet": float
        }
    """
```

**Example:**
```python
result = calculator.calculate_line(
    start={"x": 0, "y": 0},
    end={"x": 100, "y": 0}
)
# Returns: {"pixel_length": 100.0, "length_feet": 10.0}
```

---

##### calculate_polyline()

Calculate polyline measurement (multi-segment path).

```python
def calculate_polyline(
    self,
    points: list[dict[str, float]],
) -> dict[str, float]:
    """
    Calculate polyline measurement.
    
    Args:
        points: [{"x": float, "y": float}, ...]
        
    Returns:
        {
            "pixel_length": float,
            "length_feet": float,
            "segment_count": int,
            "segment_lengths": [{"pixel_length": float, "length_feet": float}, ...]
        }
    """
```

**Example:**
```python
result = calculator.calculate_polyline([
    {"x": 0, "y": 0},
    {"x": 100, "y": 0},
    {"x": 100, "y": 100}
])
# Returns: {
#   "pixel_length": 200.0,
#   "length_feet": 20.0,
#   "segment_count": 2,
#   "segment_lengths": [...]
# }
```

---

##### calculate_polygon()

Calculate polygon measurement (closed shape).

```python
def calculate_polygon(
    self,
    points: list[dict[str, float]],
    depth_inches: float | None = None,
) -> dict[str, float]:
    """
    Calculate polygon measurement.
    
    Uses shoelace formula for area calculation.
    
    Args:
        points: [{"x": float, "y": float}, ...] (closed shape)
        depth_inches: Optional depth for volume calculation
        
    Returns:
        {
            "pixel_area": float,
            "pixel_perimeter": float,
            "area_sf": float,
            "perimeter_lf": float,
            "volume_cy": float (if depth provided),
            "depth_inches": float (if depth provided)
        }
    """
```

**Example:**
```python
result = calculator.calculate_polygon(
    points=[
        {"x": 0, "y": 0},
        {"x": 100, "y": 0},
        {"x": 100, "y": 100},
        {"x": 0, "y": 100}
    ],
    depth_inches=4
)
# Returns: {
#   "area_sf": 100.0,
#   "perimeter_lf": 40.0,
#   "volume_cy": 1.23
# }
```

---

##### calculate_rectangle()

Calculate rectangle measurement.

```python
def calculate_rectangle(
    self,
    x: float,
    y: float,
    width: float,
    height: float,
    depth_inches: float | None = None,
) -> dict[str, float]:
    """
    Calculate rectangle measurement.
    
    Args:
        x: Top-left x coordinate
        y: Top-left y coordinate
        width: Width in pixels
        height: Height in pixels
        depth_inches: Optional depth for volume calculation
        
    Returns:
        {
            "width_feet": float,
            "height_feet": float,
            "area_sf": float,
            "perimeter_lf": float,
            "volume_cy": float (if depth provided)
        }
    """
```

**Example:**
```python
result = calculator.calculate_rectangle(
    x=0, y=0, width=100, height=100, depth_inches=6
)
# Returns: {
#   "width_feet": 10.0,
#   "height_feet": 10.0,
#   "area_sf": 100.0,
#   "perimeter_lf": 40.0,
#   "volume_cy": 1.85
# }
```

---

##### calculate_circle()

Calculate circle measurement.

```python
def calculate_circle(
    self,
    center: dict[str, float],
    radius: float,
    depth_inches: float | None = None,
) -> dict[str, float]:
    """
    Calculate circle measurement.
    
    Args:
        center: {"x": float, "y": float}
        radius: Radius in pixels
        depth_inches: Optional depth for volume calculation
        
    Returns:
        {
            "radius_feet": float,
            "diameter_feet": float,
            "area_sf": float,
            "circumference_lf": float,
            "volume_cy": float (if depth provided)
        }
    """
```

**Example:**
```python
result = calculator.calculate_circle(
    center={"x": 100, "y": 100},
    radius=50,
    depth_inches=4
)
# Returns: {
#   "radius_feet": 5.0,
#   "diameter_feet": 10.0,
#   "area_sf": 78.54,
#   "circumference_lf": 31.42,
#   "volume_cy": 0.97
# }
```

---

##### calculate_count()

Calculate count measurement (point).

```python
def calculate_count(self, x: float, y: float) -> dict[str, Any]:
    """
    Calculate count measurement (always returns 1).
    
    Args:
        x: X coordinate
        y: Y coordinate
        
    Returns:
        {
            "count": 1,
            "position": {"x": float, "y": float}
        }
    """
```

**Example:**
```python
result = calculator.calculate_count(100, 200)
# Returns: {"count": 1, "position": {"x": 100, "y": 200}}
```

---

## Geometry Utilities

### Point Class

2D point with distance calculations.

```python
@dataclass
class Point:
    x: float
    y: float
    
    def distance_to(self, other: "Point") -> float:
        """Calculate distance to another point."""
        
    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        
    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "Point":
        """Create from dictionary."""
```

**Example:**
```python
from app.utils.geometry import Point

p1 = Point(x=0, y=0)
p2 = Point(x=100, y=100)
distance = p1.distance_to(p2)  # Returns 141.42...
```

---

### Calculation Functions

#### calculate_line_length()

Calculate distance between two points.

```python
def calculate_line_length(start: Point, end: Point) -> float:
    """Calculate length of a line segment."""
```

#### calculate_polyline_length()

Calculate total length of a polyline.

```python
def calculate_polyline_length(points: list[Point]) -> float:
    """Calculate total length of a polyline."""
```

#### calculate_polygon_area()

Calculate area using shoelace formula.

```python
def calculate_polygon_area(points: list[Point]) -> float:
    """Calculate area of a polygon using the shoelace formula."""
```

**Algorithm:**
```
Area = 0.5 × |Σ(xi × yi+1 - xi+1 × yi)|
```

#### calculate_polygon_perimeter()

Calculate perimeter of a closed polygon.

```python
def calculate_polygon_perimeter(points: list[Point]) -> float:
    """Calculate perimeter of a polygon."""
```

#### calculate_rectangle_area()

Calculate area of a rectangle.

```python
def calculate_rectangle_area(width: float, height: float) -> float:
    """Calculate area of a rectangle."""
    return width * height
```

#### calculate_rectangle_perimeter()

Calculate perimeter of a rectangle.

```python
def calculate_rectangle_perimeter(width: float, height: float) -> float:
    """Calculate perimeter of a rectangle."""
    return 2 * (width + height)
```

#### calculate_circle_area()

Calculate area of a circle.

```python
def calculate_circle_area(radius: float) -> float:
    """Calculate area of a circle."""
    return math.pi * radius ** 2
```

#### calculate_circle_circumference()

Calculate circumference of a circle.

```python
def calculate_circle_circumference(radius: float) -> float:
    """Calculate circumference of a circle."""
    return 2 * math.pi * radius
```

---

## Usage Examples

### Basic Measurement Creation

```python
from app.services.measurement_engine import get_measurement_engine

engine = get_measurement_engine()

# Create a polygon measurement
measurement = await engine.create_measurement(
    session=db,
    condition_id=condition_id,
    page_id=page_id,
    geometry_type="polygon",
    geometry_data={
        "points": [
            {"x": 100, "y": 100},
            {"x": 200, "y": 100},
            {"x": 200, "y": 200},
            {"x": 100, "y": 200}
        ]
    }
)

print(f"Quantity: {measurement.quantity} {measurement.unit}")
```

---

### Volume Calculation

```python
# Create condition with depth
condition = Condition(
    name="4\" Concrete Slab",
    measurement_type="volume",
    unit="CY",
    depth=4  # inches
)

# Create polygon measurement
measurement = await engine.create_measurement(
    session=db,
    condition_id=condition.id,
    page_id=page_id,
    geometry_type="polygon",
    geometry_data={"points": [...]}
)

# Measurement quantity will be in cubic yards
print(f"Volume: {measurement.quantity} CY")
```

---

### Recalculate After Scale Change

```python
# Page scale changed from 10 px/ft to 20 px/ft
# Recalculate all measurements on page

result = await db.execute(
    select(Measurement.id).where(Measurement.page_id == page_id)
)
measurement_ids = [row[0] for row in result.all()]

for mid in measurement_ids:
    await engine.recalculate_measurement(db, mid)
```

---

### Batch Operations

```python
# Create multiple measurements
measurements = []
for geometry_data in geometry_list:
    measurement = await engine.create_measurement(
        session=db,
        condition_id=condition_id,
        page_id=page_id,
        geometry_type="polygon",
        geometry_data=geometry_data
    )
    measurements.append(measurement)

# Condition totals automatically updated after each creation
```

---

## Error Handling

### Common Errors

**Page Not Calibrated**
```python
ValueError: "Page scale not calibrated"
```
**Solution:** Calibrate page scale first using Phase 2B scale detection.

**Invalid Geometry Type**
```python
ValueError: "Invalid geometry type: invalid_type"
```
**Solution:** Use one of: `line`, `polyline`, `polygon`, `rectangle`, `circle`, `point`

**Condition Not Found**
```python
ValueError: "Condition not found: {condition_id}"
```
**Solution:** Verify condition exists and belongs to project.

**Measurement Type Mismatch**
- Linear measurements require `line` or `polyline` geometry
- Area measurements require `polygon`, `rectangle`, or `circle` geometry
- Volume measurements require area geometries with depth
- Count measurements require `point` geometry

---

## Performance Considerations

### Denormalized Totals

Condition totals (`total_quantity`, `measurement_count`) are denormalized for performance:

```python
# Automatically updated via SQL aggregation
condition.total_quantity = sum(m.quantity for m in condition.measurements)
condition.measurement_count = len(condition.measurements)
```

**Benefits:**
- Fast condition summary queries
- No need to aggregate measurements on every read
- Consistent totals across all queries

**Trade-offs:**
- Totals must be updated on measurement create/update/delete
- Slight write overhead for consistency

---

### Scale Dependency

All measurements require:
1. Page `scale_calibrated = true`
2. Page `scale_value` set (pixels per foot)
3. Measurements store pixel values in `geometry_data`
4. Real-world quantities calculated using `scale_value`

**Recalculation:**
- When page scale changes, all measurements must be recalculated
- Use `recalculate_measurement()` or `recalculate_all()` endpoint
- Condition totals automatically update after recalculation

---

## Testing

### Unit Tests

```python
import pytest
from app.services.measurement_engine import get_measurement_engine

@pytest.mark.asyncio
async def test_create_measurement(db_session, condition, page):
    engine = get_measurement_engine()
    
    measurement = await engine.create_measurement(
        session=db_session,
        condition_id=condition.id,
        page_id=page.id,
        geometry_type="line",
        geometry_data={
            "start": {"x": 0, "y": 0},
            "end": {"x": 100, "y": 0}
        }
    )
    
    assert measurement.quantity > 0
    assert measurement.unit == "LF"
```

---

## Related Documentation

- [Phase 3A Guide](../phase-guides/PHASE_3A_GUIDE.md) - Complete measurement engine guide
- [API Reference](../api/API_REFERENCE.md) - Measurement endpoints
- [Database Schema](../database/DATABASE_SCHEMA.md) - Measurement model structure
- [Geometry Utilities](../../backend/app/utils/geometry.py) - Calculation functions

---

**Last Updated:** January 22, 2026  
**Status:** ✅ Complete and Production Ready
