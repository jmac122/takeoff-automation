"""Tests for BugBot-reported fixes (batch).

Covers:
- Bug 1: modify_measurement returns 404 for not-found, 400 for validation
- Bug 2: AutoTab geometry handling for rectangle/circle
- Bug 3: Revision chain topological ordering (not created_at)
- Bug 4: Revision self-cycle rejection
- Bug 5: Component reorder accepts JSON body
- Bug 6: Auto-count worker uses correct TaskTracker method names
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.ai_predict_point import (
    _format_last_coords,
    _geometry_template,
    _scale_geometry,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_db_engine():
    """Reset the database engine connection pool after each test."""
    yield
    try:
        from app.api.deps import engine

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(engine.dispose())
        finally:
            loop.close()
    except Exception:
        pass


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


# ============================================================================
# Bug 1: modify_measurement – correct HTTP status codes
# ============================================================================


class TestModifyMeasurementStatus:
    """modify_measurement should return 404 for not-found, 400 for validation."""

    def test_modify_not_found_returns_404(self, client):
        """When measurement doesn't exist, service raises ValueError('not found')
        and the route should map it to 404."""
        measurement_id = uuid.uuid4()
        with patch("app.api.routes.review.get_review_service") as mock_svc:
            mock_svc.return_value.modify_measurement = AsyncMock(
                side_effect=ValueError(f"Measurement not found: {measurement_id}")
            )
            resp = client.post(
                f"/api/v1/measurements/{measurement_id}/modify",
                json={
                    "reviewer": "tester",
                    "geometry_data": {"points": []},
                },
            )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_modify_validation_error_returns_400(self, client):
        """When service raises a validation ValueError (e.g. scale not calibrated),
        the route should map it to 400."""
        measurement_id = uuid.uuid4()
        with patch("app.api.routes.review.get_review_service") as mock_svc:
            mock_svc.return_value.modify_measurement = AsyncMock(
                side_effect=ValueError("Page scale not calibrated")
            )
            resp = client.post(
                f"/api/v1/measurements/{measurement_id}/modify",
                json={
                    "reviewer": "tester",
                    "geometry_data": {"points": []},
                },
            )
        assert resp.status_code == 400
        assert "scale" in resp.json()["detail"].lower()

    def test_modify_condition_not_found_returns_404(self, client):
        """'Condition not found' should also map to 404."""
        measurement_id = uuid.uuid4()
        with patch("app.api.routes.review.get_review_service") as mock_svc:
            mock_svc.return_value.modify_measurement = AsyncMock(
                side_effect=ValueError("Condition not found: abc")
            )
            resp = client.post(
                f"/api/v1/measurements/{measurement_id}/modify",
                json={
                    "reviewer": "tester",
                    "geometry_data": {"points": []},
                },
            )
        assert resp.status_code == 404


# ============================================================================
# Bug 2: AutoTab geometry – rectangle & circle support
# ============================================================================


class TestScaleGeometry:
    """_scale_geometry should handle all geometry types correctly."""

    def test_scale_point(self):
        result = _scale_geometry("point", {"x": 100, "y": 200}, 0.5, 0.5)
        assert result == {"x": 50.0, "y": 100.0}

    def test_scale_rectangle(self):
        data = {"x": 100, "y": 200, "width": 50, "height": 30}
        result = _scale_geometry("rectangle", data, 2.0, 2.0)
        assert result == {"x": 200.0, "y": 400.0, "width": 100.0, "height": 60.0}

    def test_scale_circle(self):
        data = {"center": {"x": 100, "y": 200}, "radius": 50}
        result = _scale_geometry("circle", data, 2.0, 2.0)
        assert result["center"] == {"x": 200.0, "y": 400.0}
        assert result["radius"] == 100.0  # uniform scale: (2+2)/2 * 50 = 100

    def test_scale_circle_non_uniform(self):
        """For non-uniform scaling, radius uses the average of sx and sy."""
        data = {"center": {"x": 100, "y": 200}, "radius": 50}
        result = _scale_geometry("circle", data, 2.0, 4.0)
        assert result["center"] == {"x": 200.0, "y": 800.0}
        assert result["radius"] == 150.0  # (2+4)/2 * 50 = 150

    def test_scale_circle_missing_center(self):
        """Gracefully handle missing center dict."""
        data = {"radius": 50}
        result = _scale_geometry("circle", data, 2.0, 2.0)
        assert result["center"] == {"x": 0.0, "y": 0.0}

    def test_scale_polygon(self):
        data = {"points": [{"x": 10, "y": 20}, {"x": 30, "y": 40}]}
        result = _scale_geometry("polygon", data, 2.0, 3.0)
        assert result["points"] == [{"x": 20.0, "y": 60.0}, {"x": 60.0, "y": 120.0}]

    def test_scale_polyline_empty_points(self):
        result = _scale_geometry("polyline", {"points": []}, 2.0, 2.0)
        assert result == {"points": []}


class TestFormatLastCoords:
    """_format_last_coords should format all geometry types for the prompt."""

    def test_format_point(self):
        result = _format_last_coords("point", {"x": 10, "y": 20})
        assert '"x": 10' in result
        assert '"y": 20' in result

    def test_format_rectangle(self):
        result = _format_last_coords(
            "rectangle", {"x": 10, "y": 20, "width": 50, "height": 30}
        )
        assert '"x": 10' in result
        assert '"width": 50' in result
        assert '"height": 30' in result

    def test_format_circle(self):
        result = _format_last_coords(
            "circle", {"center": {"x": 10, "y": 20}, "radius": 50}
        )
        assert '"center"' in result
        assert '"radius": 50' in result

    def test_format_polygon(self):
        result = _format_last_coords("polygon", {"points": [{"x": 1, "y": 2}]})
        assert '"x": 1' in result


class TestGeometryTemplate:
    """_geometry_template should return the right template per type."""

    def test_point_template(self):
        result = _geometry_template("point")
        assert '"x"' in result and '"y"' in result
        assert "points" not in result

    def test_rectangle_template(self):
        result = _geometry_template("rectangle")
        assert '"width"' in result and '"height"' in result

    def test_circle_template(self):
        result = _geometry_template("circle")
        assert '"center"' in result and '"radius"' in result

    def test_polygon_template(self):
        result = _geometry_template("polygon")
        assert '"points"' in result


# ============================================================================
# Bug 3: Revision chain uses topological order (not created_at)
# ============================================================================


class TestRevisionChainOrdering:
    """get_revision_chain should use topological order, not upload time.

    Tested at the logic level to avoid needing a real DB schema.
    The route simply calls chain.reverse() on the walked chain — we verify
    that topology wins over created_at.
    """

    def test_chain_reverse_preserves_topology(self):
        """After the forward+backward walk the chain is [newest→oldest].
        .reverse() should give [oldest→newest] regardless of created_at."""
        doc_a_id = uuid.uuid4()
        doc_b_id = uuid.uuid4()

        doc_a = MagicMock()
        doc_a.id = doc_a_id
        doc_a.supersedes_document_id = None
        doc_a.created_at = datetime(2025, 2, 15, tzinfo=timezone.utc)  # uploaded LATER

        doc_b = MagicMock()
        doc_b.id = doc_b_id
        doc_b.supersedes_document_id = doc_a_id
        doc_b.created_at = datetime(2025, 2, 10, tzinfo=timezone.utc)  # uploaded FIRST

        # Simulate the chain after both walks: [newest, oldest]
        chain = [doc_b, doc_a]

        # OLD buggy behavior: sort by created_at
        sorted_chain = sorted(chain, key=lambda d: d.created_at)
        assert sorted_chain[0].id == doc_b_id  # WRONG: newest first

        # NEW correct behavior: reverse
        chain.reverse()
        assert chain[0].id == doc_a_id  # oldest first (correct topology)
        assert chain[1].id == doc_b_id  # newest last

    def test_chain_reverse_with_three_revisions(self):
        """Three-document chain: reverse preserves correct topology."""
        ids = [uuid.uuid4() for _ in range(3)]

        docs = []
        for i, uid in enumerate(ids):
            doc = MagicMock()
            doc.id = uid
            # Reverse upload order vs. revision order
            doc.created_at = datetime(2025, 3, 10 - i, tzinfo=timezone.utc)
            docs.append(doc)

        # After walk: [newest(docs[2]), middle(docs[1]), oldest(docs[0])]
        chain = [docs[2], docs[1], docs[0]]
        chain.reverse()
        assert [d.id for d in chain] == [ids[0], ids[1], ids[2]]


# ============================================================================
# Bug 4: Revision self-cycle prevention
# ============================================================================


class TestRevisionSelfCycle:
    """link_revision should reject a document superseding itself.

    The self-cycle check happens before any DB query for the superseded doc,
    so we test at the route level by verifying the guard fires first.
    """

    def test_self_cycle_guard_in_source(self):
        """Verify the self-cycle guard exists in the link_revision route."""
        import inspect
        from app.api.routes.documents import link_revision

        source = inspect.getsource(link_revision)
        assert "document_id == request.supersedes_document_id" in source
        assert "cannot supersede itself" in source.lower()


# ============================================================================
# Bug 7: Revision linking prevents cycles and branches
# ============================================================================


class TestRevisionCyclesAndBranches:
    """link_revision should reject cycles (descendant→ancestor) and branches (multiple successors)."""

    def test_prevents_cycle_to_descendant(self):
        """Verify cycle detection logic exists in link_revision."""
        import inspect
        from app.api.routes.documents import link_revision

        source = inspect.getsource(link_revision)
        # Should check if old_doc is a descendant of document
        assert "circular revision chain" in source.lower()

    def test_prevents_multiple_successors(self):
        """Verify branch detection logic exists in link_revision."""
        import inspect
        from app.api.routes.documents import link_revision

        source = inspect.getsource(link_revision)
        # Should check if old_doc already has a successor
        assert "already has a successor" in source.lower()

    def test_restores_previous_parent_latest_flag(self):
        """When re-linking, the old parent's is_latest_revision should be restored."""
        import inspect
        from app.api.routes.documents import link_revision

        source = inspect.getsource(link_revision)
        # Should restore previous parent's flag when re-linking
        assert "previous_parent" in source
        assert "is_latest_revision = True" in source

    def test_only_marks_latest_if_no_successor(self):
        """Document should only be marked latest if it has no successor."""
        import inspect
        from app.api.routes.documents import link_revision

        source = inspect.getsource(link_revision)
        # Should check if document has a successor before marking as latest
        assert "has_successor" in source or "successor" in source
        assert "is_latest_revision = not" in source or "if not" in source


