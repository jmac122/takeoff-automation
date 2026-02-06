"""Tests for export Celery task."""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from app.models.export_job import ExportJob


class TestGenerateExportTask:

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        return session

    @pytest.fixture
    def sample_export_job(self):
        job = MagicMock(spec=ExportJob)
        job.id = uuid.uuid4()
        job.project_id = uuid.uuid4()
        job.format = "excel"
        job.status = "pending"
        job.file_key = None
        return job

    @pytest.fixture
    def sample_export_data(self):
        from app.services.export.base import ExportData
        return ExportData(
            project_id=uuid.uuid4(),
            project_name="Test Project",
            project_description=None,
            client_name=None,
            conditions=[],
        )

    @patch('app.workers.export_tasks.SyncSession')
    @patch('app.workers.export_tasks.TaskTracker')
    @patch('app.workers.export_tasks.get_storage_service')
    @patch('app.workers.export_tasks._fetch_export_data_sync')
    def test_marks_started(self, mock_fetch, mock_storage_fn, mock_tracker, mock_session_cls, sample_export_data):
        """Task calls mark_started_sync at entry."""
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = MagicMock(spec=ExportJob)
        mock_fetch.return_value = sample_export_data
        mock_svc = MagicMock()
        mock_storage_fn.return_value = mock_svc

        from app.workers.export_tasks import generate_export_task
        task_id = str(uuid.uuid4())

        generate_export_task(
            str(uuid.uuid4()), str(uuid.uuid4()), "excel", task_id
        )

        mock_tracker.mark_started_sync.assert_called_once_with(mock_session, task_id)

    @patch('app.workers.export_tasks.SyncSession')
    @patch('app.workers.export_tasks.TaskTracker')
    @patch('app.workers.export_tasks.get_storage_service')
    @patch('app.workers.export_tasks._fetch_export_data_sync')
    def test_progress_updates_during_generation(self, mock_fetch, mock_storage_fn, mock_tracker, mock_session_cls, sample_export_data):
        """Task reports progress at defined intervals."""
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = MagicMock(spec=ExportJob)
        mock_fetch.return_value = sample_export_data
        mock_svc = MagicMock()
        mock_storage_fn.return_value = mock_svc

        from app.workers.export_tasks import generate_export_task
        task_id = str(uuid.uuid4())

        generate_export_task(
            str(uuid.uuid4()), str(uuid.uuid4()), "csv", task_id
        )

        # Should have progress updates at 10%, 20%, 50%, 90%
        progress_calls = mock_tracker.update_progress_sync.call_args_list
        percents = [call[0][2] for call in progress_calls]
        assert 10.0 in percents
        assert 20.0 in percents
        assert 50.0 in percents
        assert 90.0 in percents

    @patch('app.workers.export_tasks.SyncSession')
    @patch('app.workers.export_tasks.TaskTracker')
    @patch('app.workers.export_tasks.get_storage_service')
    @patch('app.workers.export_tasks._fetch_export_data_sync')
    def test_marks_completed_with_file_key(self, mock_fetch, mock_storage_fn, mock_tracker, mock_session_cls, sample_export_data):
        """Task calls mark_completed_sync with the storage file key."""
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = MagicMock(spec=ExportJob)
        mock_fetch.return_value = sample_export_data
        mock_svc = MagicMock()
        mock_storage_fn.return_value = mock_svc

        from app.workers.export_tasks import generate_export_task
        task_id = str(uuid.uuid4())

        result = generate_export_task(
            str(uuid.uuid4()), str(uuid.uuid4()), "excel", task_id
        )

        mock_tracker.mark_completed_sync.assert_called_once()
        call_kwargs = mock_tracker.mark_completed_sync.call_args
        assert "file_key" in call_kwargs[1]["result_summary"]
        assert result["status"] == "completed"

    @patch('app.workers.export_tasks.SyncSession')
    @patch('app.workers.export_tasks.TaskTracker')
    @patch('app.workers.export_tasks._fetch_export_data_sync')
    def test_retries_on_error(self, mock_fetch, mock_tracker, mock_session_cls):
        """Task attempts retry on error (calls self.retry instead of failing immediately)."""
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = MagicMock(spec=ExportJob)
        mock_fetch.side_effect = ValueError("Project not found")

        from app.workers.export_tasks import generate_export_task
        task_id = str(uuid.uuid4())

        # When called directly (not via Celery worker), self.retry() re-raises
        # the original exception. In production, Celery reschedules the task.
        with pytest.raises(ValueError, match="Project not found"):
            generate_export_task(
                str(uuid.uuid4()), str(uuid.uuid4()), "excel", task_id
            )

        # mark_failed_sync is NOT called on retry (only after retries exhausted)
        mock_tracker.mark_failed_sync.assert_not_called()

    @patch('app.workers.export_tasks.SyncSession')
    @patch('app.workers.export_tasks.TaskTracker')
    @patch('app.workers.export_tasks.get_storage_service')
    @patch('app.workers.export_tasks._fetch_export_data_sync')
    def test_uploads_result_to_storage(self, mock_fetch, mock_storage_fn, mock_tracker, mock_session_cls, sample_export_data):
        """Generated file is uploaded to S3/MinIO."""
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = MagicMock(spec=ExportJob)
        mock_fetch.return_value = sample_export_data
        mock_svc = MagicMock()
        mock_storage_fn.return_value = mock_svc

        from app.workers.export_tasks import generate_export_task

        generate_export_task(
            str(uuid.uuid4()), str(uuid.uuid4()), "csv", str(uuid.uuid4())
        )

        mock_svc.upload_bytes.assert_called_once()
        call_args = mock_svc.upload_bytes.call_args
        assert isinstance(call_args[0][0], bytes)  # file bytes
        assert call_args[0][1].endswith(".csv")  # file key ends with extension

    @patch('app.workers.export_tasks.SyncSession')
    @patch('app.workers.export_tasks.TaskTracker')
    @patch('app.workers.export_tasks.get_storage_service')
    @patch('app.workers.export_tasks._fetch_export_data_sync')
    def test_updates_export_job_status(self, mock_fetch, mock_storage_fn, mock_tracker, mock_session_cls, sample_export_data):
        """ExportJob status moves from PENDING to completed."""
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_export_job = MagicMock(spec=ExportJob)
        mock_export_job.status = "pending"
        mock_session.get.return_value = mock_export_job
        mock_fetch.return_value = sample_export_data
        mock_svc = MagicMock()
        mock_storage_fn.return_value = mock_svc

        from app.workers.export_tasks import generate_export_task

        generate_export_task(
            str(uuid.uuid4()), str(uuid.uuid4()), "pdf", str(uuid.uuid4())
        )

        # The export job status should have been updated to "completed"
        assert mock_export_job.status == "completed"
        assert mock_export_job.file_key is not None

    @patch('app.workers.export_tasks.SyncSession')
    @patch('app.workers.export_tasks.TaskTracker')
    @patch('app.workers.export_tasks.get_storage_service')
    @patch('app.workers.export_tasks._fetch_export_data_sync')
    def test_unsupported_format_raises(self, mock_fetch, mock_storage_fn, mock_tracker, mock_session_cls, sample_export_data):
        """Unsupported export format triggers retry (raises on unsupported format)."""
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = MagicMock(spec=ExportJob)
        mock_fetch.return_value = sample_export_data

        from app.workers.export_tasks import generate_export_task

        # When called directly, self.retry() re-raises the original ValueError
        with pytest.raises(ValueError, match="Unsupported export format"):
            generate_export_task(
                str(uuid.uuid4()), str(uuid.uuid4()), "docx", str(uuid.uuid4())
            )
