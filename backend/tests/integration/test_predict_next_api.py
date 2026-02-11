"""Integration tests for the predict-next-point API endpoint."""

import uuid
from unittest.mock import patch, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def base_url():
    return "http://test"


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.fixture
def mock_page():
    """Create a mock page object."""
    page = MagicMock()
    page.id = uuid.uuid4()
    page.scale_calibrated = True
    page.image_path = "/tmp/fake-page.png"
    page.image_width = 2000
    page.image_height = 1500
    return page


@pytest.fixture
def mock_document(mock_page):
    """Create a mock document object."""
    doc = MagicMock()
    doc.project_id = uuid.uuid4()
    return doc


class TestPredictNextPointEndpoint:
    """Tests for POST /pages/{page_id}/predict-next-point."""

    @patch("app.api.routes.takeoff.get_predict_point_service")
    @patch("app.api.routes.takeoff.get_calibrated_page")
    async def test_returns_200_with_prediction(
        self, mock_get_page, mock_get_service, base_url, transport, mock_page, mock_document,
    ):
        """Successful prediction returns 200 with prediction data."""
        from app.api.routes.takeoff import CalibratedPageData

        mock_get_page.return_value = CalibratedPageData(page=mock_page, document=mock_document)

        mock_service = MagicMock()
        mock_service.predict_next.return_value = {
            "geometry_type": "polyline",
            "geometry_data": {"points": [{"x": 100, "y": 200}, {"x": 300, "y": 200}]},
            "confidence": 0.82,
        }
        mock_get_service.return_value = mock_service

        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_bytes", return_value=b"fake-png"):
            async with AsyncClient(transport=transport, base_url=base_url) as client:
                response = await client.post(
                    f"/api/v1/pages/{mock_page.id}/predict-next-point",
                    json={
                        "condition_id": str(uuid.uuid4()),
                        "last_geometry_type": "polyline",
                        "last_geometry_data": {
                            "points": [{"x": 50, "y": 100}, {"x": 150, "y": 100}]
                        },
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] is not None
        assert data["prediction"]["geometry_type"] == "polyline"
        assert data["prediction"]["confidence"] == 0.82
        assert data["latency_ms"] >= 0

    @patch("app.api.routes.takeoff.get_predict_point_service")
    @patch("app.api.routes.takeoff.get_calibrated_page")
    async def test_returns_null_prediction_on_service_error(
        self, mock_get_page, mock_get_service, base_url, transport, mock_page, mock_document,
    ):
        """Service errors result in {prediction: null}, NOT a 500."""
        from app.api.routes.takeoff import CalibratedPageData

        mock_get_page.return_value = CalibratedPageData(page=mock_page, document=mock_document)

        mock_service = MagicMock()
        mock_service.predict_next.side_effect = RuntimeError("LLM exploded")
        mock_get_service.return_value = mock_service

        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_bytes", return_value=b"fake-png"):
            async with AsyncClient(transport=transport, base_url=base_url) as client:
                response = await client.post(
                    f"/api/v1/pages/{mock_page.id}/predict-next-point",
                    json={
                        "condition_id": str(uuid.uuid4()),
                        "last_geometry_type": "point",
                        "last_geometry_data": {"x": 500, "y": 300},
                    },
                )

        # Must be 200 with null prediction, never 500
        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] is None
        assert data["latency_ms"] >= 0

    @patch("app.api.routes.takeoff.get_predict_point_service")
    @patch("app.api.routes.takeoff.get_calibrated_page")
    async def test_returns_null_when_image_not_found(
        self, mock_get_page, mock_get_service, base_url, transport, mock_page, mock_document,
    ):
        """Missing image file results in null prediction."""
        from app.api.routes.takeoff import CalibratedPageData

        mock_page.image_path = "/tmp/nonexistent.png"
        mock_get_page.return_value = CalibratedPageData(page=mock_page, document=mock_document)

        with patch("pathlib.Path.exists", return_value=False):
            async with AsyncClient(transport=transport, base_url=base_url) as client:
                response = await client.post(
                    f"/api/v1/pages/{mock_page.id}/predict-next-point",
                    json={
                        "condition_id": str(uuid.uuid4()),
                        "last_geometry_type": "point",
                        "last_geometry_data": {"x": 100, "y": 100},
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] is None

    async def test_404_when_page_not_found(self, base_url, transport):
        """Non-existent page_id returns 404."""
        fake_page_id = uuid.uuid4()

        async with AsyncClient(transport=transport, base_url=base_url) as client:
            response = await client.post(
                f"/api/v1/pages/{fake_page_id}/predict-next-point",
                json={
                    "condition_id": str(uuid.uuid4()),
                    "last_geometry_type": "point",
                    "last_geometry_data": {"x": 100, "y": 100},
                },
            )

        assert response.status_code == 404

    @patch("app.api.routes.takeoff.get_calibrated_page")
    async def test_400_when_page_not_calibrated(
        self, mock_get_page, base_url, transport,
    ):
        """Uncalibrated page returns 400."""
        from fastapi import HTTPException, status

        mock_get_page.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be calibrated before AI takeoff.",
        )

        async with AsyncClient(transport=transport, base_url=base_url) as client:
            response = await client.post(
                f"/api/v1/pages/{uuid.uuid4()}/predict-next-point",
                json={
                    "condition_id": str(uuid.uuid4()),
                    "last_geometry_type": "point",
                    "last_geometry_data": {"x": 100, "y": 100},
                },
            )

        assert response.status_code == 400

    async def test_422_on_invalid_request_body(self, base_url, transport):
        """Missing required fields returns 422."""
        async with AsyncClient(transport=transport, base_url=base_url) as client:
            response = await client.post(
                f"/api/v1/pages/{uuid.uuid4()}/predict-next-point",
                json={},  # Missing required fields
            )

        assert response.status_code == 422
