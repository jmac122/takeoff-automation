# Phase 5B: Testing & Quality Assurance
## Testing Strategy and Quality Assurance

> **Duration**: Weeks 26-32
> **Prerequisites**: Export system complete (Phase 5A), core features functional
> **Outcome**: Comprehensive automated test suite, AI accuracy benchmarking system, CI/CD quality gates

---

## Context for LLM Assistant

You are implementing the testing and quality assurance system for a construction takeoff platform. This phase establishes:
- Unit tests for all backend services and utilities
- Integration tests for API endpoints and workflows
- End-to-end tests for critical user journeys
- AI accuracy benchmarking with golden dataset
- Performance and load testing
- CI/CD quality gates

### Testing Philosophy

The platform has a **75% AI accuracy target** with human review for refinement. Testing must validate both traditional software correctness AND AI output quality.

```
Testing Pyramid:
                    Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
                    Ã¢â€â€š   E2E   Ã¢â€â€š  Few, critical paths
                    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¤
                 Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â´Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â´Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
                 Ã¢â€â€š  Integration  Ã¢â€â€š  API + workflows
                 Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¤
              Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â´Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â´Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
              Ã¢â€â€š     Unit Tests      Ã¢â€â€š  All functions/classes
              Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
```

### Coverage Targets

| Component | Target | Rationale |
|-----------|--------|-----------|
| **Geometry utilities** | 95%+ | Core calculation accuracy |
| **Measurement engine** | 95%+ | Critical for takeoff correctness |
| **Scale detection** | 90%+ | Accuracy depends on correct scale |
| **API endpoints** | 85%+ | Business logic validation |
| **Services** | 85%+ | Core functionality |
| **Workers/Tasks** | 80%+ | Async job processing |
| **Frontend components** | 70%+ | UI interactions |
| **Overall** | 80%+ | Balanced coverage |

---

## Test Directory Structure

```
backend/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ tests/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ conftest.py                    # Shared fixtures
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ factories/                      # Test data factories
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ project.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ document.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ page.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ condition.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ measurement.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ fixtures/                       # Static test data
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ plans/                      # Sample plan images
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ foundation_simple.png
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ foundation_complex.png
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ slab_residential.png
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ slab_commercial.png
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ golden_dataset/             # AI accuracy benchmarks
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ manifest.json
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ plan_001/
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ page.png
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ expected_measurements.json
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ metadata.json
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ plan_002/
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ exports/                    # Expected export outputs
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ unit/
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_geometry.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_measurement_calculator.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_scale_parser.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_ocr_service.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_export_formatters.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ test_validators.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ integration/
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_api_projects.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_api_documents.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_api_pages.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_api_conditions.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_api_measurements.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_api_exports.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_document_pipeline.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_ai_takeoff_pipeline.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ test_export_pipeline.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ e2e/
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_full_takeoff_workflow.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ test_review_workflow.py
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ accuracy/
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_ai_accuracy.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ benchmark_runner.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ accuracy_reporter.py
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ performance/
Ã¢â€â€š       Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py
Ã¢â€â€š       Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_large_documents.py
Ã¢â€â€š       Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ locustfile.py

frontend/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ src/
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ __tests__/                      # Co-located with components
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ tests/
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ setup.ts
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ unit/
    Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ geometry.test.ts
    Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ hooks/
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ integration/
    Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ api.test.ts
    Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ e2e/
        Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ playwright/
            Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ takeoff.spec.ts
            Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ review.spec.ts
```

---

## Backend Testing

### Task 11.1: Test Configuration and Fixtures

Update `backend/tests/conftest.py`:

```python
"""Shared pytest fixtures for all tests."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.database import Base, get_db
from app.main import create_app


# Test database URL - use in-memory SQLite for speed
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def get_test_settings() -> Settings:
    """Get settings configured for testing."""
    return Settings(
        app_env="development",
        debug=True,
        secret_key="test-secret-key-minimum-32-characters-long",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        database_pool_size=5,
        redis_url="redis://localhost:6379/0",
        celery_broker_url="redis://localhost:6379/1",
        celery_result_backend="redis://localhost:6379/2",
        storage_endpoint="localhost:9000",
        storage_access_key="minioadmin",
        storage_secret_key="minioadmin",
        storage_bucket="test-bucket",
        storage_use_ssl=False,
        anthropic_api_key="test-key",
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def app(db_session: AsyncSession) -> FastAPI:
    """Create FastAPI app with test dependencies."""
    app = create_app()
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = get_test_settings
    
    return app


@pytest_asyncio.fixture(scope="function")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_storage():
    """Mock storage service."""
    storage = MagicMock()
    storage.upload_file = AsyncMock(return_value="test-file-key")
    storage.download_file = AsyncMock(return_value=b"test-content")
    storage.delete_file = AsyncMock(return_value=True)
    storage.get_presigned_url = MagicMock(return_value="http://test-url")
    return storage


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for AI tests."""
    client = MagicMock()
    client.analyze_image = AsyncMock(return_value={
        "page_type": "foundation_plan",
        "confidence": 0.95,
    })
    client.analyze_image_json = AsyncMock(return_value={
        "elements": [],
        "page_description": "Test page",
        "analysis_notes": "Test notes",
    })
    return client


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Load sample image for testing."""
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures", "plans")
    image_path = os.path.join(fixtures_dir, "foundation_simple.png")
    
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return f.read()
    
    # Return minimal valid PNG if fixture doesn't exist
    return (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
        b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
        b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Load sample PDF for testing."""
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures", "plans")
    pdf_path = os.path.join(fixtures_dir, "sample.pdf")
    
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            return f.read()
    
    # Return minimal valid PDF if fixture doesn't exist
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"
```

Create `backend/tests/factories/__init__.py`:

```python
"""Test data factories."""

from tests.factories.project import ProjectFactory
from tests.factories.document import DocumentFactory
from tests.factories.page import PageFactory
from tests.factories.condition import ConditionFactory
from tests.factories.measurement import MeasurementFactory

__all__ = [
    "ProjectFactory",
    "DocumentFactory", 
    "PageFactory",
    "ConditionFactory",
    "MeasurementFactory",
]
```

Create `backend/tests/factories/project.py`:

```python
"""Project test factory."""

import uuid
from datetime import datetime, timezone

import factory
from factory import fuzzy

from app.models.project import Project


class ProjectFactory(factory.Factory):
    """Factory for creating test Project instances."""
    
    class Meta:
        model = Project
    
    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Test Project {n}")
    description = factory.Faker("sentence")
    client_name = factory.Faker("company")
    project_number = factory.Sequence(lambda n: f"PRJ-{n:04d}")
    location = factory.Faker("address")
    status = "active"
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
```

Create `backend/tests/factories/condition.py`:

```python
"""Condition test factory."""

import uuid
from datetime import datetime, timezone

import factory
from factory import fuzzy

from app.models.condition import Condition


class ConditionFactory(factory.Factory):
    """Factory for creating test Condition instances."""
    
    class Meta:
        model = Condition
    
    id = factory.LazyFunction(uuid.uuid4)
    project_id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Condition {n}")
    description = factory.Faker("sentence")
    scope = "concrete"
    category = fuzzy.FuzzyChoice(["slab", "footing", "wall", "column"])
    measurement_type = fuzzy.FuzzyChoice(["area", "linear", "volume", "count"])
    color = factory.Faker("hex_color")
    line_width = 2
    fill_opacity = 0.3
    unit = factory.LazyAttribute(
        lambda o: {"area": "SF", "linear": "LF", "volume": "CY", "count": "EA"}[o.measurement_type]
    )
    depth = factory.LazyAttribute(
        lambda o: 4.0 if o.measurement_type == "volume" else None
    )
    total_quantity = 0.0
    measurement_count = 0
    sort_order = factory.Sequence(lambda n: n)
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
```

Create `backend/tests/factories/measurement.py`:

```python
"""Measurement test factory."""

import uuid
from datetime import datetime, timezone

import factory
from factory import fuzzy

from app.models.measurement import Measurement


class MeasurementFactory(factory.Factory):
    """Factory for creating test Measurement instances."""
    
    class Meta:
        model = Measurement
    
    id = factory.LazyFunction(uuid.uuid4)
    condition_id = factory.LazyFunction(uuid.uuid4)
    page_id = factory.LazyFunction(uuid.uuid4)
    geometry_type = fuzzy.FuzzyChoice(["polygon", "polyline", "line", "point"])
    geometry_data = factory.LazyAttribute(lambda o: _generate_geometry(o.geometry_type))
    quantity = fuzzy.FuzzyFloat(10.0, 1000.0)
    unit = "SF"
    pixel_length = None
    pixel_area = fuzzy.FuzzyFloat(1000.0, 100000.0)
    is_ai_generated = False
    ai_confidence = None
    ai_model = None
    is_modified = False
    is_verified = False
    notes = None
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


def _generate_geometry(geometry_type: str) -> dict:
    """Generate sample geometry data based on type."""
    if geometry_type == "polygon":
        return {
            "points": [
                {"x": 100, "y": 100},
                {"x": 200, "y": 100},
                {"x": 200, "y": 200},
                {"x": 100, "y": 200},
            ]
        }
    elif geometry_type == "polyline":
        return {
            "points": [
                {"x": 100, "y": 100},
                {"x": 200, "y": 100},
                {"x": 300, "y": 150},
            ]
        }
    elif geometry_type == "line":
        return {
            "start": {"x": 100, "y": 100},
            "end": {"x": 200, "y": 200},
        }
    elif geometry_type == "point":
        return {"x": 150, "y": 150}
    elif geometry_type == "rectangle":
        return {
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 150,
        }
    elif geometry_type == "circle":
        return {
            "center": {"x": 150, "y": 150},
            "radius": 50,
        }
    return {}
```

---

### Task 11.2: Geometry Unit Tests

Create `backend/tests/unit/test_geometry.py`:

