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
    LinkRevisionRequest,
    RevisionChainItem,
    RevisionChainResponse,
    PageComparisonRequest,
    PageComparisonResponse,
)
from app.services.document_processor import get_document_processor
from app.services.task_tracker import TaskTracker
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

    # Queue processing task with task tracking
    task_id = str(uuid.uuid4())
    await TaskTracker.register_async(
        db,
        task_id=task_id,
        task_type="document_processing",
        task_name=f"Processing {file.filename}",
        project_id=str(project_id),
        metadata={"document_id": str(document_id), "filename": file.filename},
    )
    process_document_task.apply_async(
        args=[str(document_id), str(project_id)],
        task_id=task_id,
    )

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
                revision_number=doc.revision_number,
                revision_date=doc.revision_date,
                revision_label=doc.revision_label,
                supersedes_document_id=doc.supersedes_document_id,
                is_latest_revision=doc.is_latest_revision,
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

    # Handle revision chain cleanup BEFORE deletion
    # Only restore predecessor's is_latest flag if this document IS actually latest
    # (if this is a middle revision, successors will be orphaned and keep their flags)
    if document.supersedes_document_id and document.is_latest_revision:
        result = await db.execute(
            select(Document).where(Document.id == document.supersedes_document_id)
        )
        predecessor = result.scalar_one_or_none()
        if predecessor:
            # Check if predecessor has any OTHER successors besides this one
            result = await db.execute(
                select(Document).where(
                    Document.supersedes_document_id == predecessor.id,
                    Document.id != document_id,
                )
            )
            other_successor = result.scalar_one_or_none()
            if not other_successor:
                # No other successors after we delete this doc, so predecessor becomes latest
                predecessor.is_latest_revision = True

    # Delete files from storage
    processor = get_document_processor()
    processor.delete_document_files(document.project_id, document_id)

    # Delete from database (cascades to pages, SET NULL on successors' FK)
    await db.delete(document)
    await db.commit()


# ============================================================================
# Revision Management
# ============================================================================


