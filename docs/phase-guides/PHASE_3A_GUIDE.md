# Phase 3A: Measurement Engine - Complete Guide

**Status**: ✅ Complete  
**Completion Date**: January 20, 2026  
**Prerequisites**: Phase 2B (Scale Detection) must be complete

---

## Quick Start

### For Developers New to Phase 3A

**What is Phase 3A?**  
The measurement engine converts pixel-based drawings on construction plans into real-world measurements (linear feet, square feet, cubic yards, counts) using page scale calibration.

**5-Minute Setup:**

1. **Ensure page is calibrated** (Phase 2B prerequisite)
   ```bash
   GET /api/v1/pages/{page_id}
   # Verify: scale_calibrated = true, scale_value is set
   ```

2. **Create a condition** (takeoff line item)
   ```bash
   POST /api/v1/projects/{project_id}/conditions
   {
     "name": "4\" Concrete Slab",
     "measurement_type": "area",
     "unit": "SF"
   }
   ```

3. **Create a measurement** (draw geometry)
   ```bash
   POST /api/v1/conditions/{condition_id}/measurements
   {
     "page_id": "{page_id}",
     "geometry_type": "polygon",
     "geometry_data": {
       "points": [
         {"x": 100, "y": 100},
         {"x": 200, "y": 100},
         {"x": 200, "y": 200},
         {"x": 100, "y": 200}
       ]
     }
   }
   ```

4. **Check results**
   ```bash
   GET /api/v1/conditions/{condition_id}
   # See: total_quantity, measurement_count
   ```

**Common Workflow:**
```
Create Condition → Draw Measurements → View Totals → Export
```

**Need Help?**
- See [Measurement Service Documentation](../services/MEASUREMENT_SERVICE.md) for detailed implementation
- See [API Reference](../api/API_REFERENCE.md) for all endpoints
- See [Geometry Types](#geometry-types) section below for drawing examples

---

## Overview

Phase 3A implements the core measurement engine for construction takeoff calculations. The system converts pixel-based drawings on construction plans into real-world measurements (linear feet, square feet, cubic yards, counts) using page scale calibration.

### Key Capabilities

- ✅ **6 Geometry Types**: Line, Polyline, Polygon, Rectangle, Circle, Point
- ✅ **4 Measurement Types**: Linear (LF), Area (SF), Volume (CY), Count (EA)
- ✅ **Automatic Calculations**: Pixel-to-real-world unit conversion using page scale
- ✅ **Volume Support**: Depth/thickness modifiers for concrete volume calculations
- ✅ **Condition Totals**: Automatic aggregation of measurements per condition
- ✅ **Scale Recalculation**: Recalculate all measurements when page scale changes
- ✅ **AI Tracking**: Support for AI-generated measurements with confidence scores

---

## Architecture

### System Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   FastAPI   │────▶│ Measurement │
│  (Konva.js) │     │   Backend   │     │   Engine    │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                    │
                            ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │ PostgreSQL   │     │  Geometry   │
                    │  Database    │     │ Calculator  │
                    └─────────────┘     └─────────────┘
```

### Component Overview

| Component | Purpose | Location |
|-----------|---------|----------|
| **MeasurementEngine** | Service layer for CRUD operations | `backend/app/services/measurement_engine.py` |
| **MeasurementCalculator** | Geometry calculations & unit conversion | `backend/app/utils/geometry.py` |
| **Measurement Model** | Database model | `backend/app/models/measurement.py` |
| **Condition Model** | Takeoff line item model | `backend/app/models/condition.py` |
| **API Routes** | REST endpoints | `backend/app/api/routes/measurements.py` |
| **Frontend Layer** | Konva.js rendering | `frontend/src/components/viewer/MeasurementLayer.tsx` |

---

## API Reference

### Base URL

```
http://localhost:8000/api/v1
```

### Measurement Endpoints

#### List Measurements by Condition

`GET /conditions/{condition_id}/measurements`

Get all measurements for a specific condition.

**Parameters:**
- `condition_id` (path) - UUID of the condition

**Response** `200 OK`
```json
{
  "measurements": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "condition_id": "660e8400-e29b-41d4-a716-446655440001",
      "page_id": "770e8400-e29b-41d4-a716-446655440002",
      "geometry_type": "polygon",
      "geometry_data": {
        "points": [
          {"x": 100, "y": 100},
          {"x": 200, "y": 100},
          {"x": 200, "y": 200},
          {"x": 100, "y": 200}
        ]
      },
      "quantity": 100.0,
      "unit": "SF",
      "pixel_length": null,
      "pixel_area": 10000.0,
      "is_ai_generated": false,
      "is_modified": false,
      "is_verified": false,
      "notes": null,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ],
  "total": 1
}
```

**Errors:**
| Status | Description |
|--------|-------------|
| 404 | Condition not found |

---

#### List Measurements by Page

`GET /pages/{page_id}/measurements`

Get all measurements on a specific page.

**Parameters:**
- `page_id` (path) - UUID of the page

**Response** `200 OK`
```json
{
  "measurements": [...],
  "total": 5
}
```

**Errors:**
| Status | Description |
|--------|-------------|
| 404 | Page not found |

---

#### Create Measurement

`POST /conditions/{condition_id}/measurements`

Create a new measurement. The measurement engine automatically calculates quantities based on the geometry and condition's measurement type.

**Parameters:**
- `condition_id` (path) - UUID of the condition

**Request Body:**
```json
{
  "page_id": "770e8400-e29b-41d4-a716-446655440002",
  "geometry_type": "polygon",
  "geometry_data": {
    "points": [
      {"x": 100, "y": 100},
      {"x": 200, "y": 100},
      {"x": 200, "y": 200},
      {"x": 100, "y": 200}
    ]
  },
  "notes": "Main slab area"
}
```

**Response** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "condition_id": "660e8400-e29b-41d4-a716-446655440001",
  "page_id": "770e8400-e29b-41d4-a716-446655440002",
  "geometry_type": "polygon",
  "geometry_data": {...},
  "quantity": 100.0,
  "unit": "SF",
  "pixel_area": 10000.0,
  "...": "..."
}
```

