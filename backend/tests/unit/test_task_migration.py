"""Tests for TaskTracker integration in all Celery workers.

Verifies that each worker task properly calls TaskTracker methods
at the correct lifecycle points: started, progress, completed, failed.
"""

import uuid
from unittest.mock import patch, MagicMock, PropertyMock

import celery.app.task
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_session():
    """Create a mock sync database session."""
    session = MagicMock()
    session.new = set()
    session.dirty = set()
    session.deleted = set()
    return session


def _make_mock_request(task_id=None, retries=0):
    """Create a mock Celery request object."""
    mock_req = MagicMock()
    mock_req.id = task_id or str(uuid.uuid4())
    mock_req.retries = retries
    return mock_req


# ---------------------------------------------------------------------------
# Document Task Tracking
# ---------------------------------------------------------------------------

class TestDocumentTaskTracking:
    """Verify process_document_task calls TaskTracker correctly."""

    @patch("app.workers.document_tasks.SyncSession")
    @patch("app.workers.document_tasks.get_storage_service")
    @patch("app.workers.document_tasks.get_document_processor")
    @patch("app.workers.document_tasks.TaskTracker")
    def test_marks_started_on_entry(
        self, mock_tracker, mock_processor, mock_storage, mock_session_cls
    ):
        """Task calls mark_started_sync at the beginning."""
        from app.workers.document_tasks import process_document_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_doc = MagicMock()
        mock_doc.storage_key = "test-key"
        mock_doc.file_type = "pdf"
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_doc

        mock_processor.return_value.process_document.return_value = []
        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_document_task, 'update_state', MagicMock()):
            process_document_task.__wrapped__(str(uuid.uuid4()), str(uuid.uuid4()))

        mock_tracker.mark_started_sync.assert_called_once_with(
            session, task_id
        )

    @patch("app.workers.document_tasks.SyncSession")
    @patch("app.workers.document_tasks.get_storage_service")
    @patch("app.workers.document_tasks.get_document_processor")
    @patch("app.workers.document_tasks.TaskTracker")
    def test_marks_completed_on_success(
        self, mock_tracker, mock_processor, mock_storage, mock_session_cls
    ):
        """Task calls mark_completed_sync with result summary on success."""
        from app.workers.document_tasks import process_document_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_doc = MagicMock()
        mock_doc.storage_key = "test-key"
        mock_doc.file_type = "pdf"
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_doc

        mock_processor.return_value.process_document.return_value = [
            {
                "id": uuid.uuid4(),
                "page_number": 1,
                "width": 100,
                "height": 100,
                "dpi": 150,
                "image_key": "k",
                "thumbnail_key": "t",
            }
        ]
        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        doc_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_document_task, 'update_state', MagicMock()):
            result = process_document_task.__wrapped__(doc_id, str(uuid.uuid4()))

        mock_tracker.mark_completed_sync.assert_called_once_with(
            session,
            task_id,
            {"document_id": doc_id, "page_count": 1},
            commit=False,
        )
        assert result["page_count"] == 1

    @patch("app.workers.document_tasks.SyncSession")
    @patch("app.workers.document_tasks.get_storage_service")
    @patch("app.workers.document_tasks.get_document_processor")
    @patch("app.workers.document_tasks.TaskTracker")
    def test_marks_failed_on_validation_error(
        self, mock_tracker, mock_processor, mock_storage, mock_session_cls
    ):
        """Task calls mark_failed_sync on ValueError (not retried)."""
        from app.workers.document_tasks import process_document_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Document not found
        session.query.return_value.filter.return_value.one_or_none.return_value = None

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_document_task, 'update_state', MagicMock()):
            with pytest.raises(ValueError):
                process_document_task.__wrapped__(str(uuid.uuid4()), str(uuid.uuid4()))

        mock_tracker.mark_failed_sync.assert_called_once()

    @patch("app.workers.document_tasks.SyncSession")
    @patch("app.workers.document_tasks.get_storage_service")
    @patch("app.workers.document_tasks.get_document_processor")
    @patch("app.workers.document_tasks.TaskTracker")
    def test_does_not_mark_failed_during_retry(
        self, mock_tracker, mock_processor, mock_storage, mock_session_cls
    ):
        """Task does NOT call mark_failed_sync when retrying."""
        from app.workers.document_tasks import process_document_task
        from celery.exceptions import Retry

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_doc = MagicMock()
        mock_doc.storage_key = "test-key"
        mock_doc.file_type = "pdf"
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_doc

        mock_storage.return_value.download_file.side_effect = RuntimeError("network error")

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_document_task, 'update_state', MagicMock()), \
             patch.object(process_document_task, 'retry', side_effect=Retry()):
            with pytest.raises(Retry):
                process_document_task.__wrapped__(str(uuid.uuid4()), str(uuid.uuid4()))

        mock_tracker.mark_failed_sync.assert_not_called()

    @patch("app.workers.document_tasks.SyncSession")
    @patch("app.workers.document_tasks.get_storage_service")
    @patch("app.workers.document_tasks.get_document_processor")
    @patch("app.workers.document_tasks.TaskTracker")
    def test_progress_updates_at_expected_points(
        self, mock_tracker, mock_processor, mock_storage, mock_session_cls
    ):
        """Task calls update_progress_sync at defined percentage steps."""
        from app.workers.document_tasks import process_document_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_doc = MagicMock()
        mock_doc.storage_key = "test-key"
        mock_doc.file_type = "pdf"
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_doc

        mock_processor.return_value.process_document.return_value = []
        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_document_task, 'update_state', MagicMock()):
            process_document_task.__wrapped__(str(uuid.uuid4()), str(uuid.uuid4()))

        progress_calls = mock_tracker.update_progress_sync.call_args_list
        percents = [call[0][2] for call in progress_calls]
        assert 10 in percents  # Downloading file
        assert 40 in percents  # Extracting pages
        assert 70 in percents  # Saving page records
        assert 90 in percents  # Queueing OCR

