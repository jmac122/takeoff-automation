"""Celery tasks for page classification.

IMPORTANT: This module uses SYNCHRONOUS SQLAlchemy (psycopg2 driver)
because Celery workers run in a multiprocessing context where async
database connections (asyncpg) cause InterfaceError.

FastAPI routes use ASYNC SQLAlchemy - this is the correct pattern.
"""

import time
import uuid

import structlog
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.page import Page
from app.models.classification_history import ClassificationHistory
from app.services.page_classifier import classify_page
from app.services.llm_client import get_llm_client, PROVIDER_MODELS
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


def _save_failed_classification(
    db,
    page_id: str,
    provider: str | None,
    error: str,
    latency_ms: float | None = None,
) -> None:
    """Save a failed classification attempt to history for BI tracking."""
    # Determine provider and model
    from app.services.llm_client import LLMProvider

    if provider:
        try:
            llm_provider = LLMProvider(provider)
        except ValueError:
            llm_provider = LLMProvider.ANTHROPIC
    else:
        llm_provider = LLMProvider.ANTHROPIC  # Default

    model = PROVIDER_MODELS.get(llm_provider, "unknown")

    history_entry = ClassificationHistory(
        page_id=uuid.UUID(page_id),
        llm_provider=provider or "anthropic",
        llm_model=model,
        llm_latency_ms=latency_ms,
        status="failed",
        error_message=error[:2000] if error else None,  # Truncate long errors
        raw_response={"error": error},
    )
    db.add(history_entry)
    db.commit()

    logger.info(
        "Saved failed classification to history",
        page_id=page_id,
        provider=provider,
        history_id=str(history_entry.id),
    )


@celery_app.task(bind=True, max_retries=0)  # No retries - save failures instead
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
    start_time = time.time()

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
            try:
                result = classify_page(
                    image_bytes=image_bytes,
                    ocr_text=page.ocr_text,
                    provider=provider,
                )
            except Exception as classify_error:
                # Save failed attempt to history for BI
                latency_ms = (time.time() - start_time) * 1000
                _save_failed_classification(
                    db, page_id, provider, str(classify_error), latency_ms
                )
                raise

            # Update page record with latest classification
            page.classification = f"{result.discipline}:{result.page_type}"
            page.classification_confidence = min(
                result.discipline_confidence,
                result.page_type_confidence,
            )
            page.concrete_relevance = result.concrete_relevance
            page.classification_metadata = result.to_dict()

            # Save to classification history for BI tracking
            history_entry = ClassificationHistory(
                page_id=uuid.UUID(page_id),
                classification=f"{result.discipline}:{result.page_type}",
                classification_confidence=min(
                    result.discipline_confidence,
                    result.page_type_confidence,
                ),
                discipline=result.discipline,
                discipline_confidence=result.discipline_confidence,
                page_type=result.page_type,
                page_type_confidence=result.page_type_confidence,
                concrete_relevance=result.concrete_relevance,
                concrete_elements=result.concrete_elements,
                description=result.description,
                llm_provider=result.llm_provider,
                llm_model=result.llm_model,
                llm_latency_ms=result.llm_latency_ms,
                status="success",
                raw_response=result.to_dict(),
            )
            db.add(history_entry)

            db.commit()

            logger.info(
                "Page classification complete",
                page_id=page_id,
                discipline=result.discipline,
                page_type=result.page_type,
                concrete_relevance=result.concrete_relevance,
                provider=result.llm_provider,
                latency_ms=result.llm_latency_ms,
                history_id=str(history_entry.id),
            )

            return result.to_dict()

    except Exception as e:
        logger.error("Page classification failed", page_id=page_id, error=str(e))
        # Don't retry - we've already saved the failure to history
        raise


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
