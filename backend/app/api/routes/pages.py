"""Page endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.page import Page
from app.models.document import Document
from app.models.classification_history import ClassificationHistory
from app.schemas.page import (
    PageResponse,
    PageListResponse,
    PageOCRResponse,
    PageSummaryResponse,
    PageDocumentInfo,
    ScaleUpdateRequest,
)
from app.utils.storage import get_storage_service
from app.workers.ocr_tasks import process_page_ocr_task
from app.workers.classification_tasks import classify_page_task, classify_document_pages
from app.workers.scale_tasks import detect_page_scale_task
from app.services.scale_detector import get_scale_detector
from app.config import get_settings
from pydantic import BaseModel

router = APIRouter()
settings = get_settings()


def get_viewer_image_key(image_key: str) -> str:
    """Get the PNG viewer image key from the TIFF storage key.

    The document processor stores both formats:
    - image.tiff for OCR/LLM (flattened, consistent)
    - image.png for frontend viewer (browser-compatible)
    """
    if image_key.endswith(".tiff"):
        return image_key.replace(".tiff", ".png")
    return image_key


@router.get("/documents/{document_id}/pages", response_model=PageListResponse)
async def list_document_pages(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all pages for a document."""
    result = await db.execute(
        select(Page).where(Page.document_id == document_id).order_by(Page.page_number)
    )
    pages_list = result.scalars().all()

    # Sort by sheet_number if available (natural sort), otherwise by page_number
    def natural_sort_key(page):
        """Natural sort key for sheet numbers like S0.01, S2.02, etc.
        
        Returns a tuple of (has_sheet_number, sort_key) to ensure pages
        without sheet numbers sort after those with sheet numbers,
        and to avoid comparing mixed types.
        """
        import re
        
        if page.sheet_number:
            # Extract numbers from sheet_number for natural sorting
            parts = re.split(r"(\d+\.?\d*)", page.sheet_number)
            # Convert to tuple of (type_indicator, value) to avoid mixed type comparison
            # Strings get type 0, numbers get type 1 - this keeps them grouped
            key_parts = []
            for p in parts:
                if p:
                    if p.replace(".", "", 1).isdigit():
                        key_parts.append((1, float(p)))
                    else:
                        key_parts.append((0, p.lower()))
            return (0, key_parts)  # 0 = has sheet number, sorts first
        # Pages without sheet_number sort by page_number
        return (1, [(1, float(page.page_number))])  # 1 = no sheet number, sorts after

    pages = sorted(pages_list, key=natural_sort_key)

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
            concrete_relevance=page.concrete_relevance,
            title=page.title,
            sheet_number=page.sheet_number,
            scale_text=page.scale_text,
            scale_calibrated=page.scale_calibrated,
            status=page.status,
            image_url=storage.get_presigned_url(get_viewer_image_key(page.image_key), 3600),
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

    document_info = None
    document_row = await db.execute(
        select(Document.project_id, Document.title_block_region).where(
            Document.id == page.document_id
        )
    )
    document_data = document_row.one_or_none()
    if document_data:
        document_info = PageDocumentInfo(
            project_id=document_data[0],
            title_block_region=document_data[1],
        )

    return PageResponse(
        id=page.id,
        document_id=page.document_id,
        page_number=page.page_number,
        width=page.width,
        height=page.height,
        classification=page.classification,
        classification_confidence=page.classification_confidence,
        discipline=page.discipline,
        page_type=page.page_type,
        concrete_relevance=page.concrete_relevance,
        concrete_elements=page.concrete_elements,
        description=page.description,
        llm_provider=page.llm_provider,
        llm_latency_ms=page.llm_latency_ms,
        title=page.title,
        sheet_number=page.sheet_number,
        scale_text=page.scale_text,
        scale_value=page.scale_value,
        scale_unit=page.scale_unit,
        scale_calibrated=page.scale_calibrated,
        scale_detection_method=page.scale_detection_method,
        scale_calibration_data=page.scale_calibration_data,
        status=page.status,
        image_url=storage.get_presigned_url(get_viewer_image_key(page.image_key), 3600),
        thumbnail_url=storage.get_presigned_url(page.thumbnail_key, 3600)
        if page.thumbnail_key
        else None,
        document=document_info,
    )


