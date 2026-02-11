"""Integration tests for the review API routes."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def measurement_id():
    return str(uuid.uuid4())


@pytest.fixture
def project_id():
    return str(uuid.uuid4())


@pytest.fixture
def page_id():
    return str(uuid.uuid4())


class TestApproveEndpoint:
    def test_approve_returns_review_action_response(self, client, measurement_id):
        mock_measurement = MagicMock()
        mock_measurement.id = uuid.UUID(measurement_id)

        with patch("app.api.routes.review.get_review_service") as mock_service_fn:
            mock_service = MagicMock()
            mock_service.approve_measurement = AsyncMock(return_value=mock_measurement)
            mock_service_fn.return_value = mock_service

            response = client.post(
                f"/api/v1/measurements/{measurement_id}/approve",
                json={"reviewer": "test_user", "notes": "LGTM"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["measurement_id"] == measurement_id

    def test_approve_not_found_returns_404(self, client, measurement_id):
        with patch("app.api.routes.review.get_review_service") as mock_service_fn:
            mock_service = MagicMock()
            mock_service.approve_measurement = AsyncMock(
                side_effect=ValueError("Measurement not found")
            )
            mock_service_fn.return_value = mock_service

            response = client.post(
                f"/api/v1/measurements/{measurement_id}/approve",
                json={"reviewer": "test_user"},
            )

        assert response.status_code == 404


class TestRejectEndpoint:
    def test_reject_returns_review_action_response(self, client, measurement_id):
        mock_measurement = MagicMock()
        mock_measurement.id = uuid.UUID(measurement_id)

        with patch("app.api.routes.review.get_review_service") as mock_service_fn:
            mock_service = MagicMock()
            mock_service.reject_measurement = AsyncMock(return_value=mock_measurement)
            mock_service_fn.return_value = mock_service

            response = client.post(
                f"/api/v1/measurements/{measurement_id}/reject",
                json={"reviewer": "test_user", "reason": "Incorrect area"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    def test_reject_requires_reason(self, client, measurement_id):
        response = client.post(
            f"/api/v1/measurements/{measurement_id}/reject",
            json={"reviewer": "test_user"},
        )
        assert response.status_code == 422  # Validation error


class TestModifyEndpoint:
    def test_modify_returns_review_action_response(self, client, measurement_id):
        mock_measurement = MagicMock()
        mock_measurement.id = uuid.UUID(measurement_id)
        mock_measurement.quantity = 150.0

        with patch("app.api.routes.review.get_review_service") as mock_service_fn:
            mock_service = MagicMock()
            mock_service.modify_measurement = AsyncMock(return_value=mock_measurement)
            mock_service_fn.return_value = mock_service

            response = client.post(
                f"/api/v1/measurements/{measurement_id}/modify",
                json={
                    "reviewer": "test_user",
                    "geometry_data": {"points": [{"x": 0, "y": 0}]},
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "modified"
        assert data["new_quantity"] == 150.0


class TestAutoAcceptEndpoint:
    def test_auto_accept_returns_count(self, client, project_id):
        with patch("app.api.routes.review.get_review_service") as mock_service_fn:
            mock_service = MagicMock()
            mock_service.auto_accept_batch = AsyncMock(return_value=5)
            mock_service_fn.return_value = mock_service

            response = client.post(
                f"/api/v1/projects/{project_id}/measurements/auto-accept",
                json={"threshold": 0.9},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["auto_accepted_count"] == 5
        assert data["threshold"] == 0.9


class TestReviewStatsEndpoint:
    def test_get_review_stats(self, client, project_id):
        with patch("app.api.routes.review.get_review_service") as mock_service_fn:
            mock_service = MagicMock()
            mock_service.get_review_stats = AsyncMock(return_value={
                "total": 10,
                "pending": 5,
                "approved": 3,
                "rejected": 1,
                "modified": 1,
                "ai_generated_count": 8,
                "ai_accuracy_percent": 37.5,
                "confidence_distribution": {"high": 4, "medium": 3, "low": 1},
            })
            mock_service_fn.return_value = mock_service

            response = client.get(f"/api/v1/projects/{project_id}/review-stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert data["pending"] == 5


class TestNextUnreviewedEndpoint:
    def test_get_next_unreviewed(self, client, page_id):
        mock_measurement = MagicMock()
        mock_measurement.id = uuid.uuid4()
        mock_measurement.condition_id = uuid.uuid4()
        mock_measurement.page_id = uuid.UUID(page_id)
        mock_measurement.geometry_type = "polygon"
        mock_measurement.geometry_data = {"points": []}
        mock_measurement.quantity = 100.0
        mock_measurement.unit = "SF"
        mock_measurement.pixel_length = None
        mock_measurement.pixel_area = 5000.0
        mock_measurement.is_ai_generated = True
        mock_measurement.ai_confidence = 0.85
        mock_measurement.ai_model = "claude"
        mock_measurement.is_modified = False
        mock_measurement.is_verified = False
        mock_measurement.is_rejected = False
        mock_measurement.rejection_reason = None
        mock_measurement.review_notes = None
        mock_measurement.reviewed_at = None
        mock_measurement.original_geometry = None
        mock_measurement.original_quantity = None
        mock_measurement.notes = None
        mock_measurement.extra_metadata = None
        mock_measurement.created_at = "2026-01-01T00:00:00Z"
        mock_measurement.updated_at = "2026-01-01T00:00:00Z"

        with patch("app.api.routes.review.get_review_service") as mock_service_fn:
            mock_service = MagicMock()
            mock_service.get_next_unreviewed = AsyncMock(
                return_value=(mock_measurement, 5)
            )
            mock_service_fn.return_value = mock_service

            response = client.get(
                f"/api/v1/pages/{page_id}/measurements/next-unreviewed"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["remaining_count"] == 5
        assert data["measurement"] is not None


class TestMeasurementHistoryEndpoint:
    def test_get_history(self, client, measurement_id):
        mock_entry = MagicMock()
        mock_entry.id = uuid.uuid4()
        mock_entry.measurement_id = uuid.UUID(measurement_id)
        mock_entry.action = "approved"
        mock_entry.actor = "test_user"
        mock_entry.actor_type = "user"
        mock_entry.previous_status = "pending"
        mock_entry.new_status = "approved"
        mock_entry.previous_quantity = None
        mock_entry.new_quantity = None
        mock_entry.change_description = "Approved"
        mock_entry.notes = None
        mock_entry.created_at = "2026-01-01T00:00:00Z"

        with patch("app.api.routes.review.get_review_service") as mock_service_fn:
            mock_service = MagicMock()
            mock_service.get_measurement_history = AsyncMock(return_value=[mock_entry])
            mock_service_fn.return_value = mock_service

            response = client.get(
                f"/api/v1/measurements/{measurement_id}/history"
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["action"] == "approved"

    def test_get_history_not_found(self, client, measurement_id):
        with patch("app.api.routes.review.get_review_service") as mock_service_fn:
            mock_service = MagicMock()
            mock_service.get_measurement_history = AsyncMock(
                side_effect=ValueError("Measurement not found")
            )
            mock_service_fn.return_value = mock_service

            response = client.get(
                f"/api/v1/measurements/{measurement_id}/history"
            )

        assert response.status_code == 404
