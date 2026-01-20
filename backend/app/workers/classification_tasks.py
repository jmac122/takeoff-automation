"""Celery tasks for page classification.

IMPORTANT: This module uses SYNCHRONOUS SQLAlchemy (psycopg2 driver)
because Celery workers run in a multiprocessing context where async
database connections (asyncpg) cause InterfaceError.

FastAPI routes use ASYNC SQLAlchemy - this is the correct pattern.
"""

import uuid

import structlog
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.page import Page
from app.services.page_classifier import classify_page
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
def classify_page_task(
    self,
    page_id: str,
    provider: str | None = None,
) -> dict:
    """Classify a single page.

    Args:
        page_id: Page UUID
        provider: Optional LLM provider override

    Returns:
        Classification result dict
    """
    logger.info("Starting page classification", page_id=page_id, provider=provider)

    try:
        with SyncSession() as db:
            # Get page
            page = db.execute(
                select(Page).where(Page.id == uuid.UUID(page_id))
            ).scalar_one_or_none()

            if not page:
                raise ValueError(f"Page not found: {page_id}")

            # Get page image from storage
            storage = get_storage_service()
            image_bytes = storage.download_file(page.image_key)

            # Classify
            result = classify_page(
                image_bytes=image_bytes,
                ocr_text=page.ocr_text,
                provider=provider,
            )

            # Update page record
            page.classification = f"{result.discipline}:{result.page_type}"
            page.classification_confidence = min(
                result.discipline_confidence,
                result.page_type_confidence,
            )
            page.concrete_relevance = result.concrete_relevance
            page.classification_metadata = result.to_dict()

            db.commit()

            logger.info(
                "Page classification complete",
                page_id=page_id,
                discipline=result.discipline,
                page_type=result.page_type,
                concrete_relevance=result.concrete_relevance,
                provider=result.llm_provider,
                latency_ms=result.llm_latency_ms,
            )

            return result.to_dict()

    except Exception as e:
        logger.error("Page classification failed", page_id=page_id, error=str(e))
        raise self.retry(exc=e, countdown=60)


@celery_app.task
def classify_document_pages(
    document_id: str,
    provider: str | None = None,
) -> dict:
    """Classify all pages in a document.

    Args:
        document_id: Document UUID
        provider: Optional LLM provider override

    Returns:
        Summary of classification results
    """
    logger.info("Starting document classification", document_id=document_id)

    with SyncSession() as db:
        pages = (
            db.execute(select(Page).where(Page.document_id == uuid.UUID(document_id)))
            .scalars()
            .all()
        )

        task_ids = []
        for page in pages:
            task = classify_page_task.delay(str(page.id), provider=provider)
            task_ids.append(task.id)

        return {
            "document_id": document_id,
            "pages_queued": len(task_ids),
            "task_ids": task_ids,
        }