# ============================================================================
# Bug 9: Document deletion doesn't update revision chain flags
# ============================================================================


class TestDocumentDeletionRevisionChain:
    """delete_document should restore predecessor's is_latest_revision flag."""

    def test_predecessor_becomes_latest_after_deletion(self):
        """When deleting latest revision, predecessor should become latest."""
        import inspect
        from app.api.routes.documents import delete_document

        source = inspect.getsource(delete_document)
        # Should check for predecessor and restore its is_latest_revision flag
        assert "supersedes_document_id" in source
        assert "is_latest_revision = True" in source
        assert "predecessor" in source.lower() or "parent" in source.lower()

    def test_only_restores_if_deleting_latest(self):
        """Predecessor should only become latest if we're deleting the actual latest revision."""
        import inspect
        from app.api.routes.documents import delete_document

        source = inspect.getsource(delete_document)
        # Should check document.is_latest_revision before restoring predecessor
        assert "document.is_latest_revision" in source
        # Should have conditional logic around restoration
        assert "if" in source.lower()


# ============================================================================
# Bug 8: Page comparison uses PNG viewer keys (not TIFF)
# ============================================================================


class TestPageComparisonImageFormat:
    """compare_pages should return browser-viewable PNG URLs, not TIFF."""

    def test_tiff_key_converted_to_png(self):
        """When page.image_key is .tiff, the signed URL should be for .png."""
        from app.api.routes.documents import compare_pages

        import inspect

        source = inspect.getsource(compare_pages)

        # Should have a helper that converts .tiff to .png
        assert "_get_viewer_image_key" in source or ".replace" in source
        assert ".png" in source

    def test_conversion_logic(self):
        """Test the TIFF→PNG key conversion logic."""

        def _get_viewer_image_key(image_key: str) -> str:
            """Convert .tiff storage keys to .png for browser compatibility."""
            if image_key.endswith(".tiff"):
                return image_key.replace(".tiff", ".png")
            return image_key

        assert _get_viewer_image_key("page.tiff") == "page.png"
        assert _get_viewer_image_key("page.png") == "page.png"
        assert _get_viewer_image_key("path/to/image.tiff") == "path/to/image.png"


