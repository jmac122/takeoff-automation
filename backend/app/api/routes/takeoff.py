"""API routes for AI takeoff generation."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import get_settings
from app.models.page import Page
from app.models.document import Document
from app.models.condition import Condition
from app.schemas.task import StartTaskResponse
from app.services.task_tracker import TaskTracker
from app.workers.takeoff_tasks import (
    generate_ai_takeoff_task,
    compare_providers_task,
    batch_ai_takeoff_task,
    autonomous_ai_takeoff_task,
)

router = APIRouter()
settings = get_settings()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class GenerateTakeoffRequest(BaseModel):
    """Request to generate AI takeoff."""

    condition_id: uuid.UUID
    provider: str | None = None  # Optional provider override


class AutonomousTakeoffRequest(BaseModel):
    """Request for autonomous AI takeoff - AI determines elements."""

    provider: str | None = None  # Optional provider override
    project_id: uuid.UUID | None = None  # Optional: auto-create conditions in this project


class CompareProvidersRequest(BaseModel):
    """Request to compare providers."""

    condition_id: uuid.UUID
    providers: list[str] | None = None  # None = all available


class BatchTakeoffRequest(BaseModel):
    """Request for batch AI takeoff."""

    page_ids: list[uuid.UUID]
    condition_id: uuid.UUID
    provider: str | None = None


class BatchTakeoffResponse(StartTaskResponse):
    """Response for batch takeoff."""

    pages_count: int


class AvailableProvidersResponse(BaseModel):
    """Response with available providers."""

    available: list[str]
    default: str
    task_config: dict[str, str]


# ============================================================================
# Dependencies
# ============================================================================


class CalibratedPageData:
    """Data class for calibrated page with its document."""

    def __init__(self, page: Page, document: Document):
        self.page = page
        self.document = document


async def get_calibrated_page(
    page_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CalibratedPageData:
    """Dependency to fetch and validate a calibrated page.
    
    Raises:
        HTTPException 404: If page not found
        HTTPException 400: If page not calibrated
    """
    result = await db.execute(
        select(Page, Document)
        .join(Document, Page.document_id == Document.id)
        .where(Page.id == page_id)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    page, document = row

    if not page.scale_calibrated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be calibrated before AI takeoff. Please set the scale first.",
        )

    return CalibratedPageData(page=page, document=document)


def validate_provider(provider: str | None) -> str | None:
    """Validate that provider is available if specified.
    
    Raises:
        HTTPException 400: If provider not available
    """
    if provider and provider not in settings.available_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider}' not available. "
            f"Available: {settings.available_providers}",
        )
    return provider


# ============================================================================
# Helpers
# ============================================================================


async def _register_and_dispatch(
    db: AsyncSession,
    *,
    task_type: str,
    task_name: str,
    project_id: str,
    metadata: dict | None,
    celery_task,
    args: list,
    kwargs: dict | None = None,
) -> StartTaskResponse:
    """Register a task in DB then dispatch to Celery.

    Centralises the ordering guarantee: the DB record is always created
    **before** ``apply_async`` so that ``_build_task_response`` will
    never see a Celery result without a matching ``TaskRecord``.
    """
    task_id = str(uuid.uuid4())

    await TaskTracker.register_async(
        db,
        task_id=task_id,
        task_type=task_type,
        task_name=task_name,
        project_id=project_id,
        metadata=metadata,
    )

    celery_task.apply_async(
        args=args,
        kwargs=kwargs or {},
        task_id=task_id,
    )

    return StartTaskResponse(
        task_id=task_id,
        task_type=task_type,
        task_name=task_name,
        message=task_name,
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/pages/{page_id}/ai-takeoff", response_model=StartTaskResponse)
async def generate_ai_takeoff(
    page_id: uuid.UUID,
    request: GenerateTakeoffRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    page_data: Annotated[CalibratedPageData, Depends(get_calibrated_page)],
) -> StartTaskResponse:
    """Generate AI takeoff for a page.

    Optionally specify an LLM provider to use.
    Available providers: anthropic, openai, google, xai
    """
    # Verify condition exists
    result = await db.execute(select(Condition).where(Condition.id == request.condition_id))
    condition = result.scalar_one_or_none()

    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )

    # Verify page and condition belong to the same project
    if page_data.document.project_id != condition.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page and condition must belong to the same project",
        )

    # Validate provider
    provider = validate_provider(request.provider)

    provider_msg = f" using {provider}" if provider else ""

    return await _register_and_dispatch(
        db,
        task_type="ai_takeoff",
        task_name=f"AI takeoff for page {page_id}{provider_msg}",
        project_id=str(page_data.document.project_id),
        metadata={"page_id": str(page_id), "condition_id": str(request.condition_id), "provider": provider},
        celery_task=generate_ai_takeoff_task,
        args=[str(page_id), str(request.condition_id)],
        kwargs={"provider": provider},
    )


@router.post("/pages/{page_id}/autonomous-takeoff", response_model=StartTaskResponse)
async def autonomous_ai_takeoff(
    page_id: uuid.UUID,
    request: AutonomousTakeoffRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    page_data: Annotated[CalibratedPageData, Depends(get_calibrated_page)],
) -> StartTaskResponse:
    """Autonomous AI takeoff - AI identifies ALL concrete elements on its own.

    Unlike the standard ai-takeoff endpoint, this does NOT require a pre-defined
    condition. The AI will independently analyze the drawing and identify all
    concrete elements it can find (slabs, footings, walls, columns, etc.).

    This is the true test of AI takeoff capability - replacing manual element
    identification like On Screen Takeoff / Bluebeam.

    If project_id is provided, conditions will be auto-created for each
    element type the AI discovers.
    """
    # Validate provider
    provider = validate_provider(request.provider)

    # If project_id is provided, verify it matches the page's project
    project_id_to_use: str
    if request.project_id:
        if request.project_id != page_data.document.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provided project_id does not match the page's project",
            )
        project_id_to_use = str(request.project_id)
    else:
        # Use the page's actual project
        project_id_to_use = str(page_data.document.project_id)

    provider_msg = f" using {provider}" if provider else ""

    return await _register_and_dispatch(
        db,
        task_type="autonomous_ai_takeoff",
        task_name=f"Autonomous AI takeoff for page {page_id}{provider_msg}",
        project_id=project_id_to_use,
        metadata={"page_id": str(page_id), "provider": provider},
        celery_task=autonomous_ai_takeoff_task,
        args=[str(page_id)],
        kwargs={"provider": provider, "project_id": project_id_to_use},
    )


@router.post("/pages/{page_id}/compare-providers", response_model=StartTaskResponse)
async def compare_providers(
    page_id: uuid.UUID,
    request: CompareProvidersRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    page_data: Annotated[CalibratedPageData, Depends(get_calibrated_page)],
) -> StartTaskResponse:
    """Compare AI takeoff results across multiple providers.

    Useful for benchmarking which provider works best for specific content.
    Does not create measurements - just returns comparison data.
    """
    # Verify condition exists
    result = await db.execute(select(Condition).where(Condition.id == request.condition_id))
    condition = result.scalar_one_or_none()

    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )

    # Verify page and condition belong to the same project
    if page_data.document.project_id != condition.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page and condition must belong to the same project",
        )

    # Validate providers if specified
    providers = request.providers
    if providers:
        invalid = set(providers) - set(settings.available_providers)
        if invalid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Providers not available: {invalid}. "
                f"Available: {settings.available_providers}",
            )

    return await _register_and_dispatch(
        db,
        task_type="compare_providers",
        task_name=f"Provider comparison for page {page_id}",
        project_id=str(page_data.document.project_id),
        metadata={"page_id": str(page_id), "condition_id": str(request.condition_id), "providers": providers},
        celery_task=compare_providers_task,
        args=[str(page_id), str(request.condition_id)],
        kwargs={"providers": providers},
    )


@router.post("/batch-ai-takeoff", response_model=BatchTakeoffResponse)
async def batch_ai_takeoff(
    request: BatchTakeoffRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BatchTakeoffResponse:
    """Generate AI takeoff for multiple pages.

    Queues individual tasks for each page.
    All pages must belong to the same project as the condition and be calibrated.
    """
    # Verify condition exists
    result = await db.execute(select(Condition).where(Condition.id == request.condition_id))
    condition = result.scalar_one_or_none()

    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )

    # Validate provider if specified
    validate_provider(request.provider)

    # Check for duplicate page_ids
    unique_page_ids = set(request.page_ids)
    if len(unique_page_ids) != len(request.page_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate page_ids are not allowed",
        )

    # Verify all pages exist and belong to the condition's project
    result = await db.execute(
        select(Page, Document)
        .join(Document, Page.document_id == Document.id)
        .where(Page.id.in_(request.page_ids))
    )
    rows = result.all()

    if len(rows) != len(request.page_ids):
        found_ids = {row[0].id for row in rows}
        missing = [str(pid) for pid in request.page_ids if pid not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pages not found: {missing}",
        )

    # Check all pages belong to the condition's project
    invalid_pages = [
        str(page.id) for page, doc in rows
        if doc.project_id != condition.project_id
    ]
    if invalid_pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pages do not belong to the condition's project: {invalid_pages}",
        )

    # Check all pages are calibrated
    uncalibrated_pages = [
        str(page.id) for page, doc in rows
        if not page.scale_calibrated
    ]
    if uncalibrated_pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pages must be calibrated before AI takeoff: {uncalibrated_pages}",
        )

    pages_count = len(request.page_ids)

    base_response = await _register_and_dispatch(
        db,
        task_type="batch_ai_takeoff",
        task_name=f"Batch AI takeoff for {pages_count} pages",
        project_id=str(condition.project_id),
        metadata={
            "page_ids": [str(pid) for pid in request.page_ids],
            "condition_id": str(request.condition_id),
            "provider": request.provider,
        },
        celery_task=batch_ai_takeoff_task,
        args=[[str(pid) for pid in request.page_ids], str(request.condition_id)],
        kwargs={"provider": request.provider},
    )

    return BatchTakeoffResponse(
        task_id=base_response.task_id,
        task_type=base_response.task_type,
        task_name=base_response.task_name,
        message=base_response.message,
        pages_count=pages_count,
    )


@router.get("/ai-takeoff/providers", response_model=AvailableProvidersResponse)
async def get_available_providers() -> AvailableProvidersResponse:
    """Get available LLM providers for AI takeoff."""
    return AvailableProvidersResponse(
        available=settings.available_providers,
        default=settings.default_llm_provider,
        task_config={
            "element_detection": settings.get_provider_for_task("element_detection"),
            "measurement": settings.get_provider_for_task("measurement"),
        },
    )


@router.get(
    "/tasks/{task_id}/status",
    include_in_schema=False,
)
async def get_task_status_legacy(task_id: str, request: Request) -> RedirectResponse:
    """Legacy task status endpoint — redirects to the unified Task API."""
    new_url = request.url_for("get_task_status", task_id=task_id)
    return RedirectResponse(
        url=str(new_url),
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )
