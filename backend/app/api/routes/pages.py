"""Page endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.page import Page
from app.schemas.page import (
    PageResponse,
    PageListResponse,
    PageOCRResponse,
    PageSummaryResponse,
)
from app.utils.storage import get_storage_service
from app.workers.ocr_tasks import process_page_ocr_task
from app.workers.classification_tasks import classify_page_task, classify_document_pages
from app.config import get_settings
from pydantic import BaseModel

router = APIRouter()
settings = get_settings()


@router.get("/documents/{document_id}/pages", response_model=PageListResponse)
async def list_document_pages(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all pages for a document."""
    result = await db.execute(
        select(Page).where(Page.document_id == document_id).order_by(Page.page_number)
    )
    pages = result.scalars().all()

    # Generate URLs for images
    storage = get_storage_service()
    pages_data = []
    for page in pages:
        page_dict = PageSummaryResponse(
            id=page.id,
            document_id=page.document_id,
            page_number=page.page_number,
            width=page.width,
            height=page.height,
            classification=page.classification,
            title=page.title,
            sheet_number=page.sheet_number,
            scale_text=page.scale_text,
            scale_calibrated=page.scale_calibrated,
            status=page.status,
            thumbnail_url=storage.get_presigned_url(page.thumbnail_key, 3600)
            if page.thumbnail_key
            else None,
        )
        pages_data.append(page_dict)

    return PageListResponse(pages=pages_data, total=len(pages_data))


@router.get("/pages/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get page details."""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    storage = get_storage_service()

    return PageResponse(
        id=page.id,
        document_id=page.document_id,
        page_number=page.page_number,
        width=page.width,
        height=page.height,
        classification=page.classification,
        classification_confidence=page.classification_confidence,
        title=page.title,
        sheet_number=page.sheet_number,
        scale_text=page.scale_text,
        scale_value=page.scale_value,
        scale_unit=page.scale_unit,
        scale_calibrated=page.scale_calibrated,
        status=page.status,
        image_url=storage.get_presigned_url(page.image_key, 3600),
        thumbnail_url=storage.get_presigned_url(page.thumbnail_key, 3600)
        if page.thumbnail_key
        else None,
    )


@router.get("/pages/{page_id}/image")
async def get_page_image(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get redirect URL to page image."""
    result = await db.execute(select(Page.image_key).where(Page.id == page_id))
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    storage = get_storage_service()
    url = storage.get_presigned_url(row[0], 3600)

    return RedirectResponse(url=url)


@router.get("/pages/{page_id}/ocr", response_model=PageOCRResponse)
async def get_page_ocr(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get OCR data for a page."""
    result = await db.execute(
        select(
            Page.ocr_text,
            Page.ocr_blocks,
            Page.sheet_number,
            Page.title,
            Page.scale_text,
        ).where(Page.id == page_id)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    return PageOCRResponse(
        full_text=row[0],
        blocks=row[1].get("blocks", []) if row[1] else [],
        detected_scales=row[1].get("detected_scales", []) if row[1] else [],
        detected_sheet_numbers=row[1].get("detected_sheet_numbers", [])
        if row[1]
        else [],
        detected_titles=row[1].get("detected_titles", []) if row[1] else [],
        sheet_number=row[2],
        title=row[3],
        scale_text=row[4],
    )


@router.post("/pages/{page_id}/reprocess-ocr", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_page_ocr(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reprocess OCR for a page."""
    result = await db.execute(select(Page.id).where(Page.id == page_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    process_page_ocr_task.delay(str(page_id))

    return {"status": "queued", "page_id": str(page_id)}


@router.get("/projects/{project_id}/search")
async def search_pages(
    project_id: uuid.UUID,
    q: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Search pages by OCR text within a project."""
    from sqlalchemy import text

    query = text("""
        SELECT p.id, p.document_id, p.page_number, p.title, p.sheet_number,
               ts_rank(to_tsvector('english', COALESCE(p.ocr_text, '')), 
                       plainto_tsquery('english', :query)) as rank
        FROM pages p
        JOIN documents d ON p.document_id = d.id
        WHERE d.project_id = :project_id
          AND to_tsvector('english', COALESCE(p.ocr_text, '')) @@ plainto_tsquery('english', :query)
        ORDER BY rank DESC
        LIMIT 50
    """)

    result = await db.execute(query, {"project_id": project_id, "query": q})
    rows = result.all()

    return {
        "results": [
            {
                "page_id": str(row[0]),
                "document_id": str(row[1]),
                "page_number": row[2],
                "title": row[3],
                "sheet_number": row[4],
                "relevance": float(row[5]),
            }
            for row in rows
        ],
        "total": len(rows),
    }


# ============================================================================
# Classification endpoints
# ============================================================================


class ClassifyPageRequest(BaseModel):
    """Request to classify a single page."""

    provider: str | None = None  # Optional provider override


class ClassifyDocumentRequest(BaseModel):
    """Request to classify all pages in a document."""

    provider: str | None = None  # Optional provider override


class ClassificationTaskResponse(BaseModel):
    """Response with task ID for async classification."""

    task_id: str
    message: str


class DocumentClassificationResponse(BaseModel):
    """Response for document classification."""

    document_id: str
    pages_queued: int
    task_ids: list[str]


@router.post(
    "/pages/{page_id}/classify",
    response_model=ClassificationTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def classify_page_endpoint(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: ClassifyPageRequest | None = None,
) -> ClassificationTaskResponse:
    """Trigger classification for a single page.

    Optionally specify an LLM provider to use for this classification.
    Available providers: anthropic, openai, google, xai
    """
    # Verify page exists
    result = await db.execute(select(Page.id).where(Page.id == page_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    provider = request.provider if request else None

    # Validate provider if specified
    if provider and provider not in settings.available_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' not available. "
            f"Available: {settings.available_providers}",
        )

    task = classify_page_task.delay(str(page_id), provider=provider)

    return ClassificationTaskResponse(
        task_id=task.id,
        message=f"Classification started for page {page_id}"
        + (f" using {provider}" if provider else ""),
    )


@router.post(
    "/documents/{document_id}/classify",
    response_model=DocumentClassificationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def classify_document_endpoint(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: ClassifyDocumentRequest | None = None,
) -> DocumentClassificationResponse:
    """Trigger classification for all pages in a document.

    Optionally specify an LLM provider to use for classification.
    """
    # Verify document exists (check if any pages exist)
    result = await db.execute(
        select(Page.id).where(Page.document_id == document_id).limit(1)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or has no pages",
        )

    provider = request.provider if request else None

    if provider and provider not in settings.available_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' not available. "
            f"Available: {settings.available_providers}",
        )

    result = classify_document_pages.delay(str(document_id), provider=provider)

    # Wait briefly for task to start and get info
    try:
        info = result.get(timeout=5)
        return DocumentClassificationResponse(**info)
    except Exception:
        return DocumentClassificationResponse(
            document_id=str(document_id),
            pages_queued=0,
            task_ids=[result.id],
        )


@router.get("/pages/{page_id}/classification")
async def get_page_classification(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get classification results for a page."""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return {
        "page_id": str(page.id),
        "classification": page.classification,
        "confidence": page.classification_confidence,
        "concrete_relevance": page.concrete_relevance,
        "metadata": page.classification_metadata,
    }