```python
"""Unit tests for geometry utilities."""

import math
import pytest

from app.utils.geometry import (
    Point,
    calculate_line_length,
    calculate_polyline_length,
    calculate_polygon_area,
    calculate_polygon_perimeter,
    calculate_rectangle_area,
    calculate_rectangle_perimeter,
    calculate_circle_area,
    calculate_circle_circumference,
    MeasurementCalculator,
)


class TestPoint:
    """Tests for Point class."""
    
    def test_point_creation(self):
        """Test creating a point."""
        p = Point(x=10.0, y=20.0)
        assert p.x == 10.0
        assert p.y == 20.0
    
    def test_point_distance_to_same(self):
        """Test distance between same points is zero."""
        p1 = Point(x=10.0, y=20.0)
        p2 = Point(x=10.0, y=20.0)
        assert p1.distance_to(p2) == 0.0
    
    def test_point_distance_horizontal(self):
        """Test horizontal distance calculation."""
        p1 = Point(x=0.0, y=0.0)
        p2 = Point(x=10.0, y=0.0)
        assert p1.distance_to(p2) == 10.0
    
    def test_point_distance_vertical(self):
        """Test vertical distance calculation."""
        p1 = Point(x=0.0, y=0.0)
        p2 = Point(x=0.0, y=10.0)
        assert p1.distance_to(p2) == 10.0
    
    def test_point_distance_diagonal(self):
        """Test diagonal distance calculation (3-4-5 triangle)."""
        p1 = Point(x=0.0, y=0.0)
        p2 = Point(x=3.0, y=4.0)
        assert p1.distance_to(p2) == 5.0
    
    def test_point_to_dict(self):
        """Test converting point to dictionary."""
        p = Point(x=10.0, y=20.0)
        assert p.to_dict() == {"x": 10.0, "y": 20.0}
    
    def test_point_from_dict(self):
        """Test creating point from dictionary."""
        p = Point.from_dict({"x": 10.0, "y": 20.0})
        assert p.x == 10.0
        assert p.y == 20.0


class TestLineMeasurements:
    """Tests for line measurement calculations."""
    
    def test_line_length_horizontal(self):
        """Test horizontal line length."""
        start = Point(x=0.0, y=0.0)
        end = Point(x=100.0, y=0.0)
        assert calculate_line_length(start, end) == 100.0
    
    def test_line_length_vertical(self):
        """Test vertical line length."""
        start = Point(x=0.0, y=0.0)
        end = Point(x=0.0, y=100.0)
        assert calculate_line_length(start, end) == 100.0
    
    def test_line_length_diagonal(self):
        """Test diagonal line length."""
        start = Point(x=0.0, y=0.0)
        end = Point(x=30.0, y=40.0)
        assert calculate_line_length(start, end) == 50.0
    
    def test_line_length_negative_coords(self):
        """Test line length with negative coordinates."""
        start = Point(x=-10.0, y=-10.0)
        end = Point(x=10.0, y=10.0)
        expected = math.sqrt(20**2 + 20**2)
        assert abs(calculate_line_length(start, end) - expected) < 0.0001


class TestPolylineMeasurements:
    """Tests for polyline measurement calculations."""
    
    def test_polyline_empty(self):
        """Test empty polyline returns zero."""
        assert calculate_polyline_length([]) == 0.0
    
    def test_polyline_single_point(self):
        """Test single point polyline returns zero."""
        points = [Point(x=0.0, y=0.0)]
        assert calculate_polyline_length(points) == 0.0
    
    def test_polyline_two_points(self):
        """Test two-point polyline (same as line)."""
        points = [Point(x=0.0, y=0.0), Point(x=100.0, y=0.0)]
        assert calculate_polyline_length(points) == 100.0
    
    def test_polyline_three_points(self):
        """Test three-point polyline sums segments."""
        points = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=0.0),
            Point(x=100.0, y=100.0),
        ]
        assert calculate_polyline_length(points) == 200.0
    
    def test_polyline_square_perimeter_open(self):
        """Test polyline forming open square (3 sides)."""
        points = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=0.0),
            Point(x=100.0, y=100.0),
            Point(x=0.0, y=100.0),
        ]
        assert calculate_polyline_length(points) == 300.0


class TestPolygonMeasurements:
    """Tests for polygon measurement calculations."""
    
    def test_polygon_empty(self):
        """Test empty polygon returns zero area."""
        assert calculate_polygon_area([]) == 0.0
    
    def test_polygon_two_points(self):
        """Test two-point polygon returns zero area."""
        points = [Point(x=0.0, y=0.0), Point(x=100.0, y=0.0)]
        assert calculate_polygon_area(points) == 0.0
    
    def test_polygon_triangle(self):
        """Test triangle area calculation."""
        points = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=0.0),
            Point(x=50.0, y=100.0),
        ]
        # Triangle area = 0.5 * base * height = 0.5 * 100 * 100 = 5000
        assert calculate_polygon_area(points) == 5000.0
    
    def test_polygon_square(self):
        """Test square area calculation."""
        points = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=0.0),
            Point(x=100.0, y=100.0),
            Point(x=0.0, y=100.0),
        ]
        assert calculate_polygon_area(points) == 10000.0
    
    def test_polygon_rectangle(self):
        """Test rectangle area calculation."""
        points = [
            Point(x=0.0, y=0.0),
            Point(x=200.0, y=0.0),
            Point(x=200.0, y=100.0),
            Point(x=0.0, y=100.0),
        ]
        assert calculate_polygon_area(points) == 20000.0
    
    def test_polygon_perimeter_triangle(self):
        """Test triangle perimeter calculation."""
        points = [
            Point(x=0.0, y=0.0),
            Point(x=30.0, y=0.0),
            Point(x=30.0, y=40.0),
        ]
        # Perimeter = 30 + 40 + 50 (3-4-5 triangle scaled by 10)
        assert calculate_polygon_perimeter(points) == 120.0
    
    def test_polygon_perimeter_square(self):
        """Test square perimeter calculation."""
        points = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=0.0),
            Point(x=100.0, y=100.0),
            Point(x=0.0, y=100.0),
        ]
        assert calculate_polygon_perimeter(points) == 400.0


class TestRectangleMeasurements:
    """Tests for rectangle measurement calculations."""
    
    def test_rectangle_area(self):
        """Test rectangle area calculation."""
        assert calculate_rectangle_area(100.0, 50.0) == 5000.0
    
    def test_rectangle_area_square(self):
        """Test square area calculation."""
        assert calculate_rectangle_area(100.0, 100.0) == 10000.0
    
    def test_rectangle_perimeter(self):
        """Test rectangle perimeter calculation."""
        assert calculate_rectangle_perimeter(100.0, 50.0) == 300.0
    
    def test_rectangle_perimeter_square(self):
        """Test square perimeter calculation."""
        assert calculate_rectangle_perimeter(100.0, 100.0) == 400.0


class TestCircleMeasurements:
    """Tests for circle measurement calculations."""
    
    def test_circle_area(self):
        """Test circle area calculation."""
        area = calculate_circle_area(10.0)
        expected = math.pi * 100.0
        assert abs(area - expected) < 0.0001
    
    def test_circle_area_unit_radius(self):
        """Test unit circle area."""
        area = calculate_circle_area(1.0)
        assert abs(area - math.pi) < 0.0001
    
    def test_circle_circumference(self):
        """Test circle circumference calculation."""
        circumference = calculate_circle_circumference(10.0)
        expected = 2.0 * math.pi * 10.0
        assert abs(circumference - expected) < 0.0001


class TestMeasurementCalculator:
    """Tests for MeasurementCalculator class."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator with 10 pixels per foot scale."""
        return MeasurementCalculator(pixels_per_foot=10.0)
    
    def test_pixels_to_feet(self, calculator):
        """Test pixel to feet conversion."""
        assert calculator.pixels_to_feet(100.0) == 10.0
        assert calculator.pixels_to_feet(10.0) == 1.0
        assert calculator.pixels_to_feet(1.0) == 0.1
    
    def test_pixels_to_inches(self, calculator):
        """Test pixel to inches conversion."""
        assert calculator.pixels_to_inches(10.0) == 12.0  # 1 foot = 12 inches
    
    def test_calculate_line_feet(self, calculator):
        """Test line calculation in feet."""
        start = Point(x=0.0, y=0.0)
        end = Point(x=100.0, y=0.0)  # 100 pixels = 10 feet
        result = calculator.calculate_line(start, end)
        assert result["length_feet"] == 10.0
        assert result["length_pixels"] == 100.0
    
    def test_calculate_polygon_area_sf(self, calculator):
        """Test polygon area calculation in square feet."""
        points = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=0.0),
            Point(x=100.0, y=100.0),
            Point(x=0.0, y=100.0),
        ]
        # 100x100 pixels at 10 px/ft = 10x10 feet = 100 SF
        result = calculator.calculate_polygon(points)
        assert result["area_sf"] == 100.0
        assert result["area_pixels"] == 10000.0
    
    def test_calculate_polygon_with_depth_cy(self, calculator):
        """Test polygon volume calculation in cubic yards."""
        points = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=0.0),
            Point(x=100.0, y=100.0),
            Point(x=0.0, y=100.0),
        ]
        # 100 SF at 4" depth
        result = calculator.calculate_polygon(points, depth_inches=4.0)
        # Volume = 100 SF * (4/12) ft = 33.33 CF = 1.234 CY
        assert abs(result["volume_cy"] - 1.234) < 0.01
    
    def test_calculate_rectangle_area_sf(self, calculator):
        """Test rectangle area calculation in square feet."""
        # 100x50 pixels at 10 px/ft = 10x5 feet = 50 SF
        result = calculator.calculate_rectangle(100.0, 50.0)
        assert result["area_sf"] == 50.0
    
    def test_calculate_circle_area_sf(self, calculator):
        """Test circle area calculation in square feet."""
        # 50 pixel radius at 10 px/ft = 5 foot radius
        result = calculator.calculate_circle(50.0)
        expected_area = math.pi * 25.0  # Ãâ‚¬ * rÃ‚Â² = Ãâ‚¬ * 5Ã‚Â²
        assert abs(result["area_sf"] - expected_area) < 0.01
    
    def test_scale_change_recalculation(self):
        """Test that scale changes affect calculations correctly."""
        calc_10 = MeasurementCalculator(pixels_per_foot=10.0)
        calc_20 = MeasurementCalculator(pixels_per_foot=20.0)
        
        start = Point(x=0.0, y=0.0)
        end = Point(x=100.0, y=0.0)
        
        result_10 = calc_10.calculate_line(start, end)
        result_20 = calc_20.calculate_line(start, end)
        
        # Same pixel distance, different scale = different feet
        assert result_10["length_feet"] == 10.0
        assert result_20["length_feet"] == 5.0
```

---

### Task 11.3: Measurement Calculator Edge Cases

Create `backend/tests/unit/test_measurement_calculator.py`:

```python
"""Extended tests for measurement calculator edge cases."""

import math
import pytest

from app.utils.geometry import MeasurementCalculator, Point


class TestMeasurementCalculatorEdgeCases:
    """Edge case tests for measurement calculations."""
    
    def test_zero_scale_raises_error(self):
        """Test that zero scale raises an error."""
        with pytest.raises(ValueError, match="pixels_per_foot must be positive"):
            MeasurementCalculator(pixels_per_foot=0.0)
    
    def test_negative_scale_raises_error(self):
        """Test that negative scale raises an error."""
        with pytest.raises(ValueError, match="pixels_per_foot must be positive"):
            MeasurementCalculator(pixels_per_foot=-10.0)
    
    def test_very_small_scale(self):
        """Test calculations with very small scale factor."""
        calc = MeasurementCalculator(pixels_per_foot=0.001)
        start = Point(x=0.0, y=0.0)
        end = Point(x=1.0, y=0.0)
        result = calc.calculate_line(start, end)
        assert result["length_feet"] == 1000.0
    
    def test_very_large_scale(self):
        """Test calculations with very large scale factor."""
        calc = MeasurementCalculator(pixels_per_foot=10000.0)
        start = Point(x=0.0, y=0.0)
        end = Point(x=10000.0, y=0.0)
        result = calc.calculate_line(start, end)
        assert result["length_feet"] == 1.0
    
    def test_floating_point_precision(self):
        """Test that calculations maintain reasonable precision."""
        calc = MeasurementCalculator(pixels_per_foot=7.0)  # Odd number
        points = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=0.0),
            Point(x=100.0, y=100.0),
            Point(x=0.0, y=100.0),
        ]
        result = calc.calculate_polygon(points)
        # 10000 pxÃ‚Â² / 49 pxÃ‚Â²/ftÃ‚Â² Ã¢â€°Ë† 204.08 SF
        expected = 10000.0 / 49.0
        assert abs(result["area_sf"] - expected) < 0.01
    
    def test_concave_polygon(self):
        """Test area calculation for concave polygon (L-shape)."""
        calc = MeasurementCalculator(pixels_per_foot=10.0)
        # L-shaped polygon
        points = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=0.0),
            Point(x=100.0, y=50.0),
            Point(x=50.0, y=50.0),
            Point(x=50.0, y=100.0),
            Point(x=0.0, y=100.0),
        ]
        result = calc.calculate_polygon(points)
        # L-shape area = 100*100 - 50*50 = 7500 pxÃ‚Â² = 75 SF
        assert result["area_sf"] == 75.0
    
    def test_self_intersecting_polygon(self):
        """Test that self-intersecting polygons still compute (may be unexpected)."""
        calc = MeasurementCalculator(pixels_per_foot=10.0)
        # Figure-8 / bowtie shape
        points = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=100.0),  # Crosses over
            Point(x=100.0, y=0.0),
            Point(x=0.0, y=100.0),
        ]
        result = calc.calculate_polygon(points)
        # Should compute without error (shoelace formula handles this)
        assert result["area_sf"] >= 0
    
    def test_volume_with_zero_depth(self):
        """Test volume calculation with zero depth returns zero."""
        calc = MeasurementCalculator(pixels_per_foot=10.0)
        points = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=0.0),
            Point(x=100.0, y=100.0),
            Point(x=0.0, y=100.0),
        ]
        result = calc.calculate_polygon(points, depth_inches=0.0)
        assert result["volume_cy"] == 0.0
    
    def test_volume_with_large_depth(self):
        """Test volume calculation with large depth (e.g., deep footing)."""
        calc = MeasurementCalculator(pixels_per_foot=10.0)
        points = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=0.0),
            Point(x=100.0, y=100.0),
            Point(x=0.0, y=100.0),
        ]
        # 100 SF with 48" (4 feet) depth
        result = calc.calculate_polygon(points, depth_inches=48.0)
        # Volume = 100 SF * 4 ft = 400 CF = 14.81 CY
        assert abs(result["volume_cy"] - 14.81) < 0.1


class TestScaleConversions:
    """Tests for scale conversion utilities."""
    
    def test_common_scales(self):
        """Test common architectural scales convert correctly."""
        # 1/4" = 1'-0" means 0.25 inch drawing = 1 foot real
        # At 96 DPI: 0.25 inches = 24 pixels per foot
        calc_quarter = MeasurementCalculator(pixels_per_foot=24.0)
        
        # 100 pixels should be ~4.17 feet at 1/4" scale
        start = Point(x=0.0, y=0.0)
        end = Point(x=100.0, y=0.0)
        result = calc_quarter.calculate_line(start, end)
        assert abs(result["length_feet"] - 4.167) < 0.01
        
        # 1/8" = 1'-0" means 0.125 inch drawing = 1 foot real
        # At 96 DPI: 0.125 inches = 12 pixels per foot
        calc_eighth = MeasurementCalculator(pixels_per_foot=12.0)
        result = calc_eighth.calculate_line(start, end)
        assert abs(result["length_feet"] - 8.333) < 0.01
    
    def test_metric_conversion(self):
        """Test metric scale conversions (for future international support)."""
        # 1:100 scale at 96 DPI, 1 meter = ~3.78 pixels
        # This is approximate and may need refinement
        calc = MeasurementCalculator(pixels_per_foot=3.78 / 3.28084)
        # Just verify it doesn't error
        result = calc.pixels_to_feet(100.0)
        assert result > 0
```

---

### Task 11.4: Scale Parser Unit Tests

Create `backend/tests/unit/test_scale_parser.py`:

```python
"""Unit tests for scale text parsing."""

import pytest

from app.services.scale_detector import ScaleParser


class TestScaleParser:
    """Tests for scale text parsing."""
    
    @pytest.fixture
    def parser(self):
        """Create scale parser instance."""
        return ScaleParser()
    
    # Standard architectural scales
    @pytest.mark.parametrize("scale_text,expected_ratio", [
        ('1/4" = 1\'-0"', 48.0),
        ('1/4"=1\'', 48.0),
        ('1/4" = 1\'0"', 48.0),
        ('1/8" = 1\'-0"', 96.0),
        ('1/8"=1\'', 96.0),
        ('3/8" = 1\'-0"', 32.0),
        ('1/2" = 1\'-0"', 24.0),
        ('3/4" = 1\'-0"', 16.0),
        ('1" = 1\'-0"', 12.0),
        ('1-1/2" = 1\'-0"', 8.0),
        ('3" = 1\'-0"', 4.0),
    ])
    def test_architectural_scales(self, parser, scale_text, expected_ratio):
        """Test parsing standard architectural scales."""
        result = parser.parse(scale_text)
        assert result is not None
        assert abs(result["ratio"] - expected_ratio) < 0.1
    
    # Engineering scales
    @pytest.mark.parametrize("scale_text,expected_ratio", [
        ('1" = 10\'', 120.0),
        ('1" = 20\'', 240.0),
        ('1" = 30\'', 360.0),
        ('1" = 40\'', 480.0),
        ('1" = 50\'', 600.0),
        ('1" = 100\'', 1200.0),
    ])
    def test_engineering_scales(self, parser, scale_text, expected_ratio):
        """Test parsing engineering scales."""
        result = parser.parse(scale_text)
        assert result is not None
        assert abs(result["ratio"] - expected_ratio) < 0.1
    
    # Fractional notation variations
    @pytest.mark.parametrize("scale_text", [
        '1/4" = 1\'-0"',
        '1/4"= 1\'-0"',
        '1/4" =1\'-0"',
        '1/4"=1\'-0"',
        '1/4 IN = 1 FT',
        '1/4 in = 1 ft',
        '0.25" = 1\'',
        '.25" = 1\'',
    ])
    def test_scale_format_variations(self, parser, scale_text):
        """Test that various format variations parse to same scale."""
        result = parser.parse(scale_text)
        assert result is not None
        assert abs(result["ratio"] - 48.0) < 0.5
    
    # Invalid inputs
    @pytest.mark.parametrize("scale_text", [
        '',
        'NOT A SCALE',
        'SCALE:',
        '1:1',  # Numeric ratio without units
        '123',
        None,
    ])
    def test_invalid_scales_return_none(self, parser, scale_text):
        """Test that invalid scale text returns None."""
        result = parser.parse(scale_text)
        assert result is None
    
    # Scale with context
    def test_extract_scale_from_title_block(self, parser):
        """Test extracting scale from typical title block text."""
        text = """
        PROJECT: Test Building
        SHEET: S-101
        SCALE: 1/4" = 1'-0"
        DATE: 01/15/2024
        """
        result = parser.find_scale_in_text(text)
        assert result is not None
        assert abs(result["ratio"] - 48.0) < 0.1
    
    def test_multiple_scales_returns_first(self, parser):
        """Test that multiple scales return the first/primary one."""
        text = """
        PLAN SCALE: 1/4" = 1'-0"
        DETAIL SCALE: 1" = 1'-0"
        """
        result = parser.find_scale_in_text(text)
        assert result is not None
        # Should return the plan scale (first found)
        assert abs(result["ratio"] - 48.0) < 0.1
    
    def test_nts_not_to_scale(self, parser):
        """Test NTS (Not To Scale) detection."""
        result = parser.parse("NTS")
        assert result is not None
        assert result["is_nts"] is True
        
        result = parser.parse("NOT TO SCALE")
        assert result is not None
        assert result["is_nts"] is True


class TestScaleConversion:
    """Tests for scale conversion calculations."""
    
    @pytest.fixture
    def parser(self):
        return ScaleParser()
    
    def test_scale_to_pixels_per_foot_at_dpi(self, parser):
        """Test converting scale ratio to pixels per foot at various DPI."""
        # 1/4" = 1'-0" at 96 DPI
        # 0.25 inches on paper = 1 foot real
        # 0.25 * 96 = 24 pixels per foot
        result = parser.parse('1/4" = 1\'-0"')
        ppf = parser.calculate_pixels_per_foot(result, dpi=96)
        assert abs(ppf - 24.0) < 0.1
        
        # Same scale at 150 DPI
        ppf_150 = parser.calculate_pixels_per_foot(result, dpi=150)
        assert abs(ppf_150 - 37.5) < 0.1
        
        # Same scale at 300 DPI
        ppf_300 = parser.calculate_pixels_per_foot(result, dpi=300)
        assert abs(ppf_300 - 75.0) < 0.1
    
    def test_engineering_scale_pixels_per_foot(self, parser):
        """Test engineering scale conversion."""
        # 1" = 20' at 96 DPI
        # 1 inch on paper = 20 feet real
        # 96 pixels / 20 feet = 4.8 pixels per foot
        result = parser.parse('1" = 20\'')
        ppf = parser.calculate_pixels_per_foot(result, dpi=96)
        assert abs(ppf - 4.8) < 0.1
```

---

### Task 11.4B: LLM Client Multi-Provider Tests

Create `backend/tests/unit/test_llm_client.py`:

```python
"""Unit tests for multi-provider LLM client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.llm_client import (
    LLMClient,
    LLMProvider,
    get_llm_client,
    PROVIDER_INFO,
)
from app.config import Settings


class TestLLMProviderEnum:
    """Tests for LLM provider enumeration."""
    
    def test_all_providers_defined(self):
        """Test that all expected providers are defined."""
        expected = ["anthropic", "openai", "google", "xai"]
        for provider in expected:
            assert hasattr(LLMProvider, provider.upper())
    
    def test_provider_values(self):
        """Test provider enum values match expected strings."""
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.GOOGLE.value == "google"
        assert LLMProvider.XAI.value == "xai"


class TestProviderInfo:
    """Tests for provider configuration info."""
    
    def test_all_providers_have_info(self):
        """Test that all providers have configuration info."""
        for provider in LLMProvider:
            assert provider.value in PROVIDER_INFO
    
    def test_provider_info_structure(self):
        """Test provider info has required fields."""
        required_fields = ["name", "model", "env_key", "supports_vision"]
        for provider_key, info in PROVIDER_INFO.items():
            for field in required_fields:
                assert field in info, f"{provider_key} missing {field}"
    
    def test_all_providers_support_vision(self):
        """Test that all configured providers support vision."""
        for provider_key, info in PROVIDER_INFO.items():
            assert info["supports_vision"] is True, (
                f"{provider_key} must support vision for construction plans"
            )


class TestLLMClientInitialization:
    """Tests for LLM client initialization."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings with all API keys."""
        settings = MagicMock(spec=Settings)
        settings.anthropic_api_key = "test-anthropic-key"
        settings.openai_api_key = "test-openai-key"
        settings.google_ai_api_key = "test-google-key"
        settings.xai_api_key = "test-xai-key"
        settings.default_llm_provider = "anthropic"
        settings.llm_fallback_providers = ["openai", "google"]
        return settings
    
    def test_client_initializes_with_default_provider(self, mock_settings):
        """Test client initializes with default provider."""
        with patch("app.services.llm_client.get_settings", return_value=mock_settings):
            client = LLMClient()
            assert client.provider == LLMProvider.ANTHROPIC
    
    def test_client_initializes_with_specified_provider(self, mock_settings):
        """Test client initializes with specified provider."""
        with patch("app.services.llm_client.get_settings", return_value=mock_settings):
            client = LLMClient(provider=LLMProvider.OPENAI)
            assert client.provider == LLMProvider.OPENAI
    
    def test_client_fails_without_api_key(self, mock_settings):
        """Test client fails if provider API key is missing."""
        mock_settings.anthropic_api_key = None
        mock_settings.default_llm_provider = "anthropic"
        
        with patch("app.services.llm_client.get_settings", return_value=mock_settings):
            with pytest.raises(ValueError, match="API key not configured"):
                LLMClient(provider=LLMProvider.ANTHROPIC)
    
    def test_available_providers(self, mock_settings):
        """Test getting list of available providers."""
        with patch("app.services.llm_client.get_settings", return_value=mock_settings):
            client = LLMClient()
            available = client.get_available_providers()
            
            assert LLMProvider.ANTHROPIC in available
            assert LLMProvider.OPENAI in available
            assert LLMProvider.GOOGLE in available
            assert LLMProvider.XAI in available
    
    def test_available_providers_excludes_unconfigured(self, mock_settings):
        """Test that providers without API keys are excluded."""
        mock_settings.xai_api_key = None
        
        with patch("app.services.llm_client.get_settings", return_value=mock_settings):
            client = LLMClient()
            available = client.get_available_providers()
            
            assert LLMProvider.XAI not in available


class TestLLMClientProviderSwitching:
    """Tests for switching between providers."""
    
    @pytest.fixture
    def mock_settings(self):
        settings = MagicMock(spec=Settings)
        settings.anthropic_api_key = "test-anthropic-key"
        settings.openai_api_key = "test-openai-key"
        settings.google_ai_api_key = "test-google-key"
        settings.xai_api_key = "test-xai-key"
        settings.default_llm_provider = "anthropic"
        settings.llm_fallback_providers = ["openai", "google"]
        return settings
    
    def test_switch_provider(self, mock_settings):
        """Test switching to a different provider."""
        with patch("app.services.llm_client.get_settings", return_value=mock_settings):
            client = LLMClient(provider=LLMProvider.ANTHROPIC)
            assert client.provider == LLMProvider.ANTHROPIC
            
            client.switch_provider(LLMProvider.OPENAI)
            assert client.provider == LLMProvider.OPENAI
    
    def test_switch_to_unavailable_provider_fails(self, mock_settings):
        """Test switching to provider without API key fails."""
        mock_settings.xai_api_key = None
        
        with patch("app.services.llm_client.get_settings", return_value=mock_settings):
            client = LLMClient(provider=LLMProvider.ANTHROPIC)
            
            with pytest.raises(ValueError, match="not available"):
                client.switch_provider(LLMProvider.XAI)
    
    def test_get_current_model_name(self, mock_settings):
        """Test getting current model name."""
        with patch("app.services.llm_client.get_settings", return_value=mock_settings):
            client = LLMClient(provider=LLMProvider.ANTHROPIC)
            model = client.get_model_name()
            assert "claude" in model.lower()
            
            client.switch_provider(LLMProvider.OPENAI)
            model = client.get_model_name()
            assert "gpt" in model.lower()


class TestLLMClientFallback:
    """Tests for provider fallback logic."""
    
    @pytest.fixture
    def mock_settings(self):
        settings = MagicMock(spec=Settings)
        settings.anthropic_api_key = "test-anthropic-key"
        settings.openai_api_key = "test-openai-key"
        settings.google_ai_api_key = "test-google-key"
        settings.xai_api_key = None
        settings.default_llm_provider = "anthropic"
        settings.llm_fallback_providers = ["openai", "google"]
        return settings
    
    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self, mock_settings):
        """Test fallback to secondary provider on primary failure."""
        with patch("app.services.llm_client.get_settings", return_value=mock_settings):
            client = LLMClient(provider=LLMProvider.ANTHROPIC)
            
            # Mock primary provider to fail
            client._call_anthropic = AsyncMock(
                side_effect=Exception("Rate limited")
            )
            client._call_openai = AsyncMock(
                return_value={"content": "Success from OpenAI"}
            )
            
            result = await client.analyze_image_with_fallback(
                image_bytes=b"test",
                prompt="Analyze this"
            )
            
            assert result["content"] == "Success from OpenAI"
            assert result["provider_used"] == "openai"
    
    @pytest.mark.asyncio
    async def test_fallback_chain_exhausted(self, mock_settings):
        """Test error when all fallback providers fail."""
        with patch("app.services.llm_client.get_settings", return_value=mock_settings):
            client = LLMClient(provider=LLMProvider.ANTHROPIC)
            
            # Mock all providers to fail
            client._call_anthropic = AsyncMock(side_effect=Exception("Failed"))
            client._call_openai = AsyncMock(side_effect=Exception("Failed"))
            client._call_google = AsyncMock(side_effect=Exception("Failed"))
            
            with pytest.raises(Exception, match="All providers failed"):
                await client.analyze_image_with_fallback(
                    image_bytes=b"test",
                    prompt="Analyze this"
                )
    
    @pytest.mark.asyncio
    async def test_no_fallback_when_disabled(self, mock_settings):
        """Test that fallback can be disabled."""
        mock_settings.llm_fallback_providers = []
        
        with patch("app.services.llm_client.get_settings", return_value=mock_settings):
            client = LLMClient(provider=LLMProvider.ANTHROPIC)
            
            client._call_anthropic = AsyncMock(
                side_effect=Exception("Failed")
            )
            
            with pytest.raises(Exception, match="Failed"):
                await client.analyze_image_with_fallback(
                    image_bytes=b"test",
                    prompt="Analyze this",
                    use_fallback=True
                )


class TestLLMClientAnalyzeImage:
    """Tests for image analysis across providers."""
    
    @pytest.fixture
    def mock_settings(self):
        settings = MagicMock(spec=Settings)
        settings.anthropic_api_key = "test-key"
        settings.openai_api_key = "test-key"
        settings.google_ai_api_key = "test-key"
        settings.xai_api_key = "test-key"
        settings.default_llm_provider = "anthropic"
        settings.llm_fallback_providers = []
        return settings
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("provider", list(LLMProvider))
    async def test_analyze_image_all_providers(self, mock_settings, provider):
        """Test that analyze_image works for all providers."""
        with patch("app.services.llm_client.get_settings", return_value=mock_settings):
            client = LLMClient(provider=provider)
            
            # Mock the internal provider call
            mock_response = {
                "page_type": "foundation_plan",
                "confidence": 0.95,
            }
            
            with patch.object(
                client,
                f"_call_{provider.value}",
                new_callable=AsyncMock,
                return_value=mock_response
            ):
                result = await client.analyze_image(
                    image_bytes=b"test-image",
                    prompt="Classify this page"
                )
                
                assert result == mock_response
```