**Errors:**
| Status | Description |
|--------|-------------|
| 400 | Invalid geometry type, page not calibrated, or validation error |
| 404 | Condition or page not found |

**Validation Rules:**
- Page must have `scale_calibrated = true` and `scale_value` set
- Geometry type must be one of: `line`, `polyline`, `polygon`, `rectangle`, `circle`, `point`
- Geometry data must match the geometry type structure

---

#### Get Measurement

`GET /measurements/{measurement_id}`

Get details for a specific measurement.

**Parameters:**
- `measurement_id` (path) - UUID of the measurement

**Response** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "condition_id": "660e8400-e29b-41d4-a716-446655440001",
  "page_id": "770e8400-e29b-41d4-a716-446655440002",
  "geometry_type": "polygon",
  "geometry_data": {...},
  "quantity": 100.0,
  "unit": "SF",
  "...": "..."
}
```

**Errors:**
| Status | Description |
|--------|-------------|
| 404 | Measurement not found |

---

#### Update Measurement

`PUT /measurements/{measurement_id}`

Update a measurement's geometry or notes. Quantities are automatically recalculated.

**Parameters:**
- `measurement_id` (path) - UUID of the measurement

**Request Body:**
```json
{
  "geometry_data": {
    "points": [
      {"x": 150, "y": 150},
      {"x": 250, "y": 150},
      {"x": 250, "y": 250},
      {"x": 150, "y": 250}
    ]
  },
  "notes": "Updated main slab area"
}
```

All fields are optional. Only provided fields will be updated.

**Response** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "quantity": 100.0,
  "...": "..."
}
```

**Errors:**
| Status | Description |
|--------|-------------|
| 400 | Invalid geometry data or validation error |
| 404 | Measurement not found |

---

#### Delete Measurement

`DELETE /measurements/{measurement_id}`

Delete a measurement. Condition totals are automatically updated.

**Parameters:**
- `measurement_id` (path) - UUID of the measurement

**Response** `204 No Content`

**Errors:**
| Status | Description |
|--------|-------------|
| 404 | Measurement not found |

---

#### Recalculate Measurement

`POST /measurements/{measurement_id}/recalculate`

Recalculate a measurement (e.g., after page scale change).

**Parameters:**
- `measurement_id` (path) - UUID of the measurement

**Response** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "quantity": 50.0,
  "...": "..."
}
```

**Errors:**
| Status | Description |
|--------|-------------|
| 400 | Page not calibrated or calculation error |

---

#### Recalculate All Page Measurements

`POST /pages/{page_id}/recalculate-all`

Recalculate all measurements on a page (useful after scale calibration changes).

**Parameters:**
- `page_id` (path) - UUID of the page

**Response** `200 OK`
```json
{
  "status": "success",
  "recalculated_count": 15
}
```

**Errors:**
| Status | Description |
|--------|-------------|
| 404 | Page not found |

---

## Geometry Types

### Line

Two-point linear measurement.

**Visual Representation:**
```
    Start Point              End Point
        ●────────────────────────●
        (x1, y1)              (x2, y2)
        
    Length = distance between points
