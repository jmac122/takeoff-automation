"""Integration tests for the geometry adjustment API endpoint."""

import uuid
from datetime import datetime, timezone
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


def _mock_measurement(mid: str, geometry_type: str = "line", geometry_data=None):
    """Create a mock Measurement object."""
    m = MagicMock()
    m.id = uuid.UUID(mid)
    m.geometry_type = geometry_type
    m.geometry_data = geometry_data or {"start": {"x": 5.0, "y": 0.0}, "end": {"x": 15.0, "y": 0.0}}
    m.quantity = 10.0
    m.unit = "LF"
    m.condition_id = uuid.uuid4()
    m.page_id = uuid.uuid4()
    m.is_modified = True
    m.notes = None
    m.original_geometry = None
    m.original_quantity = None
    m.pixel_length = 10.0
    m.pixel_area = None
    m.extra_metadata = {}
    m.created_at = datetime.now(timezone.utc)
    m.updated_at = datetime.now(timezone.utc)
    return m


class TestAdjustEndpoint:
    """Tests for PUT /measurements/{id}/adjust."""

    @patch("app.api.routes.measurements.get_geometry_adjuster")
    def test_nudge_returns_200(self, mock_adjuster, client, measurement_id):
        mock_svc = MagicMock()
        mock_measurement = _mock_measurement(measurement_id)
        mock_svc.adjust_measurement = AsyncMock(return_value=mock_measurement)
        mock_adjuster.return_value = mock_svc

        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "nudge", "params": {"direction": "right", "distance_px": 5}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "nudge"
        assert data["measurement_id"] == measurement_id
        assert data["status"] == "success"
        assert data["new_geometry_type"] == "line"
        assert data["new_quantity"] == 10.0
        assert data["new_unit"] == "LF"

    @patch("app.api.routes.measurements.get_geometry_adjuster")
    def test_snap_to_grid_returns_200(self, mock_adjuster, client, measurement_id):
        mock_svc = MagicMock()
        mock_measurement = _mock_measurement(measurement_id)
        mock_svc.adjust_measurement = AsyncMock(return_value=mock_measurement)
        mock_adjuster.return_value = mock_svc

        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "snap_to_grid", "params": {"grid_size_px": 10}},
        )

        assert response.status_code == 200
        assert response.json()["action"] == "snap_to_grid"

    @patch("app.api.routes.measurements.get_geometry_adjuster")
    def test_extend_returns_200(self, mock_adjuster, client, measurement_id):
        mock_svc = MagicMock()
        mock_measurement = _mock_measurement(measurement_id)
        mock_svc.adjust_measurement = AsyncMock(return_value=mock_measurement)
        mock_adjuster.return_value = mock_svc

        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "extend", "params": {"endpoint": "end", "distance_px": 20}},
        )

        assert response.status_code == 200
        assert response.json()["action"] == "extend"

    @patch("app.api.routes.measurements.get_geometry_adjuster")
    def test_trim_returns_200(self, mock_adjuster, client, measurement_id):
        mock_svc = MagicMock()
        mock_measurement = _mock_measurement(measurement_id)
        mock_svc.adjust_measurement = AsyncMock(return_value=mock_measurement)
        mock_adjuster.return_value = mock_svc

        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "trim", "params": {"trim_point": {"x": 50, "y": 0}}},
        )

        assert response.status_code == 200
        assert response.json()["action"] == "trim"

    @patch("app.api.routes.measurements.get_geometry_adjuster")
    def test_offset_returns_200(self, mock_adjuster, client, measurement_id):
        mock_svc = MagicMock()
        mock_measurement = _mock_measurement(measurement_id)
        mock_svc.adjust_measurement = AsyncMock(return_value=mock_measurement)
        mock_adjuster.return_value = mock_svc

        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "offset", "params": {"distance_px": 10}},
        )

        assert response.status_code == 200
        assert response.json()["action"] == "offset"

    @patch("app.api.routes.measurements.get_geometry_adjuster")
    def test_split_returns_200_with_created_id(self, mock_adjuster, client, measurement_id):
        mock_svc = MagicMock()
        mock_measurement = _mock_measurement(measurement_id)
        mock_svc.adjust_measurement = AsyncMock(return_value=mock_measurement)
        mock_adjuster.return_value = mock_svc

        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "split", "params": {"split_point": {"x": 50, "y": 0}}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "split"

    @patch("app.api.routes.measurements.get_geometry_adjuster")
    def test_join_returns_200(self, mock_adjuster, client, measurement_id):
        mock_svc = MagicMock()
        mock_measurement = _mock_measurement(measurement_id)
        mock_svc.adjust_measurement = AsyncMock(return_value=mock_measurement)
        mock_adjuster.return_value = mock_svc

        other_id = str(uuid.uuid4())
        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "join", "params": {"other_measurement_id": other_id}},
        )

        assert response.status_code == 200
        assert response.json()["action"] == "join"

    @patch("app.api.routes.measurements.get_geometry_adjuster")
    def test_measurement_not_found_returns_400(self, mock_adjuster, client, measurement_id):
        mock_svc = MagicMock()
        mock_svc.adjust_measurement = AsyncMock(
            side_effect=ValueError("Measurement not found: " + measurement_id)
        )
        mock_adjuster.return_value = mock_svc

        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "nudge", "params": {"direction": "up"}},
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_invalid_action_returns_422(self, client, measurement_id):
        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "invalid_action", "params": {}},
        )

        assert response.status_code == 422

    def test_nudge_missing_direction_returns_422(self, client, measurement_id):
        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "nudge", "params": {}},
        )

        assert response.status_code == 422

    def test_trim_missing_trim_point_returns_422(self, client, measurement_id):
        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "trim", "params": {}},
        )

        assert response.status_code == 422

    def test_split_missing_split_point_returns_422(self, client, measurement_id):
        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "split", "params": {}},
        )

        assert response.status_code == 422

    def test_join_missing_other_id_returns_422(self, client, measurement_id):
        response = client.put(
            f"/api/v1/measurements/{measurement_id}/adjust",
            json={"action": "join", "params": {}},
        )

        assert response.status_code == 422