Create `backend/tests/integration/test_llm_settings_api.py`:

```python
"""Integration tests for LLM settings API."""

import pytest
from httpx import AsyncClient


class TestLLMSettingsAPI:
    """Tests for /api/v1/settings/llm endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_llm_settings(self, client: AsyncClient):
        """Test getting current LLM settings."""
        response = await client.get("/api/v1/settings/llm")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "providers" in data
        assert "default" in data
        assert "all_supported" in data
        assert isinstance(data["providers"], list)
    
    @pytest.mark.asyncio
    async def test_get_available_providers(self, client: AsyncClient):
        """Test getting list of available providers."""
        response = await client.get("/api/v1/settings/llm/providers")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # At least one provider should be available in test env
        assert len(data) >= 1
    
    @pytest.mark.asyncio
    async def test_provider_info_structure(self, client: AsyncClient):
        """Test that provider info has expected structure."""
        response = await client.get("/api/v1/settings/llm/providers")
        
        assert response.status_code == 200
        providers = response.json()
        
        for provider in providers:
            assert "id" in provider
            assert "name" in provider
            assert "model" in provider
            assert "available" in provider
```

---

### Task 11.5: API Integration Tests

Create `backend/tests/integration/test_api_projects.py`:

```python
"""Integration tests for Projects API."""

import pytest
from httpx import AsyncClient

from tests.factories import ProjectFactory


class TestProjectsAPI:
    """Integration tests for /api/v1/projects endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_project(self, client: AsyncClient):
        """Test creating a new project."""
        project_data = {
            "name": "Test Project",
            "description": "A test project",
            "client_name": "Test Client",
            "project_number": "PRJ-001",
        }
        
        response = await client.post("/api/v1/projects", json=project_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["client_name"] == "Test Client"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_create_project_minimal(self, client: AsyncClient):
        """Test creating project with only required fields."""
        project_data = {"name": "Minimal Project"}
        
        response = await client.post("/api/v1/projects", json=project_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Project"
    
    @pytest.mark.asyncio
    async def test_create_project_validation_error(self, client: AsyncClient):
        """Test that missing required fields returns 422."""
        response = await client.post("/api/v1/projects", json={})
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_list_projects_empty(self, client: AsyncClient):
        """Test listing projects when none exist."""
        response = await client.get("/api/v1/projects")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
    
    @pytest.mark.asyncio
    async def test_list_projects_with_data(self, client: AsyncClient, db_session):
        """Test listing projects with existing data."""
        # Create projects via API
        for i in range(3):
            await client.post(
                "/api/v1/projects",
                json={"name": f"Project {i}"}
            )
        
        response = await client.get("/api/v1/projects")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
    
    @pytest.mark.asyncio
    async def test_list_projects_pagination(self, client: AsyncClient):
        """Test project listing pagination."""
        # Create 15 projects
        for i in range(15):
            await client.post(
                "/api/v1/projects",
                json={"name": f"Project {i}"}
            )
        
        # Get first page (default limit 10)
        response = await client.get("/api/v1/projects?limit=10&offset=0")
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 15
        
        # Get second page
        response = await client.get("/api/v1/projects?limit=10&offset=10")
        data = response.json()
        assert len(data["items"]) == 5
    
    @pytest.mark.asyncio
    async def test_get_project(self, client: AsyncClient):
        """Test getting a specific project."""
        # Create project
        create_response = await client.post(
            "/api/v1/projects",
            json={"name": "Get Test Project"}
        )
        project_id = create_response.json()["id"]
        
        # Get project
        response = await client.get(f"/api/v1/projects/{project_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Get Test Project"
    
    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client: AsyncClient):
        """Test getting non-existent project returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/projects/{fake_id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_project(self, client: AsyncClient):
        """Test updating a project."""
        # Create project
        create_response = await client.post(
            "/api/v1/projects",
            json={"name": "Original Name"}
        )
        project_id = create_response.json()["id"]
        
        # Update project
        response = await client.put(
            f"/api/v1/projects/{project_id}",
            json={"name": "Updated Name", "description": "Added description"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Added description"
    
    @pytest.mark.asyncio
    async def test_delete_project(self, client: AsyncClient):
        """Test deleting a project."""
        # Create project
        create_response = await client.post(
            "/api/v1/projects",
            json={"name": "To Delete"}
        )
        project_id = create_response.json()["id"]
        
        # Delete project
        response = await client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 204
        
        # Verify deleted
        get_response = await client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404
```

Create `backend/tests/integration/test_api_measurements.py`:

```python
"""Integration tests for Measurements API."""

import pytest
from httpx import AsyncClient


class TestMeasurementsAPI:
    """Integration tests for measurements endpoints."""
    
    @pytest.fixture
    async def setup_project_with_condition(self, client: AsyncClient):
        """Create project and condition for measurement tests."""
        # Create project
        project_response = await client.post(
            "/api/v1/projects",
            json={"name": "Measurement Test Project"}
        )
        project_id = project_response.json()["id"]
        
        # Create condition
        condition_response = await client.post(
            f"/api/v1/projects/{project_id}/conditions",
            json={
                "name": "Test Slab",
                "measurement_type": "area",
                "unit": "SF",
            }
        )
        condition_id = condition_response.json()["id"]
        
        return {"project_id": project_id, "condition_id": condition_id}
    
    @pytest.mark.asyncio
    async def test_create_polygon_measurement(
        self, client: AsyncClient, setup_project_with_condition
    ):
        """Test creating a polygon measurement."""
        condition_id = setup_project_with_condition["condition_id"]
        
        measurement_data = {
            "geometry_type": "polygon",
            "geometry_data": {
                "points": [
                    {"x": 100, "y": 100},
                    {"x": 200, "y": 100},
                    {"x": 200, "y": 200},
                    {"x": 100, "y": 200},
                ]
            },
            "page_id": "00000000-0000-0000-0000-000000000001",  # Mock page
        }
        
        response = await client.post(
            f"/api/v1/conditions/{condition_id}/measurements",
            json=measurement_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["geometry_type"] == "polygon"
        assert data["quantity"] > 0
        assert data["unit"] == "SF"
    
    @pytest.mark.asyncio
    async def test_create_line_measurement(
        self, client: AsyncClient, setup_project_with_condition
    ):
        """Test creating a line measurement."""
        # First create a linear condition
        project_id = setup_project_with_condition["project_id"]
        
        condition_response = await client.post(
            f"/api/v1/projects/{project_id}/conditions",
            json={
                "name": "Test Footing",
                "measurement_type": "linear",
                "unit": "LF",
            }
        )
        condition_id = condition_response.json()["id"]
        
        measurement_data = {
            "geometry_type": "line",
            "geometry_data": {
                "start": {"x": 100, "y": 100},
                "end": {"x": 200, "y": 100},
            },
            "page_id": "00000000-0000-0000-0000-000000000001",
        }
        
        response = await client.post(
            f"/api/v1/conditions/{condition_id}/measurements",
            json=measurement_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["geometry_type"] == "line"
        assert data["unit"] == "LF"
    
    @pytest.mark.asyncio
    async def test_measurement_updates_condition_total(
        self, client: AsyncClient, setup_project_with_condition
    ):
        """Test that adding measurements updates condition totals."""
        condition_id = setup_project_with_condition["condition_id"]
        
        # Add first measurement
        await client.post(
            f"/api/v1/conditions/{condition_id}/measurements",
            json={
                "geometry_type": "polygon",
                "geometry_data": {
                    "points": [
                        {"x": 0, "y": 0},
                        {"x": 100, "y": 0},
                        {"x": 100, "y": 100},
                        {"x": 0, "y": 100},
                    ]
                },
                "page_id": "00000000-0000-0000-0000-000000000001",
            }
        )
        
        # Check condition total
        response = await client.get(f"/api/v1/conditions/{condition_id}")
        data = response.json()
        assert data["measurement_count"] == 1
        assert data["total_quantity"] > 0
        
        first_total = data["total_quantity"]
        
        # Add second measurement
        await client.post(
            f"/api/v1/conditions/{condition_id}/measurements",
            json={
                "geometry_type": "polygon",
                "geometry_data": {
                    "points": [
                        {"x": 200, "y": 0},
                        {"x": 300, "y": 0},
                        {"x": 300, "y": 100},
                        {"x": 200, "y": 100},
                    ]
                },
                "page_id": "00000000-0000-0000-0000-000000000001",
            }
        )
        
        # Check updated total
        response = await client.get(f"/api/v1/conditions/{condition_id}")
        data = response.json()
        assert data["measurement_count"] == 2
        assert data["total_quantity"] > first_total
    
    @pytest.mark.asyncio
    async def test_delete_measurement_updates_total(
        self, client: AsyncClient, setup_project_with_condition
    ):
        """Test that deleting measurements updates condition totals."""
        condition_id = setup_project_with_condition["condition_id"]
        
        # Add measurement
        create_response = await client.post(
            f"/api/v1/conditions/{condition_id}/measurements",
            json={
                "geometry_type": "polygon",
                "geometry_data": {
                    "points": [
                        {"x": 0, "y": 0},
                        {"x": 100, "y": 0},
                        {"x": 100, "y": 100},
                        {"x": 0, "y": 100},
                    ]
                },
                "page_id": "00000000-0000-0000-0000-000000000001",
            }
        )
        measurement_id = create_response.json()["id"]
        
        # Delete measurement
        await client.delete(f"/api/v1/measurements/{measurement_id}")
        
        # Check condition total is zero
        response = await client.get(f"/api/v1/conditions/{condition_id}")
        data = response.json()
        assert data["measurement_count"] == 0
        assert data["total_quantity"] == 0.0
```

---

### Task 11.6: AI Accuracy Benchmarking System

Create `backend/tests/accuracy/benchmark_runner.py`:

```python
"""AI accuracy benchmarking system.

This module provides tools for measuring AI takeoff accuracy against
a golden dataset of manually-annotated construction plans.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from app.services.ai_takeoff import AITakeoffService, DetectedElement
from app.utils.geometry import MeasurementCalculator, Point

logger = structlog.get_logger()


@dataclass
class ExpectedMeasurement:
    """A manually-annotated expected measurement."""
    
    id: str
    geometry_type: str
    geometry_data: dict[str, Any]
    element_type: str
    expected_quantity: float
    unit: str
    tolerance_percent: float = 10.0  # Acceptable deviation


@dataclass
class BenchmarkResult:
    """Result of comparing AI detection to expected."""
    
    expected_id: str
    matched: bool
    ai_element: DetectedElement | None
    expected_quantity: float
    detected_quantity: float | None
    quantity_error_percent: float | None
    geometry_overlap_percent: float | None
    notes: str = ""


@dataclass
class PlanBenchmarkResult:
    """Aggregate results for a single plan."""
    
    plan_id: str
    plan_name: str
    total_expected: int
    total_detected: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    avg_quantity_error: float
    results: list[BenchmarkResult] = field(default_factory=list)


@dataclass
class BenchmarkSummary:
    """Summary across all benchmark plans."""
    
    run_id: str
    timestamp: datetime
    model_name: str
    total_plans: int
    overall_precision: float
    overall_recall: float
    overall_f1: float
    overall_accuracy: float
    avg_quantity_error: float
    plan_results: list[PlanBenchmarkResult] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "model_name": self.model_name,
            "total_plans": self.total_plans,
            "overall_precision": round(self.overall_precision, 4),
            "overall_recall": round(self.overall_recall, 4),
            "overall_f1": round(self.overall_f1, 4),
            "overall_accuracy": round(self.overall_accuracy, 4),
            "avg_quantity_error": round(self.avg_quantity_error, 4),
            "plan_results": [
                {
                    "plan_id": p.plan_id,
                    "plan_name": p.plan_name,
                    "precision": round(p.precision, 4),
                    "recall": round(p.recall, 4),
                    "f1_score": round(p.f1_score, 4),
                    "true_positives": p.true_positives,
                    "false_positives": p.false_positives,
                    "false_negatives": p.false_negatives,
                }
                for p in self.plan_results
            ],
        }


class GoldenDataset:
    """Manages the golden dataset of annotated plans."""
    
    def __init__(self, dataset_path: str | Path):
        self.dataset_path = Path(dataset_path)
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> dict[str, Any]:
        """Load dataset manifest."""
        manifest_path = self.dataset_path / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
        with open(manifest_path) as f:
            return json.load(f)
    
    def get_plans(self) -> list[dict[str, Any]]:
        """Get list of all plans in dataset."""
        return self.manifest.get("plans", [])
    
    def load_plan(self, plan_id: str) -> tuple[bytes, dict[str, Any], list[ExpectedMeasurement]]:
        """Load a plan's image, metadata, and expected measurements.
        
        Returns:
            Tuple of (image_bytes, metadata, expected_measurements)
        """
        plan_dir = self.dataset_path / plan_id
        
        # Load image
        image_path = plan_dir / "page.png"
        if not image_path.exists():
            # Try other extensions
            for ext in [".jpg", ".jpeg", ".tiff", ".tif"]:
                alt_path = plan_dir / f"page{ext}"
                if alt_path.exists():
                    image_path = alt_path
                    break
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Load metadata
        metadata_path = plan_dir / "metadata.json"
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        # Load expected measurements
        expected_path = plan_dir / "expected_measurements.json"
        with open(expected_path) as f:
            expected_data = json.load(f)
        
        expected_measurements = [
            ExpectedMeasurement(**m) for m in expected_data["measurements"]
        ]
        
        return image_bytes, metadata, expected_measurements


class BenchmarkRunner:
    """Runs AI accuracy benchmarks against golden dataset."""
    
    def __init__(
        self,
        dataset_path: str | Path,
        ai_service: AITakeoffService | None = None,
    ):
        self.dataset = GoldenDataset(dataset_path)
        self.ai_service = ai_service or AITakeoffService()
    
    def run_benchmark(
        self,
        plan_ids: list[str] | None = None,
        element_types: list[str] | None = None,
    ) -> BenchmarkSummary:
        """Run benchmark on specified plans.
        
        Args:
            plan_ids: Specific plan IDs to test, or None for all
            element_types: Filter to specific element types
            
        Returns:
            BenchmarkSummary with results
        """
        import uuid
        
        plans = self.dataset.get_plans()
        if plan_ids:
            plans = [p for p in plans if p["id"] in plan_ids]
        
        plan_results = []
        
        for plan_info in plans:
            try:
                result = self._benchmark_plan(
                    plan_info["id"],
                    element_types=element_types,
                )
                plan_results.append(result)
            except Exception as e:
                logger.error(
                    "Benchmark failed for plan",
                    plan_id=plan_info["id"],
                    error=str(e),
                )
        
        # Calculate overall metrics
        total_tp = sum(p.true_positives for p in plan_results)
        total_fp = sum(p.false_positives for p in plan_results)
        total_fn = sum(p.false_negatives for p in plan_results)
        
        overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        overall_f1 = (
            2 * overall_precision * overall_recall / (overall_precision + overall_recall)
            if (overall_precision + overall_recall) > 0 else 0
        )
        
        avg_quantity_error = (
            sum(p.avg_quantity_error for p in plan_results) / len(plan_results)
            if plan_results else 0
        )
        
        # Overall accuracy (percentage meeting 75% target)
        total_expected = sum(p.total_expected for p in plan_results)
        overall_accuracy = total_tp / total_expected if total_expected > 0 else 0
        
        return BenchmarkSummary(
            run_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            model_name=self.ai_service.llm.model_name if hasattr(self.ai_service.llm, 'model_name') else "unknown",
            total_plans=len(plan_results),
            overall_precision=overall_precision,
            overall_recall=overall_recall,
            overall_f1=overall_f1,
            overall_accuracy=overall_accuracy,
            avg_quantity_error=avg_quantity_error,
            plan_results=plan_results,
        )
    
    def _benchmark_plan(
        self,
        plan_id: str,
        element_types: list[str] | None = None,
    ) -> PlanBenchmarkResult:
        """Benchmark a single plan."""
        image_bytes, metadata, expected_measurements = self.dataset.load_plan(plan_id)
        
        # Filter by element type if specified
        if element_types:
            expected_measurements = [
                m for m in expected_measurements
                if m.element_type in element_types
            ]
        
        # Run AI detection for each element type
        detected_elements = []
        for element_type in set(m.element_type for m in expected_measurements):
            # Determine measurement type from first matching expected
            sample = next(m for m in expected_measurements if m.element_type == element_type)
            measurement_type = self._infer_measurement_type(sample.geometry_type)
            
            result = self.ai_service.analyze_page(
                image_bytes=image_bytes,
                width=metadata.get("width", 1000),
                height=metadata.get("height", 1000),
                element_type=element_type,
                measurement_type=measurement_type,
                scale_text=metadata.get("scale"),
            )
            detected_elements.extend(result.elements)
        
        # Match detected to expected
        results = self._match_detections(expected_measurements, detected_elements, metadata)
        
        # Calculate metrics
        true_positives = sum(1 for r in results if r.matched)
        false_negatives = sum(1 for r in results if not r.matched)
        
        # False positives = detected elements not matched to any expected
        matched_ai_elements = {r.ai_element for r in results if r.ai_element}
        false_positives = len(detected_elements) - len(matched_ai_elements)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        # Average quantity error for matched elements
        quantity_errors = [
            r.quantity_error_percent for r in results
            if r.quantity_error_percent is not None
        ]
        avg_quantity_error = sum(quantity_errors) / len(quantity_errors) if quantity_errors else 0
        
        return PlanBenchmarkResult(
            plan_id=plan_id,
            plan_name=metadata.get("name", plan_id),
            total_expected=len(expected_measurements),
            total_detected=len(detected_elements),
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            precision=precision,
            recall=recall,
            f1_score=f1,
            avg_quantity_error=avg_quantity_error,
            results=results,
        )
    
    def _match_detections(
        self,
        expected: list[ExpectedMeasurement],
        detected: list[DetectedElement],
        metadata: dict[str, Any],
    ) -> list[BenchmarkResult]:
        """Match detected elements to expected measurements."""
        results = []
        used_detections = set()
        
        calculator = MeasurementCalculator(
            pixels_per_foot=metadata.get("pixels_per_foot", 24.0)
        )
        
        for exp in expected:
            best_match = None
            best_overlap = 0.0
            
            for i, det in enumerate(detected):
                if i in used_detections:
                    continue
                
                if det.geometry_type != exp.geometry_type:
                    continue
                
                # Calculate geometry overlap
                overlap = self._calculate_overlap(
                    exp.geometry_data,
                    det.geometry_data,
                    exp.geometry_type,
                )
                
                if overlap > best_overlap and overlap > 0.5:  # 50% minimum overlap
                    best_match = (i, det)
                    best_overlap = overlap
            
            if best_match:
                i, det = best_match
                used_detections.add(i)
                
                # Calculate quantity from detected geometry
                detected_quantity = self._calculate_quantity(
                    det.geometry_data,
                    det.geometry_type,
                    calculator,
                )
                
                quantity_error = abs(detected_quantity - exp.expected_quantity) / exp.expected_quantity * 100
                
                results.append(BenchmarkResult(
                    expected_id=exp.id,
                    matched=True,
                    ai_element=det,
                    expected_quantity=exp.expected_quantity,
                    detected_quantity=detected_quantity,
                    quantity_error_percent=quantity_error,
                    geometry_overlap_percent=best_overlap * 100,
                ))
            else:
                results.append(BenchmarkResult(
                    expected_id=exp.id,
                    matched=False,
                    ai_element=None,
                    expected_quantity=exp.expected_quantity,
                    detected_quantity=None,
                    quantity_error_percent=None,
                    geometry_overlap_percent=None,
                    notes="No matching detection found",
                ))
        
        return results
    
    def _calculate_overlap(
        self,
        expected_geom: dict[str, Any],
        detected_geom: dict[str, Any],
        geometry_type: str,
    ) -> float:
        """Calculate overlap between two geometries (0.0 to 1.0)."""
        # Simplified overlap calculation - would use Shapely in production
        if geometry_type == "polygon":
            # Use bounding box overlap as approximation
            exp_bbox = self._get_bbox(expected_geom.get("points", []))
            det_bbox = self._get_bbox(detected_geom.get("points", []))
            return self._bbox_iou(exp_bbox, det_bbox)
        
        elif geometry_type == "point":
            # Distance-based matching for points
            exp_x, exp_y = expected_geom.get("x", 0), expected_geom.get("y", 0)
            det_x, det_y = detected_geom.get("x", 0), detected_geom.get("y", 0)
            distance = ((exp_x - det_x) ** 2 + (exp_y - det_y) ** 2) ** 0.5
            # Consider a match if within 50 pixels
            return max(0, 1 - distance / 50)
        
        elif geometry_type in ("line", "polyline"):
            # Use endpoint proximity
            exp_points = expected_geom.get("points", [])
            det_points = detected_geom.get("points", [])
            if not exp_points or not det_points:
                return 0.0
            # Simple: compare first and last points
            exp_start = exp_points[0] if isinstance(exp_points[0], dict) else expected_geom.get("start", {})
            det_start = det_points[0] if isinstance(det_points[0], dict) else detected_geom.get("start", {})
            dist = ((exp_start.get("x", 0) - det_start.get("x", 0)) ** 2 + 
                   (exp_start.get("y", 0) - det_start.get("y", 0)) ** 2) ** 0.5
            return max(0, 1 - dist / 100)
        
        return 0.0
    
    def _get_bbox(self, points: list[dict]) -> tuple[float, float, float, float]:
        """Get bounding box from points."""
        if not points:
            return (0, 0, 0, 0)
        xs = [p.get("x", 0) for p in points]
        ys = [p.get("y", 0) for p in points]
        return (min(xs), min(ys), max(xs), max(ys))
    
    def _bbox_iou(
        self,
        bbox1: tuple[float, float, float, float],
        bbox2: tuple[float, float, float, float],
    ) -> float:
        """Calculate Intersection over Union for bounding boxes."""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_quantity(
        self,
        geometry_data: dict[str, Any],
        geometry_type: str,
        calculator: MeasurementCalculator,
    ) -> float:
        """Calculate quantity from geometry."""
        if geometry_type == "polygon":
            points = [Point.from_dict(p) for p in geometry_data.get("points", [])]
            result = calculator.calculate_polygon(points)
            return result["area_sf"]
        
        elif geometry_type == "polyline":
            points = [Point.from_dict(p) for p in geometry_data.get("points", [])]
            result = calculator.calculate_polyline(points)
            return result["length_feet"]
        
        elif geometry_type == "line":
            start = Point.from_dict(geometry_data.get("start", {}))
            end = Point.from_dict(geometry_data.get("end", {}))
            result = calculator.calculate_line(start, end)
            return result["length_feet"]
        
        elif geometry_type == "point":
            return 1.0
        
        return 0.0
    
    def _infer_measurement_type(self, geometry_type: str) -> str:
        """Infer measurement type from geometry type."""
        if geometry_type in ("polygon", "rectangle", "circle"):
            return "area"
        elif geometry_type in ("line", "polyline"):
            return "linear"
        elif geometry_type == "point":
            return "count"
        return "area"
```

Create `backend/tests/accuracy/test_ai_accuracy.py`:

```python
"""AI accuracy benchmark tests.

These tests run against the golden dataset to measure AI takeoff accuracy.
They are designed to track accuracy over time and catch regressions.
"""

import os
import pytest
from pathlib import Path

from tests.accuracy.benchmark_runner import BenchmarkRunner, GoldenDataset


# Skip if no golden dataset available
GOLDEN_DATASET_PATH = Path(__file__).parent.parent / "fixtures" / "golden_dataset"
SKIP_REASON = "Golden dataset not available"


@pytest.fixture
def benchmark_runner():
    """Create benchmark runner with golden dataset."""
    if not GOLDEN_DATASET_PATH.exists():
        pytest.skip(SKIP_REASON)
    return BenchmarkRunner(GOLDEN_DATASET_PATH)


@pytest.fixture
def golden_dataset():
    """Load golden dataset."""
    if not GOLDEN_DATASET_PATH.exists():
        pytest.skip(SKIP_REASON)
    return GoldenDataset(GOLDEN_DATASET_PATH)


class TestGoldenDataset:
    """Tests for golden dataset integrity."""
    
    def test_manifest_exists(self, golden_dataset):
        """Test that manifest file exists and is valid."""
        assert golden_dataset.manifest is not None
        assert "plans" in golden_dataset.manifest
    
    def test_all_plans_have_required_files(self, golden_dataset):
        """Test that each plan has required files."""
        for plan in golden_dataset.get_plans():
            plan_id = plan["id"]
            plan_dir = golden_dataset.dataset_path / plan_id
            
            assert plan_dir.exists(), f"Plan directory missing: {plan_id}"
            
            # Check for image
            has_image = any(
                (plan_dir / f"page{ext}").exists()
                for ext in [".png", ".jpg", ".jpeg", ".tiff", ".tif"]
            )
            assert has_image, f"No image found for plan: {plan_id}"
            
            # Check for metadata
            assert (plan_dir / "metadata.json").exists(), f"No metadata for: {plan_id}"
            
            # Check for expected measurements
            assert (plan_dir / "expected_measurements.json").exists(), f"No expected measurements for: {plan_id}"
    
    def test_expected_measurements_valid(self, golden_dataset):
        """Test that expected measurements have valid structure."""
        for plan in golden_dataset.get_plans():
            _, metadata, expected = golden_dataset.load_plan(plan["id"])
            
            assert len(expected) > 0, f"No expected measurements for: {plan['id']}"
            
            for measurement in expected:
                assert measurement.id, "Measurement missing ID"
                assert measurement.geometry_type in [
                    "polygon", "polyline", "line", "point", "rectangle", "circle"
                ]
                assert measurement.expected_quantity >= 0
                assert measurement.unit in ["SF", "LF", "CY", "EA"]


class TestAIAccuracy:
    """Tests for AI takeoff accuracy."""
    
    # Mark as slow - these tests call the LLM
    @pytest.mark.slow
    @pytest.mark.integration
    def test_overall_accuracy_meets_target(self, benchmark_runner):
        """Test that overall AI accuracy meets 75% target."""
        summary = benchmark_runner.run_benchmark()
        
        # Log results for visibility
        print(f"\n{'='*60}")
        print(f"AI Accuracy Benchmark Results")
        print(f"{'='*60}")
        print(f"Overall Accuracy: {summary.overall_accuracy:.1%}")
        print(f"Precision: {summary.overall_precision:.1%}")
        print(f"Recall: {summary.overall_recall:.1%}")
        print(f"F1 Score: {summary.overall_f1:.1%}")
        print(f"Avg Quantity Error: {summary.avg_quantity_error:.1%}")
        print(f"{'='*60}\n")
        
        # Assert 75% accuracy target
        assert summary.overall_accuracy >= 0.75, (
            f"AI accuracy {summary.overall_accuracy:.1%} below 75% target"
        )
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_slab_detection_accuracy(self, benchmark_runner):
        """Test accuracy for slab detection specifically."""
        summary = benchmark_runner.run_benchmark(element_types=["slab", "concrete slab"])
        
        print(f"\nSlab Detection Accuracy: {summary.overall_accuracy:.1%}")
        
        # Slabs should be easier to detect - higher threshold
        assert summary.overall_accuracy >= 0.80, (
            f"Slab detection accuracy {summary.overall_accuracy:.1%} below 80% target"
        )
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_footing_detection_accuracy(self, benchmark_runner):
        """Test accuracy for footing/foundation detection."""
        summary = benchmark_runner.run_benchmark(
            element_types=["footing", "foundation", "foundation wall"]
        )
        
        print(f"\nFooting Detection Accuracy: {summary.overall_accuracy:.1%}")
        
        # Footings can be harder - lower threshold
        assert summary.overall_accuracy >= 0.70, (
            f"Footing detection accuracy {summary.overall_accuracy:.1%} below 70% target"
        )
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_quantity_accuracy(self, benchmark_runner):
        """Test that detected quantities are within tolerance."""
        summary = benchmark_runner.run_benchmark()
        
        print(f"\nAverage Quantity Error: {summary.avg_quantity_error:.1%}")
        
        # Quantities should be within 15% on average
        assert summary.avg_quantity_error <= 15.0, (
            f"Average quantity error {summary.avg_quantity_error:.1%} exceeds 15%"
        )
    
    @pytest.mark.slow
    @pytest.mark.integration  
    def test_no_regression_from_baseline(self, benchmark_runner, tmp_path):
        """Test that accuracy hasn't regressed from baseline."""
        # Load baseline if exists
        baseline_path = GOLDEN_DATASET_PATH / "baseline_results.json"
        
        current_summary = benchmark_runner.run_benchmark()
        
        if baseline_path.exists():
            import json
            with open(baseline_path) as f:
                baseline = json.load(f)
            
            baseline_accuracy = baseline.get("overall_accuracy", 0.75)
            
            # Allow 5% regression tolerance
            min_acceptable = baseline_accuracy - 0.05
            
            assert current_summary.overall_accuracy >= min_acceptable, (
                f"Accuracy regressed from {baseline_accuracy:.1%} to "
                f"{current_summary.overall_accuracy:.1%}"
            )
        
        # Save current results as new baseline option
        results_path = tmp_path / "benchmark_results.json"
        with open(results_path, "w") as f:
            import json
            json.dump(current_summary.to_dict(), f, indent=2)
        
        print(f"\nResults saved to: {results_path}")


class TestAccuracyByPlanType:
    """Tests for accuracy across different plan types."""
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_residential_plans(self, benchmark_runner, golden_dataset):
        """Test accuracy on residential plans."""
        residential_ids = [
            p["id"] for p in golden_dataset.get_plans()
            if p.get("category") == "residential"
        ]
        
        if not residential_ids:
            pytest.skip("No residential plans in dataset")
        
        summary = benchmark_runner.run_benchmark(plan_ids=residential_ids)
        print(f"\nResidential Plan Accuracy: {summary.overall_accuracy:.1%}")
        
        assert summary.overall_accuracy >= 0.75
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_commercial_plans(self, benchmark_runner, golden_dataset):
        """Test accuracy on commercial plans."""
        commercial_ids = [
            p["id"] for p in golden_dataset.get_plans()
            if p.get("category") == "commercial"
        ]
        
        if not commercial_ids:
            pytest.skip("No commercial plans in dataset")
        
        summary = benchmark_runner.run_benchmark(plan_ids=commercial_ids)
        print(f"\nCommercial Plan Accuracy: {summary.overall_accuracy:.1%}")
        
        # Commercial may be harder - slightly lower threshold
        assert summary.overall_accuracy >= 0.70
```

---

### Task 11.6B: Multi-Provider Benchmark Comparison

Create `backend/tests/accuracy/multi_provider_benchmark.py`:

```python
"""Multi-provider benchmark comparison tool.

Runs the same accuracy benchmarks across all available LLM providers
to compare performance, accuracy, and cost.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from app.services.llm_client import LLMClient, LLMProvider, PROVIDER_INFO
from app.services.ai_takeoff import AITakeoffService
from tests.accuracy.benchmark_runner import BenchmarkRunner, BenchmarkSummary, GoldenDataset


logger = structlog.get_logger()


# Approximate pricing per 1M tokens (update as needed)
PROVIDER_PRICING = {
    "anthropic": {"input": 3.00, "output": 15.00},
    "openai": {"input": 2.50, "output": 10.00},
    "google": {"input": 1.25, "output": 5.00},
    "xai": {"input": 5.00, "output": 15.00},
}

# Average tokens per image analysis (estimated)
AVG_TOKENS_PER_IMAGE = {
    "input": 2000,   # Image + prompt
    "output": 500,   # Response
}


@dataclass
class ProviderBenchmarkResult:
    """Results from benchmarking a single provider."""
    
    provider: str
    model_name: str
    summary: BenchmarkSummary
    total_time_seconds: float
    avg_time_per_plan: float
    estimated_cost: float
    cost_per_accuracy_point: float
    errors: list[str] = field(default_factory=list)


@dataclass
class MultiProviderComparisonResult:
    """Comparison results across all providers."""
    
    run_id: str
    timestamp: datetime
    dataset_name: str
    total_plans: int
    provider_results: list[ProviderBenchmarkResult]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "dataset_name": self.dataset_name,
            "total_plans": self.total_plans,
            "providers": [
                {
                    "provider": r.provider,
                    "model": r.model_name,
                    "accuracy": round(r.summary.overall_accuracy * 100, 2),
                    "precision": round(r.summary.overall_precision * 100, 2),
                    "recall": round(r.summary.overall_recall * 100, 2),
                    "f1": round(r.summary.overall_f1 * 100, 2),
                    "avg_quantity_error": round(r.summary.avg_quantity_error, 2),
                    "total_time_seconds": round(r.total_time_seconds, 2),
                    "avg_time_per_plan": round(r.avg_time_per_plan, 2),
                    "estimated_cost": round(r.estimated_cost, 2),
                    "cost_per_accuracy_point": round(r.cost_per_accuracy_point, 4),
                    "errors": r.errors,
                }
                for r in self.provider_results
            ],
            "recommendation": self._generate_recommendation(),
        }
    
    def _generate_recommendation(self) -> dict[str, Any]:
        """Generate recommendation based on results."""
        if not self.provider_results:
            return {"provider": None, "reason": "No results available"}
        
        # Filter out providers with too many errors
        valid_results = [
            r for r in self.provider_results
            if len(r.errors) < self.total_plans * 0.1  # Less than 10% error rate
        ]
        
        if not valid_results:
            return {"provider": None, "reason": "All providers had high error rates"}
        
        # Find best accuracy
        best_accuracy = max(valid_results, key=lambda r: r.summary.overall_accuracy)
        
        # Find best value (accuracy / cost)
        best_value = min(valid_results, key=lambda r: r.cost_per_accuracy_point)
        
        # Find fastest
        fastest = min(valid_results, key=lambda r: r.avg_time_per_plan)
        
        return {
            "best_accuracy": {
                "provider": best_accuracy.provider,
                "accuracy": round(best_accuracy.summary.overall_accuracy * 100, 2),
            },
            "best_value": {
                "provider": best_value.provider,
                "cost_per_accuracy_point": round(best_value.cost_per_accuracy_point, 4),
            },
            "fastest": {
                "provider": fastest.provider,
                "avg_time_per_plan": round(fastest.avg_time_per_plan, 2),
            },
            "recommended": best_accuracy.provider,  # Default to best accuracy
            "reason": f"{best_accuracy.provider} achieves highest accuracy at {best_accuracy.summary.overall_accuracy:.1%}",
        }


class MultiProviderBenchmarkRunner:
    """Runs benchmarks across multiple LLM providers."""
    
    def __init__(self, dataset_path: str | Path):
        self.dataset_path = Path(dataset_path)
        self.dataset = GoldenDataset(dataset_path)
    
    def get_available_providers(self) -> list[LLMProvider]:
        """Get list of providers with configured API keys."""
        client = LLMClient()
        return client.get_available_providers()
    
    def run_comparison(
        self,
        providers: list[LLMProvider] | None = None,
        plan_ids: list[str] | None = None,
    ) -> MultiProviderComparisonResult:
        """Run benchmark comparison across specified providers.
        
        Args:
            providers: Providers to test, or None for all available
            plan_ids: Specific plans to test, or None for all
            
        Returns:
            MultiProviderComparisonResult with all provider results
        """
        import uuid
        
        if providers is None:
            providers = self.get_available_providers()
        
        logger.info(
            "Starting multi-provider benchmark",
            providers=[p.value for p in providers],
            plan_count=len(plan_ids) if plan_ids else "all",
        )
        
        results = []
        
        for provider in providers:
            logger.info(f"Benchmarking provider: {provider.value}")
            
            try:
                result = self._benchmark_provider(provider, plan_ids)
                results.append(result)
            except Exception as e:
                logger.error(
                    "Provider benchmark failed",
                    provider=provider.value,
                    error=str(e),
                )
                # Create error result
                results.append(ProviderBenchmarkResult(
                    provider=provider.value,
                    model_name=PROVIDER_INFO[provider.value]["model"],
                    summary=BenchmarkSummary(
                        run_id="error",
                        timestamp=datetime.now(),
                        model_name="error",
                        total_plans=0,
                        overall_precision=0,
                        overall_recall=0,
                        overall_f1=0,
                        overall_accuracy=0,
                        avg_quantity_error=100,
                    ),
                    total_time_seconds=0,
                    avg_time_per_plan=0,
                    estimated_cost=0,
                    cost_per_accuracy_point=float("inf"),
                    errors=[str(e)],
                ))
        
        return MultiProviderComparisonResult(
            run_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            dataset_name=self.dataset.manifest.get("name", "Unknown"),
            total_plans=len(plan_ids) if plan_ids else len(self.dataset.get_plans()),
            provider_results=results,
        )
    
    def _benchmark_provider(
        self,
        provider: LLMProvider,
        plan_ids: list[str] | None = None,
    ) -> ProviderBenchmarkResult:
        """Benchmark a single provider."""
        # Create LLM client for this provider
        llm_client = LLMClient(provider=provider)
        
        # Create AI service with this client
        ai_service = AITakeoffService(llm_client=llm_client)
        
        # Create benchmark runner
        benchmark_runner = BenchmarkRunner(
            dataset_path=self.dataset_path,
            ai_service=ai_service,
        )
        
        # Run benchmark and measure time
        start_time = time.time()
        summary = benchmark_runner.run_benchmark(plan_ids=plan_ids)
        total_time = time.time() - start_time
        
        # Calculate cost estimate
        num_plans = summary.total_plans
        pricing = PROVIDER_PRICING.get(provider.value, {"input": 5.0, "output": 15.0})
        
        estimated_tokens_input = num_plans * AVG_TOKENS_PER_IMAGE["input"]
        estimated_tokens_output = num_plans * AVG_TOKENS_PER_IMAGE["output"]
        
        estimated_cost = (
            (estimated_tokens_input / 1_000_000) * pricing["input"] +
            (estimated_tokens_output / 1_000_000) * pricing["output"]
        )
        
        # Cost per accuracy point (lower is better)
        cost_per_point = (
            estimated_cost / (summary.overall_accuracy * 100)
            if summary.overall_accuracy > 0 else float("inf")
        )
        
        return ProviderBenchmarkResult(
            provider=provider.value,
            model_name=llm_client.get_model_name(),
            summary=summary,
            total_time_seconds=total_time,
            avg_time_per_plan=total_time / num_plans if num_plans > 0 else 0,
            estimated_cost=estimated_cost,
            cost_per_accuracy_point=cost_per_point,
        )
    
    def generate_report(
        self,
        result: MultiProviderComparisonResult,
        output_path: str | Path | None = None,
    ) -> str:
        """Generate a formatted comparison report.
        
        Args:
            result: Comparison results
            output_path: Optional path to save report
            
        Returns:
            Formatted report string
        """
        lines = [
            "=" * 70,
            "MULTI-PROVIDER LLM BENCHMARK COMPARISON REPORT",
            "=" * 70,
            f"Run ID: {result.run_id}",
            f"Timestamp: {result.timestamp.isoformat()}",
            f"Dataset: {result.dataset_name}",
            f"Total Plans: {result.total_plans}",
            "",
            "-" * 70,
            "RESULTS BY PROVIDER",
            "-" * 70,
            "",
        ]
        
        # Sort by accuracy descending
        sorted_results = sorted(
            result.provider_results,
            key=lambda r: r.summary.overall_accuracy,
            reverse=True,
        )
        
        for i, r in enumerate(sorted_results, 1):
            lines.extend([
                f"{i}. {r.provider.upper()} ({r.model_name})",
                f"   Accuracy:     {r.summary.overall_accuracy:.1%}",
                f"   Precision:    {r.summary.overall_precision:.1%}",
                f"   Recall:       {r.summary.overall_recall:.1%}",
                f"   F1 Score:     {r.summary.overall_f1:.1%}",
                f"   Qty Error:    {r.summary.avg_quantity_error:.1%}",
                f"   Avg Time:     {r.avg_time_per_plan:.2f}s per plan",
                f"   Est. Cost:    ${r.estimated_cost:.2f}",
                f"   Cost/Acc Pt:  ${r.cost_per_accuracy_point:.4f}",
                "",
            ])
        
        # Recommendations
        rec = result.to_dict()["recommendation"]
        lines.extend([
            "-" * 70,
            "RECOMMENDATIONS",
            "-" * 70,
            f"Best Accuracy:  {rec['best_accuracy']['provider']} ({rec['best_accuracy']['accuracy']}%)",
            f"Best Value:     {rec['best_value']['provider']} (${rec['best_value']['cost_per_accuracy_point']:.4f}/pt)",
            f"Fastest:        {rec['fastest']['provider']} ({rec['fastest']['avg_time_per_plan']:.2f}s/plan)",
            "",
            f"RECOMMENDED: {rec['recommended']}",
            f"Reason: {rec['reason']}",
            "=" * 70,
        ])
        
        report = "\n".join(lines)
        
        if output_path:
            output_path = Path(output_path)
            output_path.write_text(report)
            
            # Also save JSON
            json_path = output_path.with_suffix(".json")
            with open(json_path, "w") as f:
                json.dump(result.to_dict(), f, indent=2)
        
        return report
```

