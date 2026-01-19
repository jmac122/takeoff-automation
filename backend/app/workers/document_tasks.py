"""Document processing Celery tasks."""

import uuid
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.document import Document
from app.models.page import Page
from app.services.document_processor import get_document_processor
from app.utils.storage import get_storage_service
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()

# Create async engine for workers
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
def process_document_task(
    self,
    document_id: str,
    project_id: str,
) -> dict:
    """Process an uploaded document asynchronously.

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
        result = run_async(_process_document(document_id, project_id))
        return result
    except Exception as e:
        logger.error(
            "Document processing failed",
            document_id=document_id,
            error=str(e),
        )
        # Update document status to error
        run_async(_update_document_status(document_id, "error", str(e)))
        raise self.retry(exc=e, countdown=60)


async def _process_document(document_id: str, project_id: str) -> dict:
    """Async document processing implementation."""
    doc_uuid = uuid.UUID(document_id)
    proj_uuid = uuid.UUID(project_id)

    processor = get_document_processor()
    storage = get_storage_service()

    async with async_session() as session:
        # Get document
        result = await session.execute(select(Document).where(Document.id == doc_uuid))
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # Update status to processing
        document.status = "processing"
        await session.commit()

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

        await session.commit()

        logger.info(
            "Document processing complete",
            document_id=document_id,
            page_count=len(pages_data),
        )

        return {
            "status": "success",
            "document_id": document_id,
            "page_count": len(pages_data),
        }


async def _update_document_status(
    document_id: str,
    status: str,
    error: str | None = None,
) -> None:
    """Update document status in database."""
    async with async_session() as session:
        result = await session.execute(
            select(Document).where(Document.id == uuid.UUID(document_id))
        )
        document = result.scalar_one_or_none()

        if document:
            document.status = status
            if error:
                document.processing_error = error
            await session.commit()
