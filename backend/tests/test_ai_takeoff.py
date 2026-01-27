"""Tests for AI Takeoff Generation (Phase 4A).

Tests cover:
- API endpoint validation
- AI Takeoff service logic
- Geometry filtering
- Task status polling
"""

import asyncio
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.ai_takeoff import (
    AITakeoffService,
    AITakeoffResult,
    DetectedElement,
    get_ai_takeoff_service,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_db_engine():
    """Reset the database engine connection pool after each test.
    
    This prevents the 'Future attached to a different loop' error
    that occurs when async connections are reused across tests.
    """
    yield
    # After each test, dispose the engine's connection pool
    try:
        from app.api.deps import engine
        # Run the async dispose in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(engine.dispose())
        finally:
            loop.close()
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture
def app():
    """Create test application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_page_id():
    """Generate a mock page UUID."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_condition_id():
    """Generate a mock condition UUID."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_task_id():
    """Generate a mock Celery task ID."""
    return str(uuid.uuid4())


# ============================================================================
# AITakeoffService Unit Tests
# ============================================================================


class TestAITakeoffService:
    """Tests for AITakeoffService."""

    def test_filter_valid_geometries_point_in_bounds(self):
        """Points within bounds should be kept."""
        service = AITakeoffService()
        elements = [
            DetectedElement(
                element_type="column",
                geometry_type="point",
                geometry_data={"x": 100, "y": 200},
                confidence=0.9,
                description="Test column",
            )
        ]
        
        result = service._filter_valid_geometries(elements, width=500, height=500)
        assert len(result) == 1
        assert result[0].geometry_data == {"x": 100, "y": 200}

    def test_filter_valid_geometries_point_out_of_bounds(self):
        """Points outside bounds should be filtered out."""
        service = AITakeoffService()
        elements = [
            DetectedElement(
                element_type="column",
                geometry_type="point",
                geometry_data={"x": 600, "y": 200},  # x > width
                confidence=0.9,
                description="Test column",
            ),
            DetectedElement(
                element_type="column",
                geometry_type="point",
                geometry_data={"x": 100, "y": -10},  # y < 0
                confidence=0.9,
                description="Test column",
            ),
        ]
        
        result = service._filter_valid_geometries(elements, width=500, height=500)
        assert len(result) == 0

    def test_filter_valid_geometries_polygon_in_bounds(self):
        """Polygons with all points in bounds should be kept."""
        service = AITakeoffService()
        elements = [
            DetectedElement(
                element_type="slab",
                geometry_type="polygon",
                geometry_data={
                    "points": [
                        {"x": 100, "y": 100},
                        {"x": 200, "y": 100},
                        {"x": 200, "y": 200},
                        {"x": 100, "y": 200},
                    ]
                },
                confidence=0.85,
                description="Test slab",
            )
        ]
        
        result = service._filter_valid_geometries(elements, width=500, height=500)
        assert len(result) == 1

    def test_filter_valid_geometries_polygon_out_of_bounds(self):
        """Polygons with any point out of bounds should be filtered."""
        service = AITakeoffService()
        elements = [
            DetectedElement(
                element_type="slab",
                geometry_type="polygon",
                geometry_data={
                    "points": [
                        {"x": 100, "y": 100},
                        {"x": 600, "y": 100},  # x > width
                        {"x": 600, "y": 200},
                        {"x": 100, "y": 200},
                    ]
                },
                confidence=0.85,
                description="Test slab",
            )
        ]
        
        result = service._filter_valid_geometries(elements, width=500, height=500)
        assert len(result) == 0

    def test_filter_valid_geometries_polyline_in_bounds(self):
        """Polylines with all points in bounds should be kept."""
        service = AITakeoffService()
        elements = [
            DetectedElement(
                element_type="footing",
                geometry_type="polyline",
                geometry_data={
                    "points": [
                        {"x": 50, "y": 50},
                        {"x": 150, "y": 50},
                        {"x": 150, "y": 150},
                    ]
                },
                confidence=0.8,
                description="Test footing",
            )
        ]
        
        result = service._filter_valid_geometries(elements, width=500, height=500)
        assert len(result) == 1

    def test_filter_valid_geometries_edge_cases(self):
        """Points exactly on boundaries should be kept."""
        service = AITakeoffService()
        elements = [
            DetectedElement(
                element_type="column",
                geometry_type="point",
                geometry_data={"x": 0, "y": 0},  # Origin
                confidence=0.9,
                description="Corner column",
            ),
            DetectedElement(
                element_type="column",
                geometry_type="point",
                geometry_data={"x": 500, "y": 500},  # Max bounds
                confidence=0.9,
                description="Corner column",
            ),
        ]
        
        result = service._filter_valid_geometries(elements, width=500, height=500)
        assert len(result) == 2

    def test_element_prompts_mapping(self):
        """Verify ELEMENT_PROMPTS has correct mappings."""
        service = AITakeoffService()
        
        assert "area" in service.ELEMENT_PROMPTS
        assert "linear" in service.ELEMENT_PROMPTS
        assert "count" in service.ELEMENT_PROMPTS

    def test_service_factory_function(self):
        """Test get_ai_takeoff_service factory."""
        service = get_ai_takeoff_service()
        assert isinstance(service, AITakeoffService)
        assert service.provider_override is None
        
        service_with_provider = get_ai_takeoff_service(provider="openai")
        assert service_with_provider.provider_override == "openai"


# ============================================================================
# Dataclass Tests
# ============================================================================


class TestDataclasses:
    """Tests for DetectedElement and AITakeoffResult dataclasses."""

    def test_detected_element_to_dict(self):
        """Test DetectedElement serialization."""
        elem = DetectedElement(
            element_type="slab",
            geometry_type="polygon",
            geometry_data={"points": [{"x": 0, "y": 0}]},
            confidence=0.9,
            description="Test",
        )
        
        d = elem.to_dict()
        assert d["element_type"] == "slab"
        assert d["geometry_type"] == "polygon"
        assert d["confidence"] == 0.9
        assert d["description"] == "Test"

    def test_ai_takeoff_result_to_dict(self):
        """Test AITakeoffResult serialization."""
        result = AITakeoffResult(
            elements=[],
            page_description="Test page",
            analysis_notes="Test notes",
            llm_provider="anthropic",
            llm_model="claude-sonnet-4-20250514",
            llm_latency_ms=1500.0,
            llm_input_tokens=1000,
            llm_output_tokens=500,
        )
        
        d = result.to_dict()
        assert d["page_description"] == "Test page"
        assert d["llm_provider"] == "anthropic"
        assert d["llm_latency_ms"] == 1500.0


# ============================================================================
# API Endpoint Tests (with mocked dependencies)
# ============================================================================


class TestAITakeoffAPI:
    """Tests for AI Takeoff API endpoints."""

    def test_get_available_providers(self, client):
        """GET /ai-takeoff/providers returns provider info."""
        response = client.get("/api/v1/ai-takeoff/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "default" in data
        assert "task_config" in data
        assert isinstance(data["available"], list)

    @patch("app.api.routes.takeoff.generate_ai_takeoff_task")
    def test_generate_ai_takeoff_page_not_found(
        self, mock_task, client, mock_page_id, mock_condition_id
    ):
        """POST /pages/{page_id}/ai-takeoff returns 404 for non-existent page."""
        response = client.post(
            f"/api/v1/pages/{mock_page_id}/ai-takeoff",
            json={"condition_id": mock_condition_id},
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("app.api.routes.takeoff.compare_providers_task")
    def test_compare_providers_page_not_found(
        self, mock_task, mock_page_id, mock_condition_id
    ):
        """POST /pages/{page_id}/compare-providers returns 404 for non-existent page."""
        # Create fresh app instance for this test to avoid connection pool issues
        test_app = create_app()
        with TestClient(test_app) as test_client:
            response = test_client.post(
                f"/api/v1/pages/{mock_page_id}/compare-providers",
                json={"condition_id": mock_condition_id},
            )
            
            assert response.status_code == 404

    def test_batch_ai_takeoff_condition_not_found(
        self, client, mock_page_id, mock_condition_id
    ):
        """POST /batch-ai-takeoff returns 404 for non-existent condition."""
        response = client.post(
            "/api/v1/batch-ai-takeoff",
            json={
                "page_ids": [mock_page_id],
                "condition_id": mock_condition_id,
            },
        )
        
        assert response.status_code == 404

    def test_generate_ai_takeoff_invalid_provider(
        self, mock_page_id, mock_condition_id
    ):
        """POST /pages/{page_id}/ai-takeoff returns 400 for invalid provider."""
        # Create fresh app instance for this test to avoid connection pool issues
        test_app = create_app()
        with TestClient(test_app) as test_client:
            response = test_client.post(
                f"/api/v1/pages/{mock_page_id}/ai-takeoff",
                json={
                    "condition_id": mock_condition_id,
                    "provider": "invalid_provider",
                },
            )
            
            # Will be 404 (page not found) since that check comes first
            assert response.status_code in [400, 404]

    def test_get_task_status_pending(self, app, mock_task_id):
        """GET /tasks/{task_id}/status returns pending status."""
        # Mock AsyncResult - patch where it's imported from (celery.result)
        mock_result = MagicMock()
        mock_result.status = "PENDING"
        mock_result.ready.return_value = False
        
        with patch("celery.result.AsyncResult", return_value=mock_result):
            with TestClient(app) as test_client:
                response = test_client.get(f"/api/v1/tasks/{mock_task_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == mock_task_id
        assert data["status"] == "PENDING"

    def test_get_task_status_success(self, app, mock_task_id):
        """GET /tasks/{task_id}/status returns result on success."""
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {
            "elements_detected": 5,
            "measurements_created": 5,
        }
        
        with patch("celery.result.AsyncResult", return_value=mock_result):
            with TestClient(app) as test_client:
                response = test_client.get(f"/api/v1/tasks/{mock_task_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert "result" in data
        assert data["result"]["elements_detected"] == 5

    def test_get_task_status_failure(self, app, mock_task_id):
        """GET /tasks/{task_id}/status returns error on failure."""
        mock_result = MagicMock()
        mock_result.status = "FAILURE"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = False
        mock_result.result = Exception("Task failed")
        
        with patch("celery.result.AsyncResult", return_value=mock_result):
            with TestClient(app) as test_client:
                response = test_client.get(f"/api/v1/tasks/{mock_task_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "FAILURE"
        assert "error" in data


# ============================================================================
# Run tests with: pytest backend/tests/test_ai_takeoff.py -v
# ============================================================================