# ---------------------------------------------------------------------------
# OCR Task Tracking
# ---------------------------------------------------------------------------

class TestOCRTaskTracking:
    """Verify process_page_ocr_task calls TaskTracker correctly."""

    @patch("app.workers.ocr_tasks.SyncSession")
    @patch("app.workers.ocr_tasks.get_storage_service")
    @patch("app.workers.ocr_tasks.get_ocr_service")
    @patch("app.workers.ocr_tasks.get_title_block_parser")
    @patch("app.workers.ocr_tasks.TaskTracker")
    def test_marks_started_on_entry(
        self, mock_tracker, mock_parser, mock_ocr, mock_storage, mock_session_cls
    ):
        """Task calls mark_started_sync at the beginning."""
        from app.workers.ocr_tasks import process_page_ocr_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.status = "ready"
        mock_page.image_key = "test.tiff"
        mock_page.width = 100
        mock_page.height = 100
        mock_page.ocr_blocks = None
        mock_page.sheet_number = "S1"
        mock_page.title = "Test"
        mock_page.scale_text = None
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_page

        mock_ocr_result = MagicMock()
        mock_ocr_result.full_text = "test text"
        mock_ocr_result.blocks = []
        mock_ocr_result.detected_scale_texts = []
        mock_ocr_result.detected_sheet_numbers = []
        mock_ocr_result.detected_titles = []
        mock_ocr.return_value.extract_text.return_value = mock_ocr_result

        mock_parser.return_value.parse_title_block.return_value = {}

        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_page_ocr_task, 'update_state', MagicMock()):
            process_page_ocr_task.__wrapped__(str(uuid.uuid4()))

        mock_tracker.mark_started_sync.assert_called_once_with(
            session, task_id
        )

    @patch("app.workers.ocr_tasks.SyncSession")
    @patch("app.workers.ocr_tasks.get_storage_service")
    @patch("app.workers.ocr_tasks.get_ocr_service")
    @patch("app.workers.ocr_tasks.get_title_block_parser")
    @patch("app.workers.ocr_tasks.TaskTracker")
    def test_marks_completed_on_success(
        self, mock_tracker, mock_parser, mock_ocr, mock_storage, mock_session_cls
    ):
        """Task calls mark_completed_sync with result summary on success."""
        from app.workers.ocr_tasks import process_page_ocr_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        page_id = str(uuid.uuid4())
        mock_page = MagicMock()
        mock_page.status = "ready"
        mock_page.image_key = "test.tiff"
        mock_page.width = 100
        mock_page.height = 100
        mock_page.ocr_blocks = None
        mock_page.sheet_number = "S1"
        mock_page.title = "Test"
        mock_page.scale_text = None
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_page

        mock_ocr_result = MagicMock()
        mock_ocr_result.full_text = "test text"
        mock_ocr_result.blocks = []
        mock_ocr_result.detected_scale_texts = []
        mock_ocr_result.detected_sheet_numbers = []
        mock_ocr_result.detected_titles = []
        mock_ocr.return_value.extract_text.return_value = mock_ocr_result

        mock_parser.return_value.parse_title_block.return_value = {}

        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_page_ocr_task, 'update_state', MagicMock()):
            process_page_ocr_task.__wrapped__(page_id)

        mock_tracker.mark_completed_sync.assert_called_once()
        call_args = mock_tracker.mark_completed_sync.call_args
        assert call_args[0][1] == task_id

    @patch("app.workers.ocr_tasks.SyncSession")
    @patch("app.workers.ocr_tasks.TaskTracker")
    def test_marks_failed_on_validation_error(
        self, mock_tracker, mock_session_cls
    ):
        """Task calls mark_failed_sync on ValueError."""
        from app.workers.ocr_tasks import process_page_ocr_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Page not found
        session.query.return_value.filter.return_value.one_or_none.return_value = None

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_page_ocr_task, 'update_state', MagicMock()):
            with pytest.raises(ValueError):
                process_page_ocr_task.__wrapped__(str(uuid.uuid4()))

        mock_tracker.mark_failed_sync.assert_called_once()

    @patch("app.workers.ocr_tasks.SyncSession")
    @patch("app.workers.ocr_tasks.get_storage_service")
    @patch("app.workers.ocr_tasks.get_ocr_service")
    @patch("app.workers.ocr_tasks.get_title_block_parser")
    @patch("app.workers.ocr_tasks.TaskTracker")
    def test_does_not_mark_failed_during_retry(
        self, mock_tracker, mock_parser, mock_ocr, mock_storage, mock_session_cls
    ):
        """Task does NOT call mark_failed_sync when retrying."""
        from app.workers.ocr_tasks import process_page_ocr_task
        from celery.exceptions import Retry

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.status = "ready"
        mock_page.image_key = "test.tiff"
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_page

        mock_storage.return_value.download_file.side_effect = RuntimeError("network error")

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_page_ocr_task, 'update_state', MagicMock()), \
             patch.object(process_page_ocr_task, 'retry', side_effect=Retry()):
            with pytest.raises(Retry):
                process_page_ocr_task.__wrapped__(str(uuid.uuid4()))

        mock_tracker.mark_failed_sync.assert_not_called()

    @patch("app.workers.ocr_tasks.SyncSession")
    @patch("app.workers.ocr_tasks.get_storage_service")
    @patch("app.workers.ocr_tasks.get_ocr_service")
    @patch("app.workers.ocr_tasks.get_title_block_parser")
    @patch("app.workers.ocr_tasks.TaskTracker")
    def test_progress_updates_at_expected_points(
        self, mock_tracker, mock_parser, mock_ocr, mock_storage, mock_session_cls
    ):
        """Task calls update_progress_sync at defined percentage steps."""
        from app.workers.ocr_tasks import process_page_ocr_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.status = "ready"
        mock_page.image_key = "test.tiff"
        mock_page.width = 100
        mock_page.height = 100
        mock_page.ocr_blocks = None
        mock_page.sheet_number = "S1"
        mock_page.title = "Test"
        mock_page.scale_text = None
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_page

        mock_ocr_result = MagicMock()
        mock_ocr_result.full_text = "test text"
        mock_ocr_result.blocks = []
        mock_ocr_result.detected_scale_texts = []
        mock_ocr_result.detected_sheet_numbers = []
        mock_ocr_result.detected_titles = []
        mock_ocr.return_value.extract_text.return_value = mock_ocr_result

        mock_parser.return_value.parse_title_block.return_value = {}
        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(process_page_ocr_task, 'update_state', MagicMock()):
            process_page_ocr_task.__wrapped__(str(uuid.uuid4()))

        progress_calls = mock_tracker.update_progress_sync.call_args_list
        percents = [call[0][2] for call in progress_calls]
        assert 10 in percents  # Downloading page image
        assert 40 in percents  # Running OCR
        assert 70 in percents  # Parsing title block
        assert 90 in percents  # Saving results