@router.get("/pages/{page_id}/image")
async def get_page_image(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get redirect URL to page image (PNG for browser compatibility)."""
    result = await db.execute(select(Page.image_key).where(Page.id == page_id))
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    storage = get_storage_service()
    # Return PNG version for browser compatibility
    viewer_key = get_viewer_image_key(row[0])
    url = storage.get_presigned_url(viewer_key, 3600)

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
    """Reprocess OCR for a page.

    Useful when OCR failed due to errors (e.g., database truncation) or
    when OCR data needs to be refreshed with improved extraction logic.
    """
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    # Set status to processing when reprocessing OCR (unless already processing)
    if page.status != "processing":
        page.status = "processing"
        page.processing_error = None
        await db.commit()

    process_page_ocr_task.delay(str(page_id))

    return {
        "status": "queued",
        "page_id": str(page_id),
        "message": "OCR reprocessing queued",
    }


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

    provider: str | None = (
        None  # Optional provider override (only used if use_vision=True)
    )
    use_vision: bool = (
        False  # If True, use expensive LLM vision. If False (default), use fast OCR
    )


class ClassifyDocumentRequest(BaseModel):
    """Request to classify all pages in a document."""

    provider: str | None = (
        None  # Optional provider override (only used if use_vision=True)
    )
    use_vision: bool = (
        False  # If True, use expensive LLM vision. If False (default), use fast OCR
    )


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

    By default, uses fast OCR-based classification (free, instant).
    Set use_vision=true to use LLM vision models (slower, costs money, but more detailed).
    """
    # Verify page exists
    result = await db.execute(select(Page.id).where(Page.id == page_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    provider = request.provider if request else None
    use_vision = request.use_vision if request else False

    # Validate provider if specified
    if provider and provider not in settings.available_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' not available. "
            f"Available: {settings.available_providers}",
        )

    task = classify_page_task.delay(
        str(page_id),
        provider=provider,
        use_vision=use_vision,
    )

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

    By default, uses fast OCR-based classification (free, instant).
    Set use_vision=true to use LLM vision models (slower, costs money, but more detailed).
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
    use_vision = request.use_vision if request else False

    if provider and provider not in settings.available_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' not available. "
            f"Available: {settings.available_providers}",
        )

    result = classify_document_pages.delay(
        str(document_id),
        provider=provider,
        use_vision=use_vision,
    )

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


@router.get("/pages/{page_id}/classification/history")
async def get_page_classification_history(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
) -> dict:
    """Get classification history for a page.

    Returns all historical classification runs for BI analysis,
    ordered by most recent first.
    """
    # Verify page exists
    page_result = await db.execute(select(Page.id).where(Page.id == page_id))
    if not page_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Page not found")

    # Get classification history
    result = await db.execute(
        select(ClassificationHistory)
        .where(ClassificationHistory.page_id == page_id)
        .order_by(ClassificationHistory.created_at.desc())
        .limit(limit)
    )
    history = result.scalars().all()

    return {
        "page_id": str(page_id),
        "total": len(history),
        "history": [entry.to_dict() for entry in history],
    }


@router.get("/classification/history")
async def get_all_classification_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
) -> dict:
    """Get all recent classification history across all pages.

    Returns recent classification runs for BI analysis timeline,
    ordered by most recent first. Includes page/document context.
    """
    from sqlalchemy.orm import selectinload

    # Get classification history with page relationship
    result = await db.execute(
        select(ClassificationHistory)
        .options(selectinload(ClassificationHistory.page))
        .order_by(ClassificationHistory.created_at.desc())
        .limit(limit)
    )
    history = result.scalars().all()

    # Build response with page context
    history_with_context = []
    for entry in history:
        entry_dict = entry.to_dict()
        if entry.page:
            entry_dict["page_number"] = entry.page.page_number
            entry_dict["sheet_number"] = entry.page.sheet_number
            entry_dict["document_id"] = str(entry.page.document_id)
        history_with_context.append(entry_dict)

    return {
        "total": len(history),
        "history": history_with_context,
    }


