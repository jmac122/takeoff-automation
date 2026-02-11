"""Celery task for auto-count detection."""

from __future__ import annotations

import uuid

import structlog
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker, selectinload

from app.config import get_settings
from app.models.auto_count import AutoCountDetection, AutoCountSession
from app.models.condition import Condition
from app.models.measurement import Measurement
from app.models.page import Page
from app.services.auto_count.template_matcher import MatchResult, TemplateMatchingService
from app.services.task_tracker import TaskTracker
from app.utils.storage import get_storage_service
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()

# Celery workers use SYNC SQLAlchemy (psycopg2), not asyncpg
sync_database_url = str(settings.database_url).replace("+asyncpg", "")
sync_engine = create_engine(sync_database_url, pool_pre_ping=True, pool_size=5)
SyncSession = sessionmaker(bind=sync_engine)


def _report_progress(task, db: Session, percent: int, message: str) -> None:
    """Update task progress."""
    try:
        TaskTracker.update_sync(
            db,
            task_id=task.request.id,
            progress=percent,
            message=message,
        )
    except Exception:
        pass  # Progress reporting should never block the main task


@celery_app.task(bind=True, max_retries=3)
def auto_count_task(
    self,
    session_id: str,
    provider: str | None = None,
) -> dict:
    """Run auto-count detection for a session.

    Args:
        session_id: UUID of the AutoCountSession.
        provider: Optional LLM provider override.

    Returns:
        Dict with detection summary.
    """
    db = SyncSession()

    try:
        _report_progress(self, db, 5, "Loading session data")

        # Load session
        session = db.execute(
            select(AutoCountSession).where(
                AutoCountSession.id == uuid.UUID(session_id)
            )
        ).scalar_one_or_none()

        if session is None:
            raise ValueError(f"AutoCountSession {session_id} not found")

        session.status = "processing"
        db.commit()

        # Load page
        page = db.get(Page, session.page_id)
        if page is None:
            raise ValueError(f"Page {session.page_id} not found")

        _report_progress(self, db, 10, "Downloading page image")

        # Download page image from storage
        storage = get_storage_service()
        page_image_bytes = storage.download_file(page.image_key)

        # Get image dimensions
        image_width, image_height = _get_image_dimensions(page_image_bytes)

        _report_progress(self, db, 20, "Running template matching")

        # Step 1: Template matching (OpenCV)
        all_matches: list[MatchResult] = []
        template_count = 0
        llm_count = 0
        method = session.detection_method

        if method in ("template", "hybrid"):
            matcher = TemplateMatchingService(
                confidence_threshold=session.confidence_threshold,
                scale_tolerance=session.scale_tolerance,
                rotation_tolerance=session.rotation_tolerance,
            )
            template_matches = matcher.find_matches(
                page_image_bytes=page_image_bytes,
                template_bbox=session.template_bbox,
            )
            template_count = len(template_matches)
            all_matches.extend(template_matches)

            logger.info(
                "Template matching complete",
                session_id=session_id,
                matches=template_count,
            )

        _report_progress(self, db, 50, "Running LLM detection")

        # Step 2: LLM detection (synchronous wrapper for async service)
        if method in ("llm", "hybrid"):
            import asyncio

            from app.services.auto_count.llm_similarity import LLMSimilarityService

            llm_service = LLMSimilarityService(provider=provider)

            # Run async LLM call in a new event loop
            try:
                loop = asyncio.new_event_loop()
                llm_matches = loop.run_until_complete(
                    llm_service.find_similar(
                        page_image_bytes=page_image_bytes,
                        template_bbox=session.template_bbox,
                        image_width=image_width,
                        image_height=image_height,
                    )
                )
                loop.close()
            except Exception as e:
                logger.warning(
                    "LLM detection failed, continuing with template matches",
                    error=str(e),
                )
                llm_matches = []

            llm_count = len(llm_matches)

            # Merge with template matches
            if method == "hybrid" and all_matches:
                all_matches = _merge_detections(all_matches, llm_matches)
            elif not all_matches:
                all_matches = llm_matches

        _report_progress(self, db, 75, f"Storing {len(all_matches)} detections")

        # Step 3: Store detections
        for match in all_matches:
            source = "template"
            if method == "llm":
                source = "llm"
            elif method == "hybrid" and template_count > 0 and llm_count > 0:
                source = "both"

            detection = AutoCountDetection(
                session_id=session.id,
                bbox={
                    "x": match.x,
                    "y": match.y,
                    "w": match.w,
                    "h": match.h,
                },
                center_x=match.center_x,
                center_y=match.center_y,
                confidence=match.confidence,
                detection_source=source,
                status="pending",
            )
            db.add(detection)

        # Update session summary
        session.status = "completed"
        session.total_detections = len(all_matches)
        session.template_match_count = template_count
        session.llm_match_count = llm_count
        db.commit()

        _report_progress(self, db, 100, "Detection complete")

        # Mark task complete
        TaskTracker.complete_sync(
            db,
            task_id=self.request.id,
            result={
                "session_id": session_id,
                "total_detections": len(all_matches),
                "template_matches": template_count,
                "llm_matches": llm_count,
            },
        )

        return {
            "session_id": session_id,
            "status": "completed",
            "total_detections": len(all_matches),
            "template_matches": template_count,
            "llm_matches": llm_count,
        }

    except ValueError as e:
        # Validation errors — don't retry
        logger.error("Auto count validation error", error=str(e))
        _fail_session(db, session_id, str(e))
        TaskTracker.fail_sync(db, task_id=self.request.id, error=str(e))
        raise

    except Exception as e:
        logger.error("Auto count task failed", error=str(e))
        try:
            _fail_session(db, session_id, str(e))
            self.retry(countdown=60)
        except MaxRetriesExceededError:
            _fail_session(db, session_id, f"Max retries exceeded: {e}")
            TaskTracker.fail_sync(db, task_id=self.request.id, error=str(e))
            raise

    finally:
        db.close()


def _fail_session(db: Session, session_id: str, error: str) -> None:
    """Mark a session as failed."""
    try:
        session = db.execute(
            select(AutoCountSession).where(
                AutoCountSession.id == uuid.UUID(session_id)
            )
        ).scalar_one_or_none()
        if session:
            session.status = "failed"
            session.error_message = error
            db.commit()
    except Exception:
        pass


def _get_image_dimensions(image_bytes: bytes) -> tuple[int, int]:
    """Get image width and height from bytes."""
    try:
        import cv2
        import numpy as np

        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is not None:
            return img.shape[1], img.shape[0]
    except ImportError:
        pass

    # Fallback: try PIL
    try:
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(image_bytes))
        return img.size
    except ImportError:
        pass

    return 0, 0


def _merge_detections(
    template_matches: list[MatchResult],
    llm_matches: list[MatchResult],
) -> list[MatchResult]:
    """Merge template and LLM matches, deduplicating overlaps."""
    matcher = TemplateMatchingService()
    merged = list(template_matches)

    for llm_match in llm_matches:
        is_duplicate = False
        for i, existing in enumerate(merged):
            iou = matcher._compute_iou(llm_match, existing)
            if iou > 0.30:
                if llm_match.confidence > existing.confidence:
                    merged[i] = llm_match
                is_duplicate = True
                break
        if not is_duplicate:
            merged.append(llm_match)

    return merged
