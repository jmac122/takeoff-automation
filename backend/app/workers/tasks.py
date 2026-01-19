"""Celery tasks for background processing."""

from app.workers.celery_app import celery_app


@celery_app.task
def process_document(document_id: str) -> dict:
    """Process a document asynchronously."""
    return {"document_id": document_id, "status": "processed"}