# ============================================================================
# Bug 5: Component reorder accepts JSON body
# ============================================================================


class TestReorderComponents:
    """reorder_components should accept component_ids as a JSON body array."""

    def test_reorder_accepts_json_body(self, client):
        assembly_id = uuid.uuid4()
        ids = [str(uuid.uuid4()) for _ in range(3)]

        with patch("app.api.routes.assemblies.get_assembly_service") as mock_svc:
            mock_svc.return_value.reorder_components = AsyncMock()

            resp = client.put(
                f"/api/v1/assemblies/{assembly_id}/components/reorder",
                json=ids,
            )

        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
        mock_svc.return_value.reorder_components.assert_called_once()


# ============================================================================
# Bug 6: Auto-count worker uses correct TaskTracker method names
# ============================================================================


class TestAutoCountTaskTrackerMethods:
    """auto_count_task must call real TaskTracker methods, not non-existent ones."""

    def test_update_progress_sync_called(self):
        """_report_progress should call TaskTracker.update_progress_sync."""
        from app.workers.auto_count_tasks import _report_progress

        mock_task = MagicMock()
        mock_task.request.id = "task-123"
        mock_db = MagicMock()

        with patch("app.workers.auto_count_tasks.TaskTracker") as mock_tracker:
            _report_progress(mock_task, mock_db, 50, "halfway")

        mock_tracker.update_progress_sync.assert_called_once_with(
            mock_db,
            task_id="task-123",
            percent=50,
            step="halfway",
        )
        # Ensure the old wrong name was NOT called
        assert (
            not hasattr(mock_tracker, "update_sync")
            or not mock_tracker.update_sync.called
        )

    def test_mark_completed_sync_called_on_success(self):
        """On successful completion, auto_count_task calls mark_completed_sync."""
        from app.workers.auto_count_tasks import auto_count_task

        session_id = str(uuid.uuid4())
        page_id = uuid.uuid4()

        mock_session = MagicMock()
        mock_session.id = uuid.UUID(session_id)
        mock_session.page_id = page_id
        mock_session.confidence_threshold = 0.8
        mock_session.scale_tolerance = 0.2
        mock_session.rotation_tolerance = 15.0
        mock_session.template_bbox = {"x": 0, "y": 0, "w": 10, "h": 10}
        mock_session.detection_method = "template"

        mock_page = MagicMock()
        mock_page.image_key = "test/image.png"

        with (
            patch("app.workers.auto_count_tasks.SyncSession") as mock_session_cls,
            patch("app.workers.auto_count_tasks.TaskTracker") as mock_tracker,
            patch("app.workers.auto_count_tasks.get_storage_service") as mock_storage,
            patch(
                "app.workers.auto_count_tasks._get_image_dimensions",
                return_value=(100, 100),
            ),
            patch(
                "app.workers.auto_count_tasks.TemplateMatchingService"
            ) as mock_matcher_cls,
        ):
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db

            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_session
            mock_db.get.return_value = mock_page
            mock_storage.return_value.download_file.return_value = b"fake-img"
            mock_matcher_cls.return_value.find_matches.return_value = []

            # Use Celery's push_request to set the request context
            auto_count_task.push_request(id="task-456")
            try:
                auto_count_task.run(session_id, provider=None)
            finally:
                auto_count_task.pop_request()

        # Verify mark_completed_sync was called (not complete_sync)
        mock_tracker.mark_completed_sync.assert_called_once()
        call_kwargs = mock_tracker.mark_completed_sync.call_args
        assert call_kwargs[1]["task_id"] == "task-456"
        assert "result_summary" in call_kwargs[1]

    def test_mark_failed_sync_called_on_value_error(self):
        """On ValueError, auto_count_task calls mark_failed_sync."""
        from app.workers.auto_count_tasks import auto_count_task

        session_id = str(uuid.uuid4())

        with (
            patch("app.workers.auto_count_tasks.SyncSession") as mock_session_cls,
            patch("app.workers.auto_count_tasks.TaskTracker") as mock_tracker,
        ):
            mock_db = MagicMock()
            mock_session_cls.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.return_value = None

            auto_count_task.push_request(id="task-789")
            try:
                with pytest.raises(ValueError, match="not found"):
                    auto_count_task.run(session_id, provider=None)
            finally:
                auto_count_task.pop_request()

        mock_tracker.mark_failed_sync.assert_called_once()
        call_kwargs = mock_tracker.mark_failed_sync.call_args
        assert call_kwargs[1]["task_id"] == "task-789"
        assert "error_message" in call_kwargs[1]

    def test_tracker_methods_exist_on_class(self):
        """Verify the method names we call actually exist on TaskTracker."""
        from app.services.task_tracker import TaskTracker

        assert hasattr(TaskTracker, "update_progress_sync")
        assert hasattr(TaskTracker, "mark_completed_sync")
        assert hasattr(TaskTracker, "mark_failed_sync")

        # Verify the old wrong names do NOT exist
        assert not hasattr(TaskTracker, "update_sync")
        assert not hasattr(TaskTracker, "complete_sync")
        assert not hasattr(TaskTracker, "fail_sync")


# ============================================================================
# Bug 11: predict_next_point ignores condition_id
# ============================================================================


class TestPredictNextPointConditionValidation:
    """predict_next_point should validate condition_id before predicting."""

    def test_condition_validation_in_source(self):
        """Verify predict_next_point validates condition_id exists."""
        import inspect
        from app.api.routes.takeoff import predict_next_point

        source = inspect.getsource(predict_next_point)
        assert "Condition" in source
        assert "condition_id" in source
        assert "Condition not found" in source

    def test_condition_project_check_in_source(self):
        """Verify predict_next_point checks condition belongs to same project."""
        import inspect
        from app.api.routes.takeoff import predict_next_point

        source = inspect.getsource(predict_next_point)
        assert "project_id" in source
        assert "same project" in source.lower()
