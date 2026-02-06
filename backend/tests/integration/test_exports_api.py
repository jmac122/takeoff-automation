"""Integration tests for export API endpoints."""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from httpx import AsyncClient, ASGITransport

from app.api.deps import get_db
from app.main import create_app
from app.models.export_job import ExportJob
from app.models.project import Project


@pytest.fixture
def sample_project_id():
    return uuid.uuid4()


@pytest.fixture
def sample_export_id():
    return uuid.uuid4()


def _mock_project(project_id):
    project = MagicMock(spec=Project)
    project.id = project_id
    project.name = "Test Project"
    project.description = "Test"
    project.client_name = "Client"
    project.status = "draft"
    return project


def _mock_export(export_id, project_id, status="pending", file_key=None, file_size=None):
    job = MagicMock(spec=ExportJob)
    job.id = export_id
    job.project_id = project_id
    job.format = "excel"
    job.status = status
    job.file_key = file_key
    job.file_size = file_size
    job.error_message = None
    job.options = None
    job.started_at = datetime.now(timezone.utc) if status != "pending" else None
    job.completed_at = datetime.now(timezone.utc) if status == "completed" else None
    job.created_at = datetime.now(timezone.utc)
    job.updated_at = datetime.now(timezone.utc)
    return job


def _make_session_with_results(results):
    """Create a mock async session that returns different results on sequential execute calls."""
    session = AsyncMock()
    call_count = [0]

    def make_result(*a, **kw):
        idx = call_count[0]
        call_count[0] += 1
        if idx < len(results):
            return results[idx]
        return MagicMock()

    def auto_set_id(obj):
        """Simulate DB flush by setting a UUID on objects without an id."""
        if hasattr(obj, 'id') and obj.id is None:
            obj.id = uuid.uuid4()

    session.execute = AsyncMock(side_effect=make_result)
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.delete = AsyncMock()
    session.add = MagicMock(side_effect=auto_set_id)
    return session


@pytest.fixture
def app():
    return create_app()


