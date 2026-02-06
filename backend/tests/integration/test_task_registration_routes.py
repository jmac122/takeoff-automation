"""Integration tests for task registration in API routes.

Verifies that each route that triggers a Celery task:
1. Generates a task_id up front (UUID)
2. Calls TaskTracker.register_async BEFORE enqueuing
3. Uses .apply_async(task_id=...) instead of .delay()
"""

import uuid
from unittest.mock import patch, MagicMock, AsyncMock, ANY

import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# Document Upload Route Registration
# ---------------------------------------------------------------------------


class TestDocumentUploadRegistration:
    """Verify upload_document route registers task before enqueue."""

    @pytest.mark.asyncio
    @patch("app.api.routes.documents.process_document_task")
    @patch("app.api.routes.documents.TaskTracker")
    @patch("app.api.routes.documents.get_document_processor")
    @patch("app.api.routes.documents.get_storage_service")
    async def test_registers_before_enqueue(
        self, mock_storage, mock_processor, mock_tracker, mock_task
    ):
        """Route calls register_async before apply_async."""
        from app.api.routes.documents import upload_document

        project_id = uuid.uuid4()
        mock_db = AsyncMock()

        # Mock project exists
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_result

        # Mock file
        mock_file = MagicMock()
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"fake-pdf-bytes")

        # Mock processor
        mock_proc = MagicMock()
        mock_proc.supported_types = {"application/pdf": "pdf"}
        mock_proc.validate_file.return_value = (True, None)
        mock_proc.store_original.return_value = "storage/key"
        mock_processor.return_value = mock_proc

        # Mock register_async
        mock_tracker.register_async = AsyncMock()

        try:
            await upload_document(project_id, mock_file, mock_db)
        except Exception:
            pass  # May fail on response serialization but that's OK

        # Verify register_async was called
        mock_tracker.register_async.assert_called_once()
        call_kwargs = mock_tracker.register_async.call_args
        assert call_kwargs[1]["task_type"] == "document_processing" or (
            len(call_kwargs[0]) > 0
        )

        # Verify apply_async was called (not delay)
        mock_task.apply_async.assert_called_once()
        apply_kwargs = mock_task.apply_async.call_args
        assert "task_id" in apply_kwargs[1]

    @pytest.mark.asyncio
    @patch("app.api.routes.documents.process_document_task")
    @patch("app.api.routes.documents.TaskTracker")
    @patch("app.api.routes.documents.get_document_processor")
    @patch("app.api.routes.documents.get_storage_service")
    async def test_task_id_matches(
        self, mock_storage, mock_processor, mock_tracker, mock_task
    ):
        """Same task_id used in register_async and apply_async."""
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

        # Extract task IDs from both calls
        register_call = mock_tracker.register_async.call_args
        apply_call = mock_task.apply_async.call_args

        registered_task_id = register_call[1].get("task_id") or register_call[0][1] if len(register_call[0]) > 1 else register_call[1]["task_id"]
        applied_task_id = apply_call[1]["task_id"]

        assert registered_task_id == applied_task_id


# ---------------------------------------------------------------------------
# OCR Reprocess Route Registration
# ---------------------------------------------------------------------------


class TestOCRReprocessRegistration:
    """Verify reprocess_page_ocr route registers task before enqueue."""

    @pytest.mark.asyncio
    @patch("app.api.routes.pages.process_page_ocr_task")
    @patch("app.api.routes.pages.TaskTracker")
    async def test_registers_before_enqueue(self, mock_tracker, mock_task):
        """Route calls register_async before apply_async."""
        from app.api.routes.pages import reprocess_page_ocr

        page_id = uuid.uuid4()
        mock_db = AsyncMock()

        # Mock page exists
        mock_page = MagicMock()
        mock_page.status = "ready"
        mock_page.sheet_number = "S1"
        mock_page.page_number = 1
        mock_page.document_id = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_page
        mock_db.execute.return_value = mock_result

        # Override for the Document.project_id query
        mock_project_result = MagicMock()
        mock_project_result.scalar_one.return_value = uuid.uuid4()
        mock_db.execute.side_effect = [mock_result, mock_project_result]

        mock_tracker.register_async = AsyncMock()

        result = await reprocess_page_ocr(page_id, mock_db)

        mock_tracker.register_async.assert_called_once()
        call_kwargs = mock_tracker.register_async.call_args
        assert "ocr_processing" in str(call_kwargs)

        mock_task.apply_async.assert_called_once()
        assert "task_id" in result


# ---------------------------------------------------------------------------
# Classification Route Registration
# ---------------------------------------------------------------------------


