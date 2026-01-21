"""OCR processing Celery tasks.

IMPORTANT: This module uses SYNCHRONOUS SQLAlchemy (psycopg2 driver)
because Celery workers run in a multiprocessing context where async
database connections (asyncpg) cause InterfaceError.

FastAPI routes use ASYNC SQLAlchemy - this is the correct pattern.
"""

import uuid

import structlog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.page import Page
from app.services.ocr_service import get_ocr_service, get_title_block_parser
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
            page_uuid = uuid.UUID(page_id)

            # Get page (sync query)
            page = session.query(Page).filter(Page.id == page_uuid).one_or_none()
            if not page:
                raise ValueError(f"Page not found: {page_id}")

            # Download page image
            storage = get_storage_service()
            image_bytes = storage.download_file(page.image_key)

            # Run OCR
            ocr_service = get_ocr_service()
            ocr_result = ocr_service.extract_text(image_bytes)

            # Parse title block
            title_block_parser = get_title_block_parser()
            title_block_data = title_block_parser.parse_title_block(
                ocr_result.blocks,
                page.width,
                page.height,
            )

            # Update page with OCR data
            page.ocr_text = ocr_result.full_text
            page.ocr_blocks = {
                "blocks": [b.to_dict() for b in ocr_result.blocks],
                "detected_scales": ocr_result.detected_scale_texts,
                "detected_sheet_numbers": ocr_result.detected_sheet_numbers,
                "detected_titles": ocr_result.detected_titles,
                "title_block": title_block_data,
            }

            # Set sheet number, title, and scale - PRIORITIZE title block data
            # Title blocks are more reliable than full-page pattern matching

            # Extract sheet number and title separately first
            extracted_sheet_number = None
            extracted_title = None

            # Sheet number: title block first, then full-page patterns
            if title_block_data.get("sheet_number"):
                extracted_sheet_number = title_block_data["sheet_number"]
            elif ocr_result.detected_sheet_numbers:
                extracted_sheet_number = ocr_result.detected_sheet_numbers[0]

            # Title: title block first, then full-page patterns
            if title_block_data.get("sheet_title"):
                extracted_title = title_block_data["sheet_title"]
            elif ocr_result.detected_titles:
                extracted_title = ocr_result.detected_titles[0]

            # Combine sheet number and title for display (e.g., "S0.01 - GENERAL NOTES")
            if extracted_sheet_number and extracted_title:
                page.sheet_number = f"{extracted_sheet_number} - {extracted_title}"
            elif extracted_sheet_number:
                page.sheet_number = extracted_sheet_number

            # Store title separately for potential future use
            page.title = extracted_title

            # Scale: title block first, then full-page patterns
            if title_block_data.get("scale"):
                page.scale_text = title_block_data["scale"]
            elif ocr_result.detected_scale_texts:
                page.scale_text = ocr_result.detected_scale_texts[0]

            page.status = "completed"
            session.commit()

            logger.info(
                "OCR processing complete",
                page_id=page_id,
                text_length=len(ocr_result.full_text),
                blocks_count=len(ocr_result.blocks),
            )

        # Automatically classify page after OCR completes (using fast OCR-based classification)
        from app.workers.classification_tasks import classify_page_task

        classify_page_task.delay(page_id, provider=None, use_vision=False)

        logger.info("Queued automatic classification after OCR", page_id=page_id)

        return {
            "status": "success",
            "page_id": page_id,
            "text_length": len(ocr_result.full_text),
            "sheet_number": page.sheet_number,
            "title": page.title,
            "scale_text": page.scale_text,
        }

    except Exception as e:
        logger.error("OCR processing failed", page_id=page_id, error=str(e))

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

        raise self.retry(exc=e, countdown=30)


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
