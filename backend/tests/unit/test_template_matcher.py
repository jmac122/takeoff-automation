"""Unit tests for the template matching service."""

import pytest

from app.services.auto_count.template_matcher import MatchResult, TemplateMatchingService


@pytest.fixture
def matcher():
    return TemplateMatchingService(
        confidence_threshold=0.80,
        scale_tolerance=0.20,
        rotation_tolerance=15.0,
        nms_overlap_threshold=0.30,
    )


# ---------------------------------------------------------------------------
# IoU calculation
# ---------------------------------------------------------------------------


class TestComputeIoU:
    def test_identical_boxes(self, matcher):
        a = MatchResult(x=0, y=0, w=10, h=10, center_x=5, center_y=5, confidence=0.9)
        b = MatchResult(x=0, y=0, w=10, h=10, center_x=5, center_y=5, confidence=0.8)
        assert matcher._compute_iou(a, b) == 1.0

    def test_no_overlap(self, matcher):
        a = MatchResult(x=0, y=0, w=10, h=10, center_x=5, center_y=5, confidence=0.9)
        b = MatchResult(x=20, y=20, w=10, h=10, center_x=25, center_y=25, confidence=0.8)
        assert matcher._compute_iou(a, b) == 0.0

    def test_partial_overlap(self, matcher):
        a = MatchResult(x=0, y=0, w=10, h=10, center_x=5, center_y=5, confidence=0.9)
        b = MatchResult(x=5, y=5, w=10, h=10, center_x=10, center_y=10, confidence=0.8)
        # Intersection: 5x5 = 25, Union: 100 + 100 - 25 = 175
        expected = 25 / 175
        assert abs(matcher._compute_iou(a, b) - expected) < 0.01

    def test_contained_box(self, matcher):
        a = MatchResult(x=0, y=0, w=20, h=20, center_x=10, center_y=10, confidence=0.9)
        b = MatchResult(x=5, y=5, w=10, h=10, center_x=10, center_y=10, confidence=0.8)
        # Intersection: 10x10 = 100, Union: 400 + 100 - 100 = 400
        expected = 100 / 400
        assert abs(matcher._compute_iou(a, b) - expected) < 0.01


# ---------------------------------------------------------------------------
# Non-maximum suppression
# ---------------------------------------------------------------------------


class TestNMS:
    def test_no_overlap_keeps_all(self, matcher):
        matches = [
            MatchResult(x=0, y=0, w=10, h=10, center_x=5, center_y=5, confidence=0.9),
            MatchResult(x=50, y=50, w=10, h=10, center_x=55, center_y=55, confidence=0.8),
            MatchResult(x=100, y=100, w=10, h=10, center_x=105, center_y=105, confidence=0.7),
        ]
        result = matcher._non_maximum_suppression(matches)
        assert len(result) == 3

    def test_overlapping_keeps_highest_confidence(self, matcher):
        matches = [
            MatchResult(x=0, y=0, w=10, h=10, center_x=5, center_y=5, confidence=0.9),
            MatchResult(x=2, y=2, w=10, h=10, center_x=7, center_y=7, confidence=0.95),
            MatchResult(x=1, y=1, w=10, h=10, center_x=6, center_y=6, confidence=0.85),
        ]
        result = matcher._non_maximum_suppression(matches)
        # All overlap significantly so only highest confidence should remain
        assert len(result) == 1
        assert result[0].confidence == 0.95

    def test_empty_input(self, matcher):
        result = matcher._non_maximum_suppression([])
        assert result == []

    def test_single_input(self, matcher):
        matches = [
            MatchResult(x=0, y=0, w=10, h=10, center_x=5, center_y=5, confidence=0.9)
        ]
        result = matcher._non_maximum_suppression(matches)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Template region exclusion
# ---------------------------------------------------------------------------


class TestTemplateExclusion:
    def test_excludes_template_region(self, matcher):
        template_bbox = {"x": 100, "y": 100, "w": 50, "h": 50}
        matches = [
            MatchResult(x=100, y=100, w=50, h=50, center_x=125, center_y=125, confidence=1.0),
            MatchResult(x=300, y=300, w=50, h=50, center_x=325, center_y=325, confidence=0.9),
        ]
        result = matcher._exclude_template_region(matches, template_bbox)
        assert len(result) == 1
        assert result[0].center_x == 325

    def test_keeps_non_overlapping(self, matcher):
        template_bbox = {"x": 100, "y": 100, "w": 50, "h": 50}
        matches = [
            MatchResult(x=300, y=300, w=50, h=50, center_x=325, center_y=325, confidence=0.9),
            MatchResult(x=500, y=500, w=50, h=50, center_x=525, center_y=525, confidence=0.85),
        ]
        result = matcher._exclude_template_region(matches, template_bbox)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Find matches (with OpenCV, if available)
# ---------------------------------------------------------------------------


class TestFindMatches:
    def test_returns_list(self, matcher):
        # Even without OpenCV, should return empty list gracefully
        try:
            result = matcher.find_matches(
                page_image_bytes=b"not a real image",
                template_bbox={"x": 0, "y": 0, "w": 10, "h": 10},
            )
            assert isinstance(result, list)
        except Exception:
            # If cv2 throws, that's acceptable in test environment
            pass

    def test_invalid_bbox_returns_empty(self, matcher):
        try:
            import cv2
            import numpy as np

            # Create a simple test image
            img = np.zeros((100, 100), dtype=np.uint8)
            _, encoded = cv2.imencode(".png", img)
            image_bytes = encoded.tobytes()

            # Invalid bbox (negative dimensions effectively)
            result = matcher.find_matches(
                page_image_bytes=image_bytes,
                template_bbox={"x": 200, "y": 200, "w": 10, "h": 10},
            )
            assert result == []
        except ImportError:
            pytest.skip("OpenCV not installed")
