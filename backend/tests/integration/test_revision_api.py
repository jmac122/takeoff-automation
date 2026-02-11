"""Integration tests for the revision management API routes."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def project_id():
    return str(uuid.uuid4())


@pytest.fixture
def document_id():
    return str(uuid.uuid4())


@pytest.fixture
def old_document_id():
    return str(uuid.uuid4())


def _mock_document(doc_id, project_id, **overrides):
    """Create a mock Document with default fields."""
    doc = MagicMock()
    doc.id = uuid.UUID(doc_id)
    doc.project_id = uuid.UUID(project_id)
    doc.filename = f"{doc_id}.pdf"
    doc.original_filename = "test.pdf"
    doc.file_type = "pdf"
    doc.file_size = 1024
    doc.page_count = 5
    doc.mime_type = "application/pdf"
    doc.storage_key = f"projects/{project_id}/documents/{doc_id}/test.pdf"
    doc.status = "processed"
    doc.created_at = datetime(2025, 1, 1, 12, 0, 0)
    doc.updated_at = datetime(2025, 1, 1, 12, 0, 0)
    doc.title_block_region = None
    doc.revision_number = None
    doc.revision_date = None
    doc.revision_label = None
    doc.supersedes_document_id = None
    doc.is_latest_revision = True
    doc.pages = []
    doc.processing_error = None
    for key, val in overrides.items():
        setattr(doc, key, val)
    return doc


class TestLinkRevision:
    """Tests for PUT /api/v1/documents/{id}/revision."""

    def test_link_revision_success(self, client, document_id, old_document_id, project_id):
        doc = _mock_document(document_id, project_id)
        old_doc = _mock_document(old_document_id, project_id)

        mock_db = AsyncMock()

        # First query: load current document (selectinload)
        result1 = MagicMock()
        result1.scalar_one_or_none.return_value = doc
        # Second query: load old document
        result2 = MagicMock()
        result2.scalar_one_or_none.return_value = old_doc

        mock_db.execute = AsyncMock(side_effect=[result1, result2])
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("app.api.routes.documents.get_db", return_value=mock_db):
            response = client.put(
                f"/api/v1/documents/{document_id}/revision",
                json={
                    "supersedes_document_id": old_document_id,
                    "revision_number": "B",
                    "revision_label": "Issued for Construction",
                },
            )

        assert response.status_code == 200
        # Verify the document attributes were updated
        assert doc.supersedes_document_id == uuid.UUID(old_document_id)
        assert doc.revision_number == "B"
        assert doc.revision_label == "Issued for Construction"
        assert doc.is_latest_revision is True
        assert old_doc.is_latest_revision is False

    def test_link_revision_document_not_found(self, client, document_id, old_document_id):
        mock_db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        with patch("app.api.routes.documents.get_db", return_value=mock_db):
            response = client.put(
                f"/api/v1/documents/{document_id}/revision",
                json={"supersedes_document_id": old_document_id},
            )

        assert response.status_code == 404

    def test_link_revision_superseded_not_found(self, client, document_id, old_document_id, project_id):
        doc = _mock_document(document_id, project_id)
        mock_db = AsyncMock()

        result1 = MagicMock()
        result1.scalar_one_or_none.return_value = doc
        result2 = MagicMock()
        result2.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(side_effect=[result1, result2])

        with patch("app.api.routes.documents.get_db", return_value=mock_db):
            response = client.put(
                f"/api/v1/documents/{document_id}/revision",
                json={"supersedes_document_id": old_document_id},
            )

        assert response.status_code == 404

    def test_link_revision_different_projects(self, client, document_id, old_document_id, project_id):
        other_project_id = str(uuid.uuid4())
        doc = _mock_document(document_id, project_id)
        old_doc = _mock_document(old_document_id, other_project_id)

        mock_db = AsyncMock()
        result1 = MagicMock()
        result1.scalar_one_or_none.return_value = doc
        result2 = MagicMock()
        result2.scalar_one_or_none.return_value = old_doc

        mock_db.execute = AsyncMock(side_effect=[result1, result2])

        with patch("app.api.routes.documents.get_db", return_value=mock_db):
            response = client.put(
                f"/api/v1/documents/{document_id}/revision",
                json={"supersedes_document_id": old_document_id},
            )

        assert response.status_code == 400
        assert "same project" in response.json()["detail"]


class TestGetRevisionChain:
    """Tests for GET /api/v1/documents/{id}/revisions."""

    def test_chain_single_document(self, client, document_id, project_id):
        doc = _mock_document(document_id, project_id)

        mock_db = AsyncMock()

        # First query: load document by ID
        result1 = MagicMock()
        result1.scalar_one_or_none.return_value = doc

        # Forward walk query (no next doc)
        result_forward = MagicMock()
        result_forward.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(side_effect=[result1, result_forward])

        with patch("app.api.routes.documents.get_db", return_value=mock_db):
            response = client.get(f"/api/v1/documents/{document_id}/revisions")

        assert response.status_code == 200
        data = response.json()
        assert data["current_document_id"] == document_id
        assert len(data["chain"]) == 1
        assert data["chain"][0]["id"] == document_id

    def test_chain_not_found(self, client, document_id):
        mock_db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        with patch("app.api.routes.documents.get_db", return_value=mock_db):
            response = client.get(f"/api/v1/documents/{document_id}/revisions")

        assert response.status_code == 404


class TestComparePages:
    """Tests for POST /api/v1/documents/compare-pages."""

    def test_compare_pages_both_exist(self, client, project_id):
        old_doc_id = str(uuid.uuid4())
        new_doc_id = str(uuid.uuid4())
        old_page_id = uuid.uuid4()
        new_page_id = uuid.uuid4()

        old_page = MagicMock()
        old_page.id = old_page_id
        old_page.image_key = "pages/old.png"

        new_page = MagicMock()
        new_page.id = new_page_id
        new_page.image_key = "pages/new.png"

        mock_db = AsyncMock()
        result_old = MagicMock()
        result_old.scalar_one_or_none.return_value = old_page
        result_new = MagicMock()
        result_new.scalar_one_or_none.return_value = new_page

        mock_db.execute = AsyncMock(side_effect=[result_old, result_new])

        mock_storage = MagicMock()
        mock_storage.get_presigned_url.side_effect = [
            "https://storage/old.png?signed",
            "https://storage/new.png?signed",
        ]

        with (
            patch("app.api.routes.documents.get_db", return_value=mock_db),
            patch("app.api.routes.documents.get_storage_service", return_value=mock_storage),
        ):
            response = client.post(
                "/api/v1/documents/compare-pages",
                json={
                    "old_document_id": old_doc_id,
                    "new_document_id": new_doc_id,
                    "page_number": 1,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["has_both"] is True
        assert data["page_number"] == 1
        assert data["old_image_url"] is not None
        assert data["new_image_url"] is not None

    def test_compare_pages_old_missing(self, client):
        old_doc_id = str(uuid.uuid4())
        new_doc_id = str(uuid.uuid4())
        new_page_id = uuid.uuid4()

        new_page = MagicMock()
        new_page.id = new_page_id
        new_page.image_key = "pages/new.png"

        mock_db = AsyncMock()
        result_old = MagicMock()
        result_old.scalar_one_or_none.return_value = None
        result_new = MagicMock()
        result_new.scalar_one_or_none.return_value = new_page

        mock_db.execute = AsyncMock(side_effect=[result_old, result_new])

        mock_storage = MagicMock()
        mock_storage.get_presigned_url.return_value = "https://storage/new.png?signed"

        with (
            patch("app.api.routes.documents.get_db", return_value=mock_db),
            patch("app.api.routes.documents.get_storage_service", return_value=mock_storage),
        ):
            response = client.post(
                "/api/v1/documents/compare-pages",
                json={
                    "old_document_id": old_doc_id,
                    "new_document_id": new_doc_id,
                    "page_number": 3,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["has_both"] is False
        assert data["old_page_id"] is None
        assert data["old_image_url"] is None
        assert data["new_image_url"] is not None

    def test_compare_pages_neither_exist(self, client):
        mock_db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        mock_storage = MagicMock()

        with (
            patch("app.api.routes.documents.get_db", return_value=mock_db),
            patch("app.api.routes.documents.get_storage_service", return_value=mock_storage),
        ):
            response = client.post(
                "/api/v1/documents/compare-pages",
                json={
                    "old_document_id": str(uuid.uuid4()),
                    "new_document_id": str(uuid.uuid4()),
                    "page_number": 1,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["has_both"] is False
        assert data["old_image_url"] is None
        assert data["new_image_url"] is None
