"""Document endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.document import Document
from app.models.project import Project
from app.models.page import Page
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentStatusResponse,
    TitleBlockRegionUpdateRequest,
    TitleBlockRegionUpdateResponse,
)
from app.services.document_processor import get_document_processor
from app.utils.storage import get_storage_service
from app.workers.document_tasks import process_document_task
from app.workers.ocr_tasks import process_document_title_block_task

router = APIRouter()


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: uuid.UUID,
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Upload a document to a project."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Validate file type
    processor = get_document_processor()
    if file.content_type not in processor.supported_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}",
        )

    # Read file
    file_bytes = await file.read()

    # Validate file content
    is_valid, error = processor.validate_file(file_bytes, file.content_type)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file: {error}",
        )

    # Create document record
    document_id = uuid.uuid4()
    file_type = processor.supported_types[file.content_type]

    document = Document(
        id=document_id,
        project_id=project_id,
        filename=f"{document_id}.{file_type}",
        original_filename=file.filename or "unknown",
        file_type=file_type,
        file_size=len(file_bytes),
        mime_type=file.content_type,
        storage_key="",  # Will be updated after upload
        status="uploading",
    )
    db.add(document)
    await db.commit()

    # Store original file
    try:
        storage_key = processor.store_original(
            file_bytes=file_bytes,
            project_id=project_id,
            document_id=document_id,
            filename=document.filename,
            mime_type=file.content_type,
        )
        document.storage_key = storage_key
        document.status = "uploaded"
        await db.commit()
    except Exception as e:
        document.status = "error"
        document.processing_error = str(e)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store file",
        )

    # Queue processing task
    process_document_task.delay(str(document_id), str(project_id))

    # Reload document with pages eagerly loaded (will be empty until worker processes it)
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .options(selectinload(Document.pages))
    )
    document = result.scalar_one()
    return document


@router.get("/projects/{project_id}/documents", response_model=DocumentListResponse)
async def list_project_documents(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all documents for a project."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get documents
    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                project_id=doc.project_id,
                filename=doc.filename,
                original_filename=doc.original_filename,
                file_type=doc.file_type,
                file_size=doc.file_size,
                page_count=doc.page_count,
                status=doc.status,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                pages=[],  # Don't load pages for list view
                title_block_region=doc.title_block_region,
            )
            for doc in documents
        ],
        total=len(documents),
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get document details."""
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.pages))
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.get("/documents/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get document processing status."""
    result = await db.execute(
        select(Document.status, Document.page_count, Document.processing_error).where(
            Document.id == document_id
        )
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return DocumentStatusResponse(
        status=row[0],
        page_count=row[1],
        error=row[2],
    )


@router.put(
    "/documents/{document_id}/title-block-region",
    response_model=TitleBlockRegionUpdateResponse,
)
async def update_title_block_region(
    document_id: uuid.UUID,
    request: TitleBlockRegionUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Save a title block region and queue OCR for all pages."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if request.x + request.width > 1 or request.y + request.height > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Region must fit within normalized bounds",
        )

    document.title_block_region = {
        "x": request.x,
        "y": request.y,
        "width": request.width,
        "height": request.height,
        "source_page_id": str(request.source_page_id)
        if request.source_page_id
        else None,
    }
    await db.commit()

    page_result = await db.execute(
        select(Page.id).where(Page.document_id == document_id)
    )
    page_ids = page_result.scalars().all()

    process_document_title_block_task.delay(str(document_id))

    return TitleBlockRegionUpdateResponse(
        status="queued",
        document_id=document_id,
        pages_queued=len(page_ids),
        title_block_region=document.title_block_region,
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a document and all associated files."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete files from storage
    processor = get_document_processor()
    processor.delete_document_files(document.project_id, document_id)

    # Delete from database (cascades to pages)
    await db.delete(document)
    await db.commit()
