"""Tests for page display field endpoints."""

import uuid
from unittest.mock import AsyncMock
from types import SimpleNamespace

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.api.deps import get_db
from tests.factories.mock_db import MockResult


# ============================================================================
# Helpers
# ============================================================================


def _make_page(
    page_id: uuid.UUID | None = None,
    display_name: str | None = None,
    display_order: int | None = None,
    group_name: str | None = None,
    is_relevant: bool = True,
) -> SimpleNamespace:
    """Create a fake Page-like object."""
    return SimpleNamespace(
        id=page_id or uuid.uuid4(),
        document_id=uuid.uuid4(),
        page_number=1,
        width=3300,
        height=2550,
        dpi=150,
        image_key="pages/test/image.tiff",
        thumbnail_key="pages/test/thumb.png",
        display_name=display_name,
        display_order=display_order,
        group_name=group_name,
        is_relevant=is_relevant,
        status="ready",
    )


# ============================================================================
# Tests: PUT /pages/{id}/display
# ============================================================================


class TestUpdatePageDisplay:

    @pytest.mark.asyncio
    async def test_set_display_name(self):
        """PUT /pages/{id}/display updates display_name."""
        page = _make_page()

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MockResult([page]))
        mock_db.commit = AsyncMock()

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    f"/api/v1/pages/{page.id}/display",
                    json={"display_name": "Ground Floor Plan"},
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Ground Floor Plan"
        assert page.display_name == "Ground Floor Plan"

    @pytest.mark.asyncio
    async def test_set_display_order(self):
        """PUT /pages/{id}/display updates display_order."""
        page = _make_page()

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MockResult([page]))
        mock_db.commit = AsyncMock()

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    f"/api/v1/pages/{page.id}/display",
                    json={"display_order": 5},
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["display_order"] == 5
        assert page.display_order == 5

    @pytest.mark.asyncio
    async def test_set_group_name(self):
        """PUT /pages/{id}/display updates group_name."""
        page = _make_page()

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MockResult([page]))
        mock_db.commit = AsyncMock()

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    f"/api/v1/pages/{page.id}/display",
                    json={"group_name": "Foundation Plans"},
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["group_name"] == "Foundation Plans"
        assert page.group_name == "Foundation Plans"

    @pytest.mark.asyncio
    async def test_nonexistent_page_returns_404(self):
        """PUT /pages/{id}/display returns 404 for unknown page."""
        fake_id = uuid.uuid4()

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MockResult([]))

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    f"/api/v1/pages/{fake_id}/display",
                    json={"display_name": "Test"},
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404


# ============================================================================
# Tests: PUT /pages/{id}/relevance
# ============================================================================


class TestUpdatePageRelevance:

    @pytest.mark.asyncio
    async def test_mark_irrelevant(self):
        """PUT /pages/{id}/relevance with is_relevant=false works."""
        page = _make_page(is_relevant=True)

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MockResult([page]))
        mock_db.commit = AsyncMock()

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    f"/api/v1/pages/{page.id}/relevance",
                    json={"is_relevant": False},
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["is_relevant"] is False
        assert page.is_relevant is False

    @pytest.mark.asyncio
    async def test_mark_relevant(self):
        """PUT /pages/{id}/relevance with is_relevant=true works."""
        page = _make_page(is_relevant=False)

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MockResult([page]))
        mock_db.commit = AsyncMock()

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    f"/api/v1/pages/{page.id}/relevance",
                    json={"is_relevant": True},
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["is_relevant"] is True
        assert page.is_relevant is True

    @pytest.mark.asyncio
    async def test_nonexistent_page_returns_404(self):
        """PUT /pages/{id}/relevance returns 404 for unknown page."""
        fake_id = uuid.uuid4()

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MockResult([]))

        app = create_app()
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    f"/api/v1/pages/{fake_id}/relevance",
                    json={"is_relevant": False},
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404
