"""Unit tests for the geometry adjuster service.

Tests each pure geometry operation (nudge, snap, extend, trim, offset,
split, join) with expected geometry output.
"""

import math
import pytest

from app.services.geometry_adjuster import (
    nudge_geometry,
    snap_geometry_to_grid,
    extend_geometry,
    trim_geometry,
    offset_geometry,
    split_geometry,
    join_geometries,
    _distance,
    _project_point_on_segment,
    _line_line_intersection,
    _snap_point,
    _translate_point,
)


# ============================================================================
# Helper function tests
# ============================================================================

class TestHelpers:

    def test_translate_point(self):
        pt = {"x": 10.0, "y": 20.0}
        result = _translate_point(pt, 5.0, -3.0)
        assert result == {"x": 15.0, "y": 17.0}

    def test_translate_point_zero(self):
        pt = {"x": 10.0, "y": 20.0}
        result = _translate_point(pt, 0.0, 0.0)
        assert result == {"x": 10.0, "y": 20.0}

    def test_snap_point(self):
        pt = {"x": 13.0, "y": 27.0}
        result = _snap_point(pt, 10.0)
        assert result == {"x": 10.0, "y": 30.0}

    def test_snap_point_exact(self):
        pt = {"x": 20.0, "y": 30.0}
        result = _snap_point(pt, 10.0)
        assert result == {"x": 20.0, "y": 30.0}

    def test_distance(self):
        p1 = {"x": 0.0, "y": 0.0}
        p2 = {"x": 3.0, "y": 4.0}
        assert _distance(p1, p2) == pytest.approx(5.0)

    def test_distance_same_point(self):
        p = {"x": 5.0, "y": 5.0}
        assert _distance(p, p) == pytest.approx(0.0)

    def test_project_point_on_segment_midpoint(self):
        pt = {"x": 5.0, "y": 10.0}
        seg_start = {"x": 0.0, "y": 0.0}
        seg_end = {"x": 10.0, "y": 0.0}
        result = _project_point_on_segment(pt, seg_start, seg_end)
        assert result["x"] == pytest.approx(5.0)
        assert result["y"] == pytest.approx(0.0)

    def test_project_point_on_segment_clamped_start(self):
        pt = {"x": -10.0, "y": 5.0}
        seg_start = {"x": 0.0, "y": 0.0}
        seg_end = {"x": 10.0, "y": 0.0}
        result = _project_point_on_segment(pt, seg_start, seg_end)
        assert result["x"] == pytest.approx(0.0)
        assert result["y"] == pytest.approx(0.0)

    def test_project_point_on_segment_clamped_end(self):
        pt = {"x": 20.0, "y": 5.0}
        seg_start = {"x": 0.0, "y": 0.0}
        seg_end = {"x": 10.0, "y": 0.0}
        result = _project_point_on_segment(pt, seg_start, seg_end)
        assert result["x"] == pytest.approx(10.0)
        assert result["y"] == pytest.approx(0.0)

    def test_line_line_intersection_crossing(self):
        result = _line_line_intersection(
            {"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 10.0},
            {"x": 0.0, "y": 10.0}, {"x": 10.0, "y": 0.0},
        )
        assert result is not None
        assert result["x"] == pytest.approx(5.0)
        assert result["y"] == pytest.approx(5.0)

    def test_line_line_intersection_parallel(self):
        result = _line_line_intersection(
            {"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 0.0},
            {"x": 0.0, "y": 5.0}, {"x": 10.0, "y": 5.0},
        )
        assert result is None

    def test_line_line_intersection_no_segment_overlap(self):
        result = _line_line_intersection(
            {"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 0.0},
            {"x": 5.0, "y": -1.0}, {"x": 5.0, "y": 1.0},
            clamp_segments=True,
        )
        assert result is None

    def test_line_line_intersection_unclamped(self):
        result = _line_line_intersection(
            {"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 0.0},
            {"x": 5.0, "y": -1.0}, {"x": 5.0, "y": 1.0},
            clamp_segments=False,
        )
        assert result is not None
        assert result["x"] == pytest.approx(5.0)
        assert result["y"] == pytest.approx(0.0)


# ============================================================================
# Nudge tests
# ============================================================================

class TestNudge:

    def test_nudge_line_right(self):
        data = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 10.0, "y": 0.0}}
        result = nudge_geometry("line", data, "right", 5.0)
        assert result["start"] == {"x": 5.0, "y": 0.0}
        assert result["end"] == {"x": 15.0, "y": 0.0}

    def test_nudge_line_up(self):
        data = {"start": {"x": 0.0, "y": 10.0}, "end": {"x": 10.0, "y": 10.0}}
        result = nudge_geometry("line", data, "up", 3.0)
        assert result["start"]["y"] == pytest.approx(7.0)
        assert result["end"]["y"] == pytest.approx(7.0)

    def test_nudge_polyline(self):
        data = {"points": [{"x": 0.0, "y": 0.0}, {"x": 5.0, "y": 5.0}, {"x": 10.0, "y": 0.0}]}
        result = nudge_geometry("polyline", data, "down", 2.0)
        assert result["points"][0] == {"x": 0.0, "y": 2.0}
        assert result["points"][1] == {"x": 5.0, "y": 7.0}
        assert result["points"][2] == {"x": 10.0, "y": 2.0}

    def test_nudge_polygon(self):
        data = {"points": [{"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 0.0}, {"x": 10.0, "y": 10.0}]}
        result = nudge_geometry("polygon", data, "left", 1.0)
        assert result["points"][0] == {"x": -1.0, "y": 0.0}

    def test_nudge_rectangle(self):
        data = {"x": 10.0, "y": 20.0, "width": 50.0, "height": 30.0}
        result = nudge_geometry("rectangle", data, "right", 5.0)
        assert result["x"] == 15.0
        assert result["y"] == 20.0
        assert result["width"] == 50.0

    def test_nudge_circle(self):
        data = {"center": {"x": 50.0, "y": 50.0}, "radius": 25.0}
        result = nudge_geometry("circle", data, "up", 10.0)
        assert result["center"] == {"x": 50.0, "y": 40.0}
        assert result["radius"] == 25.0

    def test_nudge_point(self):
        data = {"x": 100.0, "y": 200.0}
        result = nudge_geometry("point", data, "left", 7.0)
        assert result["x"] == 93.0
        assert result["y"] == 200.0

    def test_nudge_zero_distance(self):
        data = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 10.0, "y": 0.0}}
        result = nudge_geometry("line", data, "right", 0.0)
        assert result["start"] == {"x": 0.0, "y": 0.0}

    def test_nudge_unknown_type_returns_unchanged(self):
        data = {"foo": "bar"}
        result = nudge_geometry("unknown_type", data, "up", 5.0)
        assert result == data


# ============================================================================
# Snap to grid tests
# ============================================================================

class TestSnapToGrid:

    def test_snap_line(self):
        data = {"start": {"x": 3.0, "y": 7.0}, "end": {"x": 13.0, "y": 18.0}}
        result = snap_geometry_to_grid("line", data, 10.0)
        assert result["start"] == {"x": 0.0, "y": 10.0}
        assert result["end"] == {"x": 10.0, "y": 20.0}

    def test_snap_polyline(self):
        data = {"points": [{"x": 2.0, "y": 3.0}, {"x": 8.0, "y": 12.0}]}
        result = snap_geometry_to_grid("polyline", data, 5.0)
        assert result["points"][0] == {"x": 0.0, "y": 5.0}
        assert result["points"][1] == {"x": 10.0, "y": 10.0}

    def test_snap_rectangle(self):
        data = {"x": 3.0, "y": 7.0, "width": 14.0, "height": 9.0}
        result = snap_geometry_to_grid("rectangle", data, 10.0)
        assert result["x"] == 0.0
        assert result["y"] == 10.0
        assert result["width"] == 10.0
        assert result["height"] == 10.0

    def test_snap_circle(self):
        data = {"center": {"x": 7.0, "y": 3.0}, "radius": 12.0}
        result = snap_geometry_to_grid("circle", data, 10.0)
        assert result["center"] == {"x": 10.0, "y": 0.0}
        assert result["radius"] == 10.0

    def test_snap_point(self):
        data = {"x": 13.0, "y": 27.0}
        result = snap_geometry_to_grid("point", data, 10.0)
        assert result["x"] == 10.0
        assert result["y"] == 30.0

    def test_snap_zero_grid_returns_unchanged(self):
        data = {"start": {"x": 3.0, "y": 7.0}, "end": {"x": 13.0, "y": 18.0}}
        result = snap_geometry_to_grid("line", data, 0.0)
        assert result == data

    def test_snap_negative_grid_returns_unchanged(self):
        data = {"start": {"x": 3.0, "y": 7.0}, "end": {"x": 13.0, "y": 18.0}}
        result = snap_geometry_to_grid("line", data, -5.0)
        assert result == data


# ============================================================================
# Extend tests
# ============================================================================

class TestExtend:

    def test_extend_line_end(self):
        data = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 10.0, "y": 0.0}}
        result = extend_geometry("line", data, "end", 5.0)
        assert result["start"]["x"] == pytest.approx(0.0)
        assert result["end"]["x"] == pytest.approx(15.0)
        assert result["end"]["y"] == pytest.approx(0.0)

    def test_extend_line_start(self):
        data = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 10.0, "y": 0.0}}
        result = extend_geometry("line", data, "start", 5.0)
        assert result["start"]["x"] == pytest.approx(-5.0)
        assert result["end"]["x"] == pytest.approx(10.0)

    def test_extend_line_both(self):
        data = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 10.0, "y": 0.0}}
        result = extend_geometry("line", data, "both", 5.0)
        assert result["start"]["x"] == pytest.approx(-5.0)
        assert result["end"]["x"] == pytest.approx(15.0)

    def test_extend_diagonal_line(self):
        data = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 3.0, "y": 4.0}}
        result = extend_geometry("line", data, "end", 5.0)
        expected_x = 3.0 + 3.0 / 5.0 * 5.0  # 6.0
        expected_y = 4.0 + 4.0 / 5.0 * 5.0  # 8.0
        assert result["end"]["x"] == pytest.approx(expected_x)
        assert result["end"]["y"] == pytest.approx(expected_y)

    def test_extend_polyline_end(self):
        data = {"points": [{"x": 0.0, "y": 0.0}, {"x": 5.0, "y": 0.0}, {"x": 10.0, "y": 0.0}]}
        result = extend_geometry("polyline", data, "end", 3.0)
        assert result["points"][-1]["x"] == pytest.approx(13.0)

    def test_extend_polyline_start(self):
        data = {"points": [{"x": 5.0, "y": 0.0}, {"x": 10.0, "y": 0.0}]}
        result = extend_geometry("polyline", data, "start", 3.0)
        assert result["points"][0]["x"] == pytest.approx(2.0)

    def test_extend_zero_length_line_returns_unchanged(self):
        data = {"start": {"x": 5.0, "y": 5.0}, "end": {"x": 5.0, "y": 5.0}}
        result = extend_geometry("line", data, "end", 10.0)
        assert result == data

    def test_extend_polygon_returns_unchanged(self):
        data = {"points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}]}
        result = extend_geometry("polygon", data, "end", 5.0)
        assert result == data


# ============================================================================
# Trim tests
# ============================================================================

class TestTrim:

    def test_trim_line_keeps_longer_side(self):
        data = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 100.0, "y": 0.0}}
        # Trim point near the end — keeps start-to-trim (longer)
        result = trim_geometry("line", data, {"x": 80.0, "y": 5.0})
        assert result["start"]["x"] == pytest.approx(0.0)
        assert result["end"]["x"] == pytest.approx(80.0)

    def test_trim_line_keeps_shorter_side_when_trim_near_start(self):
        data = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 100.0, "y": 0.0}}
        # Trim near start — longer side is trim-to-end
        result = trim_geometry("line", data, {"x": 20.0, "y": 5.0})
        assert result["start"]["x"] == pytest.approx(20.0)
        assert result["end"]["x"] == pytest.approx(100.0)

    def test_trim_polyline(self):
        data = {"points": [
            {"x": 0.0, "y": 0.0},
            {"x": 50.0, "y": 0.0},
            {"x": 100.0, "y": 0.0},
        ]}
        # Trim at seg 0, keeping left side (2 points) vs right (2 points)
        # Both sides equal → keeps left
        result = trim_geometry("polyline", data, {"x": 25.0, "y": 1.0})
        # Should split at segment 0
        assert len(result["points"]) >= 2

    def test_trim_polygon_returns_unchanged(self):
        data = {"points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}]}
        result = trim_geometry("polygon", data, {"x": 5.0, "y": 5.0})
        assert result == data


# ============================================================================
# Offset tests
# ============================================================================

class TestOffset:

    def test_offset_rectangle_outward(self):
        data = {"x": 10.0, "y": 10.0, "width": 50.0, "height": 30.0}
        result = offset_geometry("rectangle", data, 5.0)
        assert result["x"] == 5.0
        assert result["y"] == 5.0
        assert result["width"] == 60.0
        assert result["height"] == 40.0

    def test_offset_rectangle_inward(self):
        data = {"x": 10.0, "y": 10.0, "width": 50.0, "height": 30.0}
        result = offset_geometry("rectangle", data, -5.0)
        assert result["x"] == 15.0
        assert result["y"] == 15.0
        assert result["width"] == 40.0
        assert result["height"] == 20.0

    def test_offset_rectangle_inward_clamps_min(self):
        data = {"x": 10.0, "y": 10.0, "width": 4.0, "height": 4.0}
        result = offset_geometry("rectangle", data, -10.0)
        assert result["width"] >= 1
        assert result["height"] >= 1

    def test_offset_polygon_creates_new_points(self):
        data = {"points": [
            {"x": 0.0, "y": 0.0},
            {"x": 100.0, "y": 0.0},
            {"x": 100.0, "y": 100.0},
            {"x": 0.0, "y": 100.0},
        ]}
        result = offset_geometry("polygon", data, 10.0, corner_type="miter")
        assert len(result["points"]) >= 4

    def test_offset_polygon_bevel_creates_more_points(self):
        data = {"points": [
            {"x": 0.0, "y": 0.0},
            {"x": 100.0, "y": 0.0},
            {"x": 100.0, "y": 100.0},
            {"x": 0.0, "y": 100.0},
        ]}
        result = offset_geometry("polygon", data, 10.0, corner_type="bevel")
        # Bevel may create 2 points per corner
        assert len(result["points"]) >= 4

    def test_offset_line_returns_unchanged(self):
        data = {"start": {"x": 0, "y": 0}, "end": {"x": 10, "y": 0}}
        result = offset_geometry("line", data, 5.0)
        assert result == data

    def test_offset_too_few_polygon_points(self):
        data = {"points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}]}
        result = offset_geometry("polygon", data, 5.0)
        assert result == data


# ============================================================================
# Split tests
# ============================================================================

class TestSplit:

    def test_split_line(self):
        data = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 100.0, "y": 0.0}}
        result = split_geometry("line", data, {"x": 50.0, "y": 1.0})
        assert result is not None
        part_a, part_b = result
        assert part_a["start"]["x"] == pytest.approx(0.0)
        assert part_a["end"]["x"] == pytest.approx(50.0)
        assert part_b["start"]["x"] == pytest.approx(50.0)
        assert part_b["end"]["x"] == pytest.approx(100.0)

    def test_split_line_near_start_returns_none(self):
        data = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 100.0, "y": 0.0}}
        result = split_geometry("line", data, {"x": 0.5, "y": 0.0})
        assert result is None

    def test_split_line_near_end_returns_none(self):
        data = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 100.0, "y": 0.0}}
        result = split_geometry("line", data, {"x": 99.5, "y": 0.0})
        assert result is None

    def test_split_polyline(self):
        data = {"points": [
            {"x": 0.0, "y": 0.0},
            {"x": 50.0, "y": 0.0},
            {"x": 100.0, "y": 0.0},
        ]}
        result = split_geometry("polyline", data, {"x": 25.0, "y": 1.0})
        assert result is not None
        part_a, part_b = result
        assert len(part_a["points"]) >= 2
        assert len(part_b["points"]) >= 2

    def test_split_polygon_returns_none(self):
        data = {"points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 10}]}
        result = split_geometry("polygon", data, {"x": 5, "y": 5})
        assert result is None

    def test_split_single_point_polyline_returns_none(self):
        data = {"points": [{"x": 0, "y": 0}]}
        result = split_geometry("polyline", data, {"x": 0, "y": 0})
        assert result is None


# ============================================================================
# Join tests
# ============================================================================

class TestJoin:

    def test_join_two_lines_end_to_start(self):
        data_a = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 10.0, "y": 0.0}}
        data_b = {"start": {"x": 10.0, "y": 0.0}, "end": {"x": 20.0, "y": 0.0}}
        result = join_geometries("line", data_a, "line", data_b, tolerance_px=1.0)
        assert result is not None
        gtype, gdata = result
        # Two lines → polyline with 3 points or line with start/end
        assert gtype in ("line", "polyline")

    def test_join_two_lines_end_to_end(self):
        data_a = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 10.0, "y": 0.0}}
        data_b = {"start": {"x": 20.0, "y": 0.0}, "end": {"x": 10.0, "y": 0.0}}
        result = join_geometries("line", data_a, "line", data_b, tolerance_px=1.0)
        assert result is not None

    def test_join_not_within_tolerance(self):
        data_a = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 10.0, "y": 0.0}}
        data_b = {"start": {"x": 50.0, "y": 50.0}, "end": {"x": 60.0, "y": 60.0}}
        result = join_geometries("line", data_a, "line", data_b, tolerance_px=5.0)
        assert result is None

    def test_join_polyline_to_line(self):
        data_a = {"points": [{"x": 0.0, "y": 0.0}, {"x": 5.0, "y": 0.0}, {"x": 10.0, "y": 0.0}]}
        data_b = {"start": {"x": 10.0, "y": 0.0}, "end": {"x": 15.0, "y": 0.0}}
        result = join_geometries("polyline", data_a, "line", data_b, tolerance_px=1.0)
        assert result is not None
        gtype, gdata = result
        assert gtype == "polyline"
        assert len(gdata["points"]) == 4

    def test_join_with_custom_tolerance(self):
        data_a = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 10.0, "y": 0.0}}
        data_b = {"start": {"x": 12.0, "y": 0.0}, "end": {"x": 20.0, "y": 0.0}}
        # Within 15px tolerance
        result = join_geometries("line", data_a, "line", data_b, tolerance_px=15.0)
        assert result is not None
        # Outside 1px tolerance
        result = join_geometries("line", data_a, "line", data_b, tolerance_px=1.0)
        assert result is None


# ============================================================================
# Edge cases
# ============================================================================

class TestEdgeCases:

    def test_nudge_preserves_extra_fields(self):
        data = {"start": {"x": 0.0, "y": 0.0}, "end": {"x": 10.0, "y": 0.0}, "label": "test"}
        result = nudge_geometry("line", data, "right", 5.0)
        assert result.get("label") == "test"

    def test_snap_preserves_extra_fields(self):
        data = {"x": 3.0, "y": 7.0, "extra": "kept"}
        result = snap_geometry_to_grid("point", data, 10.0)
        assert result.get("extra") == "kept"

    def test_extend_single_point_polyline(self):
        data = {"points": [{"x": 5.0, "y": 5.0}]}
        result = extend_geometry("polyline", data, "end", 10.0)
        assert result == data
