"""Pytest configuration and fixtures for backend tests."""

import os
import pytest
from unittest.mock import MagicMock, patch


# Set test environment variables before importing app modules
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-characters-long")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
os.environ.setdefault("STORAGE_ENDPOINT", "localhost:9000")
os.environ.setdefault("STORAGE_ACCESS_KEY", "minioadmin")
os.environ.setdefault("STORAGE_SECRET_KEY", "minioadmin")
os.environ.setdefault("STORAGE_BUCKET", "test-bucket")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


@pytest.fixture(autouse=True)
def mock_database():
    """Mock database for unit tests."""
    with patch("app.api.deps.get_db") as mock_get_db:
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_celery_task():
    """Mock Celery task execution."""
    with patch("app.workers.celery_app.celery_app") as mock:
        mock_task = MagicMock()
        mock_task.delay.return_value = MagicMock(id="test-task-id")
        yield mock_task


@pytest.fixture
def mock_storage():
    """Mock storage service."""
    with patch("app.utils.storage.get_storage_service") as mock:
        mock_service = MagicMock()
        mock_service.download_file.return_value = b"fake-image-bytes"
        mock.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for AI tests."""
    with patch("app.services.llm_client.get_llm_client") as mock:
        mock_client = MagicMock()
        mock_client.analyze_image_json.return_value = (
            {
                "page_description": "Test page",
                "elements": [
                    {
                        "geometry_type": "polygon",
                        "points": [
                            {"x": 100, "y": 100},
                            {"x": 200, "y": 100},
                            {"x": 200, "y": 200},
                            {"x": 100, "y": 200},
                        ],
                        "confidence": 0.9,
                        "description": "Test slab",
                    }
                ],
                "analysis_notes": "Test notes",
            },
            MagicMock(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                latency_ms=1500,
                input_tokens=1000,
                output_tokens=500,
            ),
        )
        mock.return_value = mock_client
        yield mock_client
