"""Geometry adjustment service for quick-edit operations.

Provides nudge, snap-to-grid, extend, trim, offset, split, and join
operations on measurement geometry. Each operation takes raw geometry_data
(the JSONB stored on Measurement) and returns updated geometry_data.
"""

import math
import uuid
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.condition import Condition
from app.models.measurement import Measurement
from app.models.page import Page
from app.utils.geometry import MeasurementCalculator

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Pure geometry helpers (operate on dicts matching geometry_data shapes)
# ---------------------------------------------------------------------------

def _translate_point(pt: dict[str, float], dx: float, dy: float) -> dict[str, float]:
    """Translate a {x, y} point."""
    return {"x": pt["x"] + dx, "y": pt["y"] + dy}


def _snap_point(pt: dict[str, float], grid_size: float) -> dict[str, float]:
    """Snap a point to the nearest grid intersection."""
    return {
        "x": round(pt["x"] / grid_size) * grid_size,
        "y": round(pt["y"] / grid_size) * grid_size,
    }


def _distance(p1: dict[str, float], p2: dict[str, float]) -> float:
    return math.sqrt((p2["x"] - p1["x"]) ** 2 + (p2["y"] - p1["y"]) ** 2)


def _project_point_on_segment(
    pt: dict[str, float],
    seg_start: dict[str, float],
    seg_end: dict[str, float],
) -> dict[str, float]:
    """Project a point onto a line segment, clamped to [0, 1]."""
    dx = seg_end["x"] - seg_start["x"]
    dy = seg_end["y"] - seg_start["y"]
    len_sq = dx * dx + dy * dy
    if len_sq < 1e-12:
        return dict(seg_start)
    t = max(0.0, min(1.0, ((pt["x"] - seg_start["x"]) * dx + (pt["y"] - seg_start["y"]) * dy) / len_sq))
    return {"x": seg_start["x"] + t * dx, "y": seg_start["y"] + t * dy}


def _line_line_intersection(
    a1: dict[str, float],
    a2: dict[str, float],
    b1: dict[str, float],
    b2: dict[str, float],
    *,
    clamp_segments: bool = True,
) -> dict[str, float] | None:
    """Find the intersection of two line segments (or infinite lines if not clamped)."""
    x1, y1 = a1["x"], a1["y"]
    x2, y2 = a2["x"], a2["y"]
    x3, y3 = b1["x"], b1["y"]
    x4, y4 = b2["x"], b2["y"]

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if clamp_segments and not (0 <= t <= 1 and 0 <= u <= 1):
        return None

    return {"x": x1 + t * (x2 - x1), "y": y1 + t * (y2 - y1)}


def _perpendicular(v: dict[str, float]) -> dict[str, float]:
    """Return the left-perpendicular unit normal."""
    length = math.sqrt(v["x"] ** 2 + v["y"] ** 2)
    if length < 1e-12:
        return {"x": 0.0, "y": 0.0}
    return {"x": -v["y"] / length, "y": v["x"] / length}


# ---------------------------------------------------------------------------
# Nudge
# ---------------------------------------------------------------------------

def nudge_geometry(
    geometry_type: str,
    geometry_data: dict[str, Any],
    direction: str,
    distance_px: float,
) -> dict[str, Any]:
    """Move an entire measurement by *distance_px* in *direction*.

    direction: "up" | "down" | "left" | "right"
    """
    dx = distance_px if direction == "right" else (-distance_px if direction == "left" else 0.0)
    dy = distance_px if direction == "down" else (-distance_px if direction == "up" else 0.0)

    if geometry_type == "line":
        return {
            **geometry_data,
            "start": _translate_point(geometry_data["start"], dx, dy),
            "end": _translate_point(geometry_data["end"], dx, dy),
        }
    elif geometry_type in ("polyline", "polygon"):
        return {
            **geometry_data,
            "points": [_translate_point(p, dx, dy) for p in geometry_data["points"]],
        }
    elif geometry_type == "rectangle":
        return {
            **geometry_data,
            "x": geometry_data["x"] + dx,
            "y": geometry_data["y"] + dy,
        }
    elif geometry_type == "circle":
        return {
            **geometry_data,
            "center": _translate_point(geometry_data["center"], dx, dy),
        }
    elif geometry_type == "point":
        return {
            **geometry_data,
            "x": geometry_data["x"] + dx,
            "y": geometry_data["y"] + dy,
        }
    else:
        return geometry_data


