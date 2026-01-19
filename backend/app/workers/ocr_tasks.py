"""OCR processing Celery tasks."""

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.page import Page
from app.services.ocr_service import get_ocr_service, get_title_block_parser
from app.utils.storage import get_storage_service
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()

engine = create_async_engine(str(settings.database_url))
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def run_async(coro):
    """Run an async coroutine in sync context."""
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def process_page_ocr_task(self, page_id: str) -> dict:
    """Process OCR for a single page.

    Args:
        page_id: Page UUID as string

    Returns:
        OCR processing result
    """
    logger.info("Starting OCR processing", page_id=page_id)

    try:
        result = run_async(_process_page_ocr(page_id))
        return result
    except Exception as e:
        logger.error("OCR processing failed", page_id=page_id, error=str(e))
        run_async(_update_page_ocr_error(page_id, str(e)))
        raise self.retry(exc=e, countdown=30)


@celery_app.task(bind=True)
def process_document_ocr_task(self, document_id: str) -> dict:
    """Process OCR for all pages in a document.

    Args:
        document_id: Document UUID as string

    Returns:
        Summary of OCR processing
    """
    logger.info("Starting document OCR", document_id=document_id)

    result = run_async(_process_document_ocr(document_id))
    return result


async def _process_page_ocr(page_id: str) -> dict:
    """Process OCR for a single page."""
    page_uuid = uuid.UUID(page_id)

    ocr_service = get_ocr_service()
    title_block_parser = get_title_block_parser()
    storage = get_storage_service()

    async with async_session() as session:
        # Get page
        result = await session.execute(select(Page).where(Page.id == page_uuid))
        page = result.scalar_one_or_none()

        if not page:
            raise ValueError(f"Page not found: {page_id}")

        # Download page image
        image_bytes = storage.download_file(page.image_key)

        # Run OCR
        ocr_result = ocr_service.extract_text(image_bytes)

        # Parse title block
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

        # Set sheet number and title from detected values
        if ocr_result.detected_sheet_numbers:
            page.sheet_number = ocr_result.detected_sheet_numbers[0]
        elif title_block_data["sheet_number"]:
            page.sheet_number = title_block_data["sheet_number"]

        if ocr_result.detected_titles:
            page.title = ocr_result.detected_titles[0]
        elif title_block_data["sheet_title"]:
            page.title = title_block_data["sheet_title"]

        # Store detected scale text (not yet calibrated)
        if ocr_result.detected_scale_texts:
            page.scale_text = ocr_result.detected_scale_texts[0]
        elif title_block_data["scale"]:
            page.scale_text = title_block_data["scale"]

        await session.commit()

        logger.info(
            "OCR processing complete",
            page_id=page_id,
            text_length=len(ocr_result.full_text),
            blocks_count=len(ocr_result.blocks),
        )

        return {
            "status": "success",
            "page_id": page_id,
            "text_length": len(ocr_result.full_text),
            "sheet_number": page.sheet_number,
            "title": page.title,
            "scale_text": page.scale_text,
        }


async def _process_document_ocr(document_id: str) -> dict:
    """Process OCR for all pages in a document."""
    doc_uuid = uuid.UUID(document_id)

    async with async_session() as session:
        # Get all pages for document
        result = await session.execute(
            select(Page.id).where(Page.document_id == doc_uuid)
        )
        page_ids = [str(row[0]) for row in result.all()]

    # Queue OCR tasks for each page
    for page_id in page_ids:
        process_page_ocr_task.delay(page_id)

    return {
        "status": "queued",
        "document_id": document_id,
        "pages_queued": len(page_ids),
    }


async def _update_page_ocr_error(page_id: str, error: str) -> None:
    """Update page with OCR error."""
    async with async_session() as session:
        result = await session.execute(
            select(Page).where(Page.id == uuid.UUID(page_id))
        )
        page = result.scalar_one_or_none()

        if page:
            page.processing_error = f"OCR error: {error}"
            await session.commit()
