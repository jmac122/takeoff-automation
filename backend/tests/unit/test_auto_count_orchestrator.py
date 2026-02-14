"""Unit tests for the auto count orchestrator."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.auto_count.orchestrator import AutoCountService
from app.services.auto_count.template_matcher import MatchResult


@pytest.fixture
def service():
    return AutoCountService()


# ---------------------------------------------------------------------------
# Merge detections
# ---------------------------------------------------------------------------


class TestMergeDetections:
    def test_non_overlapping_merges_all(self, service):
        template = [
            MatchResult(x=0, y=0, w=10, h=10, center_x=5, center_y=5, confidence=0.9),
        ]
        llm = [
            MatchResult(x=100, y=100, w=10, h=10, center_x=105, center_y=105, confidence=0.85),
        ]
        result = service._merge_detections(template, llm)
        assert len(result) == 2

    def test_overlapping_keeps_higher_confidence(self, service):
        template = [
            MatchResult(x=0, y=0, w=10, h=10, center_x=5, center_y=5, confidence=0.8),
        ]
        llm = [
            MatchResult(x=2, y=2, w=10, h=10, center_x=7, center_y=7, confidence=0.95),
        ]
        result = service._merge_detections(template, llm)
        assert len(result) == 1
        assert result[0].confidence == 0.95

    def test_overlapping_keeps_template_if_higher(self, service):
        template = [
            MatchResult(x=0, y=0, w=10, h=10, center_x=5, center_y=5, confidence=0.95),
        ]
        llm = [
            MatchResult(x=2, y=2, w=10, h=10, center_x=7, center_y=7, confidence=0.80),
        ]
        result = service._merge_detections(template, llm)
        assert len(result) == 1
        assert result[0].confidence == 0.95

    def test_empty_inputs(self, service):
        assert service._merge_detections([], []) == []
        assert len(service._merge_detections([], [
            MatchResult(x=0, y=0, w=10, h=10, center_x=5, center_y=5, confidence=0.9)
        ])) == 1


# ---------------------------------------------------------------------------
# Session creation
# ---------------------------------------------------------------------------


class TestSessionCreation:
    @pytest.mark.asyncio
    async def test_create_session_missing_page_raises(self, service):
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Page .* not found"):
            await service.create_session(
                db=mock_db,
                page_id=uuid.uuid4(),
                condition_id=uuid.uuid4(),
                template_bbox={"x": 0, "y": 0, "w": 10, "h": 10},
            )

    @pytest.mark.asyncio
    async def test_create_session_missing_condition_raises(self, service):
        mock_db = AsyncMock()

        # First get (page) returns something, second get (condition) returns None
        mock_page = MagicMock()
        mock_db.get = AsyncMock(side_effect=[mock_page, None])

        with pytest.raises(ValueError, match="Condition .* not found"):
            await service.create_session(
                db=mock_db,
                page_id=uuid.uuid4(),
                condition_id=uuid.uuid4(),
                template_bbox={"x": 0, "y": 0, "w": 10, "h": 10},
            )


# ---------------------------------------------------------------------------
# Detection review
# ---------------------------------------------------------------------------


class TestDetectionReview:
    @pytest.mark.asyncio
    async def test_confirm_detection_missing_raises(self, service):
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Detection .* not found"):
            await service.confirm_detection(
                db=mock_db,
                detection_id=uuid.uuid4(),
            )

    @pytest.mark.asyncio
    async def test_reject_detection_missing_raises(self, service):
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Detection .* not found"):
            await service.reject_detection(
                db=mock_db,
                detection_id=uuid.uuid4(),
            )