# ---------------------------------------------------------------------------
# Classification Task Tracking
# ---------------------------------------------------------------------------

class TestClassificationTaskTracking:
    """Verify classify_page_task calls TaskTracker correctly."""

    @patch("app.workers.classification_tasks.SyncSession")
    @patch("app.workers.classification_tasks.get_ocr_classifier")
    @patch("app.workers.classification_tasks.TaskTracker")
    def test_marks_started_on_entry(
        self, mock_tracker, mock_classifier, mock_session_cls
    ):
        """Task calls mark_started_sync at the beginning."""
        from app.workers.classification_tasks import classify_page_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.ocr_text = "test ocr text"
        mock_page.sheet_number = "S1"
        mock_page.title = "Structural"
        mock_page.document_id = uuid.uuid4()
        session.execute.return_value.scalar_one_or_none.return_value = mock_page

        mock_result = MagicMock()
        mock_result.discipline = "structural"
        mock_result.discipline_confidence = 0.95
        mock_result.page_type = "plan"
        mock_result.page_type_confidence = 0.90
        mock_result.concrete_relevance = "high"
        mock_result.concrete_elements = ["slab"]
        mock_result.description = "test"
        mock_classifier.return_value.classify_from_ocr.return_value = mock_result

        # Mock the document query for updated_at
        mock_doc = MagicMock()
        session.execute.return_value.scalar_one.return_value = mock_doc

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(classify_page_task, 'update_state', MagicMock()):
            classify_page_task.__wrapped__(str(uuid.uuid4()))

        mock_tracker.mark_started_sync.assert_called_once_with(
            session, task_id
        )

    @patch("app.workers.classification_tasks.SyncSession")
    @patch("app.workers.classification_tasks.get_ocr_classifier")
    @patch("app.workers.classification_tasks.TaskTracker")
    def test_marks_completed_on_success(
        self, mock_tracker, mock_classifier, mock_session_cls
    ):
        """Task calls mark_completed_sync with result summary on success."""
        from app.workers.classification_tasks import classify_page_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        page_id = str(uuid.uuid4())
        mock_page = MagicMock()
        mock_page.ocr_text = "test ocr text"
        mock_page.sheet_number = "S1"
        mock_page.title = "Structural"
        mock_page.document_id = uuid.uuid4()
        session.execute.return_value.scalar_one_or_none.return_value = mock_page

        mock_result = MagicMock()
        mock_result.discipline = "structural"
        mock_result.discipline_confidence = 0.95
        mock_result.page_type = "plan"
        mock_result.page_type_confidence = 0.90
        mock_result.concrete_relevance = "high"
        mock_result.concrete_elements = ["slab"]
        mock_result.description = "test"
        mock_result.llm_provider = "ocr"
        mock_result.llm_model = "google-cloud-vision"
        mock_result.llm_latency_ms = 100
        mock_classifier.return_value.classify_from_ocr.return_value = mock_result

        mock_doc = MagicMock()
        session.execute.return_value.scalar_one.return_value = mock_doc

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(classify_page_task, 'update_state', MagicMock()):
            classify_page_task.__wrapped__(page_id)

        mock_tracker.mark_completed_sync.assert_called_once()

    @patch("app.workers.classification_tasks.SyncSession")
    @patch("app.workers.classification_tasks.TaskTracker")
    def test_marks_failed_on_error(
        self, mock_tracker, mock_session_cls
    ):
        """Task calls mark_failed_sync on unrecoverable error."""
        from app.workers.classification_tasks import classify_page_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Page not found
        session.execute.return_value.scalar_one_or_none.return_value = None

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(classify_page_task, 'update_state', MagicMock()):
            with pytest.raises(ValueError):
                classify_page_task.__wrapped__(str(uuid.uuid4()))

        # max_retries=0, so mark_failed_sync is called directly
        mock_tracker.mark_failed_sync.assert_called_once()

    @patch("app.workers.classification_tasks.SyncSession")
    @patch("app.workers.classification_tasks.get_ocr_classifier")
    @patch("app.workers.classification_tasks.TaskTracker")
    def test_progress_updates_at_expected_points(
        self, mock_tracker, mock_classifier, mock_session_cls
    ):
        """Task calls update_progress_sync at defined percentage steps."""
        from app.workers.classification_tasks import classify_page_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.ocr_text = "test ocr text"
        mock_page.sheet_number = "S1"
        mock_page.title = "Structural"
        mock_page.document_id = uuid.uuid4()
        session.execute.return_value.scalar_one_or_none.return_value = mock_page

        mock_result = MagicMock()
        mock_result.discipline = "structural"
        mock_result.discipline_confidence = 0.95
        mock_result.page_type = "plan"
        mock_result.page_type_confidence = 0.90
        mock_result.concrete_relevance = "high"
        mock_result.concrete_elements = ["slab"]
        mock_result.description = "test"
        mock_result.llm_provider = "ocr"
        mock_result.llm_model = "google-cloud-vision"
        mock_result.llm_latency_ms = 100
        mock_classifier.return_value.classify_from_ocr.return_value = mock_result

        mock_doc = MagicMock()
        session.execute.return_value.scalar_one.return_value = mock_doc

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(classify_page_task, 'update_state', MagicMock()):
            classify_page_task.__wrapped__(str(uuid.uuid4()))

        progress_calls = mock_tracker.update_progress_sync.call_args_list
        percents = [call[0][2] for call in progress_calls]
        assert 10 in percents  # Loading page data
        assert 30 in percents  # Running classification
        assert 70 in percents  # Updating page record
        assert 90 in percents  # Saving classification history

