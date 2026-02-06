"""Tests for the sheets endpoint -- GET /projects/{id}/sheets."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.api.deps import get_db


# ============================================================================
# Fixtures
# ============================================================================


def _make_page(
    document_id: uuid.UUID,
    page_number: int = 1,
    page_id: uuid.UUID | None = None,
    discipline: str | None = None,
    sheet_number: str | None = None,
    title: str | None = None,
    display_name: str | None = None,
    display_order: int | None = None,
    group_name: str | None = None,
    is_relevant: bool = True,
    scale_text: str | None = None,
    scale_value: float | None = None,
    scale_calibrated: bool = False,
    scale_detection_method: str | None = None,
    classification: str | None = None,
    classification_confidence: float | None = None,
    page_type: str | None = None,
) -> SimpleNamespace:
    """Create a fake Page-like object using SimpleNamespace."""
    return SimpleNamespace(
        id=page_id or uuid.uuid4(),
        document_id=document_id,
        page_number=page_number,
        width=3300,
        height=2550,
        dpi=150,
        image_key=f"pages/{page_id or 'test'}/image.tiff",
        thumbnail_key=f"pages/{page_id or 'test'}/thumbnail.png",
        discipline=discipline,
        sheet_number=sheet_number,
        title=title,
        display_name=display_name,
        display_order=display_order,
        group_name=group_name,
        is_relevant=is_relevant,
        scale_text=scale_text,
        scale_value=scale_value,
        scale_calibrated=scale_calibrated,
        scale_detection_method=scale_detection_method,
        classification=classification,
        classification_confidence=classification_confidence,
        page_type=page_type,
        status="ready",
    )


# ============================================================================
# Test helpers
# ============================================================================


class MockResult:
    """Mocks an SQLAlchemy result."""

    def __init__(self, data):
        self._data = data

    def scalars(self):
        return self

    def all(self):
        return self._data

    def scalar_one_or_none(self):
        return self._data[0] if self._data else None

    def one_or_none(self):
        return self._data[0] if self._data else None

    def __iter__(self):
        return iter(self._data)


class MockRow:
    """Simulates a SQLAlchemy row with (page, measurement_count)."""

    def __init__(self, page, measurement_count=0):
        self._data = (page, measurement_count)

    def __getitem__(self, idx):
        return self._data[idx]


def _mock_storage():
    """Create a mock storage service."""
    svc = MagicMock()
    svc.get_presigned_url.return_value = "https://example.com/image.png"
    return svc


# ============================================================================
# Tests
# ============================================================================


class TestGetProjectSheets:

    @pytest.fixture
    def project_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def doc_id(self):
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_returns_all_pages_for_project(self, project_id, doc_id):
        """GET /projects/{id}/sheets returns all relevant pages."""
        pages = [
            _make_page(doc_id, page_number=1, discipline="Structural", sheet_number="S1.01"),
            _make_page(doc_id, page_number=2, discipline="Structural", sheet_number="S1.02"),
            _make_page(doc_id, page_number=3, discipline="Architectural", sheet_number="A1.01"),
        ]

        call_count = 0

        async def mock_execute(query, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockResult([project_id])
            return MockResult([MockRow(p, 0) for p in pages])

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.api.routes.sheets.get_storage_service", return_value=_mock_storage()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(f"/api/v1/projects/{project_id}/sheets")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["groups"]) == 2

    @pytest.mark.asyncio
    async def test_includes_classification_data(self, project_id, doc_id):
        """Each sheet includes discipline, page_type from classification."""
        page = _make_page(
            doc_id,
            page_number=1,
            discipline="Structural",
            page_type="floor_plan",
            classification="structural_floor_plan",
            classification_confidence=0.92,
        )

        call_count = 0

        async def mock_execute(query, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockResult([project_id])
            return MockResult([MockRow(page, 0)])

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.api.routes.sheets.get_storage_service", return_value=_mock_storage()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(f"/api/v1/projects/{project_id}/sheets")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        sheet = data["groups"][0]["sheets"][0]
        assert sheet["discipline"] == "Structural"
        assert sheet["page_type"] == "floor_plan"
        assert sheet["classification"] == "structural_floor_plan"
        assert sheet["classification_confidence"] == 0.92

    @pytest.mark.asyncio
    async def test_includes_scale_data(self, project_id, doc_id):
        """Each sheet includes scale_text, scale_value, scale_calibrated."""
        page = _make_page(
            doc_id,
            page_number=1,
            discipline="Structural",
            scale_text='1/4" = 1\'-0"',
            scale_value=12.5,
            scale_calibrated=True,
            scale_detection_method="vision_llm",
        )

        call_count = 0

        async def mock_execute(query, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockResult([project_id])
            return MockResult([MockRow(page, 0)])

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.api.routes.sheets.get_storage_service", return_value=_mock_storage()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(f"/api/v1/projects/{project_id}/sheets")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        sheet = data["groups"][0]["sheets"][0]
        assert sheet["scale_text"] == '1/4" = 1\'-0"'
        assert sheet["scale_value"] == 12.5
        assert sheet["scale_calibrated"] is True
        assert sheet["scale_detection_method"] == "vision_llm"

    @pytest.mark.asyncio
    async def test_includes_measurement_counts(self, project_id, doc_id):
        """Each sheet includes count of measurements on that page."""
        page = _make_page(doc_id, page_number=1, discipline="Structural")

        call_count = 0

        async def mock_execute(query, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockResult([project_id])
            return MockResult([MockRow(page, 5)])

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.api.routes.sheets.get_storage_service", return_value=_mock_storage()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(f"/api/v1/projects/{project_id}/sheets")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        sheet = data["groups"][0]["sheets"][0]
        assert sheet["measurement_count"] == 5

    @pytest.mark.asyncio
    async def test_grouped_by_discipline(self, project_id, doc_id):
        """Response groups sheets by discipline field."""
        pages = [
            _make_page(doc_id, page_number=1, discipline="Structural", sheet_number="S1.01"),
            _make_page(doc_id, page_number=2, discipline="Structural", sheet_number="S1.02"),
            _make_page(doc_id, page_number=3, discipline="Architectural", sheet_number="A1.01"),
            _make_page(doc_id, page_number=4, discipline="Mechanical", sheet_number="M1.01"),
        ]

        call_count = 0

        async def mock_execute(query, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockResult([project_id])
            return MockResult([MockRow(p, 0) for p in pages])

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.api.routes.sheets.get_storage_service", return_value=_mock_storage()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(f"/api/v1/projects/{project_id}/sheets")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        group_names = [g["group_name"] for g in data["groups"]]
        assert "Structural" in group_names
        assert "Architectural" in group_names
        assert "Mechanical" in group_names
        structural = next(g for g in data["groups"] if g["group_name"] == "Structural")
        assert len(structural["sheets"]) == 2

    @pytest.mark.asyncio
    async def test_sorted_by_display_order(self, project_id, doc_id):
        """Sheets within groups are sorted by display_order, then sheet_number."""
        pages = [
            _make_page(doc_id, page_number=1, discipline="Structural", sheet_number="S1.02", display_order=2),
            _make_page(doc_id, page_number=2, discipline="Structural", sheet_number="S1.01", display_order=1),
        ]

        call_count = 0

        async def mock_execute(query, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockResult([project_id])
            return MockResult([MockRow(p, 0) for p in pages])

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.api.routes.sheets.get_storage_service", return_value=_mock_storage()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(f"/api/v1/projects/{project_id}/sheets")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        sheets = data["groups"][0]["sheets"]
        assert sheets[0]["display_order"] == 1
        assert sheets[1]["display_order"] == 2

    @pytest.mark.asyncio
    async def test_nonexistent_project_returns_404(self):
        """GET for unknown project_id returns 404."""
        fake_id = uuid.uuid4()

        async def mock_execute(query, *args, **kwargs):
            return MockResult([])

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.api.routes.sheets.get_storage_service", return_value=_mock_storage()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(f"/api/v1/projects/{fake_id}/sheets")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_empty_project_returns_empty_list(self, project_id):
        """Project with no documents returns empty sheets array."""
        call_count = 0

        async def mock_execute(query, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockResult([project_id])
            return MockResult([])

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.api.routes.sheets.get_storage_service", return_value=_mock_storage()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get(f"/api/v1/projects/{project_id}/sheets")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["groups"] == []