```

**Geometry Data Structure:**
```json
{
  "start": {"x": 100, "y": 100},
  "end": {"x": 200, "y": 200}
}
```

**Calculations:**
- Pixel length: Distance between start and end points
- Length (feet): `pixel_length / pixels_per_foot`

**Use Cases:**
- Footings
- Curbs
- Edge forms
- Linear concrete elements

**Example:**
```python
# 100-pixel line on page with scale 10 px/ft
calculator = MeasurementCalculator(pixels_per_foot=10)
result = calculator.calculate_line(
    start={"x": 0, "y": 0},
    end={"x": 100, "y": 0}
)
# result = {"pixel_length": 100, "length_feet": 10.0}
```

---

### Polyline

Multi-segment path measurement.

**Visual Representation:**
```
    Point 1      Point 2      Point 3      Point 4
        ●──────────●──────────●──────────●
        
    Total Length = sum of all segment lengths
    Segments: [seg1, seg2, seg3]
```

**Geometry Data Structure:**
```json
{
  "points": [
    {"x": 100, "y": 100},
    {"x": 200, "y": 100},
    {"x": 200, "y": 200},
    {"x": 300, "y": 200}
  ]
}
```

**Calculations:**
- Pixel length: Sum of all segment lengths
- Length (feet): `total_pixel_length / pixels_per_foot`
- Segment lengths: Individual segment distances

**Use Cases:**
- Irregular linear paths
- Curved edges (approximated)
- Multi-segment footings

**Example:**
```python
calculator = MeasurementCalculator(pixels_per_foot=10)
result = calculator.calculate_polyline(
    points=[
        {"x": 0, "y": 0},
        {"x": 100, "y": 0},
        {"x": 100, "y": 100}
    ]
)
# result = {
#   "pixel_length": 200.0,
#   "length_feet": 20.0,
#   "segments": [100.0, 100.0]
# }
```

---

### Polygon

Closed shape for area measurements.

**Visual Representation:**
```
        Point 1 ●──────────● Point 2
                 │          │
                 │   Area   │
                 │          │
        Point 4 ●──────────● Point 3
        
    Closed shape: Last point connects to first
    Area calculated using shoelace formula
    Perimeter = sum of all edge lengths
```

**Geometry Data Structure:**
```json
{
  "points": [
    {"x": 100, "y": 100},
    {"x": 200, "y": 100},
    {"x": 200, "y": 200},
    {"x": 100, "y": 200}
  ]
}
```

**Calculations:**
- Pixel area: Shoelace formula
- Area (SF): `pixel_area / (pixels_per_foot ** 2)`
- Perimeter (LF): Sum of edge lengths
- Volume (CY): `area_sf * (depth_inches / 12) / 27` (if depth provided)

**Use Cases:**
- Slabs
- Paving areas
- Irregular shapes
- Volume calculations with depth

**Example:**
```python
calculator = MeasurementCalculator(pixels_per_foot=10)
result = calculator.calculate_polygon(
    points=[
        {"x": 0, "y": 0},
        {"x": 100, "y": 0},
        {"x": 100, "y": 100},
        {"x": 0, "y": 100}
    ],
    depth_inches=4
)
# result = {
#   "area_sf": 100.0,
#   "perimeter_lf": 40.0,
#   "volume_cy": 1.23
# }
```

---

### Rectangle

Axis-aligned rectangular area.

**Visual Representation:**
```
        (x, y) ●───────────────┐
                │               │
                │     Area      │ height
                │               │
                └───────────────┘
                    width
        
    Area = width × height
    Perimeter = 2 × (width + height)
```

**Geometry Data Structure:**
```json
{
  "x": 100,
  "y": 100,
  "width": 200,
  "height": 150,
  "rotation": 0  // Optional
}
```

**Calculations:**
- Pixel area: `width * height`
- Area (SF): `pixel_area / (pixels_per_foot ** 2)`
- Perimeter (LF): `2 * (width + height) / pixels_per_foot`
- Volume (CY): `area_sf * (depth_inches / 12) / 27` (if depth provided)

**Use Cases:**
- Rectangular slabs
- Paving areas
- Foundation pads

**Example:**
```python
calculator = MeasurementCalculator(pixels_per_foot=10)
result = calculator.calculate_rectangle(
    x=0, y=0, width=100, height=100, depth_inches=6
)
# result = {
#   "area_sf": 100.0,
#   "perimeter_lf": 40.0,
#   "volume_cy": 1.85
# }
```

---

### Circle

Radial shape for area measurements.

**Visual Representation:**
```
                ╱     ╲
              ╱         ╲
             │    ●      │ radius
             │  center   │
              ╲         ╱
                ╲_____╱
                
    Area = π × radius²
    Circumference = 2 × π × radius
    Diameter = 2 × radius