# ---------------------------------------------------------------------------
# Scale Detection Task Tracking
# ---------------------------------------------------------------------------

class TestScaleDetectionTaskTracking:
    """Verify detect_page_scale_task calls TaskTracker correctly."""

    @patch("app.workers.scale_tasks.SyncSession")
    @patch("app.workers.scale_tasks.get_storage_service")
    @patch("app.workers.scale_tasks.get_scale_detector")
    @patch("app.workers.scale_tasks.TaskTracker")
    def test_marks_started_on_entry(
        self, mock_tracker, mock_detector, mock_storage, mock_session_cls
    ):
        """Task calls mark_started_sync at the beginning."""
        from app.workers.scale_tasks import detect_page_scale_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.image_key = "test.tiff"
        mock_page.ocr_blocks = {"blocks": [], "detected_scales": []}
        mock_page.ocr_text = "test"
        mock_page.page_width_inches = None
        mock_page.scale_calibration_data = None
        mock_page.scale_text = None
        mock_page.scale_value = None
        mock_page.scale_calibrated = False
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_page

        mock_detector.return_value.detect_scale.return_value = {"best_scale": None}
        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(detect_page_scale_task, 'update_state', MagicMock()):
            detect_page_scale_task.__wrapped__(str(uuid.uuid4()))

        mock_tracker.mark_started_sync.assert_called_once_with(
            session, task_id
        )

    @patch("app.workers.scale_tasks.SyncSession")
    @patch("app.workers.scale_tasks.get_storage_service")
    @patch("app.workers.scale_tasks.get_scale_detector")
    @patch("app.workers.scale_tasks.TaskTracker")
    def test_marks_completed_on_success(
        self, mock_tracker, mock_detector, mock_storage, mock_session_cls
    ):
        """Task calls mark_completed_sync with result summary on success."""
        from app.workers.scale_tasks import detect_page_scale_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.image_key = "test.tiff"
        mock_page.ocr_blocks = {"blocks": [], "detected_scales": []}
        mock_page.ocr_text = "test"
        mock_page.page_width_inches = None
        mock_page.scale_calibration_data = None
        mock_page.scale_text = "1/4\" = 1'-0\""
        mock_page.scale_value = 10.5
        mock_page.scale_calibrated = True
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_page

        mock_detector.return_value.detect_scale.return_value = {
            "best_scale": {
                "text": "1/4\" = 1'-0\"",
                "confidence": 0.95,
            }
        }
        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(detect_page_scale_task, 'update_state', MagicMock()):
            detect_page_scale_task.__wrapped__(str(uuid.uuid4()))

        mock_tracker.mark_completed_sync.assert_called_once()

    @patch("app.workers.scale_tasks.SyncSession")
    @patch("app.workers.scale_tasks.TaskTracker")
    def test_marks_failed_on_validation_error(
        self, mock_tracker, mock_session_cls
    ):
        """Task calls mark_failed_sync on ValueError."""
        from app.workers.scale_tasks import detect_page_scale_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Page not found
        session.query.return_value.filter.return_value.one_or_none.return_value = None

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(detect_page_scale_task, 'update_state', MagicMock()):
            with pytest.raises(ValueError):
                detect_page_scale_task.__wrapped__(str(uuid.uuid4()))

        mock_tracker.mark_failed_sync.assert_called_once()

    @patch("app.workers.scale_tasks.SyncSession")
    @patch("app.workers.scale_tasks.get_storage_service")
    @patch("app.workers.scale_tasks.get_scale_detector")
    @patch("app.workers.scale_tasks.TaskTracker")
    def test_does_not_mark_failed_during_retry(
        self, mock_tracker, mock_detector, mock_storage, mock_session_cls
    ):
        """Task does NOT call mark_failed_sync when retrying."""
        from app.workers.scale_tasks import detect_page_scale_task
        from celery.exceptions import Retry

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.image_key = "test.tiff"
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_page

        mock_storage.return_value.download_file.side_effect = RuntimeError("fail")

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(detect_page_scale_task, 'update_state', MagicMock()), \
             patch.object(detect_page_scale_task, 'retry', side_effect=Retry()):
            with pytest.raises(Retry):
                detect_page_scale_task.__wrapped__(str(uuid.uuid4()))

        mock_tracker.mark_failed_sync.assert_not_called()

    @patch("app.workers.scale_tasks.SyncSession")
    @patch("app.workers.scale_tasks.get_storage_service")
    @patch("app.workers.scale_tasks.get_scale_detector")
    @patch("app.workers.scale_tasks.TaskTracker")
    def test_progress_updates_at_expected_points(
        self, mock_tracker, mock_detector, mock_storage, mock_session_cls
    ):
        """Task calls update_progress_sync at defined percentage steps."""
        from app.workers.scale_tasks import detect_page_scale_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.image_key = "test.tiff"
        mock_page.ocr_blocks = {"blocks": [], "detected_scales": []}
        mock_page.ocr_text = "test"
        mock_page.page_width_inches = None
        mock_page.scale_calibration_data = None
        mock_page.scale_text = None
        mock_page.scale_value = None
        mock_page.scale_calibrated = False
        session.query.return_value.filter.return_value.one_or_none.return_value = mock_page

        mock_detector.return_value.detect_scale.return_value = {"best_scale": None}
        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(detect_page_scale_task, 'update_state', MagicMock()):
            detect_page_scale_task.__wrapped__(str(uuid.uuid4()))

        progress_calls = mock_tracker.update_progress_sync.call_args_list
        percents = [call[0][2] for call in progress_calls]
        assert 10 in percents  # Loading page data
        assert 30 in percents  # Downloading image
        assert 60 in percents  # Detecting scale
        assert 90 in percents  # Saving results

