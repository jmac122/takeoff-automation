"""Document processing Celery tasks.

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
from app.models.document import Document
from app.models.page import Page
from app.services.document_processor import get_document_processor
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
            file_bytes = storage.download_file(document.storage_key)

            # Process document and extract pages
            pages_data = processor.process_document(
                document_id=doc_uuid,
                project_id=proj_uuid,
                file_bytes=file_bytes,
                file_type=document.file_type,
                dpi=150,
            )

            # Create page records
            for page_data in pages_data:
                page = Page(
                    id=page_data["id"],
                    document_id=doc_uuid,
                    page_number=page_data["page_number"],
                    width=page_data["width"],
                    height=page_data["height"],
                    dpi=page_data["dpi"],
                    image_key=page_data["image_key"],
                    thumbnail_key=page_data["thumbnail_key"],
                    status="ready",
                )
                session.add(page)

            # Update document status
            document.status = "ready"
            document.page_count = len(pages_data)

            session.commit()

            logger.info(
                "Document processing complete",
                document_id=document_id,
                page_count=len(pages_data),
            )

            # Queue OCR processing for the document
            from app.workers.ocr_tasks import process_document_ocr_task

            process_document_ocr_task.delay(document_id)

            return {
                "status": "success",
                "document_id": document_id,
                "page_count": len(pages_data),
            }

    except Exception as e:
        logger.error(
            "Document processing failed",
            document_id=document_id,
            error=str(e),
        )

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

        raise self.retry(exc=e, countdown=60)