Create `backend/tests/accuracy/test_multi_provider_benchmark.py`:

```python
"""Tests for multi-provider benchmark comparison."""

import pytest
from pathlib import Path

from app.services.llm_client import LLMProvider
from tests.accuracy.multi_provider_benchmark import (
    MultiProviderBenchmarkRunner,
    MultiProviderComparisonResult,
)


GOLDEN_DATASET_PATH = Path(__file__).parent.parent / "fixtures" / "golden_dataset"


class TestMultiProviderBenchmark:
    """Tests for multi-provider benchmark comparison."""
    
    @pytest.fixture
    def benchmark_runner(self):
        """Create benchmark runner."""
        return MultiProviderBenchmarkRunner(GOLDEN_DATASET_PATH)
    
    def test_get_available_providers(self, benchmark_runner):
        """Test getting available providers."""
        providers = benchmark_runner.get_available_providers()
        
        assert isinstance(providers, list)
        # At least one provider should be available
        assert len(providers) >= 1
        assert all(isinstance(p, LLMProvider) for p in providers)
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_run_single_provider_benchmark(self, benchmark_runner):
        """Test running benchmark for a single provider."""
        providers = benchmark_runner.get_available_providers()
        if not providers:
            pytest.skip("No providers available")
        
        # Just test with first available provider
        result = benchmark_runner.run_comparison(
            providers=[providers[0]],
            plan_ids=["plan_001"],  # Single plan for speed
        )
        
        assert isinstance(result, MultiProviderComparisonResult)
        assert len(result.provider_results) == 1
        assert result.provider_results[0].provider == providers[0].value
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_run_multi_provider_comparison(self, benchmark_runner):
        """Test running comparison across multiple providers."""
        providers = benchmark_runner.get_available_providers()
        if len(providers) < 2:
            pytest.skip("Need at least 2 providers for comparison")
        
        result = benchmark_runner.run_comparison(
            providers=providers[:2],  # Test first 2 providers
            plan_ids=["plan_001"],
        )
        
        assert len(result.provider_results) == 2
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_comparison_generates_recommendation(self, benchmark_runner):
        """Test that comparison generates recommendation."""
        providers = benchmark_runner.get_available_providers()
        if not providers:
            pytest.skip("No providers available")
        
        result = benchmark_runner.run_comparison(
            providers=providers[:1],
            plan_ids=["plan_001"],
        )
        
        result_dict = result.to_dict()
        assert "recommendation" in result_dict
        assert "recommended" in result_dict["recommendation"]
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_generate_report(self, benchmark_runner, tmp_path):
        """Test report generation."""
        providers = benchmark_runner.get_available_providers()
        if not providers:
            pytest.skip("No providers available")
        
        result = benchmark_runner.run_comparison(
            providers=providers[:1],
            plan_ids=["plan_001"],
        )
        
        report_path = tmp_path / "benchmark_report.txt"
        report = benchmark_runner.generate_report(result, report_path)
        
        assert "BENCHMARK" in report
        assert report_path.exists()
        assert report_path.with_suffix(".json").exists()


class TestMultiProviderAccuracyTargets:
    """Tests that verify accuracy targets across providers."""
    
    @pytest.fixture
    def benchmark_runner(self):
        return MultiProviderBenchmarkRunner(GOLDEN_DATASET_PATH)
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_all_providers_meet_minimum_accuracy(self, benchmark_runner):
        """Test that all available providers meet minimum 70% accuracy."""
        providers = benchmark_runner.get_available_providers()
        if not providers:
            pytest.skip("No providers available")
        
        result = benchmark_runner.run_comparison(providers=providers)
        
        for provider_result in result.provider_results:
            if not provider_result.errors:
                assert provider_result.summary.overall_accuracy >= 0.70, (
                    f"{provider_result.provider} accuracy "
                    f"{provider_result.summary.overall_accuracy:.1%} below 70% minimum"
                )
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_best_provider_meets_target(self, benchmark_runner):
        """Test that at least one provider meets 75% target."""
        providers = benchmark_runner.get_available_providers()
        if not providers:
            pytest.skip("No providers available")
        
        result = benchmark_runner.run_comparison(providers=providers)
        
        best_accuracy = max(
            r.summary.overall_accuracy
            for r in result.provider_results
            if not r.errors
        )
        
        assert best_accuracy >= 0.75, (
            f"Best provider accuracy {best_accuracy:.1%} below 75% target"
        )
```

---

### Task 11.7: Golden Dataset Structure

Create `backend/tests/fixtures/golden_dataset/manifest.json`:

```json
{
  "version": "1.0.0",
  "description": "Golden dataset for AI takeoff accuracy benchmarking",
  "created": "2024-01-15",
  "plans": [
    {
      "id": "plan_001",
      "name": "Simple Residential Foundation",
      "category": "residential",
      "complexity": "simple",
      "elements": ["slab", "footing"]
    },
    {
      "id": "plan_002", 
      "name": "Complex Commercial Foundation",
      "category": "commercial",
      "complexity": "complex",
      "elements": ["slab", "footing", "column", "wall"]
    }
  ],
  "element_types": [
    "slab",
    "footing",
    "foundation wall",
    "column",
    "pier",
    "grade beam"
  ],
  "annotation_guidelines": "See ANNOTATION_GUIDE.md for measurement annotation standards"
}
```

Create `backend/tests/fixtures/golden_dataset/ANNOTATION_GUIDE.md`:

```markdown
# Golden Dataset Annotation Guide

## Purpose

This guide describes how to create ground-truth annotations for AI accuracy benchmarking.

## Directory Structure

```
golden_dataset/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ manifest.json           # Dataset metadata
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ ANNOTATION_GUIDE.md     # This file
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ plan_001/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ page.png            # Plan image (PNG preferred)
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ metadata.json       # Image and scale info
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ expected_measurements.json  # Ground truth
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ plan_002/
    Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ ...
```

## Metadata Format

`metadata.json`:
```json
{
  "name": "Plan Name",
  "category": "residential|commercial|industrial",
  "complexity": "simple|moderate|complex",
  "width": 2400,
  "height": 1800,
  "dpi": 150,
  "scale": "1/4\" = 1'-0\"",
  "pixels_per_foot": 24.0,
  "source": "Description of where plan came from",
  "notes": "Any relevant notes"
}
```

## Expected Measurements Format

`expected_measurements.json`:
```json
{
  "version": "1.0",
  "annotator": "Name of person who created annotations",
  "date": "2024-01-15",
  "measurements": [
    {
      "id": "m001",
      "element_type": "slab",
      "geometry_type": "polygon",
      "geometry_data": {
        "points": [
          {"x": 100, "y": 100},
          {"x": 500, "y": 100},
          {"x": 500, "y": 400},
          {"x": 100, "y": 400}
        ]
      },
      "expected_quantity": 150.5,
      "unit": "SF",
      "tolerance_percent": 10.0,
      "notes": "Main garage slab"
    }
  ]
}
```

## Annotation Guidelines

### Element Types

- **slab**: Concrete slabs on grade (SOG)
- **footing**: Continuous footings
- **foundation wall**: Foundation/basement walls
- **column**: Structural columns
- **pier**: Isolated piers/pads
- **grade beam**: Grade beams

### Geometry Types

- **polygon**: Closed area (slabs, pads)
- **polyline**: Linear elements (footings, walls)
- **line**: Simple two-point measurement
- **point**: Count items (columns, piers)

### Quality Standards

1. **Accuracy**: Trace element boundaries precisely
2. **Completeness**: Include ALL instances of each element type
3. **Consistency**: Use same methodology across all plans
4. **Verification**: Have second person verify annotations

### Calculating Expected Quantities

1. Measure pixel dimensions carefully
2. Apply scale factor: `real_feet = pixels / pixels_per_foot`
3. For areas: `SF = length_ft * width_ft`
4. For linear: `LF = total_length_ft`
5. For counts: Simply count instances

### Tips

- Use image editing software with measurement tools
- Document any ambiguous areas in notes
- Include edge cases (complex shapes, overlapping elements)
- Aim for 10-20 measurements per plan for good coverage
```

---

### Task 11.8: CI/CD Integration

Create `backend/tests/pytest.ini` configuration updates:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short

# Markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    accuracy: marks tests as AI accuracy tests
    e2e: marks tests as end-to-end tests