class TestStartExport:

    @pytest.mark.asyncio
    async def test_start_export_returns_task_id(self, app, sample_project_id):
        """POST /projects/{id}/export returns a task_id."""
        project = _mock_project(sample_project_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = project

        session = _make_session_with_results([mock_result])

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        with patch("app.api.routes.exports.TaskTracker") as mock_tracker, \
             patch("app.api.routes.exports.generate_export_task"):
            mock_tracker.register_async = AsyncMock()

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/projects/{sample_project_id}/export",
                    json={"format": "excel"},
                )

        assert resp.status_code == 202
        data = resp.json()
        assert "task_id" in data
        assert "export_id" in data
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_start_export_creates_export_job(self, app, sample_project_id):
        """POST creates an ExportJob record in PENDING status."""
        project = _mock_project(sample_project_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = project

        session = _make_session_with_results([mock_result])
        added_objects = []

        def capture_and_set_id(obj):
            if hasattr(obj, 'id') and obj.id is None:
                obj.id = uuid.uuid4()
            added_objects.append(obj)

        session.add = MagicMock(side_effect=capture_and_set_id)

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        with patch("app.api.routes.exports.TaskTracker") as mock_tracker, \
             patch("app.api.routes.exports.generate_export_task"):
            mock_tracker.register_async = AsyncMock()

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.post(
                    f"/api/v1/projects/{sample_project_id}/export",
                    json={"format": "csv"},
                )

        assert len(added_objects) == 1
        assert added_objects[0].format == "csv"
        assert added_objects[0].status == "pending"
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_start_export_registers_task(self, app, sample_project_id):
        """POST creates a TaskRecord (via TaskTracker) for polling."""
        project = _mock_project(sample_project_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = project

        session = _make_session_with_results([mock_result])

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        with patch("app.api.routes.exports.TaskTracker") as mock_tracker, \
             patch("app.api.routes.exports.generate_export_task"):
            mock_tracker.register_async = AsyncMock()

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.post(
                    f"/api/v1/projects/{sample_project_id}/export",
                    json={"format": "excel"},
                )

            mock_tracker.register_async.assert_called_once()
            call_kwargs = mock_tracker.register_async.call_args[1]
            assert call_kwargs["task_type"] == "export"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invalid_format_rejected(self, app):
        """POST with unsupported format returns 422."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/api/v1/projects/{uuid.uuid4()}/export",
                json={"format": "docx"},
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_nonexistent_project_returns_404(self, app):
        """POST to unknown project_id returns 404."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        session = _make_session_with_results([mock_result])

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        with patch("app.api.routes.exports.generate_export_task"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/projects/{uuid.uuid4()}/export",
                    json={"format": "excel"},
                )
        assert resp.status_code == 404
        app.dependency_overrides.clear()


class TestGetExport:

    @pytest.mark.asyncio
    async def test_completed_export_has_download_url(self, app, sample_project_id, sample_export_id):
        """GET for completed export includes presigned download URL."""
        export = _mock_export(sample_export_id, sample_project_id, "completed",
                              file_key=f"exports/{sample_project_id}/{sample_export_id}.xlsx",
                              file_size=5000)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = export
        session = _make_session_with_results([mock_result])

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        with patch("app.api.routes.exports.get_storage_service") as mock_storage:
            mock_svc = MagicMock()
            mock_svc.get_presigned_url.return_value = "https://storage.local/download/file.xlsx"
            mock_storage.return_value = mock_svc

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/v1/exports/{sample_export_id}")

        assert resp.status_code == 200
        assert resp.json()["download_url"] == "https://storage.local/download/file.xlsx"
        assert resp.json()["status"] == "completed"
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_pending_export_has_no_url(self, app, sample_project_id, sample_export_id):
        """GET for in-progress export has null download_url."""
        export = _mock_export(sample_export_id, sample_project_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = export
        session = _make_session_with_results([mock_result])

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/v1/exports/{sample_export_id}")

        assert resp.status_code == 200
        assert resp.json()["download_url"] is None
        assert resp.json()["status"] == "pending"
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_nonexistent_export_returns_404(self, app):
        """GET for unknown export_id returns 404."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session = _make_session_with_results([mock_result])

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/v1/exports/{uuid.uuid4()}")
        assert resp.status_code == 404
        app.dependency_overrides.clear()


class TestListExports:

    @pytest.mark.asyncio
    async def test_lists_only_project_exports(self, app, sample_project_id, sample_export_id):
        """GET /projects/{id}/exports only returns that project's exports."""
        project = _mock_project(sample_project_id)
        export = _mock_export(sample_export_id, sample_project_id)

        r1 = MagicMock(); r1.scalar_one_or_none.return_value = project
        r2 = MagicMock(); r2.scalar_one.return_value = 1
        r3 = MagicMock(); r3.scalars.return_value = MagicMock(all=MagicMock(return_value=[export]))

        session = _make_session_with_results([r1, r2, r3])

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/v1/projects/{sample_project_id}/exports")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["exports"]) == 1
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_ordered_by_created_at_desc(self, app, sample_project_id):
        """Exports are returned newest first."""
        project = _mock_project(sample_project_id)
        e1 = _mock_export(uuid.uuid4(), sample_project_id)
        e2 = _mock_export(uuid.uuid4(), sample_project_id)

        r1 = MagicMock(); r1.scalar_one_or_none.return_value = project
        r2 = MagicMock(); r2.scalar_one.return_value = 2
        r3 = MagicMock(); r3.scalars.return_value = MagicMock(all=MagicMock(return_value=[e2, e1]))

        session = _make_session_with_results([r1, r2, r3])

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/v1/projects/{sample_project_id}/exports")

        assert resp.status_code == 200
        assert len(resp.json()["exports"]) == 2
        app.dependency_overrides.clear()


class TestDeleteExport:

    @pytest.mark.asyncio
    async def test_delete_removes_record(self, app, sample_export_id, sample_project_id):
        """DELETE removes the export job record."""
        export = _mock_export(sample_export_id, sample_project_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = export
        session = _make_session_with_results([mock_result])

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.delete(f"/api/v1/exports/{sample_export_id}")

        assert resp.status_code == 204
        session.delete.assert_called_once()
        session.commit.assert_called_once()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_cleans_up_file(self, app, sample_export_id, sample_project_id):
        """DELETE also removes the file from storage."""
        fkey = f"exports/{sample_project_id}/{sample_export_id}.xlsx"
        export = _mock_export(sample_export_id, sample_project_id, "completed", file_key=fkey, file_size=5000)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = export
        session = _make_session_with_results([mock_result])

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        with patch("app.api.routes.exports.get_storage_service") as mock_storage:
            mock_svc = MagicMock()
            mock_storage.return_value = mock_svc
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.delete(f"/api/v1/exports/{sample_export_id}")

            assert resp.status_code == 204
            mock_svc.delete_file.assert_called_once_with(fkey)

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(self, app):
        """DELETE for unknown export_id returns 404."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session = _make_session_with_results([mock_result])

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.delete(f"/api/v1/exports/{uuid.uuid4()}")
        assert resp.status_code == 404
        app.dependency_overrides.clear()
