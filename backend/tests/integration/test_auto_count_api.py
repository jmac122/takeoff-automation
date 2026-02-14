"""Integration tests for the auto count API routes."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def page_id():
    return str(uuid.uuid4())


@pytest.fixture
def condition_id():
    return str(uuid.uuid4())


@pytest.fixture
def session_id():
    return str(uuid.uuid4())


@pytest.fixture
def detection_id():
    return str(uuid.uuid4())


def _mock_session(session_id: str, page_id: str, condition_id: str, detections=None):
    """Create a mock auto count session."""
    session = MagicMock()
    session.id = uuid.UUID(session_id)
    session.page_id = uuid.UUID(page_id)
    session.condition_id = uuid.UUID(condition_id)
    session.template_bbox = {"x": 100, "y": 100, "w": 50, "h": 50}
    session.confidence_threshold = 0.80
    session.scale_tolerance = 0.20
    session.rotation_tolerance = 15.0
    session.detection_method = "hybrid"
    session.status = "completed"
    session.total_detections = 5
    session.confirmed_count = 0
    session.rejected_count = 0
    session.error_message = None
    session.processing_time_ms = 1234.5
    session.template_match_count = 3
    session.llm_match_count = 2
    session.created_at = "2026-01-01T00:00:00Z"
    session.updated_at = "2026-01-01T00:00:00Z"
    session.detections = detections or []
    return session


def _mock_detection(detection_id: str, session_id: str, confidence: float = 0.90):
    """Create a mock detection."""
    det = MagicMock()
    det.id = uuid.UUID(detection_id)
    det.session_id = uuid.UUID(session_id)
    det.measurement_id = None
    det.bbox = {"x": 200, "y": 200, "w": 50, "h": 50}
    det.center_x = 225.0
    det.center_y = 225.0
    det.confidence = confidence
    det.detection_source = "template"
    det.status = "pending"
    det.is_auto_confirmed = False
    det.created_at = "2026-01-01T00:00:00Z"
    det.updated_at = "2026-01-01T00:00:00Z"
    return det


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


class TestGetSession:
    def test_get_session_returns_200(
        self, client, session_id, page_id, condition_id
    ):
        mock_session = _mock_session(session_id, page_id, condition_id)

        with patch(
            "app.api.routes.auto_count.get_auto_count_service"
        ) as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.get_session = AsyncMock(return_value=mock_session)
            mock_svc_fn.return_value = mock_svc

            response = client.get(
                f"/api/v1/auto-count-sessions/{session_id}"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["status"] == "completed"

    def test_get_session_not_found(self, client, session_id):
        with patch(
            "app.api.routes.auto_count.get_auto_count_service"
        ) as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.get_session = AsyncMock(
                side_effect=ValueError("not found")
            )
            mock_svc_fn.return_value = mock_svc

            response = client.get(
                f"/api/v1/auto-count-sessions/{session_id}"
            )

        assert response.status_code == 404


class TestListSessions:
    def test_list_page_sessions(self, client, page_id):
        with patch(
            "app.api.routes.auto_count.get_auto_count_service"
        ) as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.list_sessions = AsyncMock(return_value=[])
            mock_svc_fn.return_value = mock_svc

            response = client.get(
                f"/api/v1/pages/{page_id}/auto-count-sessions"
            )

        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# Detection review
# ---------------------------------------------------------------------------


class TestConfirmDetection:
    def test_confirm_returns_200(
        self, client, detection_id, session_id
    ):
        mock_det = _mock_detection(detection_id, session_id)
        mock_det.status = "confirmed"

        with patch(
            "app.api.routes.auto_count.get_auto_count_service"
        ) as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.confirm_detection = AsyncMock(return_value=mock_det)
            mock_svc_fn.return_value = mock_svc

            response = client.post(
                f"/api/v1/auto-count-detections/{detection_id}/confirm"
            )

        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"


class TestRejectDetection:
    def test_reject_returns_200(
        self, client, detection_id, session_id
    ):
        mock_det = _mock_detection(detection_id, session_id)
        mock_det.status = "rejected"

        with patch(
            "app.api.routes.auto_count.get_auto_count_service"
        ) as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.reject_detection = AsyncMock(return_value=mock_det)
            mock_svc_fn.return_value = mock_svc

            response = client.post(
                f"/api/v1/auto-count-detections/{detection_id}/reject"
            )

        assert response.status_code == 200
        assert response.json()["status"] == "rejected"


class TestBulkConfirm:
    def test_bulk_confirm_returns_count(self, client, session_id):
        with patch(
            "app.api.routes.auto_count.get_auto_count_service"
        ) as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.bulk_confirm_above_threshold = AsyncMock(return_value=3)
            mock_svc_fn.return_value = mock_svc

            response = client.post(
                f"/api/v1/auto-count-sessions/{session_id}/bulk-confirm",
                json={"threshold": 0.85},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["confirmed_count"] == 3
        assert data["threshold"] == 0.85


class TestCreateMeasurements:
    def test_create_measurements_returns_count(self, client, session_id):
        with patch(
            "app.api.routes.auto_count.get_auto_count_service"
        ) as mock_svc_fn:
            mock_svc = MagicMock()
            mock_svc.create_measurements_from_confirmed = AsyncMock(return_value=5)
            mock_svc_fn.return_value = mock_svc

            response = client.post(
                f"/api/v1/auto-count-sessions/{session_id}/create-measurements"
            )

        assert response.status_code == 200
        assert response.json()["measurements_created"] == 5
