"""API routes for AI takeoff generation."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import get_settings
from app.models.page import Page
from app.models.document import Document
from app.models.condition import Condition
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

    condition_id: str
    provider: str | None = None  # Optional provider override

    @field_validator("condition_id")
    @classmethod
    def validate_condition_id(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid UUID format: {v}")


class AutonomousTakeoffRequest(BaseModel):
    """Request for autonomous AI takeoff - AI determines elements."""

    provider: str | None = None  # Optional provider override
    project_id: str | None = None  # Optional: auto-create conditions in this project

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            uuid.UUID(v)
            return v
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid UUID format: {v}")


class CompareProvidersRequest(BaseModel):
    """Request to compare providers."""

    condition_id: str
    providers: list[str] | None = None  # None = all available

    @field_validator("condition_id")
    @classmethod
    def validate_condition_id(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid UUID format: {v}")


class BatchTakeoffRequest(BaseModel):
    """Request for batch AI takeoff."""

    page_ids: list[str]
    condition_id: str
    provider: str | None = None

    @field_validator("condition_id")
    @classmethod
    def validate_condition_id(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid UUID format: {v}")

    @field_validator("page_ids")
    @classmethod
    def validate_page_ids(cls, v: list[str]) -> list[str]:
        for page_id in v:
            try:
                uuid.UUID(page_id)
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid UUID format in page_ids: {page_id}")
        return v


class TakeoffTaskResponse(BaseModel):
    """Response with task ID."""

    task_id: str
    message: str
    provider: str | None = None


class BatchTakeoffResponse(BaseModel):
    """Response for batch takeoff."""

    task_id: str
    message: str
    pages_count: int


class AvailableProvidersResponse(BaseModel):
    """Response with available providers."""

    available: list[str]
    default: str
    task_config: dict[str, str]


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/pages/{page_id}/ai-takeoff", response_model=TakeoffTaskResponse)
async def generate_ai_takeoff(
    page_id: uuid.UUID,
    request: GenerateTakeoffRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TakeoffTaskResponse:
    """Generate AI takeoff for a page.

    Optionally specify an LLM provider to use.
    Available providers: anthropic, openai, google, xai
    """
    # Verify page exists and get its project via document
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

    # Verify page is calibrated
    if not page.scale_calibrated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be calibrated before AI takeoff. Please set the scale first.",
        )

    # Verify condition exists
    condition_uuid = uuid.UUID(request.condition_id)
    result = await db.execute(select(Condition).where(Condition.id == condition_uuid))
    condition = result.scalar_one_or_none()

    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )

    # Verify page and condition belong to the same project
    if document.project_id != condition.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page and condition must belong to the same project",
        )

    # Validate provider if specified
    provider = request.provider
    if provider and provider not in settings.available_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider}' not available. "
            f"Available: {settings.available_providers}",
        )

    # Queue the task
    task = generate_ai_takeoff_task.delay(
        str(page_id),
        request.condition_id,
        provider=provider,
    )

    provider_msg = f" using {provider}" if provider else ""

    return TakeoffTaskResponse(
        task_id=task.id,
        message=f"AI takeoff started for page {page_id}{provider_msg}",
        provider=provider,
    )


@router.post("/pages/{page_id}/autonomous-takeoff", response_model=TakeoffTaskResponse)
async def autonomous_ai_takeoff(
    page_id: uuid.UUID,
    request: AutonomousTakeoffRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TakeoffTaskResponse:
    """Autonomous AI takeoff - AI identifies ALL concrete elements on its own.

    Unlike the standard ai-takeoff endpoint, this does NOT require a pre-defined
    condition. The AI will independently analyze the drawing and identify all
    concrete elements it can find (slabs, footings, walls, columns, etc.).

    This is the true test of AI takeoff capability - replacing manual element
    identification like On Screen Takeoff / Bluebeam.

    If project_id is provided, conditions will be auto-created for each
    element type the AI discovers.
    """
    # Verify page exists and get its project via document
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

    # Verify page is calibrated
    if not page.scale_calibrated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be calibrated before AI takeoff. Please set the scale first.",
        )

    # Validate provider if specified
    provider = request.provider
    if provider and provider not in settings.available_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider}' not available. "
            f"Available: {settings.available_providers}",
        )

    # If project_id is provided, verify it matches the page's project
    project_id_to_use = request.project_id
    if project_id_to_use:
        project_uuid = uuid.UUID(project_id_to_use)
        if project_uuid != document.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provided project_id does not match the page's project",
            )
    else:
        # Use the page's actual project
        project_id_to_use = str(document.project_id)

    # Queue the autonomous task
    task = autonomous_ai_takeoff_task.delay(
        str(page_id),
        provider=provider,
        project_id=project_id_to_use,
    )

    provider_msg = f" using {provider}" if provider else ""

    return TakeoffTaskResponse(
        task_id=task.id,
        message=f"Autonomous AI takeoff started for page {page_id}{provider_msg}",
        provider=provider,
    )


@router.post("/pages/{page_id}/compare-providers", response_model=TakeoffTaskResponse)
async def compare_providers(
    page_id: uuid.UUID,
    request: CompareProvidersRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TakeoffTaskResponse:
    """Compare AI takeoff results across multiple providers.

    Useful for benchmarking which provider works best for specific content.
    Does not create measurements - just returns comparison data.
    """
    # Verify page exists and get its project via document
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
            detail="Page must be calibrated before comparison",
        )

    # Verify condition exists
    condition_uuid = uuid.UUID(request.condition_id)
    result = await db.execute(select(Condition).where(Condition.id == condition_uuid))
    condition = result.scalar_one_or_none()
    
    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )

    # Verify page and condition belong to the same project
    if document.project_id != condition.project_id:
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

    task = compare_providers_task.delay(
        str(page_id),
        request.condition_id,
        providers=providers,
    )

    return TakeoffTaskResponse(
        task_id=task.id,
        message=f"Provider comparison started for page {page_id}",
    )


@router.post("/batch-ai-takeoff", response_model=BatchTakeoffResponse)
async def batch_ai_takeoff(
    request: BatchTakeoffRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BatchTakeoffResponse:
    """Generate AI takeoff for multiple pages.

    Queues individual tasks for each page.
    All pages must belong to the same project as the condition.
    """
    # Verify condition exists
    condition_uuid = uuid.UUID(request.condition_id)
    result = await db.execute(select(Condition).where(Condition.id == condition_uuid))
    condition = result.scalar_one_or_none()
    
    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )

    # Validate provider if specified
    if request.provider and request.provider not in settings.available_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{request.provider}' not available. "
            f"Available: {settings.available_providers}",
        )

    # Verify all pages exist and belong to the condition's project
    page_uuids = [uuid.UUID(pid) for pid in request.page_ids]
    result = await db.execute(
        select(Page, Document)
        .join(Document, Page.document_id == Document.id)
        .where(Page.id.in_(page_uuids))
    )
    rows = result.all()
    
    if len(rows) != len(page_uuids):
        found_ids = {str(row[0].id) for row in rows}
        missing = [pid for pid in request.page_ids if pid not in found_ids]
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

    # Queue batch task
    task = batch_ai_takeoff_task.delay(
        request.page_ids,
        request.condition_id,
        provider=request.provider,
    )

    return BatchTakeoffResponse(
        task_id=task.id,
        message=f"Batch AI takeoff queued for {len(request.page_ids)} pages",
        pages_count=len(request.page_ids),
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


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str) -> dict:
    """Get status of a Celery task.

    Returns the task state and result if complete.
    """
    from celery.result import AsyncResult
    from app.workers.celery_app import celery_app

    result = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "status": result.status,
    }

    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.result) if result.result else "Task failed"

    return response