# ---------------------------------------------------------------------------
# Autonomous Takeoff Task Tracking
# ---------------------------------------------------------------------------

class TestAutonomousTakeoffTaskTracking:
    """Verify autonomous_ai_takeoff_task calls TaskTracker correctly."""

    @patch("app.workers.takeoff_tasks.SyncSession")
    @patch("app.workers.takeoff_tasks.get_storage_service")
    @patch("app.workers.takeoff_tasks.get_ai_takeoff_service")
    @patch("app.workers.takeoff_tasks.TaskTracker")
    def test_marks_started_on_entry(
        self, mock_tracker, mock_ai, mock_storage, mock_session_cls
    ):
        """Task calls mark_started_sync at the beginning."""
        from app.workers.takeoff_tasks import autonomous_ai_takeoff_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.scale_calibrated = True
        mock_page.scale_value = 10.0
        mock_page.document_id = uuid.uuid4()
        mock_page.image_key = "test.tiff"

        mock_doc = MagicMock()
        mock_doc.project_id = uuid.uuid4()

        session.query.return_value.filter.return_value.one_or_none.return_value = mock_page
        session.query.return_value.filter.return_value.one.return_value = mock_doc

        mock_ai_result = MagicMock()
        mock_ai_result.elements = []
        mock_ai_result.page_description = "test"
        mock_ai_result.analysis_notes = "test"
        mock_ai_result.llm_provider = "anthropic"
        mock_ai_result.llm_model = "claude"
        mock_ai_result.llm_latency_ms = 100
        mock_ai.return_value.analyze_page_autonomous.return_value = mock_ai_result

        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(autonomous_ai_takeoff_task, 'update_state', MagicMock()):
            autonomous_ai_takeoff_task.__wrapped__(
                str(uuid.uuid4()), project_id=str(mock_doc.project_id)
            )

        mock_tracker.mark_started_sync.assert_called_once()

    @patch("app.workers.takeoff_tasks.SyncSession")
    @patch("app.workers.takeoff_tasks.get_storage_service")
    @patch("app.workers.takeoff_tasks.get_ai_takeoff_service")
    @patch("app.workers.takeoff_tasks.TaskTracker")
    def test_progress_updates_at_expected_points(
        self, mock_tracker, mock_ai, mock_storage, mock_session_cls
    ):
        """Task reports progress at loading, AI analysis, measurements, and finalizing."""
        from app.workers.takeoff_tasks import autonomous_ai_takeoff_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.scale_calibrated = True
        mock_page.scale_value = 10.0
        mock_page.document_id = uuid.uuid4()
        mock_page.image_key = "test.tiff"

        mock_doc = MagicMock()
        mock_doc.project_id = uuid.uuid4()

        session.query.return_value.filter.return_value.one_or_none.return_value = mock_page
        session.query.return_value.filter.return_value.one.return_value = mock_doc

        mock_ai_result = MagicMock()
        mock_ai_result.elements = []
        mock_ai_result.page_description = "test"
        mock_ai_result.analysis_notes = "test"
        mock_ai_result.llm_provider = "anthropic"
        mock_ai_result.llm_model = "claude"
        mock_ai_result.llm_latency_ms = 100
        mock_ai.return_value.analyze_page_autonomous.return_value = mock_ai_result

        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(autonomous_ai_takeoff_task, 'update_state', MagicMock()):
            autonomous_ai_takeoff_task.__wrapped__(
                str(uuid.uuid4()), project_id=str(mock_doc.project_id)
            )

        progress_calls = mock_tracker.update_progress_sync.call_args_list
        percents = [call[0][2] for call in progress_calls]
        assert 10 in percents  # Loading
        assert 30 in percents  # AI analysis
        assert 70 in percents  # Creating measurements
        assert 90 in percents  # Finalizing

