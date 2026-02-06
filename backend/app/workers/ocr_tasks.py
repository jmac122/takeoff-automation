"""OCR processing Celery tasks.

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
from app.models.document import Document
from app.models.page import Page
from app.services.ocr_service import get_ocr_service, get_title_block_parser
from app.services.task_tracker import TaskTracker
from app.utils.image_utils import crop_image_bytes, resolve_region_to_pixels
from app.utils.storage import get_storage_service
from app.workers.celery_app import celery_app

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


def _apply_title_block_to_page(
    page: Page,
    title_block_data: dict,
    detected_scales: list[str] | None = None,
    allow_detected_scales: bool = True,
) -> None:
    """Apply title block extraction results to a page."""
    extracted_sheet_number = title_block_data.get("sheet_number")
    extracted_title = title_block_data.get("sheet_title")

    if extracted_sheet_number:
        extracted_sheet_number = extracted_sheet_number[:50]

    if extracted_title:
        extracted_title = extracted_title[:500]

    if extracted_sheet_number and extracted_title:
        combined = f"{extracted_sheet_number} - {extracted_title}"
        if len(combined) <= 50:
            page.sheet_number = combined
        else:
            page.sheet_number = extracted_sheet_number
            page.title = extracted_title
    elif extracted_sheet_number:
        page.sheet_number = extracted_sheet_number
    elif extracted_title:
        if len(extracted_title) <= 50:
            page.sheet_number = extracted_title
        else:
            page.title = extracted_title

    if extracted_title and not page.title:
        page.title = extracted_title

    if title_block_data.get("scale"):
        # Truncate to database column limit (VARCHAR 100)
        page.scale_text = title_block_data["scale"][:100]
    elif allow_detected_scales and detected_scales:
        # Truncate to database column limit (VARCHAR 100)
        page.scale_text = detected_scales[0][:100]


def _offset_ocr_blocks(
    blocks: list,
    offset_x: int,
    offset_y: int,
) -> list[dict]:
    """Offset OCR block bounding boxes to page coordinates."""
    adjusted_blocks = []
    for block in blocks:
        block_dict = block.to_dict()
        bbox = block_dict.get("bounding_box", {})
        block_dict["bounding_box"] = {
            "x": bbox.get("x", 0) + offset_x,
            "y": bbox.get("y", 0) + offset_y,
            "width": bbox.get("width", 0),
            "height": bbox.get("height", 0),
        }
        adjusted_blocks.append(block_dict)
    return adjusted_blocks


@celery_app.task(bind=True, max_retries=3)
def process_page_ocr_task(self, page_id: str) -> dict:
    """Process OCR for a single page using SYNC database.

    Args:
        page_id: Page UUID as string

    Returns:
        OCR processing result
    """
    logger.info("Starting OCR processing", page_id=page_id)

    try:
        with SyncSession() as session:
            # Mark task as started
            TaskTracker.mark_started_sync(session, self.request.id)

            page_uuid = uuid.UUID(page_id)

            # Get page (sync query)
            page = session.query(Page).filter(Page.id == page_uuid).one_or_none()
            if not page:
                raise ValueError(f"Page not found: {page_id}")

            # Set status to processing when reprocessing OCR (unless already processing)
            if page.status != "processing":
                previous_status = page.status
                page.status = "processing"
                page.processing_error = None
                session.commit()
                logger.info(
                    "Set page status to processing for OCR",
                    page_id=page_id,
                    previous_status=previous_status,
                )

            # Download page image
            self.update_state(state="PROGRESS", meta={"percent": 10, "step": "Downloading page image"})
            TaskTracker.update_progress_sync(session, self.request.id, 10, "Downloading page image")
            storage = get_storage_service()
            image_bytes = storage.download_file(page.image_key)

            # Run OCR
            self.update_state(state="PROGRESS", meta={"percent": 40, "step": "Running OCR"})
            TaskTracker.update_progress_sync(session, self.request.id, 40, "Running OCR")
            ocr_service = get_ocr_service()
            ocr_result = ocr_service.extract_text(image_bytes)

            # Parse title block
            self.update_state(state="PROGRESS", meta={"percent": 70, "step": "Parsing title block"})
            TaskTracker.update_progress_sync(session, self.request.id, 70, "Parsing title block")
            title_block_parser = get_title_block_parser()
            title_block_data = title_block_parser.parse_title_block(
                ocr_result.blocks,
                page.width,
                page.height,
            )

            # Update page with OCR data
            self.update_state(state="PROGRESS", meta={"percent": 90, "step": "Saving results"})
            TaskTracker.update_progress_sync(session, self.request.id, 90, "Saving results")
            page.ocr_text = ocr_result.full_text
            page.ocr_blocks = {
                "blocks": [b.to_dict() for b in ocr_result.blocks],
                "detected_scales": ocr_result.detected_scale_texts,
                "detected_sheet_numbers": ocr_result.detected_sheet_numbers,
                "detected_titles": ocr_result.detected_titles,
                "title_block": title_block_data,
            }

            # Set sheet number, title, and scale from title block data
            _apply_title_block_to_page(
                page,
                title_block_data,
                detected_scales=ocr_result.detected_scale_texts,
                allow_detected_scales=True,
            )

            # Mark title block source
            if page.ocr_blocks is None:
                page.ocr_blocks = {}
            page.ocr_blocks["title_block_source"] = "auto"

            # Capture values before committing (to avoid DetachedInstanceError)
            result_data = {
                "status": "success",
                "page_id": page_id,
                "text_length": len(ocr_result.full_text),
                "sheet_number": page.sheet_number,
                "title": page.title,
                "scale_text": page.scale_text,
            }

            TaskTracker.mark_completed_sync(
                session, self.request.id, result_data, commit=False
            )
            session.commit()

            logger.info(
                "OCR processing complete",
                page_id=page_id,
                text_length=len(ocr_result.full_text),
                blocks_count=len(ocr_result.blocks),
            )

        # Automatically classify page after OCR completes (using fast OCR-based classification)
        # Queue this AFTER session is closed to avoid DetachedInstanceError
        from app.workers.classification_tasks import classify_page_task

        classify_page_task.delay(page_id, provider=None, use_vision=False)

        logger.info("Queued automatic classification after OCR", page_id=page_id)

        return result_data

    except ValueError as e:
        logger.error(
            "OCR processing validation failed (not retrying)",
            page_id=page_id,
            error=str(e),
        )
        with SyncSession() as session:
            TaskTracker.mark_failed_sync(session, self.request.id, str(e), tb_module.format_exc())
        raise

    except Exception as e:
        logger.error("OCR processing failed", page_id=page_id, error=str(e))
        original_traceback = tb_module.format_exc()

        # Update page with error
        try:
            with SyncSession() as session:
                page = (
                    session.query(Page)
                    .filter(Page.id == uuid.UUID(page_id))
                    .one_or_none()
                )
                if page:
                    page.status = "error"
                    page.processing_error = f"OCR error: {str(e)}"
                    session.commit()
        except Exception as update_error:
            logger.error("Failed to update page error", error=str(update_error))

        try:
            raise self.retry(exc=e, countdown=30)
        except MaxRetriesExceededError:
            with SyncSession() as session:
                TaskTracker.mark_failed_sync(
                    session, self.request.id, str(e), original_traceback
                )
            raise


@celery_app.task(bind=True)
def process_document_ocr_task(self, document_id: str) -> dict:
    """Process OCR for all pages in a document using SYNC database.

    Args:
        document_id: Document UUID as string

    Returns:
        Summary of OCR processing
    """
    logger.info("Starting document OCR", document_id=document_id)

    doc_uuid = uuid.UUID(document_id)

    with SyncSession() as session:
        # Get all pages for document (sync query)
        pages = session.query(Page.id).filter(Page.document_id == doc_uuid).all()
        page_ids = [str(page.id) for page in pages]

    # Queue OCR tasks for each page
    for page_id in page_ids:
        process_page_ocr_task.delay(page_id)

    logger.info(
        "Document OCR tasks queued",
        document_id=document_id,
        pages_queued=len(page_ids),
    )

    return {
        "status": "queued",
        "document_id": document_id,
        "pages_queued": len(page_ids),
    }


@celery_app.task(bind=True, max_retries=3)
def process_page_title_block_ocr_task(self, page_id: str) -> dict:
    """Process title block OCR for a single page using SYNC database."""
    logger.info("Starting title block OCR", page_id=page_id)

    try:
        with SyncSession() as session:
            page_uuid = uuid.UUID(page_id)

            page = session.query(Page).filter(Page.id == page_uuid).one_or_none()
            if not page:
                raise ValueError(f"Page not found: {page_id}")

            document = (
                session.query(Document)
                .filter(Document.id == page.document_id)
                .one_or_none()
            )
            if not document or not document.title_block_region:
                return {
                    "status": "skipped",
                    "page_id": page_id,
                    "reason": "missing_title_block_region",
                }

            region = resolve_region_to_pixels(
                document.title_block_region, page.width, page.height
            )

            storage = get_storage_service()
            image_bytes = storage.download_file(page.image_key)
            cropped_bytes, crop_width, crop_height = crop_image_bytes(
                image_bytes, region
            )

            ocr_service = get_ocr_service()
            ocr_result = ocr_service.extract_text(cropped_bytes)

            title_block_parser = get_title_block_parser()
            title_block_data = title_block_parser.parse_title_block(
                ocr_result.blocks,
                crop_width,
                crop_height,
                use_full_region=True,
            )

            ocr_blocks = page.ocr_blocks or {}
            ocr_blocks["title_block"] = title_block_data
            ocr_blocks["title_block_source"] = "manual_region"
            ocr_blocks["title_block_region"] = {
                "bbox": region,
                "blocks": _offset_ocr_blocks(
                    ocr_result.blocks,
                    offset_x=region["x"],
                    offset_y=region["y"],
                ),
                "full_text": ocr_result.full_text,
                "detected_sheet_numbers": ocr_result.detected_sheet_numbers,
                "detected_titles": ocr_result.detected_titles,
            }
            page.ocr_blocks = ocr_blocks

            _apply_title_block_to_page(
                page,
                title_block_data,
                detected_scales=None,
                allow_detected_scales=False,
            )

            result_data = {
                "status": "success",
                "page_id": page_id,
                "sheet_number": page.sheet_number,
                "title": page.title,
            }

            session.commit()

            logger.info(
                "Title block OCR complete",
                page_id=page_id,
                blocks_count=len(ocr_result.blocks),
            )

            return result_data

    except Exception as e:
        logger.error("Title block OCR failed", page_id=page_id, error=str(e))

        try:
            with SyncSession() as session:
                page = (
                    session.query(Page)
                    .filter(Page.id == uuid.UUID(page_id))
                    .one_or_none()
                )
                if page:
                    page.processing_error = f"Title block OCR error: {str(e)}"
                    session.commit()
        except Exception as update_error:
            logger.error(
                "Failed to update title block OCR error",
                error=str(update_error),
            )

        raise self.retry(exc=e, countdown=30)


@celery_app.task(bind=True)
def process_document_title_block_task(self, document_id: str) -> dict:
    """Process title block OCR for all pages in a document."""
    logger.info("Starting document title block OCR", document_id=document_id)

    doc_uuid = uuid.UUID(document_id)

    with SyncSession() as session:
        document = (
            session.query(Document).filter(Document.id == doc_uuid).one_or_none()
        )
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        if not document.title_block_region:
            return {
                "status": "skipped",
                "document_id": document_id,
                "pages_queued": 0,
                "reason": "missing_title_block_region",
            }

        pages = session.query(Page.id).filter(Page.document_id == doc_uuid).all()
        page_ids = [str(page.id) for page in pages]

    for page_id in page_ids:
        process_page_title_block_ocr_task.delay(page_id)

    logger.info(
        "Document title block OCR tasks queued",
        document_id=document_id,
        pages_queued=len(page_ids),
    )

    return {
        "status": "queued",
        "document_id": document_id,
        "pages_queued": len(page_ids),
    }
