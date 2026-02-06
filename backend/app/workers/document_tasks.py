"""Document processing Celery tasks.

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
from app.services.document_processor import get_document_processor
from app.services.task_tracker import TaskTracker
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
def process_document_task(
    self,
    document_id: str,
    project_id: str,
) -> dict:
    """Process an uploaded document using SYNC database.

    Args:
        document_id: Document UUID as string
        project_id: Project UUID as string

    Returns:
        Processing result dictionary
    """
    logger.info(
        "Starting document processing",
        document_id=document_id,
        task_id=self.request.id,
    )

    try:
        doc_uuid = uuid.UUID(document_id)
        proj_uuid = uuid.UUID(project_id)

        processor = get_document_processor()
        storage = get_storage_service()

        with SyncSession() as session:
            # Mark task as started
            TaskTracker.mark_started_sync(session, self.request.id)

            # Get document (sync query)
            document = (
                session.query(Document).filter(Document.id == doc_uuid).one_or_none()
            )

            if not document:
                raise ValueError(f"Document not found: {document_id}")

            # Update status to processing
            document.status = "processing"
            session.commit()

            # Download original file
            self.update_state(state="PROGRESS", meta={"percent": 10, "step": "Downloading file"})
            TaskTracker.update_progress_sync(session, self.request.id, 10, "Downloading file")
            file_bytes = storage.download_file(document.storage_key)

            # Process document and extract pages
            self.update_state(state="PROGRESS", meta={"percent": 40, "step": "Extracting pages"})
            TaskTracker.update_progress_sync(session, self.request.id, 40, "Extracting pages")
            pages_data = processor.process_document(
                document_id=doc_uuid,
                project_id=proj_uuid,
                file_bytes=file_bytes,
                file_type=document.file_type,
                dpi=150,
            )

            # Create page records
            self.update_state(state="PROGRESS", meta={"percent": 70, "step": "Saving page records"})
            TaskTracker.update_progress_sync(session, self.request.id, 70, "Saving page records")
            for page_data in pages_data:
                page = Page(
                    id=page_data["id"],
                    document_id=doc_uuid,
                    page_number=page_data["page_number"],
                    width=page_data["width"],
                    height=page_data["height"],
                    dpi=page_data["dpi"],
                    page_width_inches=page_data.get("page_width_inches"),
                    page_height_inches=page_data.get("page_height_inches"),
                    image_key=page_data["image_key"],
                    thumbnail_key=page_data["thumbnail_key"],
                    status="ready",
                )
                session.add(page)

            # Update document status
            document.status = "ready"
            document.page_count = len(pages_data)

            # Queue OCR processing for the document
            self.update_state(state="PROGRESS", meta={"percent": 90, "step": "Queueing OCR"})
            TaskTracker.update_progress_sync(session, self.request.id, 90, "Queueing OCR")

            result_summary = {
                "document_id": document_id,
                "page_count": len(pages_data),
            }

            TaskTracker.mark_completed_sync(
                session, self.request.id, result_summary, commit=False
            )
            session.commit()

            logger.info(
                "Document processing complete",
                document_id=document_id,
                page_count=len(pages_data),
            )

            from app.workers.ocr_tasks import process_document_ocr_task

            process_document_ocr_task.delay(document_id)

            return {
                "status": "success",
                "document_id": document_id,
                "page_count": len(pages_data),
            }

    except ValueError as e:
        logger.error(
            "Document processing validation failed (not retrying)",
            document_id=document_id,
            error=str(e),
        )
        with SyncSession() as session:
            TaskTracker.mark_failed_sync(session, self.request.id, str(e), tb_module.format_exc())
            document = (
                session.query(Document)
                .filter(Document.id == uuid.UUID(document_id))
                .one_or_none()
            )
            if document:
                document.status = "error"
                document.processing_error = str(e)
                session.commit()
        raise

    except Exception as e:
        logger.error(
            "Document processing failed",
            document_id=document_id,
            error=str(e),
        )
        original_traceback = tb_module.format_exc()

        # Update document status to error
        try:
            with SyncSession() as session:
                document = (
                    session.query(Document)
                    .filter(Document.id == uuid.UUID(document_id))
                    .one_or_none()
                )
                if document:
                    document.status = "error"
                    document.processing_error = str(e)
                    session.commit()
        except Exception as update_error:
            logger.error("Failed to update document error", error=str(update_error))

        try:
            raise self.retry(exc=e, countdown=60)
        except MaxRetriesExceededError:
            with SyncSession() as session:
                TaskTracker.mark_failed_sync(
                    session, self.request.id, str(e), original_traceback
                )
            raise