# ---------------------------------------------------------------------------
# Compare Providers Task Tracking
# ---------------------------------------------------------------------------

class TestCompareProvidersTaskTracking:
    """Verify compare_providers_task calls TaskTracker correctly."""

    @patch("app.workers.takeoff_tasks.SyncSession")
    @patch("app.workers.takeoff_tasks.get_storage_service")
    @patch("app.workers.takeoff_tasks.get_ai_takeoff_service")
    @patch("app.workers.takeoff_tasks.TaskTracker")
    def test_marks_started_on_entry(
        self, mock_tracker, mock_ai, mock_storage, mock_session_cls
    ):
        """Task calls mark_started_sync at the beginning."""
        from app.workers.takeoff_tasks import compare_providers_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.scale_calibrated = True
        mock_page.image_key = "test.tiff"
        mock_page.width = 100
        mock_page.height = 100
        mock_page.scale_text = "1/4\" = 1'-0\""
        mock_page.ocr_text = "test"

        mock_condition = MagicMock()
        mock_condition.name = "Slab"
        mock_condition.measurement_type = "area"

        session.query.return_value.filter.return_value.one_or_none.side_effect = [
            mock_page,
            mock_condition,
        ]

        mock_ai.return_value.analyze_page_multi_provider.return_value = {}
        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(compare_providers_task, 'update_state', MagicMock()):
            compare_providers_task.__wrapped__(
                str(uuid.uuid4()), str(uuid.uuid4()), providers=[]
            )

        mock_tracker.mark_started_sync.assert_called_once()

    @patch("app.workers.takeoff_tasks.SyncSession")
    @patch("app.workers.takeoff_tasks.get_storage_service")
    @patch("app.workers.takeoff_tasks.get_ai_takeoff_service")
    @patch("app.workers.takeoff_tasks.TaskTracker")
    def test_marks_completed_on_success(
        self, mock_tracker, mock_ai, mock_storage, mock_session_cls
    ):
        """Task calls mark_completed_sync on success."""
        from app.workers.takeoff_tasks import compare_providers_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.scale_calibrated = True
        mock_page.image_key = "test.tiff"
        mock_page.width = 100
        mock_page.height = 100
        mock_page.scale_text = "test"
        mock_page.ocr_text = "test"

        mock_condition = MagicMock()
        mock_condition.name = "Slab"
        mock_condition.measurement_type = "area"

        session.query.return_value.filter.return_value.one_or_none.side_effect = [
            mock_page,
            mock_condition,
        ]

        mock_ai.return_value.analyze_page_multi_provider.return_value = {}
        mock_storage.return_value.download_file.return_value = b"fake-bytes"

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(compare_providers_task, 'update_state', MagicMock()):
            compare_providers_task.__wrapped__(
                str(uuid.uuid4()), str(uuid.uuid4()), providers=[]
            )

        mock_tracker.mark_completed_sync.assert_called_once()