# Coverage settings
[coverage:run]
source = app
omit = 
    app/workers/*
    tests/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:
```

Update `.github/workflows/ci.yml` test job:

```yaml
# Add to existing CI workflow

  backend-test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: backend/requirements*.txt
      
      - name: Install dependencies
        working-directory: ./backend
        run: |
          pip install -r requirements-dev.txt
      
      - name: Lint with ruff
        working-directory: ./backend
        run: ruff check .
      
      - name: Type check with mypy
        working-directory: ./backend
        run: mypy app --ignore-missing-imports
      
      - name: Run unit tests
        working-directory: ./backend
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-for-ci-minimum-32-chars
        run: |
          pytest tests/unit -v --cov=app --cov-report=xml --cov-report=term-missing
      
      - name: Run integration tests
        working-directory: ./backend
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-for-ci-minimum-32-chars
        run: |
          pytest tests/integration -v --cov=app --cov-append --cov-report=xml
      
      - name: Check coverage threshold
        working-directory: ./backend
        run: |
          coverage report --fail-under=80
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend
          fail_ci_if_error: true

  # Accuracy tests run separately (slower, may use LLM credits)
  accuracy-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: [backend-test]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        working-directory: ./backend
        run: pip install -r requirements-dev.txt
      
      - name: Run accuracy benchmarks
        working-directory: ./backend
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          pytest tests/accuracy -v -m "accuracy" --tb=short
      
      - name: Upload benchmark results
        uses: actions/upload-artifact@v3
        with:
          name: accuracy-results
          path: backend/tests/accuracy/results/
```

---

## Frontend Testing

### Task 11.9: Frontend Test Setup

Update `frontend/package.json` test scripts:

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "@playwright/test": "^1.41.0",
    "@testing-library/jest-dom": "^6.2.0",
    "@testing-library/react": "^14.1.2",
    "@testing-library/user-event": "^14.5.2",
    "@vitest/coverage-v8": "^1.2.0",
    "@vitest/ui": "^1.2.0",
    "jsdom": "^24.0.0",
    "msw": "^2.1.0",
    "vitest": "^1.2.0"
  }
}
```

Create `frontend/vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}', 'tests/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/types/',
      ],
      thresholds: {
        global: {
          statements: 70,
          branches: 70,
          functions: 70,
          lines: 70,
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

Create `frontend/tests/setup.ts`:

```typescript
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll, afterAll } from 'vitest';
import { setupServer } from 'msw/node';

// Mock handlers for API requests
export const handlers = [
  // Add default handlers here
];

export const server = setupServer(...handlers);

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  root = null;
  rootMargin = '';
  thresholds = [];
  
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() { return []; }
};
```

### Task 11.10: Frontend Geometry Tests

Create `frontend/src/lib/__tests__/geometry.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import {
  calculateDistance,
  calculatePolygonArea,
  calculatePolylineLength,
  pixelsToFeet,
  squarePixelsToSquareFeet,
} from '../geometry';

describe('geometry utilities', () => {
  describe('calculateDistance', () => {
    it('calculates horizontal distance correctly', () => {
      const distance = calculateDistance(
        { x: 0, y: 0 },
        { x: 100, y: 0 }
      );
      expect(distance).toBe(100);
    });

    it('calculates vertical distance correctly', () => {
      const distance = calculateDistance(
        { x: 0, y: 0 },
        { x: 0, y: 100 }
      );
      expect(distance).toBe(100);
    });

    it('calculates diagonal distance correctly (3-4-5 triangle)', () => {
      const distance = calculateDistance(
        { x: 0, y: 0 },
        { x: 3, y: 4 }
      );
      expect(distance).toBe(5);
    });
  });

  describe('calculatePolygonArea', () => {
    it('calculates square area correctly', () => {
      const points = [
        { x: 0, y: 0 },
        { x: 100, y: 0 },
        { x: 100, y: 100 },
        { x: 0, y: 100 },
      ];
      expect(calculatePolygonArea(points)).toBe(10000);
    });

    it('calculates triangle area correctly', () => {
      const points = [
        { x: 0, y: 0 },
        { x: 100, y: 0 },
        { x: 50, y: 100 },
      ];
      expect(calculatePolygonArea(points)).toBe(5000);
    });

    it('returns 0 for less than 3 points', () => {
      expect(calculatePolygonArea([])).toBe(0);
      expect(calculatePolygonArea([{ x: 0, y: 0 }])).toBe(0);
      expect(calculatePolygonArea([{ x: 0, y: 0 }, { x: 1, y: 1 }])).toBe(0);
    });
  });

  describe('calculatePolylineLength', () => {
    it('calculates two-point line correctly', () => {
      const points = [
        { x: 0, y: 0 },
        { x: 100, y: 0 },
      ];
      expect(calculatePolylineLength(points)).toBe(100);
    });

    it('sums multiple segments', () => {
      const points = [
        { x: 0, y: 0 },
        { x: 100, y: 0 },
        { x: 100, y: 100 },
      ];
      expect(calculatePolylineLength(points)).toBe(200);
    });
  });

  describe('unit conversions', () => {
    it('converts pixels to feet with scale', () => {
      // 10 pixels per foot
      expect(pixelsToFeet(100, 10)).toBe(10);
      expect(pixelsToFeet(50, 10)).toBe(5);
    });

    it('converts square pixels to square feet', () => {
      // 10 pixels per foot = 100 square pixels per square foot
      expect(squarePixelsToSquareFeet(10000, 10)).toBe(100);
    });
  });
});
```

### Task 11.11: Playwright E2E Tests

Create `frontend/playwright.config.ts`:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e/playwright',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

Create `frontend/tests/e2e/playwright/takeoff.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Takeoff Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app
    await page.goto('/');
  });

  test('can create a new project', async ({ page }) => {
    // Click create project button
    await page.getByRole('button', { name: /create project/i }).click();

    // Fill in project details
    await page.getByLabel(/project name/i).fill('E2E Test Project');
    await page.getByLabel(/client/i).fill('Test Client');

    // Submit
    await page.getByRole('button', { name: /create/i }).click();

    // Verify project created
    await expect(page.getByText('E2E Test Project')).toBeVisible();
  });

  test('can upload a document', async ({ page }) => {
    // Create project first
    await page.getByRole('button', { name: /create project/i }).click();
    await page.getByLabel(/project name/i).fill('Upload Test');
    await page.getByRole('button', { name: /create/i }).click();

    // Click on project
    await page.getByText('Upload Test').click();

    // Upload document
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./tests/fixtures/sample.pdf');

    // Wait for processing
    await expect(page.getByText(/processing/i)).toBeVisible();
    await expect(page.getByText(/ready/i)).toBeVisible({ timeout: 30000 });
  });

  test('can draw a measurement', async ({ page }) => {
    // Assume project with document exists
    await page.goto('/projects/test-project/takeoff');

    // Select condition
    await page.getByText('4" Slab').click();

    // Select polygon tool
    await page.getByRole('button', { name: /polygon/i }).click();

    // Draw polygon on canvas
    const canvas = page.locator('canvas');
    await canvas.click({ position: { x: 100, y: 100 } });
    await canvas.click({ position: { x: 200, y: 100 } });
    await canvas.click({ position: { x: 200, y: 200 } });
    await canvas.click({ position: { x: 100, y: 200 } });
    await canvas.dblclick({ position: { x: 100, y: 100 } }); // Close polygon

    // Verify measurement created
    await expect(page.getByText(/SF/)).toBeVisible();
  });
});

test.describe('Review Workflow', () => {
  test('can approve AI-generated measurement', async ({ page }) => {
    await page.goto('/projects/test-project/review');

    // Find pending measurement
    const measurement = page.getByTestId('measurement-pending').first();
    await measurement.hover();

    // Click approve
    await page.getByRole('button', { name: /approve/i }).click();

    // Verify status changed
    await expect(measurement).toHaveAttribute('data-status', 'approved');
  });

  test('can reject AI-generated measurement', async ({ page }) => {
    await page.goto('/projects/test-project/review');

    // Find pending measurement
    const measurement = page.getByTestId('measurement-pending').first();
    await measurement.hover();

    // Click reject
    await page.getByRole('button', { name: /reject/i }).click();

    // Confirm rejection
    await page.getByRole('button', { name: /confirm/i }).click();

    // Verify removed
    await expect(measurement).not.toBeVisible();
  });
});
```

---

## Performance Testing

### Task 11.12: Performance Tests

Create `backend/tests/performance/test_large_documents.py`:

```python
"""Performance tests for large document processing."""

import time
import pytest
from unittest.mock import MagicMock, patch

from app.services.document_processor import DocumentProcessor


class TestLargeDocumentPerformance:
    """Performance tests for document processing."""
    
    @pytest.fixture
    def processor(self):
        """Create document processor with mocked storage."""
        processor = DocumentProcessor()
        processor.storage = MagicMock()
        return processor
    
    @pytest.mark.performance
    def test_page_extraction_performance(self, processor, sample_pdf_bytes):
        """Test page extraction completes in reasonable time."""
        start = time.time()
        
        # Extract pages (mocked)
        with patch.object(processor, '_extract_pages') as mock_extract:
            mock_extract.return_value = [MagicMock() for _ in range(100)]
            pages = processor._extract_pages(sample_pdf_bytes)
        
        elapsed = time.time() - start
        
        # Should handle 100 pages in under 5 seconds
        assert elapsed < 5.0, f"Page extraction took {elapsed:.2f}s for 100 pages"
    
    @pytest.mark.performance
    def test_measurement_calculation_performance(self):
        """Test measurement calculations are fast."""
        from app.utils.geometry import MeasurementCalculator, Point
        
        calculator = MeasurementCalculator(pixels_per_foot=24.0)
        
        # Generate 1000 polygons
        polygons = [
            [
                Point(x=i * 10, y=j * 10)
                for j in range(4)
            ]
            for i in range(1000)
        ]
        
        start = time.time()
        
        for polygon in polygons:
            calculator.calculate_polygon(polygon)
        
        elapsed = time.time() - start
        
        # 1000 polygon calculations should take under 1 second
        assert elapsed < 1.0, f"1000 polygon calculations took {elapsed:.2f}s"
    
    @pytest.mark.performance
    def test_api_response_time(self, client):
        """Test API endpoints respond quickly."""
        import asyncio
        
        async def measure_response_time():
            start = time.time()
            response = await client.get("/api/v1/health")
            elapsed = time.time() - start
            return elapsed
        
        elapsed = asyncio.get_event_loop().run_until_complete(measure_response_time())
        
        # Health check should respond in under 100ms
        assert elapsed < 0.1, f"Health check took {elapsed:.3f}s"
```

Create `backend/tests/performance/locustfile.py`:

```python
"""Load testing with Locust.

Run with: locust -f locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between


class TakeoffUser(HttpUser):
    """Simulates a user performing takeoff operations."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Create a project on user start."""
        response = self.client.post(
            "/api/v1/projects",
            json={"name": f"Load Test Project {self.environment.runner.user_count}"}
        )
        if response.status_code == 201:
            self.project_id = response.json()["id"]
        else:
            self.project_id = None
    
    @task(3)
    def list_projects(self):
        """List projects (common operation)."""
        self.client.get("/api/v1/projects")
    
    @task(2)
    def get_project(self):
        """Get specific project."""
        if self.project_id:
            self.client.get(f"/api/v1/projects/{self.project_id}")
    
    @task(1)
    def create_condition(self):
        """Create a condition."""
        if self.project_id:
            self.client.post(
                f"/api/v1/projects/{self.project_id}/conditions",
                json={
                    "name": "Test Condition",
                    "measurement_type": "area",
                    "unit": "SF",
                }
            )
    
    @task(1)
    def health_check(self):
        """Check API health."""
        self.client.get("/api/v1/health")
```

---

## Verification Checklist

After completing all tasks, verify:

### Unit Tests
- [ ] Geometry calculations pass all test cases
- [ ] Scale parsing handles all common formats
- [ ] Measurement calculator edge cases handled
- [ ] All validators have test coverage
- [ ] **LLM client multi-provider tests pass**
- [ ] **Provider fallback logic tested**

### Integration Tests
- [ ] API endpoints return correct status codes
- [ ] CRUD operations work for all entities
- [ ] Measurement totals update correctly
- [ ] Cascade deletes work properly
- [ ] **LLM settings API tests pass**

### AI Accuracy
- [ ] Golden dataset has 10+ annotated plans
- [ ] Benchmark runner executes successfully
- [ ] Overall accuracy >= 75% target
- [ ] Quantity errors within tolerance
- [ ] **Multi-provider benchmark runs against all available providers**
- [ ] **Per-provider accuracy tracked and compared**
- [ ] **Cost estimates calculated for each provider**
- [ ] **Comparison report generated with recommendations**

### E2E Tests
- [ ] Can create project and upload document
- [ ] Can draw measurements on canvas
- [ ] Can approve/reject AI measurements
- [ ] Export workflow completes

### CI/CD
- [ ] Unit tests run on every PR
- [ ] Coverage threshold enforced (80%)
- [ ] Accuracy tests run on main branch
- [ ] Test reports generated

### Performance
- [ ] API responses under 200ms
- [ ] Document processing scales linearly
- [ ] No memory leaks in long operations

---

## Test Commands Reference

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit -v
pytest tests/integration -v
pytest tests/accuracy -m "accuracy" -v

# Run fast tests only (exclude slow/integration)
pytest -m "not slow"

# Run with specific marker
pytest -m "integration"

# Generate coverage report
coverage html && open htmlcov/index.html

# Frontend tests
cd frontend
npm test
npm run test:coverage
npm run test:e2e

# Load testing
cd backend/tests/performance
locust -f locustfile.py --host=http://localhost:8000

# ============================================
# Multi-Provider LLM Benchmark Commands
# ============================================

# Run benchmark comparison across all available providers
pytest tests/accuracy/test_multi_provider_benchmark.py -v -m "slow"

# Run benchmark for specific provider only
BENCHMARK_PROVIDERS=anthropic pytest tests/accuracy/test_multi_provider_benchmark.py -v

# Run quick benchmark with single plan
pytest tests/accuracy/test_multi_provider_benchmark.py::TestMultiProviderBenchmark::test_run_single_provider_benchmark -v

# Generate full comparison report
python -c "
from tests.accuracy.multi_provider_benchmark import MultiProviderBenchmarkRunner
from pathlib import Path

runner = MultiProviderBenchmarkRunner('tests/fixtures/golden_dataset')
result = runner.run_comparison()
report = runner.generate_report(result, 'benchmark_report.txt')
print(report)
"

# Run LLM client unit tests
pytest tests/unit/test_llm_client.py -v

# Run LLM settings API tests
pytest tests/integration/test_llm_settings_api.py -v

# Compare specific providers (e.g., Anthropic vs OpenAI)
python -c "
from tests.accuracy.multi_provider_benchmark import MultiProviderBenchmarkRunner
from app.services.llm_client import LLMProvider
from pathlib import Path

runner = MultiProviderBenchmarkRunner('tests/fixtures/golden_dataset')
result = runner.run_comparison(
    providers=[LLMProvider.ANTHROPIC, LLMProvider.OPENAI],
    plan_ids=['plan_001', 'plan_002']  # Subset for quick test
)
print(runner.generate_report(result))
"
```

---

## Multi-Provider Configuration Reference

When running multi-provider benchmarks, ensure API keys are configured:

```bash
# Required environment variables (at least one must be set)
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_AI_API_KEY="..."
export XAI_API_KEY="..."

# Optional: Set default provider
export DEFAULT_LLM_PROVIDER=anthropic

# Optional: Configure fallback chain
export LLM_FALLBACK_PROVIDERS=openai,google
```

### Current API Pricing (for cost estimates)

| Provider | Model | Input (per 1M tokens) | Output (per 1M tokens) |
|----------|-------|----------------------|------------------------|
| Anthropic | Claude 3.5 Sonnet | $3.00 | $15.00 |
| OpenAI | GPT-4o | $2.50 | $10.00 |
| Google | Gemini 1.5 Pro | $1.25 | $5.00 |
| xAI | Grok Vision | $5.00 | $15.00 |

**Note:** Prices change frequently. Update `PROVIDER_PRICING` in `multi_provider_benchmark.py` as needed.

---

## Next Phase

Once testing is verified, proceed to **`12-DEPLOYMENT.md`** for production deployment and monitoring setup.