# ---------------------------------------------------------------------------
# Snap to grid
# ---------------------------------------------------------------------------

def snap_geometry_to_grid(
    geometry_type: str,
    geometry_data: dict[str, Any],
    grid_size_px: float,
) -> dict[str, Any]:
    """Snap all vertices / anchor points of a measurement to a grid."""
    if grid_size_px <= 0:
        return geometry_data

    if geometry_type == "line":
        return {
            **geometry_data,
            "start": _snap_point(geometry_data["start"], grid_size_px),
            "end": _snap_point(geometry_data["end"], grid_size_px),
        }
    elif geometry_type in ("polyline", "polygon"):
        return {
            **geometry_data,
            "points": [_snap_point(p, grid_size_px) for p in geometry_data["points"]],
        }
    elif geometry_type == "rectangle":
        snapped = _snap_point({"x": geometry_data["x"], "y": geometry_data["y"]}, grid_size_px)
        return {
            **geometry_data,
            "x": snapped["x"],
            "y": snapped["y"],
            "width": round(geometry_data["width"] / grid_size_px) * grid_size_px,
            "height": round(geometry_data["height"] / grid_size_px) * grid_size_px,
        }
    elif geometry_type == "circle":
        return {
            **geometry_data,
            "center": _snap_point(geometry_data["center"], grid_size_px),
            "radius": round(geometry_data["radius"] / grid_size_px) * grid_size_px,
        }
    elif geometry_type == "point":
        snapped = _snap_point({"x": geometry_data["x"], "y": geometry_data["y"]}, grid_size_px)
        return {**geometry_data, **snapped}
    else:
        return geometry_data


# ---------------------------------------------------------------------------
# Extend  (lines / polylines only)
# ---------------------------------------------------------------------------

def extend_geometry(
    geometry_type: str,
    geometry_data: dict[str, Any],
    endpoint: str,
    distance_px: float,
) -> dict[str, Any]:
    """Extend a line or the last segment of a polyline by *distance_px*.

    endpoint: "start" | "end" | "both"
    """
    if geometry_type == "line":
        start = geometry_data["start"]
        end = geometry_data["end"]
        dx = end["x"] - start["x"]
        dy = end["y"] - start["y"]
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1e-12:
            return geometry_data
        ux, uy = dx / length, dy / length

        new_start = dict(start)
        new_end = dict(end)

        if endpoint in ("start", "both"):
            new_start = {"x": start["x"] - ux * distance_px, "y": start["y"] - uy * distance_px}
        if endpoint in ("end", "both"):
            new_end = {"x": end["x"] + ux * distance_px, "y": end["y"] + uy * distance_px}

        return {**geometry_data, "start": new_start, "end": new_end}

    elif geometry_type == "polyline":
        points = list(geometry_data["points"])
        if len(points) < 2:
            return geometry_data

        if endpoint in ("end", "both"):
            p1 = points[-2]
            p2 = points[-1]
            dx = p2["x"] - p1["x"]
            dy = p2["y"] - p1["y"]
            length = math.sqrt(dx * dx + dy * dy)
            if length > 1e-12:
                ux, uy = dx / length, dy / length
                points[-1] = {"x": p2["x"] + ux * distance_px, "y": p2["y"] + uy * distance_px}

        if endpoint in ("start", "both"):
            p1 = points[1]
            p2 = points[0]
            dx = p2["x"] - p1["x"]
            dy = p2["y"] - p1["y"]
            length = math.sqrt(dx * dx + dy * dy)
            if length > 1e-12:
                ux, uy = dx / length, dy / length
                points[0] = {"x": p2["x"] + ux * distance_px, "y": p2["y"] + uy * distance_px}

        return {**geometry_data, "points": points}
    else:
        return geometry_data


# ---------------------------------------------------------------------------
# Trim  (lines / polylines only)
# ---------------------------------------------------------------------------

