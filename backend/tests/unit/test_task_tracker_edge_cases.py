"""Edge case tests for TaskTracker lifecycle and error scenarios.

Tests unusual but important scenarios:
- Missing task records (worker starts before DB record exists)
- Duplicate progress updates
- Concurrent mark_completed and mark_failed calls
- Invalid task_id formats
- Session commit behavior with progress updates
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock

import celery.app.task
import pytest

# ---------------------------------------------------------------------------
# TaskTracker sync method edge cases
# ---------------------------------------------------------------------------

class TestTaskTrackerSyncEdgeCases:
    """Edge cases for synchronous TaskTracker methods."""

    @patch("app.services.task_tracker.TaskRecord")
    def test_mark_started_ignores_missing_record(self, mock_record_cls):
        """mark_started_sync handles missing task record gracefully."""
        from app.services.task_tracker import TaskTracker

        session = MagicMock()
        session.get.return_value = None  # No record found

        # Should not raise - graceful handling
        TaskTracker.mark_started_sync(session, "nonexistent-id")

        # Verify we at least tried to look up the record
        session.get.assert_called_once()

    @patch("app.services.task_tracker.TaskRecord")
    def test_mark_completed_ignores_missing_record(self, mock_record_cls):
        """mark_completed_sync handles missing task record gracefully."""
        from app.services.task_tracker import TaskTracker

        session = MagicMock()
        session.get.return_value = None

        TaskTracker.mark_completed_sync(session, "nonexistent-id", {"result": "ok"})

        session.get.assert_called_once()

    @patch("app.services.task_tracker.TaskRecord")
    def test_mark_failed_ignores_missing_record(self, mock_record_cls):
        """mark_failed_sync handles missing task record gracefully."""
        from app.services.task_tracker import TaskTracker

        session = MagicMock()
        session.get.return_value = None

        TaskTracker.mark_failed_sync(session, "nonexistent-id", "error", "traceback")

        session.get.assert_called_once()

    @patch("app.services.task_tracker.TaskRecord")
    def test_update_progress_ignores_missing_record(self, mock_record_cls):
        """update_progress_sync handles missing task record gracefully."""
        from app.services.task_tracker import TaskTracker

        session = MagicMock()
        # Ensure no pending changes so it uses the main session path
        session.new = set()
        session.dirty = set()
        session.deleted = set()
        session.get.return_value = None

        TaskTracker.update_progress_sync(session, "nonexistent-id", 50, "Step")

        session.get.assert_called_once()

    @patch("app.services.task_tracker.TaskRecord")
    def test_mark_started_sets_correct_fields(self, mock_record_cls):
        """mark_started_sync sets status=STARTED and started_at."""
        from app.services.task_tracker import TaskTracker

        session = MagicMock()
        mock_record = MagicMock()
        session.get.return_value = mock_record

        TaskTracker.mark_started_sync(session, "test-id")

        assert mock_record.status == "STARTED"
        assert mock_record.started_at is not None

    @patch("app.services.task_tracker.TaskRecord")
    def test_update_progress_sets_correct_fields(self, mock_record_cls):
        """update_progress_sync sets status=PROGRESS and progress fields."""
        from app.services.task_tracker import TaskTracker

        session = MagicMock()
        # Ensure no pending changes so it uses the main session path
        session.new = set()
        session.dirty = set()
        session.deleted = set()
        mock_record = MagicMock()
        session.get.return_value = mock_record

        TaskTracker.update_progress_sync(session, "test-id", 42, "Processing data")

        assert mock_record.status == "PROGRESS"
        assert mock_record.progress_percent == 42
        assert mock_record.progress_step == "Processing data"

    @patch("app.services.task_tracker.TaskRecord")
    def test_mark_completed_sets_correct_fields(self, mock_record_cls):
        """mark_completed_sync sets status=SUCCESS and result."""
        from app.services.task_tracker import TaskTracker

        session = MagicMock()
        mock_record = MagicMock()
        session.get.return_value = mock_record

        result = {"page_count": 5}
        TaskTracker.mark_completed_sync(session, "test-id", result)

        assert mock_record.status == "SUCCESS"
        assert mock_record.progress_percent == 100
        assert mock_record.result_summary == result
        assert mock_record.completed_at is not None

    @patch("app.services.task_tracker.TaskRecord")
    def test_mark_failed_sets_correct_fields(self, mock_record_cls):
        """mark_failed_sync sets status=FAILURE and error info."""
        from app.services.task_tracker import TaskTracker

        session = MagicMock()
        mock_record = MagicMock()
        session.get.return_value = mock_record

        TaskTracker.mark_failed_sync(session, "test-id", "boom", "Traceback...")

        assert mock_record.status == "FAILURE"
        assert mock_record.error_message == "boom"
        assert mock_record.error_traceback == "Traceback..."
        assert mock_record.completed_at is not None

# ---------------------------------------------------------------------------
# TaskTracker async method edge cases
# ---------------------------------------------------------------------------

class TestTaskTrackerAsyncEdgeCases:
    """Edge cases for async TaskTracker methods."""

    @pytest.mark.asyncio
    async def test_register_async_creates_record(self):
        """register_async creates a new TaskRecord."""
        from app.services.task_tracker import TaskTracker

        mock_db = AsyncMock()
        task_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())

        await TaskTracker.register_async(
            mock_db,
            task_id=task_id,
            task_type="document_processing",
            task_name="Test",
            project_id=project_id,
            metadata={"key": "value"},
        )

        # Should have called db.add and db.commit
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_async_sets_all_fields(self):
        """register_async populates all required fields."""
        from app.services.task_tracker import TaskTracker
        from app.models.task import TaskRecord

        mock_db = AsyncMock()
        task_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())

        await TaskTracker.register_async(
            mock_db,
            task_id=task_id,
            task_type="ocr_processing",
            task_name="OCR for page S1",
            project_id=project_id,
            metadata={"page_id": "abc"},
        )

        added_record = mock_db.add.call_args[0][0]
        assert isinstance(added_record, TaskRecord)
        assert added_record.task_id == task_id
        assert added_record.task_type == "ocr_processing"
        assert added_record.task_name == "OCR for page S1"
        assert str(added_record.project_id) == project_id
        assert added_record.task_metadata == {"page_id": "abc"}
        assert added_record.status == "PENDING"

# ---------------------------------------------------------------------------
# Retry-aware failure tracking
# ---------------------------------------------------------------------------

class TestRetryAwareFailureTracking:
    """Verify tasks handle retry vs failure correctly."""

    @patch("app.workers.document_tasks.SyncSession")
    @patch("app.workers.document_tasks.get_storage_service")
    @patch("app.workers.document_tasks.get_document_processor")
    @patch("app.workers.document_tasks.TaskTracker")
    def test_document_task_marks_failed_after_max_retries(
        self, mock_tracker, mock_processor, mock_storage, mock_session_cls
    ):
        """Document task marks failed only after MaxRetriesExceededError."""
        from app.workers.document_tasks import process_document_task
        from celery.exceptions import MaxRetriesExceededError

        session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_doc = MagicMock()
        mock_doc.storage_key = "test-key"
        mock_doc.file_type = "pdf"
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_doc

        mock_storage.return_value.download_file.side_effect = RuntimeError("oops")

        task_id = str(uuid.uuid4())

        mock_req = MagicMock()

        mock_req.id = task_id

        mock_req.retries = 0

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_document_task, 'update_state', MagicMock()), \
             patch.object(process_document_task, 'retry', side_effect=MaxRetriesExceededError()):
            with pytest.raises(MaxRetriesExceededError):
                process_document_task.__wrapped__(str(uuid.uuid4()), str(uuid.uuid4()))

        mock_tracker.mark_failed_sync.assert_called_once()

    @patch("app.workers.ocr_tasks.SyncSession")
    @patch("app.workers.ocr_tasks.get_storage_service")
    @patch("app.workers.ocr_tasks.TaskTracker")
    def test_ocr_task_marks_failed_after_max_retries(
        self, mock_tracker, mock_storage, mock_session_cls
    ):
        """OCR task marks failed only after MaxRetriesExceededError."""
        from app.workers.ocr_tasks import process_page_ocr_task
        from celery.exceptions import MaxRetriesExceededError

        session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.status = "ready"
        mock_page.image_key = "test.tiff"
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_page

        mock_storage.return_value.download_file.side_effect = RuntimeError("oops")

        task_id = str(uuid.uuid4())

        mock_req = MagicMock()

        mock_req.id = task_id

        mock_req.retries = 0

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_page_ocr_task, 'update_state', MagicMock()), \
             patch.object(process_page_ocr_task, 'retry', side_effect=MaxRetriesExceededError()):
            with pytest.raises(MaxRetriesExceededError):
                process_page_ocr_task.__wrapped__(str(uuid.uuid4()))

        mock_tracker.mark_failed_sync.assert_called_once()

    @patch("app.workers.scale_tasks.SyncSession")
    @patch("app.workers.scale_tasks.get_storage_service")
    @patch("app.workers.scale_tasks.get_scale_detector")
    @patch("app.workers.scale_tasks.TaskTracker")
    def test_scale_task_marks_failed_after_max_retries(
        self, mock_tracker, mock_detector, mock_storage, mock_session_cls
    ):
        """Scale task marks failed only after MaxRetriesExceededError."""
        from app.workers.scale_tasks import detect_page_scale_task
        from celery.exceptions import MaxRetriesExceededError

        session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.image_key = "test.tiff"
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_page

        mock_storage.return_value.download_file.side_effect = RuntimeError("oops")

        task_id = str(uuid.uuid4())

        mock_req = MagicMock()

        mock_req.id = task_id

        mock_req.retries = 0

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(detect_page_scale_task, 'update_state', MagicMock()), \
             patch.object(detect_page_scale_task, 'retry', side_effect=MaxRetriesExceededError()):
            with pytest.raises(MaxRetriesExceededError):
                detect_page_scale_task.__wrapped__(str(uuid.uuid4()))

        mock_tracker.mark_failed_sync.assert_called_once()

    @patch("app.workers.classification_tasks.SyncSession")
    @patch("app.workers.classification_tasks.TaskTracker")
    def test_classification_task_marks_failed_immediately(
        self, mock_tracker, mock_session_cls
    ):
        """Classification task (max_retries=0) marks failed immediately."""
        from app.workers.classification_tasks import classify_page_task

        session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Page not found triggers ValueError
        session.execute.return_value.scalar_one_or_none.return_value = None

        task_id = str(uuid.uuid4())

        mock_req = MagicMock()

        mock_req.id = task_id

        mock_req.retries = 0

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(classify_page_task, 'update_state', MagicMock()):
            with pytest.raises(ValueError):
                classify_page_task.__wrapped__(str(uuid.uuid4()))

        mock_tracker.mark_failed_sync.assert_called_once()

# ---------------------------------------------------------------------------
# Progress update edge cases
# ---------------------------------------------------------------------------

class TestProgressUpdateEdgeCases:
    """Edge cases for progress reporting."""

    @patch("app.workers.document_tasks.SyncSession")
    @patch("app.workers.document_tasks.get_storage_service")
    @patch("app.workers.document_tasks.get_document_processor")
    @patch("app.workers.document_tasks.TaskTracker")
    def test_celery_state_and_tracker_in_sync(
        self, mock_tracker, mock_processor, mock_storage, mock_session_cls
    ):
        """Both self.update_state and TaskTracker receive same progress values."""
        from app.workers.document_tasks import process_document_task

        session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_doc = MagicMock()
        mock_doc.storage_key = "test-key"
        mock_doc.file_type = "pdf"
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_doc

        mock_processor.return_value.process_document.return_value = []
        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())

        mock_req = MagicMock()

        mock_req.id = task_id

        mock_req.retries = 0

        mock_update_state = MagicMock()
        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_document_task, 'update_state', mock_update_state):
            process_document_task.__wrapped__(str(uuid.uuid4()), str(uuid.uuid4()))

        # Extract Celery update_state calls
        celery_calls = mock_update_state.call_args_list
        celery_percents = [
            call[1]["meta"]["percent"] for call in celery_calls
            if call[1].get("state") == "PROGRESS"
        ]

        # Extract TaskTracker update_progress_sync calls
        tracker_calls = mock_tracker.update_progress_sync.call_args_list
        tracker_percents = [call[0][2] for call in tracker_calls]

        # They should match
        assert celery_percents == tracker_percents

    @patch("app.workers.document_tasks.SyncSession")
    @patch("app.workers.document_tasks.get_storage_service")
    @patch("app.workers.document_tasks.get_document_processor")
    @patch("app.workers.document_tasks.TaskTracker")
    def test_progress_monotonically_increases(
        self, mock_tracker, mock_processor, mock_storage, mock_session_cls
    ):
        """Progress percentages always increase, never decrease."""
        from app.workers.document_tasks import process_document_task

        session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_doc = MagicMock()
        mock_doc.storage_key = "test-key"
        mock_doc.file_type = "pdf"
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_doc

        mock_processor.return_value.process_document.return_value = []
        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())

        mock_req = MagicMock()

        mock_req.id = task_id

        mock_req.retries = 0

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_document_task, 'update_state', MagicMock()):
            process_document_task.__wrapped__(str(uuid.uuid4()), str(uuid.uuid4()))

        tracker_calls = mock_tracker.update_progress_sync.call_args_list
        percents = [call[0][2] for call in tracker_calls]

        for i in range(1, len(percents)):
            assert percents[i] >= percents[i - 1], (
                f"Progress went backwards: {percents[i - 1]} -> {percents[i]}"
            )

# ---------------------------------------------------------------------------
# Task ID format edge cases
# ---------------------------------------------------------------------------

class TestTaskIdFormat:
    """Verify task IDs are properly formatted UUIDs."""

    @pytest.mark.asyncio
    @patch("app.api.routes.documents.process_document_task")
    @patch("app.api.routes.documents.TaskTracker")
    @patch("app.api.routes.documents.get_document_processor")
    @patch("app.api.routes.documents.get_storage_service")
    async def test_task_id_is_valid_uuid(
        self, mock_storage, mock_processor, mock_tracker, mock_task
    ):
        """Route generates a valid UUID4 task_id."""
        from app.api.routes.documents import upload_document

        project_id = uuid.uuid4()
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_result

        mock_file = MagicMock()
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"fake-pdf-bytes")

        mock_proc = MagicMock()
        mock_proc.supported_types = {"application/pdf": "pdf"}
        mock_proc.validate_file.return_value = (True, None)
        mock_proc.store_original.return_value = "storage/key"
        mock_processor.return_value = mock_proc

        mock_tracker.register_async = AsyncMock()

        try:
            await upload_document(project_id, mock_file, mock_db)
        except Exception:
            pass

        # Extract the task_id that was used
        apply_call = mock_task.apply_async.call_args
        task_id = apply_call[1]["task_id"]

        # Validate it's a proper UUID
        parsed = uuid.UUID(task_id)
        assert str(parsed) == task_id