@router.put("/documents/{document_id}/revision", response_model=DocumentResponse)
async def link_revision(
    document_id: uuid.UUID,
    request: LinkRevisionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Link a document as a revision of another document.

    Sets the current document's supersedes_document_id and marks the
    previous document as no longer the latest revision.
    """
    # Load current document
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.pages))
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Load the document being superseded
    result = await db.execute(
        select(Document).where(Document.id == request.supersedes_document_id)
    )
    old_doc = result.scalar_one_or_none()
    if not old_doc:
        raise HTTPException(status_code=404, detail="Superseded document not found")

    # Reject self-cycles
    if document_id == request.supersedes_document_id:
        raise HTTPException(
            status_code=400,
            detail="A document cannot supersede itself",
        )

    # Must be in the same project
    if document.project_id != old_doc.project_id:
        raise HTTPException(
            status_code=400,
            detail="Documents must belong to the same project",
        )

    # Reject cycles: check if old_doc is a descendant of document
    # (i.e., document is already in old_doc's ancestor chain)
    current = old_doc
    visited = {old_doc.id}
    while current.supersedes_document_id and current.supersedes_document_id not in visited:
        if current.supersedes_document_id == document_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot create circular revision chain",
            )
        visited.add(current.supersedes_document_id)
        result = await db.execute(
            select(Document).where(Document.id == current.supersedes_document_id)
        )
        current = result.scalar_one_or_none()
        if not current:
            break

    # Reject branches: check if old_doc already has a successor
    result = await db.execute(
        select(Document).where(Document.supersedes_document_id == old_doc.id)
    )
    existing_successor = result.scalar_one_or_none()
    if existing_successor and existing_successor.id != document_id:
        raise HTTPException(
            status_code=400,
            detail=f"Document already has a successor: {existing_successor.original_filename}",
        )

    # If document was previously linked to a different parent, restore
    # that old parent's is_latest_revision flag (it no longer has a successor)
    previous_parent_id = document.supersedes_document_id
    if previous_parent_id and previous_parent_id != request.supersedes_document_id:
        result = await db.execute(
            select(Document).where(Document.id == previous_parent_id)
        )
        previous_parent = result.scalar_one_or_none()
        if previous_parent:
            # Check if the previous parent has any OTHER successors
            result = await db.execute(
                select(Document).where(
                    Document.supersedes_document_id == previous_parent_id,
                    Document.id != document_id,
                )
            )
            other_successor = result.scalar_one_or_none()
            if not other_successor:
                # No other successors, restore is_latest_revision
                previous_parent.is_latest_revision = True

    # Update current document
    document.supersedes_document_id = request.supersedes_document_id
    document.revision_number = request.revision_number
    document.revision_date = request.revision_date
    document.revision_label = request.revision_label
    
    # Only mark as latest if this document has no successor
    result = await db.execute(
        select(Document).where(Document.supersedes_document_id == document_id)
    )
    has_successor = result.scalar_one_or_none() is not None
    document.is_latest_revision = not has_successor

    # Mark new parent as no longer latest
    old_doc.is_latest_revision = False

    await db.commit()
    await db.refresh(document)
    return document


@router.get(
    "/documents/{document_id}/revisions",
    response_model=RevisionChainResponse,
)
async def get_revision_chain(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the full revision chain for a document.

    Walks the supersedes_document_id chain backwards to build an ordered
    list from oldest to newest revision.
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Collect all documents in this project that form a chain
    # Walk backward from the given document
    chain: list[Document] = [document]
    current = document
    visited = {document.id}
    while (
        current.supersedes_document_id and current.supersedes_document_id not in visited
    ):
        result = await db.execute(
            select(Document).where(Document.id == current.supersedes_document_id)
        )
        prev = result.scalar_one_or_none()
        if not prev:
            break
        visited.add(prev.id)
        chain.append(prev)
        current = prev

    # Walk forward from the given document (find docs that supersede it)
    current = document
    while True:
        result = await db.execute(
            select(Document).where(
                Document.supersedes_document_id == current.id,
                Document.id.notin_(visited),
            )
        )
        next_doc = result.scalars().first()
        if not next_doc:
            break
        visited.add(next_doc.id)
        chain.insert(0, next_doc)  # Insert at front (newer)
        current = next_doc

    # The chain is currently ordered newest → oldest (forward walk
    # inserted at front, backward walk appended).  Reverse to get
    # oldest-first, preserving the topological order from the
    # supersedes_document_id linked list rather than relying on
    # created_at which can differ from true revision sequence.
    chain.reverse()

    return RevisionChainResponse(
        chain=[
            RevisionChainItem(
                id=doc.id,
                original_filename=doc.original_filename,
                revision_number=doc.revision_number,
                revision_date=doc.revision_date,
                revision_label=doc.revision_label,
                is_latest_revision=doc.is_latest_revision,
                page_count=doc.page_count,
                created_at=doc.created_at,
            )
            for doc in chain
        ],
        current_document_id=document_id,
    )


@router.post(
    "/documents/compare-pages",
    response_model=PageComparisonResponse,
)
async def compare_pages(
    request: PageComparisonRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Compare a specific page between two document revisions.

    Returns image URLs for both pages so the frontend can render
    an overlay comparison.
    """
    storage = get_storage_service()

    # Find old page
    old_page_result = await db.execute(
        select(Page).where(
            Page.document_id == request.old_document_id,
            Page.page_number == request.page_number,
        )
    )
    old_page = old_page_result.scalar_one_or_none()

    # Find new page
    new_page_result = await db.execute(
        select(Page).where(
            Page.document_id == request.new_document_id,
            Page.page_number == request.page_number,
        )
    )
    new_page = new_page_result.scalar_one_or_none()

    old_image_url = None
    new_image_url = None

    # Convert TIFF keys to PNG for browser-viewable URLs
    def _get_viewer_image_key(image_key: str) -> str:
        """Convert .tiff storage keys to .png for browser compatibility."""
        if image_key.endswith(".tiff"):
            return image_key.replace(".tiff", ".png")
        return image_key

    if old_page and old_page.image_key:
        try:
            viewer_key = _get_viewer_image_key(old_page.image_key)
            old_image_url = storage.get_presigned_url(
                viewer_key, expires_in=3600
            )
        except Exception:
            pass

    if new_page and new_page.image_key:
        try:
            viewer_key = _get_viewer_image_key(new_page.image_key)
            new_image_url = storage.get_presigned_url(
                viewer_key, expires_in=3600
            )
        except Exception:
            pass

    return PageComparisonResponse(
        old_page_id=old_page.id if old_page else None,
        new_page_id=new_page.id if new_page else None,
        old_image_url=old_image_url,
        new_image_url=new_image_url,
        page_number=request.page_number,
        has_both=old_page is not None and new_page is not None,
    )