def trim_geometry(
    geometry_type: str,
    geometry_data: dict[str, Any],
    trim_point: dict[str, float],
) -> dict[str, Any]:
    """Trim a line at the projected trim_point, keeping the longer side."""
    if geometry_type == "line":
        start = geometry_data["start"]
        end = geometry_data["end"]
        projected = _project_point_on_segment(trim_point, start, end)

        dist_to_start = _distance(projected, start)
        dist_to_end = _distance(projected, end)

        # Keep the longer side
        if dist_to_start >= dist_to_end:
            return {**geometry_data, "end": projected}
        else:
            return {**geometry_data, "start": projected}

    elif geometry_type == "polyline":
        points = geometry_data["points"]
        if len(points) < 2:
            return geometry_data

        # Find which segment the trim_point is closest to
        best_seg = 0
        best_dist = float("inf")
        best_proj = points[0]

        for i in range(len(points) - 1):
            proj = _project_point_on_segment(trim_point, points[i], points[i + 1])
            d = _distance(trim_point, proj)
            if d < best_dist:
                best_dist = d
                best_seg = i
                best_proj = proj

        # Decide which side to keep (keep longer portion)
        # Segments before the split vs after
        left_points = points[: best_seg + 1] + [best_proj]
        right_points = [best_proj] + points[best_seg + 1 :]

        if len(left_points) >= len(right_points):
            return {**geometry_data, "points": left_points}
        else:
            return {**geometry_data, "points": right_points}
    else:
        return geometry_data


# ---------------------------------------------------------------------------
# Offset  (polygons / rectangles only — creates a new geometry)
# ---------------------------------------------------------------------------

def offset_geometry(
    geometry_type: str,
    geometry_data: dict[str, Any],
    distance_px: float,
    corner_type: str = "miter",
) -> dict[str, Any]:
    """Create a parallel offset of a polygon or rectangle.

    distance > 0 = outward, < 0 = inward.
    corner_type: "miter" | "bevel"
    """
    if geometry_type == "rectangle":
        return {
            **geometry_data,
            "x": geometry_data["x"] - distance_px,
            "y": geometry_data["y"] - distance_px,
            "width": max(1, geometry_data["width"] + 2 * distance_px),
            "height": max(1, geometry_data["height"] + 2 * distance_px),
        }

    if geometry_type != "polygon":
        return geometry_data

    points = geometry_data["points"]
    n = len(points)
    if n < 3:
        return geometry_data

    new_points: list[dict[str, float]] = []

    for i in range(n):
        prev_pt = points[(i - 1 + n) % n]
        curr_pt = points[i]
        next_pt = points[(i + 1) % n]

        # Edge vectors
        e1 = {"x": curr_pt["x"] - prev_pt["x"], "y": curr_pt["y"] - prev_pt["y"]}
        e2 = {"x": next_pt["x"] - curr_pt["x"], "y": next_pt["y"] - curr_pt["y"]}

        n1 = _perpendicular(e1)
        n2 = _perpendicular(e2)

        # Average normal
        avg_x = n1["x"] + n2["x"]
        avg_y = n1["y"] + n2["y"]
        avg_len = math.sqrt(avg_x ** 2 + avg_y ** 2)

        if avg_len < 1e-12:
            new_points.append(dict(curr_pt))
            continue

        avg_x /= avg_len
        avg_y /= avg_len

        # Miter length
        dot = n1["x"] * n2["x"] + n1["y"] * n2["y"]
        dot = max(-1.0, min(1.0, dot))
        angle = math.acos(dot)
        cos_half = math.cos(angle / 2) if angle > 1e-6 else 1.0
        miter_len = distance_px / cos_half if cos_half > 1e-6 else distance_px

        if corner_type == "miter" and abs(miter_len) < abs(distance_px) * 4:
            new_points.append({
                "x": curr_pt["x"] + avg_x * miter_len,
                "y": curr_pt["y"] + avg_y * miter_len,
            })
        else:
            # Bevel — two points
            new_points.append({
                "x": curr_pt["x"] + n1["x"] * distance_px,
                "y": curr_pt["y"] + n1["y"] * distance_px,
            })
            new_points.append({
                "x": curr_pt["x"] + n2["x"] * distance_px,
                "y": curr_pt["y"] + n2["y"] * distance_px,
            })

    return {**geometry_data, "points": new_points}


# ---------------------------------------------------------------------------
# Split  (lines / polylines → two measurements)
# ---------------------------------------------------------------------------