```

**Geometry Data Structure:**
```json
{
  "center": {"x": 150, "y": 150},
  "radius": 50
}
```

**Calculations:**
- Pixel area: `π * radius²`
- Area (SF): `pixel_area / (pixels_per_foot ** 2)`
- Circumference (LF): `2 * π * radius / pixels_per_foot`
- Diameter (feet): `2 * radius / pixels_per_foot`
- Volume (CY): `area_sf * (depth_inches / 12) / 27` (if depth provided)

**Use Cases:**
- Circular slabs
- Column pads
- Round foundations

**Example:**
```python
calculator = MeasurementCalculator(pixels_per_foot=10)
result = calculator.calculate_circle(
    center={"x": 100, "y": 100},
    radius=50,
    depth_inches=4
)
# result = {
#   "area_sf": 78.54,
#   "circumference_lf": 31.42,
#   "diameter_feet": 10.0,
#   "volume_cy": 0.97
# }
```

---

### Point

Single location marker for counting.

**Visual Representation:**
```
        ×
        ● (x, y)
        
    Count = 1 (always)
    Used for: Piers, columns, anchors, etc.
```

**Geometry Data Structure:**
```json
{
  "x": 150,
  "y": 150
}
```

**Calculations:**
- Count: Always 1
- Quantity: 1 EA (each)

**Use Cases:**
- Piers
- Columns
- Anchors
- Count-based items

**Example:**
```python
calculator = MeasurementCalculator(pixels_per_foot=10)
result = calculator.calculate_count(
    point={"x": 100, "y": 100}
)
# result = {"count": 1}
```

---

## Measurement Types

### Linear (LF)

Measures length in linear feet.

**Supported Geometries:**
- Line
- Polyline

**Example Condition:**
```json
{
  "name": "Strip Footing",
  "measurement_type": "linear",
  "unit": "LF"
}
```

**Calculation:**
- Quantity = `length_feet` from geometry calculation

---

### Area (SF)

Measures area in square feet.

**Supported Geometries:**
- Polygon
- Rectangle
- Circle

**Example Condition:**
```json
{
  "name": "4\" Concrete Slab",
  "measurement_type": "area",
  "unit": "SF"
}
```

**Calculation:**
- Quantity = `area_sf` from geometry calculation

---

### Volume (CY)

Measures volume in cubic yards (requires depth).

**Supported Geometries:**
- Polygon (with depth)
- Rectangle (with depth)
- Circle (with depth)

**Example Condition:**
```json
{
  "name": "4\" Concrete Slab",
  "measurement_type": "volume",
  "unit": "CY",
  "depth": 4  // inches
}
```

**Calculation:**
- Quantity = `volume_cy` from geometry calculation
- Uses condition's `depth` field (in inches)

---

### Count (EA)

Measures quantity as count (each).

**Supported Geometries:**
- Point

**Example Condition:**
```json
{
  "name": "Concrete Column",
  "measurement_type": "count",
  "unit": "EA"
}
```

**Calculation:**
- Quantity = 1 per point

---

## Usage Examples

### Example 1: Create a Linear Measurement

**Step 1: Create Condition**
```bash
POST /api/v1/projects/{project_id}/conditions
{
  "name": "Strip Footing",
  "measurement_type": "linear",
  "unit": "LF",
  "color": "#EF4444"
}
```

**Step 2: Create Measurement**
```bash
POST /api/v1/conditions/{condition_id}/measurements
{
  "page_id": "page-uuid",
  "geometry_type": "line",
  "geometry_data": {
    "start": {"x": 100, "y": 100},
    "end": {"x": 500, "y": 100}
  }
}
```

**Result:**
- If page scale is 10 px/ft, measurement calculates to 40 LF
- Condition `total_quantity` increases by 40
- Condition `measurement_count` increases by 1

---

### Example 2: Create a Volume Measurement

**Step 1: Create Condition with Depth**
```bash
POST /api/v1/projects/{project_id}/conditions
{
  "name": "4\" Concrete Slab",
  "measurement_type": "volume",
  "unit": "CY",
  "depth": 4,
  "color": "#22C55E"
}
```

**Step 2: Create Polygon Measurement**
```bash
POST /api/v1/conditions/{condition_id}/measurements
{
  "page_id": "page-uuid",
  "geometry_type": "polygon",
  "geometry_data": {
    "points": [
      {"x": 100, "y": 100},
      {"x": 200, "y": 100},
      {"x": 200, "y": 200},
      {"x": 100, "y": 200}
    ]
  }
}
```

**Result:**
- If page scale is 10 px/ft:
  - Area = 100 SF (10ft × 10ft)
  - Volume = 1.23 CY (100 SF × 4/12 ft ÷ 27)
- Condition `total_quantity` increases by 1.23 CY

---

### Example 3: Recalculate After Scale Change

**Scenario:** Page scale changed from 10 px/ft to 20 px/ft

**Step 1: Recalibrate Page Scale**
```bash
PUT /api/v1/pages/{page_id}/scale
{
  "scale_value": 20,
  "scale_unit": "foot"
}
```

**Step 2: Recalculate All Measurements**
```bash
POST /api/v1/pages/{page_id}/recalculate-all
```

**Result:**
- All measurements recalculate with new scale
- Quantities adjust (e.g., 40 LF becomes 20 LF)
- Condition totals automatically update

---

## Implementation Details

### Measurement Engine Service

The `MeasurementEngine` class handles all measurement operations:

```python
from app.services.measurement_engine import get_measurement_engine