# ---------------------------------------------------------------------------
# Batch Takeoff Task Tracking
# ---------------------------------------------------------------------------

class TestBatchTakeoffTaskTracking:
    """Verify batch_ai_takeoff_task calls TaskTracker correctly."""

    @patch("app.workers.takeoff_tasks.generate_ai_takeoff_task")
    @patch("app.workers.takeoff_tasks.SyncSession")
    @patch("app.workers.takeoff_tasks.TaskTracker")
    def test_marks_started_on_entry(
        self, mock_tracker, mock_session_cls, mock_gen_task
    ):
        """Task calls mark_started_sync at the beginning."""
        from app.workers.takeoff_tasks import batch_ai_takeoff_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_gen_task.delay.return_value = MagicMock(id="sub-task-id")

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(batch_ai_takeoff_task, 'update_state', MagicMock()):
            batch_ai_takeoff_task.__wrapped__(
                [str(uuid.uuid4())], str(uuid.uuid4())
            )

        mock_tracker.mark_started_sync.assert_called()

    @patch("app.workers.takeoff_tasks.generate_ai_takeoff_task")
    @patch("app.workers.takeoff_tasks.SyncSession")
    @patch("app.workers.takeoff_tasks.TaskTracker")
    def test_marks_completed_on_success(
        self, mock_tracker, mock_session_cls, mock_gen_task
    ):
        """Task calls mark_completed_sync on success."""
        from app.workers.takeoff_tasks import batch_ai_takeoff_task

        session = _make_mock_session()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_gen_task.delay.return_value = MagicMock(id="sub-task-id")

        task_id = str(uuid.uuid4())
        mock_req = _make_mock_request(task_id)

        with patch.object(celery.app.task.Task, 'request', new_callable=PropertyMock, return_value=mock_req), \
             patch.object(batch_ai_takeoff_task, 'update_state', MagicMock()):
            batch_ai_takeoff_task.__wrapped__(
                [str(uuid.uuid4())], str(uuid.uuid4())
            )

        mock_tracker.mark_completed_sync.assert_called()
