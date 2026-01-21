"""Scale detection Celery tasks."""

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.page import Page
from app.services.scale_detector import get_scale_detector
from app.utils.storage import get_storage_service
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()

engine = create_async_engine(str(settings.database_url))
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def run_async(coro):
    """Run async coroutine in sync context."""
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=2)
def detect_page_scale_task(self, page_id: str) -> dict:
    """Detect scale for a single page.

    Args:
        page_id: Page UUID as string

    Returns:
        Scale detection result
    """
    logger.info("Starting scale detection", page_id=page_id)

    try:
        result = run_async(_detect_page_scale(page_id))
        return result
    except Exception as e:
        logger.error("Scale detection failed", page_id=page_id, error=str(e))
        raise self.retry(exc=e, countdown=30)


async def _detect_page_scale(page_id: str) -> dict:
    """Detect scale for a page."""
    page_uuid = uuid.UUID(page_id)

    detector = get_scale_detector()
    storage = get_storage_service()

    async with async_session() as session:
        result = await session.execute(select(Page).where(Page.id == page_uuid))
        page = result.scalar_one_or_none()

        if not page:
            raise ValueError(f"Page not found: {page_id}")

        # Download image
        image_bytes = storage.download_file(page.image_key)

        # Get pre-detected scale texts from OCR
        detected_scales = []
        if page.ocr_blocks and "detected_scales" in page.ocr_blocks:
            detected_scales = page.ocr_blocks["detected_scales"]

        # Detect scale
        detection = detector.detect_scale(
            image_bytes,
            ocr_text=page.ocr_text,
            detected_scale_texts=detected_scales,
            ocr_blocks=page.ocr_blocks,
        )

        # Update page with scale info
        if detection["best_scale"]:
            best = detection["best_scale"]
            page.scale_text = best["text"]
            page.scale_value = best.get("pixels_per_foot")
            page.scale_detection_method = best.get(
                "method"
            )  # vision_llm, ocr_predetected, etc.

            if best["confidence"] >= 0.85 and page.scale_value:
                page.scale_calibrated = True

        # Store full detection data
        # If new detection has no bbox but old one does, preserve the old bbox
        if detection.get("best_scale") and not detection["best_scale"].get("bbox"):
            # New detection missing bbox - check if we have old data with bbox
            if page.scale_calibration_data and page.scale_calibration_data.get(
                "best_scale"
            ):
                old_bbox = page.scale_calibration_data["best_scale"].get("bbox")
                if old_bbox:
                    # Preserve the old bbox
                    detection["best_scale"]["bbox"] = old_bbox
                    logger.info("Preserved bbox from previous detection")

        page.scale_calibration_data = detection

        await session.commit()

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


@celery_app.task(bind=True)
def detect_document_scales_task(self, document_id: str) -> dict:
    """Detect scales for all pages in a document.

    Args:
        document_id: Document UUID as string

    Returns:
        Batch detection results
    """
    logger.info("Starting document scale detection", document_id=document_id)

    try:
        result = run_async(_detect_document_scales(document_id))
        return result
    except Exception as e:
        logger.error(
            "Document scale detection failed", document_id=document_id, error=str(e)
        )
        raise


async def _detect_document_scales(document_id: str) -> dict:
    """Detect scales for all pages in a document."""
    from app.models.document import Document

    doc_uuid = uuid.UUID(document_id)

    async with async_session() as session:
        result = await session.execute(select(Document).where(Document.id == doc_uuid))
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # Get all pages
        result = await session.execute(
            select(Page).where(Page.document_id == doc_uuid).order_by(Page.page_number)
        )
        pages = result.scalars().all()

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


@celery_app.task(bind=True)
def calibrate_page_scale_task(
    self,
    page_id: str,
    pixel_distance: float,
    real_distance: float,
    real_unit: str = "foot",
) -> dict:
    """Calibrate page scale from known distance.

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
        result = run_async(
            _calibrate_page_scale(page_id, pixel_distance, real_distance, real_unit)
        )
        return result
    except Exception as e:
        logger.error("Scale calibration failed", page_id=page_id, error=str(e))
        raise


async def _calibrate_page_scale(
    page_id: str,
    pixel_distance: float,
    real_distance: float,
    real_unit: str,
) -> dict:
    """Calibrate page scale."""
    page_uuid = uuid.UUID(page_id)

    detector = get_scale_detector()

    async with async_session() as session:
        result = await session.execute(select(Page).where(Page.id == page_uuid))
        page = result.scalar_one_or_none()

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

        await session.commit()

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
