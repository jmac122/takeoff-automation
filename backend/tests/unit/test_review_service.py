"""Unit tests for the ReviewService."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.measurement import Measurement
from app.models.measurement_history import MeasurementHistory
from app.models.condition import Condition
from app.services.review_service import ReviewService


@pytest.fixture
def review_service():
    return ReviewService()


@pytest.fixture
def mock_measurement():
    m = MagicMock(spec=Measurement)
    m.id = uuid.uuid4()
    m.condition_id = uuid.uuid4()
    m.page_id = uuid.uuid4()
    m.geometry_type = "polygon"
    m.geometry_data = {"points": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 1, "y": 1}]}
    m.quantity = 100.0
    m.unit = "SF"
    m.is_verified = False
    m.is_rejected = False
    m.is_modified = False
    m.is_ai_generated = True
    m.ai_confidence = 0.95
    m.rejection_reason = None
    m.review_notes = None
    m.reviewed_at = None
    m.original_geometry = None
    m.original_quantity = None
    return m


@pytest.fixture
def mock_condition():
    c = MagicMock(spec=Condition)
    c.id = uuid.uuid4()
    c.project_id = uuid.uuid4()
    c.measurement_type = "area"
    c.depth = None
    c.unit = "SF"
    return c


class TestDeriveStatus:
    def test_pending(self, review_service, mock_measurement):
        mock_measurement.is_verified = False
        mock_measurement.is_rejected = False
        mock_measurement.is_modified = False
        assert review_service._derive_status(mock_measurement) == "pending"

    def test_approved(self, review_service, mock_measurement):
        mock_measurement.is_verified = True
        mock_measurement.is_rejected = False
        mock_measurement.is_modified = False
        assert review_service._derive_status(mock_measurement) == "approved"

    def test_rejected(self, review_service, mock_measurement):
        mock_measurement.is_rejected = True
        mock_measurement.is_verified = False
        assert review_service._derive_status(mock_measurement) == "rejected"

    def test_modified(self, review_service, mock_measurement):
        mock_measurement.is_verified = True
        mock_measurement.is_modified = True
        mock_measurement.is_rejected = False
        assert review_service._derive_status(mock_measurement) == "modified"


class TestApproveMeasurement:
    @pytest.mark.asyncio
    async def test_approve_sets_verified(self, review_service, mock_measurement, mock_condition):
        session = AsyncMock()
        session.get = AsyncMock(side_effect=lambda model, id: {
            Measurement: mock_measurement,
            Condition: mock_condition,
        }.get(model))

        with patch("app.services.review_service.get_measurement_engine") as mock_engine_fn:
            mock_engine = MagicMock()
            mock_engine._update_condition_totals = AsyncMock()
            mock_engine_fn.return_value = mock_engine

            result = await review_service.approve_measurement(
                session=session,
                measurement_id=mock_measurement.id,
                reviewer="test_user",
                notes="Looks good",
            )

        assert mock_measurement.is_verified is True
        assert mock_measurement.is_rejected is False
        assert mock_measurement.review_notes == "Looks good"
        assert mock_measurement.reviewed_at is not None
        session.add.assert_called_once()
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_not_found(self, review_service):
        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Measurement not found"):
            await review_service.approve_measurement(
                session=session,
                measurement_id=uuid.uuid4(),
                reviewer="test_user",
            )


class TestRejectMeasurement:
    @pytest.mark.asyncio
    async def test_reject_sets_rejected(self, review_service, mock_measurement, mock_condition):
        session = AsyncMock()
        session.get = AsyncMock(side_effect=lambda model, id: {
            Measurement: mock_measurement,
            Condition: mock_condition,
        }.get(model))

        with patch("app.services.review_service.get_measurement_engine") as mock_engine_fn:
            mock_engine = MagicMock()
            mock_engine._update_condition_totals = AsyncMock()
            mock_engine_fn.return_value = mock_engine

            result = await review_service.reject_measurement(
                session=session,
                measurement_id=mock_measurement.id,
                reviewer="test_user",
                reason="Incorrect area",
            )

        assert mock_measurement.is_rejected is True
        assert mock_measurement.is_verified is False
        assert mock_measurement.rejection_reason == "Incorrect area"
        session.add.assert_called_once()
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reject_not_found(self, review_service):
        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Measurement not found"):
            await review_service.reject_measurement(
                session=session,
                measurement_id=uuid.uuid4(),
                reviewer="test_user",
                reason="Bad",
            )


class TestModifyMeasurement:
    @pytest.mark.asyncio
    async def test_modify_stores_original_on_first_edit(self, review_service, mock_measurement, mock_condition):
        session = AsyncMock()
        mock_page = MagicMock()
        mock_page.scale_value = 48.0

        session.get = AsyncMock(side_effect=lambda model, id: {
            Measurement: mock_measurement,
            Condition: mock_condition,
        }.get(model))
        # Override for Page
        original_get = session.get
        async def custom_get(model, id):
            from app.models.page import Page
            if model == Page:
                return mock_page
            return await original_get(model, id)
        session.get = AsyncMock(side_effect=custom_get)

        with patch("app.services.review_service.get_measurement_engine") as mock_engine_fn:
            mock_engine = MagicMock()
            mock_engine._calculate_geometry.return_value = {"area_sf": 150.0}
            mock_engine._extract_quantity.return_value = 150.0
            mock_engine._update_condition_totals = AsyncMock()
            mock_engine_fn.return_value = mock_engine

            new_geometry = {"points": [{"x": 0, "y": 0}, {"x": 2, "y": 0}, {"x": 2, "y": 2}]}
            result = await review_service.modify_measurement(
                session=session,
                measurement_id=mock_measurement.id,
                reviewer="test_user",
                geometry_data=new_geometry,
            )

        # Original should store the pre-modification geometry
        assert mock_measurement.original_geometry == {"points": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 1, "y": 1}]}
        # geometry_data should be updated to new geometry
        assert mock_measurement.geometry_data == new_geometry
        assert mock_measurement.is_modified is True
        assert mock_measurement.is_verified is True


class TestGetReviewStats:
    @pytest.mark.asyncio
    async def test_returns_stats(self, review_service):
        session = AsyncMock()
        mock_row = MagicMock()
        mock_row.total = 10
        mock_row.pending = 5
        mock_row.approved = 3
        mock_row.rejected = 1
        mock_row.modified = 1
        mock_row.ai_generated_count = 8
        mock_row.ai_approved = 3
        mock_row.confidence_high = 4
        mock_row.confidence_medium = 3
        mock_row.confidence_low = 1

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        session.execute = AsyncMock(return_value=mock_result)

        stats = await review_service.get_review_stats(
            session=session,
            project_id=uuid.uuid4(),
        )

        assert stats["total"] == 10
        assert stats["pending"] == 5
        assert stats["approved"] == 3
        assert stats["rejected"] == 1
        assert stats["ai_accuracy_percent"] == 37.5
        assert stats["confidence_distribution"]["high"] == 4


class TestGetNextUnreviewed:
    @pytest.mark.asyncio
    async def test_returns_next(self, review_service, mock_measurement):
        session = AsyncMock()

        # Count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 3

        # Next query
        mock_next_result = MagicMock()
        mock_next_result.scalar_one_or_none.return_value = mock_measurement

        session.execute = AsyncMock(side_effect=[mock_count_result, mock_next_result])

        measurement, count = await review_service.get_next_unreviewed(
            session=session,
            page_id=uuid.uuid4(),
        )

        assert measurement == mock_measurement
        assert count == 3