engine = get_measurement_engine()

# Create measurement
measurement = await engine.create_measurement(
    session=db,
    condition_id=condition_id,
    page_id=page_id,
    geometry_type="polygon",
    geometry_data={"points": [...]}
)

# Update measurement
measurement = await engine.update_measurement(
    session=db,
    measurement_id=measurement_id,
    geometry_data={"points": [...]}
)

# Delete measurement
await engine.delete_measurement(db, measurement_id)

# Recalculate measurement
measurement = await engine.recalculate_measurement(db, measurement_id)
```

### Automatic Condition Total Updates

When measurements are created, updated, or deleted, condition totals are automatically recalculated:

```python
# After measurement create/update/delete
condition.total_quantity = sum(m.quantity for m in condition.measurements)
condition.measurement_count = len(condition.measurements)
```

### Scale Dependency

All measurements require:
1. Page must have `scale_calibrated = true`
2. Page must have `scale_value` set (pixels per foot)
3. Measurements store pixel values in `geometry_data`
4. Real-world quantities calculated using `scale_value`

---

## Error Handling

### Common Errors

**Page Not Calibrated**
```json
{
  "detail": "Page scale not calibrated"
}
```
**Solution:** Calibrate the page scale first using Phase 2B scale detection endpoints.

**Invalid Geometry Type**
```json
{
  "detail": "Invalid geometry type: invalid_type"
}
```
**Solution:** Use one of: `line`, `polyline`, `polygon`, `rectangle`, `circle`, `point`

**Condition Not Found**
```json
{
  "detail": "Condition not found: {condition_id}"
}
```
**Solution:** Verify the condition ID exists and belongs to the project.

**Measurement Type Mismatch**
- Linear measurements require `line` or `polyline` geometry
- Area measurements require `polygon`, `rectangle`, or `circle` geometry
- Volume measurements require area geometries with depth
- Count measurements require `point` geometry

---

## Testing

### Manual Testing Checklist

- [ ] Create linear measurement (line geometry)
- [ ] Create area measurement (polygon geometry)
- [ ] Create volume measurement (rectangle with depth)
- [ ] Create count measurement (point geometry)
- [ ] Update measurement geometry
- [ ] Delete measurement
- [ ] Verify condition totals update correctly
- [ ] Recalculate after scale change
- [ ] List measurements by condition
- [ ] List measurements by page

### API Testing

```bash
# Create condition
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/conditions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Slab",
    "measurement_type": "area",
    "unit": "SF"
  }'

# Create measurement
curl -X POST http://localhost:8000/api/v1/conditions/{condition_id}/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "page_id": "{page_id}",
    "geometry_type": "polygon",
    "geometry_data": {
      "points": [
        {"x": 100, "y": 100},
        {"x": 200, "y": 100},
        {"x": 200, "y": 200},
        {"x": 100, "y": 200}
      ]
    }
  }'

# List measurements
curl http://localhost:8000/api/v1/conditions/{condition_id}/measurements
```

---

## Related Documentation

- [Phase 3A Specification](../../plans/06-MEASUREMENT-ENGINE.md)
- [API Reference](../api/API_REFERENCE.md) - Complete API endpoint documentation
- [Database Schema](../database/DATABASE_SCHEMA.md) - Database structure
- [Phase 3A Complete](./PHASE_3A_COMPLETE.md) - Implementation completion report
- [Phase 2B Scale Detection](./PHASE_2B_COMPLETE.md) - Prerequisite phase

---

**Last Updated:** January 22, 2026  
**Status:** ✅ Complete and Production Ready