def split_geometry(
    geometry_type: str,
    geometry_data: dict[str, Any],
    split_point: dict[str, float],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Split a line or polyline at *split_point* into two geometries.

    Returns a tuple of two geometry_data dicts, or None if splitting
    is not applicable.
    """
    if geometry_type == "line":
        start = geometry_data["start"]
        end = geometry_data["end"]
        projected = _project_point_on_segment(split_point, start, end)

        # Don't split if too close to an endpoint
        if _distance(projected, start) < 1.0 or _distance(projected, end) < 1.0:
            return None

        part_a = {**geometry_data, "start": dict(start), "end": projected}
        part_b = {**geometry_data, "start": projected, "end": dict(end)}
        return (part_a, part_b)

    elif geometry_type == "polyline":
        points = geometry_data["points"]
        if len(points) < 2:
            return None

        # Find nearest segment
        best_seg = 0
        best_dist = float("inf")
        best_proj = points[0]

        for i in range(len(points) - 1):
            proj = _project_point_on_segment(split_point, points[i], points[i + 1])
            d = _distance(split_point, proj)
            if d < best_dist:
                best_dist = d
                best_seg = i
                best_proj = proj

        left = points[: best_seg + 1] + [best_proj]
        right = [best_proj] + points[best_seg + 1 :]

        if len(left) < 2 or len(right) < 2:
            return None

        part_a = {**geometry_data, "points": left}
        part_b = {**geometry_data, "points": right}
        return (part_a, part_b)
    else:
        return None


# ---------------------------------------------------------------------------
# Join  (lines → single line or polyline)
# ---------------------------------------------------------------------------

def join_geometries(
    type_a: str,
    data_a: dict[str, Any],
    type_b: str,
    data_b: dict[str, Any],
    tolerance_px: float = 15.0,
) -> tuple[str, dict[str, Any]] | None:
    """Join two line/polyline geometries if endpoints are within tolerance.

    Returns (new_geometry_type, new_geometry_data) or None.
    """
    # Collect ordered point lists from each geometry
    def _to_points(gtype: str, gdata: dict) -> list[dict[str, float]]:
        if gtype == "line":
            return [gdata["start"], gdata["end"]]
        elif gtype == "polyline":
            return list(gdata["points"])
        return []

    pts_a = _to_points(type_a, data_a)
    pts_b = _to_points(type_b, data_b)

    if len(pts_a) < 2 or len(pts_b) < 2:
        return None

    # Check which endpoints are close
    connections: list[tuple[str, list[dict[str, float]]]] = []

    if _distance(pts_a[-1], pts_b[0]) < tolerance_px:
        connections.append(("a_end_b_start", pts_a + pts_b[1:]))
    if _distance(pts_a[-1], pts_b[-1]) < tolerance_px:
        connections.append(("a_end_b_end", pts_a + list(reversed(pts_b))[1:]))
    if _distance(pts_a[0], pts_b[-1]) < tolerance_px:
        connections.append(("a_start_b_end", pts_b + pts_a[1:]))
    if _distance(pts_a[0], pts_b[0]) < tolerance_px:
        connections.append(("a_start_b_start", list(reversed(pts_b)) + pts_a[1:]))

    if not connections:
        return None

    # Pick the first valid connection
    joined_points = connections[0][1]

    if len(joined_points) == 2:
        return ("line", {"start": joined_points[0], "end": joined_points[1]})
    else:
        return ("polyline", {"points": joined_points})


# ---------------------------------------------------------------------------
# High-level async service that wraps DB operations
# ---------------------------------------------------------------------------

class GeometryAdjusterService:
    """Async service for adjusting measurement geometry with DB persistence."""

    async def adjust_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        action: str,
        params: dict[str, Any],
    ) -> Measurement:
        """Apply a geometry adjustment to a measurement.

        Args:
            session: DB session
            measurement_id: Target measurement
            action: One of nudge, snap_to_grid, extend, trim, offset, split, join
            params: Action-specific parameters

        Returns:
            Updated Measurement (or the first part for split)
        """
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")

        gtype = measurement.geometry_type
        gdata = dict(measurement.geometry_data)
        new_gdata: dict[str, Any] | None = None
        extra_measurement: Measurement | None = None

        if action == "nudge":
            new_gdata = nudge_geometry(
                gtype,
                gdata,
                direction=params["direction"],
                distance_px=params.get("distance_px", 1.0),
            )

        elif action == "snap_to_grid":
            new_gdata = snap_geometry_to_grid(
                gtype,
                gdata,
                grid_size_px=params.get("grid_size_px", 10.0),
            )

        elif action == "extend":
            new_gdata = extend_geometry(
                gtype,
                gdata,
                endpoint=params.get("endpoint", "end"),
                distance_px=params.get("distance_px", 20.0),
            )

        elif action == "trim":
            if "trim_point" not in params:
                raise ValueError("trim requires 'trim_point' param with {x, y}")
            new_gdata = trim_geometry(gtype, gdata, trim_point=params["trim_point"])

        elif action == "offset":
            new_gdata = offset_geometry(
                gtype,
                gdata,
                distance_px=params.get("distance_px", 10.0),
                corner_type=params.get("corner_type", "miter"),
            )

        elif action == "split":
            if "split_point" not in params:
                raise ValueError("split requires 'split_point' param with {x, y}")
            result = split_geometry(gtype, gdata, split_point=params["split_point"])
            if result is None:
                raise ValueError("Cannot split this geometry at the given point")

            part_a, part_b = result
            new_gdata = part_a

            # Create second measurement
            extra_measurement = Measurement(
                condition_id=measurement.condition_id,
                page_id=measurement.page_id,
                geometry_type=gtype,
                geometry_data=part_b,
                quantity=0.0,  # will be recalculated
                unit=measurement.unit,
                is_modified=True,
                notes=f"Split from {measurement_id}",
            )
            session.add(extra_measurement)

        elif action == "join":
            other_id = params.get("other_measurement_id")
            if not other_id:
                raise ValueError("join requires 'other_measurement_id'")
            other = await session.get(Measurement, uuid.UUID(str(other_id)))
            if not other:
                raise ValueError(f"Other measurement not found: {other_id}")

            result = join_geometries(
                gtype,
                gdata,
                other.geometry_type,
                dict(other.geometry_data),
                tolerance_px=params.get("tolerance_px", 15.0),
            )
            if result is None:
                raise ValueError("Cannot join: endpoints are not within tolerance")

            new_type, new_data = result
            measurement.geometry_type = new_type
            new_gdata = new_data

            # Delete the other measurement
            await session.delete(other)
        else:
            raise ValueError(f"Unknown adjust action: {action}")

        if new_gdata is None:
            raise ValueError("Adjustment produced no result")

        # Store original geometry for undo reference (first time only)
        if not measurement.original_geometry:
            measurement.original_geometry = gdata
            measurement.original_quantity = measurement.quantity

        measurement.geometry_data = new_gdata
        measurement.is_modified = True

        # Recalculate quantities
        await self._recalculate(session, measurement)
        if extra_measurement:
            await self._recalculate(session, extra_measurement)

        # Update condition totals
        condition = await session.get(Condition, measurement.condition_id)
        if condition:
            await self._update_condition_totals(session, condition)

        await session.commit()
        await session.refresh(measurement)

        return measurement

    async def _recalculate(self, session: AsyncSession, measurement: Measurement) -> None:
        """Recalculate quantity for a measurement after geometry change."""
        page = await session.get(Page, measurement.page_id)
        condition = await session.get(Condition, measurement.condition_id)

        if not page or not page.scale_value or not condition:
            return

        calculator = MeasurementCalculator(page.scale_value)
        from app.services.measurement_engine import get_measurement_engine
        engine = get_measurement_engine()

        calculation = engine._calculate_geometry(
            calculator,
            measurement.geometry_type,
            measurement.geometry_data,
            condition.depth,
        )
        measurement.quantity = engine._extract_quantity(calculation, condition.measurement_type)
        measurement.pixel_length = calculation.get("pixel_length")
        measurement.pixel_area = calculation.get("pixel_area")
        measurement.extra_metadata = {"calculation": calculation}

    async def _update_condition_totals(
        self,
        session: AsyncSession,
        condition: Condition,
    ) -> None:
        """Update condition's denormalized totals."""
        from sqlalchemy import func
        result = await session.execute(
            select(
                func.sum(Measurement.quantity),
                func.count(Measurement.id),
            ).where(
                Measurement.condition_id == condition.id,
                Measurement.is_rejected == False,  # noqa: E712
            )
        )
        row = result.one()
        condition.total_quantity = row[0] or 0.0
        condition.measurement_count = row[1] or 0


# Singleton
_service: GeometryAdjusterService | None = None


def get_geometry_adjuster() -> GeometryAdjusterService:
    """Get the geometry adjuster singleton."""
    global _service
    if _service is None:
        _service = GeometryAdjusterService()
    return _service
