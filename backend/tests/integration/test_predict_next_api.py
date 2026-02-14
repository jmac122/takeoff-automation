"""Integration tests for the predict-next-point API endpoint."""

import uuid
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api.deps import get_db
from app.api.routes.takeoff import get_calibrated_page, CalibratedPageData


@pytest.fixture
def base_url():
    return "http://test"


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.fixture
def shared_project_id():
    """Shared project ID for page/condition consistency."""
    return uuid.uuid4()


@pytest.fixture
def mock_page():
    """Create a mock page object."""
    page = MagicMock()
    page.id = uuid.uuid4()
    page.scale_calibrated = True
    page.image_key = "projects/test/pages/fake.png"
    page.width = 2000
    page.height = 1500
    return page


@pytest.fixture
def mock_document(shared_project_id):
    """Create a mock document with shared project_id."""
    doc = MagicMock()
    doc.project_id = shared_project_id
    return doc


@pytest.fixture
def mock_condition(shared_project_id):
    """Create a mock condition with same project_id as document."""
    condition = MagicMock()
    condition.id = uuid.uuid4()
    condition.project_id = shared_project_id
    return condition


@pytest.fixture
def mock_db_session(mock_condition):
    """Create an async-compatible mock DB session that returns the mock condition."""
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_condition
    session.execute.return_value = mock_result
    return session


@pytest.fixture
def override_deps(mock_page, mock_document, mock_db_session):
    """Override FastAPI dependencies for testing."""
    page_data = CalibratedPageData(page=mock_page, document=mock_document)

    async def override_get_calibrated_page():
        return page_data

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_calibrated_page] = override_get_calibrated_page
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


class TestPredictNextPointEndpoint:
    """Tests for POST /pages/{page_id}/predict-next-point."""

    @patch("app.api.routes.takeoff.get_predict_point_service")
    @patch("app.api.routes.takeoff.get_storage_service")
    async def test_returns_200_with_prediction(
        self, mock_get_storage, mock_get_service, base_url, transport,
        mock_page, mock_condition, override_deps,
    ):
        """Successful prediction returns 200 with prediction data."""
        mock_storage = MagicMock()
        mock_storage.download_file.return_value = b"fake-png"
        mock_get_storage.return_value = mock_storage

        mock_service = MagicMock()
        mock_service.predict_next.return_value = {
            "geometry_type": "polyline",
            "geometry_data": {"points": [{"x": 100, "y": 200}, {"x": 300, "y": 200}]},
            "confidence": 0.82,
        }
        mock_get_service.return_value = mock_service

        async with AsyncClient(transport=transport, base_url=base_url) as client:
            response = await client.post(
                f"/api/v1/pages/{mock_page.id}/predict-next-point",
                json={
                    "condition_id": str(mock_condition.id),
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
    @patch("app.api.routes.takeoff.get_storage_service")
    async def test_returns_null_prediction_on_service_error(
        self, mock_get_storage, mock_get_service, base_url, transport,
        mock_page, mock_condition, override_deps,
    ):
        """Service errors result in {prediction: null}, NOT a 500."""
        mock_storage = MagicMock()
        mock_storage.download_file.return_value = b"fake-png"
        mock_get_storage.return_value = mock_storage

        mock_service = MagicMock()
        mock_service.predict_next.side_effect = RuntimeError("LLM exploded")
        mock_get_service.return_value = mock_service

        async with AsyncClient(transport=transport, base_url=base_url) as client:
            response = await client.post(
                f"/api/v1/pages/{mock_page.id}/predict-next-point",
                json={
                    "condition_id": str(mock_condition.id),
                    "last_geometry_type": "point",
                    "last_geometry_data": {"x": 500, "y": 300},
                },
            )

        # Must be 200 with null prediction, never 500
        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] is None
        assert data["latency_ms"] >= 0

    async def test_returns_null_when_no_image_key(
        self, base_url, transport, mock_page, mock_condition, override_deps,
    ):
        """Missing image key results in null prediction."""
        mock_page.image_key = None

        async with AsyncClient(transport=transport, base_url=base_url) as client:
            response = await client.post(
                f"/api/v1/pages/{mock_page.id}/predict-next-point",
                json={
                    "condition_id": str(mock_condition.id),
                    "last_geometry_type": "point",
                    "last_geometry_data": {"x": 100, "y": 100},
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] is None

    async def test_404_when_condition_not_found(
        self, base_url, transport, mock_page, mock_document, mock_db_session,
    ):
        """Non-existent condition_id returns 404."""
        page_data = CalibratedPageData(page=mock_page, document=mock_document)

        # Configure DB to return None for condition lookup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        async def override_page():
            return page_data

        async def override_db():
            yield mock_db_session

        app.dependency_overrides[get_calibrated_page] = override_page
        app.dependency_overrides[get_db] = override_db

        try:
            async with AsyncClient(transport=transport, base_url=base_url) as client:
                response = await client.post(
                    f"/api/v1/pages/{mock_page.id}/predict-next-point",
                    json={
                        "condition_id": str(uuid.uuid4()),
                        "last_geometry_type": "point",
                        "last_geometry_data": {"x": 100, "y": 100},
                    },
                )

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    async def test_400_when_condition_wrong_project(
        self, base_url, transport, mock_page, mock_document, mock_db_session,
    ):
        """Condition from different project returns 400."""
        page_data = CalibratedPageData(page=mock_page, document=mock_document)

        # Condition with different project_id
        wrong_condition = MagicMock()
        wrong_condition.id = uuid.uuid4()
        wrong_condition.project_id = uuid.uuid4()  # Different from document's project

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = wrong_condition
        mock_db_session.execute.return_value = mock_result

        async def override_page():
            return page_data

        async def override_db():
            yield mock_db_session

        app.dependency_overrides[get_calibrated_page] = override_page
        app.dependency_overrides[get_db] = override_db

        try:
            async with AsyncClient(transport=transport, base_url=base_url) as client:
                response = await client.post(
                    f"/api/v1/pages/{mock_page.id}/predict-next-point",
                    json={
                        "condition_id": str(wrong_condition.id),
                        "last_geometry_type": "point",
                        "last_geometry_data": {"x": 100, "y": 100},
                    },
                )

            assert response.status_code == 400
            assert "same project" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    async def test_422_on_invalid_request_body(self, base_url, transport, override_deps):
        """Missing required fields returns 422."""
        async with AsyncClient(transport=transport, base_url=base_url) as client:
            response = await client.post(
                f"/api/v1/pages/{uuid.uuid4()}/predict-next-point",
                json={},  # Missing required fields
            )

        assert response.status_code == 422