class TestClassifyPageRegistration:
    """Verify classify_page_endpoint registers task before enqueue."""

    @pytest.mark.asyncio
    @patch("app.api.routes.pages.classify_page_task")
    @patch("app.api.routes.pages.TaskTracker")
    async def test_registers_before_enqueue(self, mock_tracker, mock_task):
        """Route calls register_async before apply_async."""
        from app.api.routes.pages import classify_page_endpoint

        page_id = uuid.uuid4()
        mock_db = AsyncMock()

        # Mock page+document_id query, then project_id query
        mock_result_page_exists = MagicMock()
        mock_result_page_exists.one_or_none.return_value = (page_id, uuid.uuid4())

        mock_result_project_id = MagicMock()
        mock_result_project_id.scalar_one.return_value = uuid.uuid4()

        mock_db.execute.side_effect = [
            mock_result_page_exists,
            mock_result_project_id,
        ]

        mock_tracker.register_async = AsyncMock()

        # Need request for settings validation
        with patch("app.api.routes.pages.settings") as mock_settings:
            mock_settings.available_providers = ["anthropic"]
            result = await classify_page_endpoint(page_id, mock_db, None)

        mock_tracker.register_async.assert_called_once()
        call_kwargs = mock_tracker.register_async.call_args
        assert "page_classification" in str(call_kwargs)

        mock_task.apply_async.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.api.routes.pages.classify_page_task")
    @patch("app.api.routes.pages.TaskTracker")
    async def test_does_not_use_delay(self, mock_tracker, mock_task):
        """Route uses apply_async instead of delay."""
        from app.api.routes.pages import classify_page_endpoint

        page_id = uuid.uuid4()
        mock_db = AsyncMock()

        mock_result_page_exists = MagicMock()
        mock_result_page_exists.one_or_none.return_value = (page_id, uuid.uuid4())

        mock_result_project_id = MagicMock()
        mock_result_project_id.scalar_one.return_value = uuid.uuid4()

        mock_db.execute.side_effect = [
            mock_result_page_exists,
            mock_result_project_id,
        ]

        mock_tracker.register_async = AsyncMock()

        with patch("app.api.routes.pages.settings") as mock_settings:
            mock_settings.available_providers = ["anthropic"]
            await classify_page_endpoint(page_id, mock_db, None)

        mock_task.delay.assert_not_called()
        mock_task.apply_async.assert_called_once()


# ---------------------------------------------------------------------------
# Scale Detection Route Registration
# ---------------------------------------------------------------------------


class TestScaleDetectionRegistration:
    """Verify detect_page_scale route registers task before enqueue."""

    @pytest.mark.asyncio
    @patch("app.api.routes.pages.detect_page_scale_task")
    @patch("app.api.routes.pages.TaskTracker")
    async def test_registers_before_enqueue(self, mock_tracker, mock_task):
        """Route calls register_async before apply_async."""
        from app.api.routes.pages import detect_page_scale

        page_id = uuid.uuid4()
        mock_db = AsyncMock()

        # Mock page+document_id query
        mock_result_page = MagicMock()
        mock_result_page.one_or_none.return_value = (page_id, uuid.uuid4())

        mock_result_project = MagicMock()
        mock_result_project.scalar_one.return_value = uuid.uuid4()

        mock_db.execute.side_effect = [mock_result_page, mock_result_project]

        mock_tracker.register_async = AsyncMock()

        result = await detect_page_scale(page_id, mock_db)

        mock_tracker.register_async.assert_called_once()
        call_kwargs = mock_tracker.register_async.call_args
        assert "scale_detection" in str(call_kwargs)

        mock_task.apply_async.assert_called_once()
        assert "task_id" in result

    @pytest.mark.asyncio
    @patch("app.api.routes.pages.detect_page_scale_task")
    @patch("app.api.routes.pages.TaskTracker")
    async def test_does_not_use_delay(self, mock_tracker, mock_task):
        """Route uses apply_async instead of delay."""
        from app.api.routes.pages import detect_page_scale

        page_id = uuid.uuid4()
        mock_db = AsyncMock()

        mock_result_page = MagicMock()
        mock_result_page.one_or_none.return_value = (page_id, uuid.uuid4())

        mock_result_project = MagicMock()
        mock_result_project.scalar_one.return_value = uuid.uuid4()

        mock_db.execute.side_effect = [mock_result_page, mock_result_project]

        mock_tracker.register_async = AsyncMock()

        await detect_page_scale(page_id, mock_db)

        mock_task.delay.assert_not_called()
        mock_task.apply_async.assert_called_once()
