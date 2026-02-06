"""Scale detection Celery tasks.

IMPORTANT: This module uses SYNCHRONOUS SQLAlchemy (psycopg2 driver)
because Celery workers run in a multiprocessing context where async
database connections (asyncpg) cause InterfaceError.

FastAPI routes use ASYNC SQLAlchemy - this is the correct pattern.
"""

import traceback as tb_module
import uuid

from celery.exceptions import MaxRetriesExceededError
import structlog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.page import Page
from app.services.scale_detector import get_scale_detector
from app.services.task_tracker import TaskTracker
from app.utils.storage import get_storage_service
from app.workers.celery_app import celery_app
from app.workers.progress import report_progress as _report_progress

logger = structlog.get_logger()
settings = get_settings()

# Create SYNC engine for Celery workers (remove +asyncpg from URL)
sync_database_url = str(settings.database_url).replace("+asyncpg", "")
sync_engine = create_engine(
    sync_database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SyncSession = sessionmaker(bind=sync_engine)


@celery_app.task(bind=True, max_retries=2)
def detect_page_scale_task(self, page_id: str) -> dict:
    """Detect scale for a single page using SYNC database.

    Args:
        page_id: Page UUID as string

    Returns:
        Scale detection result
    """
    logger.info("Starting scale detection", page_id=page_id)

    try:
        with SyncSession() as session:
            # Mark task as started
            TaskTracker.mark_started_sync(session, self.request.id)

            page_uuid = uuid.UUID(page_id)

            # Get page (sync query)
            _report_progress(self, session, 10, "Loading page data")
            page = session.query(Page).filter(Page.id == page_uuid).one_or_none()

            if not page:
                raise ValueError(f"Page not found: {page_id}")

            detector = get_scale_detector()
            storage = get_storage_service()

            # Download image
            _report_progress(self, session, 30, "Downloading image")
            image_bytes = storage.download_file(page.image_key)

            # Get pre-detected scale texts from OCR
            detected_scales = []
            if page.ocr_blocks and "detected_scales" in page.ocr_blocks:
                detected_scales = page.ocr_blocks["detected_scales"]

            # Check if OCR blocks are missing (may indicate OCR failure)
            if not page.ocr_blocks or not page.ocr_blocks.get("blocks"):
                logger.warning(
                    "OCR blocks missing for scale detection",
                    page_id=page_id,
                    ocr_text_exists=bool(page.ocr_text),
                    ocr_blocks_exists=bool(page.ocr_blocks),
                    ocr_status=page.status,
                    message="Scale detection will use LLM bbox (less accurate). "
                    "Consider re-running OCR for pixel-perfect accuracy.",
                )

            # Detect scale
            _report_progress(self, session, 60, "Detecting scale")
            detection = detector.detect_scale(
                image_bytes,
                ocr_text=page.ocr_text,
                detected_scale_texts=detected_scales,
                ocr_blocks=page.ocr_blocks,
            )

            # Update page with scale info
            _report_progress(self, session, 90, "Saving results")
            if detection["best_scale"]:
                best = detection["best_scale"]
                page.scale_text = best["text"]
                page.scale_detection_method = best.get(
                    "method"
                )  # vision_llm, ocr_predetected, etc.

                # Calculate accurate pixels_per_foot using physical page dimensions
                scale_ratio = best.get("ratio")
                if page.page_width_inches and page.page_width_inches > 0 and scale_ratio and scale_ratio > 0:
                    pixels_per_inch = page.width / page.page_width_inches
                    page.scale_value = pixels_per_inch * 12 / scale_ratio
                    logger.info(
                        "Calculated pixels_per_foot from physical dimensions",
                        page_id=page_id,
                        page_width_px=page.width,
                        page_width_inches=page.page_width_inches,
                        pixels_per_inch=pixels_per_inch,
                        scale_ratio=scale_ratio,
                        pixels_per_foot=page.scale_value,
                    )
                else:
                    page.scale_value = best.get("pixels_per_foot")
                    logger.warning(
                        "Using legacy pixels_per_foot estimate (no physical dimensions)",
                        page_id=page_id,
                        pixels_per_foot=page.scale_value,
                    )

                if best["confidence"] >= 0.85 and page.scale_value:
                    page.scale_calibrated = True

            # Store full detection data
            if detection.get("best_scale") and not detection["best_scale"].get("bbox"):
                if page.scale_calibration_data and page.scale_calibration_data.get(
                    "best_scale"
                ):
                    old_bbox = page.scale_calibration_data["best_scale"].get("bbox")
                    if old_bbox:
                        detection["best_scale"]["bbox"] = old_bbox
                        logger.info("Preserved bbox from previous detection")

            page.scale_calibration_data = detection

            result_summary = {
                "page_id": page_id,
                "scale_text": page.scale_text,
                "scale_value": page.scale_value,
                "calibrated": page.scale_calibrated,
            }

            TaskTracker.mark_completed_sync(
                session, self.request.id, result_summary, commit=False
            )
            session.commit()

            logger.info(
                "Scale detection complete",
                page_id=page_id,
                scale_text=page.scale_text,
                scale_value=page.scale_value,
                calibrated=page.scale_calibrated,
            )

            return {
                "status": "success",
                "page_id": page_id,
                "scale_text": page.scale_text,
                "scale_value": page.scale_value,
                "calibrated": page.scale_calibrated,
                "detection": detection,
            }

    except ValueError as e:
        logger.error(
            "Scale detection validation failed (not retrying)",
            page_id=page_id,
            error=str(e),
        )
        with SyncSession() as session:
            TaskTracker.mark_failed_sync(session, self.request.id, str(e), tb_module.format_exc())
        raise

    except Exception as e:
        logger.error("Scale detection failed", page_id=page_id, error=str(e))
        original_traceback = tb_module.format_exc()
        try:
            raise self.retry(exc=e, countdown=30)
        except MaxRetriesExceededError:
            with SyncSession() as session:
                TaskTracker.mark_failed_sync(
                    session, self.request.id, str(e), original_traceback
                )
            raise


@celery_app.task(bind=True)
def detect_document_scales_task(self, document_id: str) -> dict:
    """Detect scales for all pages in a document using SYNC database.

    Args:
        document_id: Document UUID as string

    Returns:
        Batch detection results
    """
    logger.info("Starting document scale detection", document_id=document_id)

    try:
        doc_uuid = uuid.UUID(document_id)

        with SyncSession() as session:
            # Verify document exists (check if any pages exist)
            from app.models.document import Document

            document = (
                session.query(Document).filter(Document.id == doc_uuid).one_or_none()
            )

            if not document:
                raise ValueError(f"Document not found: {document_id}")

            # Get all pages
            pages = (
                session.query(Page)
                .filter(Page.document_id == doc_uuid)
                .order_by(Page.page_number)
                .all()
            )

            # Queue scale detection for each page
            results = []
            for page in pages:
                # Trigger async task
                task = detect_page_scale_task.delay(str(page.id))
                results.append(
                    {
                        "page_id": str(page.id),
                        "page_number": page.page_number,
                        "task_id": task.id,
                    }
                )

            logger.info(
                "Document scale detection queued",
                document_id=document_id,
                page_count=len(pages),
            )

            return {
                "status": "queued",
                "document_id": document_id,
                "page_count": len(pages),
                "tasks": results,
            }

    except Exception as e:
        logger.error(
            "Document scale detection failed", document_id=document_id, error=str(e)
        )
        raise


@celery_app.task(bind=True)
def calibrate_page_scale_task(
    self,
    page_id: str,
    pixel_distance: float,
    real_distance: float,
    real_unit: str = "foot",
) -> dict:
    """Calibrate page scale from known distance using SYNC database.

    Args:
        page_id: Page UUID as string
        pixel_distance: Distance in pixels
        real_distance: Real-world distance
        real_unit: Unit of real distance

    Returns:
        Calibration result
    """
    logger.info(
        "Starting scale calibration",
        page_id=page_id,
        pixel_distance=pixel_distance,
        real_distance=real_distance,
        unit=real_unit,
    )

    try:
        page_uuid = uuid.UUID(page_id)

        detector = get_scale_detector()

        with SyncSession() as session:
            # Get page (sync query)
            page = session.query(Page).filter(Page.id == page_uuid).one_or_none()

            if not page:
                raise ValueError(f"Page not found: {page_id}")

            # Calculate scale
            calibration = detector.calculate_scale_from_calibration(
                pixel_distance=pixel_distance,
                real_distance=real_distance,
                real_unit=real_unit,
            )

            # Update page
            page.scale_value = calibration["pixels_per_foot"]
            page.scale_unit = "foot"
            page.scale_calibrated = True
            page.scale_detection_method = "manual_calibration"

            # Store calibration data
            if not page.scale_calibration_data:
                page.scale_calibration_data = {}
            page.scale_calibration_data["calibration"] = calibration
            page.scale_calibration_data["calibration_input"] = {
                "pixel_distance": pixel_distance,
                "real_distance": real_distance,
                "real_unit": real_unit,
            }

            session.commit()

            logger.info(
                "Scale calibration complete",
                page_id=page_id,
                pixels_per_foot=calibration["pixels_per_foot"],
            )

            return {
                "status": "success",
                "page_id": page_id,
                "pixels_per_foot": calibration["pixels_per_foot"],
                "estimated_scale_ratio": calibration["estimated_ratio"],
            }

    except Exception as e:
        logger.error("Scale calibration failed", page_id=page_id, error=str(e))
        raise