@router.get("/documents/{document_id}/classification/progress")
async def get_document_classification_progress(
    document_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get classification progress for a document.

    Returns the number of pages classified vs total pages.
    Useful for showing progress bars during batch classification.
    """
    from sqlalchemy import func

    # Get total pages
    total_result = await db.execute(
        select(func.count(Page.id)).where(Page.document_id == document_id)
    )
    total_pages = total_result.scalar() or 0

    # Get classified pages (pages with classification data)
    classified_result = await db.execute(
        select(func.count(Page.id))
        .where(Page.document_id == document_id)
        .where(Page.classification.isnot(None))
    )
    classified_pages = classified_result.scalar() or 0

    # Calculate progress percentage
    progress_percent = (classified_pages / total_pages * 100) if total_pages > 0 else 0

    # Check if classification is complete
    is_complete = classified_pages == total_pages and total_pages > 0

    return {
        "document_id": str(document_id),
        "total_pages": total_pages,
        "classified_pages": classified_pages,
        "remaining_pages": total_pages - classified_pages,
        "progress_percent": round(progress_percent, 1),
        "is_complete": is_complete,
    }


@router.get("/classification/stats")
async def get_classification_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get aggregate classification statistics for BI.

    Returns stats grouped by provider/model for performance comparison.
    """
    from sqlalchemy import func

    # Get stats by provider/model
    result = await db.execute(
        select(
            ClassificationHistory.llm_provider,
            ClassificationHistory.llm_model,
            func.count(ClassificationHistory.id).label("total_runs"),
            func.avg(ClassificationHistory.llm_latency_ms).label("avg_latency_ms"),
            func.min(ClassificationHistory.llm_latency_ms).label("min_latency_ms"),
            func.max(ClassificationHistory.llm_latency_ms).label("max_latency_ms"),
            func.avg(ClassificationHistory.classification_confidence).label(
                "avg_confidence"
            ),
        )
        .group_by(
            ClassificationHistory.llm_provider,
            ClassificationHistory.llm_model,
        )
        .order_by(func.count(ClassificationHistory.id).desc())
    )
    rows = result.all()

    # Get concrete relevance distribution by provider
    relevance_result = await db.execute(
        select(
            ClassificationHistory.llm_provider,
            ClassificationHistory.concrete_relevance,
            func.count(ClassificationHistory.id).label("count"),
        ).group_by(
            ClassificationHistory.llm_provider,
            ClassificationHistory.concrete_relevance,
        )
    )
    relevance_rows = relevance_result.all()

    # Build relevance distribution dict
    relevance_by_provider: dict = {}
    for row in relevance_rows:
        provider = row[0]
        relevance = row[1] or "unknown"
        count = row[2]
        if provider not in relevance_by_provider:
            relevance_by_provider[provider] = {}
        relevance_by_provider[provider][relevance] = count

    return {
        "by_provider": [
            {
                "provider": row[0],
                "model": row[1],
                "total_runs": row[2],
                "avg_latency_ms": round(row[3], 2) if row[3] else None,
                "min_latency_ms": round(row[4], 2) if row[4] else None,
                "max_latency_ms": round(row[5], 2) if row[5] else None,
                "avg_confidence": round(row[6], 3) if row[6] else None,
                "relevance_distribution": relevance_by_provider.get(row[0], {}),
            }
            for row in rows
        ],
        "total_classifications": sum(row[2] for row in rows),
    }


# ============================================================================
# Scale Detection and Calibration endpoints
# ============================================================================


@router.post("/pages/{page_id}/detect-scale", status_code=status.HTTP_202_ACCEPTED)
async def detect_page_scale(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Trigger automatic scale detection for a page."""
    result = await db.execute(select(Page.id).where(Page.id == page_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    detect_page_scale_task.delay(str(page_id))

    return {"status": "queued", "page_id": str(page_id)}


@router.get("/pages/{page_id}/scale-detection-status")
async def get_scale_detection_status(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get status of scale detection task.

    Returns lightweight status without full page data.
    """
    result = await db.execute(
        select(
            Page.scale_calibration_data,
            Page.scale_text,
            Page.scale_value,
            Page.scale_calibrated,
        ).where(Page.id == page_id)
    )
    page_data = result.one_or_none()

    if not page_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    scale_calibration_data, scale_text, scale_value, scale_calibrated = page_data

    # If no detection data yet, still processing
    if not scale_calibration_data:
        return {
            "status": "processing",
            "scale_text": None,
            "scale_value": None,
            "calibrated": False,
            "detection": None,
        }

    # Detection complete
    return {
        "status": "complete",
        "scale_text": scale_text,
        "scale_value": scale_value,
        "calibrated": scale_calibrated,
        "detection": scale_calibration_data,
    }


@router.put("/pages/{page_id}/scale")
async def update_page_scale(
    page_id: uuid.UUID,
    request: ScaleUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Manually set or update page scale."""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    page.scale_value = request.scale_value
    page.scale_unit = request.scale_unit
    page.scale_calibrated = True

    if request.scale_text:
        page.scale_text = request.scale_text

    # Store calibration source
    if not page.scale_calibration_data:
        page.scale_calibration_data = {}
    page.scale_calibration_data["manual_calibration"] = {
        "scale_value": request.scale_value,
        "scale_unit": request.scale_unit,
        "scale_text": request.scale_text,
    }

    await db.commit()

    return {
        "status": "success",
        "page_id": str(page_id),
        "scale_value": page.scale_value,
        "scale_unit": page.scale_unit,
        "scale_calibrated": page.scale_calibrated,
    }


@router.post("/pages/{page_id}/calibrate")
async def calibrate_page_scale(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    pixel_distance: float,
    real_distance: float,
    real_unit: str = "foot",
):
    """Calibrate page scale using a known distance.

    The user draws a line on the page and specifies the real-world distance.
    """
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    detector = get_scale_detector()

    try:
        calibration = detector.calculate_scale_from_calibration(
            pixel_distance=pixel_distance,
            real_distance=real_distance,
            real_unit=real_unit,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Update page
    page.scale_value = calibration["pixels_per_foot"]
    page.scale_unit = "foot"
    page.scale_calibrated = True

    # Store calibration data
    if not page.scale_calibration_data:
        page.scale_calibration_data = {}
    page.scale_calibration_data["calibration"] = calibration
    page.scale_calibration_data["calibration_input"] = {
        "pixel_distance": pixel_distance,
        "real_distance": real_distance,
        "real_unit": real_unit,
    }

    await db.commit()

    return {
        "status": "success",
        "page_id": str(page_id),
        "pixels_per_foot": calibration["pixels_per_foot"],
        "estimated_scale_ratio": calibration["estimated_ratio"],
    }


@router.post("/pages/{page_id}/copy-scale-from/{source_page_id}")
async def copy_scale_from_page(
    page_id: uuid.UUID,
    source_page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Copy scale settings from another page."""
    # Get source page
    result = await db.execute(select(Page).where(Page.id == source_page_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source page not found",
        )

    if not source.scale_calibrated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source page is not calibrated",
        )

    # Get target page
    result = await db.execute(select(Page).where(Page.id == page_id))
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target page not found",
        )

    # Copy scale
    target.scale_value = source.scale_value
    target.scale_unit = source.scale_unit
    target.scale_text = source.scale_text
    target.scale_calibrated = True

    if not target.scale_calibration_data:
        target.scale_calibration_data = {}
    target.scale_calibration_data["copied_from"] = str(source_page_id)

    await db.commit()

    return {
        "status": "success",
        "page_id": str(page_id),
        "scale_value": target.scale_value,
        "copied_from": str(source_page_id),
    }
