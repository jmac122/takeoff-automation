"""Assembly endpoints for cost estimation and management."""

import uuid
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.assembly import (
    AssemblyCreate,
    AssemblyDetailResponse,
    AssemblyTemplateResponse,
    AssemblyUpdate,
    ComponentCreate,
    ComponentResponse,
    ComponentUpdate,
    FormulaValidateRequest,
    FormulaValidateResponse,
    ProjectCostSummaryResponse,
)
from app.services.assembly_service import get_assembly_service
from app.services.formula_engine import (
    FORMULA_PRESETS,
    FormulaContext,
    get_formula_engine,
)

router = APIRouter()
logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Assembly Templates
# ---------------------------------------------------------------------------


@router.get(
    "/assembly-templates",
    response_model=list[AssemblyTemplateResponse],
)
async def list_assembly_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    scope: str | None = Query(default=None),
    category: str | None = Query(default=None),
    measurement_type: str | None = Query(default=None),
):
    """List assembly templates, optionally filtered."""
    from sqlalchemy import select

    from app.models.assembly import AssemblyTemplate

    query = select(AssemblyTemplate).where(AssemblyTemplate.is_active.is_(True))

    if scope:
        query = query.where(AssemblyTemplate.scope == scope)
    if category:
        query = query.where(AssemblyTemplate.category == category)
    if measurement_type:
        query = query.where(AssemblyTemplate.measurement_type == measurement_type)

    query = query.order_by(AssemblyTemplate.category, AssemblyTemplate.name)
    result = await db.execute(query)
    templates = result.scalars().all()
    return [AssemblyTemplateResponse.model_validate(t) for t in templates]


@router.get(
    "/assembly-templates/{template_id}",
    response_model=AssemblyTemplateResponse,
)
async def get_assembly_template(
    template_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a single assembly template by ID."""
    from sqlalchemy import select

    from app.models.assembly import AssemblyTemplate

    result = await db.execute(
        select(AssemblyTemplate).where(AssemblyTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )
    return AssemblyTemplateResponse.model_validate(template)


# ---------------------------------------------------------------------------
# Assembly CRUD
# ---------------------------------------------------------------------------


@router.post(
    "/conditions/{condition_id}/assembly",
    response_model=AssemblyDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assembly(
    condition_id: uuid.UUID,
    request: AssemblyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create an assembly for a condition."""
    service = get_assembly_service()

    try:
        assembly = await service.create_assembly_for_condition(
            session=db,
            condition_id=condition_id,
            name=request.name,
            template_id=request.template_id,
            description=request.description,
        )
        return AssemblyDetailResponse.model_validate(assembly)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/conditions/{condition_id}/assembly",
    response_model=AssemblyDetailResponse | None,
)
async def get_condition_assembly(
    condition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the assembly for a condition, or null if none exists."""
    service = get_assembly_service()
    assembly = await service.get_condition_assembly(
        session=db,
        condition_id=condition_id,
    )
    if assembly is None:
        return None
    return AssemblyDetailResponse.model_validate(assembly)


@router.get(
    "/assemblies/{assembly_id}",
    response_model=AssemblyDetailResponse,
)
async def get_assembly(
    assembly_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get an assembly by ID with all components."""
    service = get_assembly_service()

    try:
        assembly = await service.get_assembly(
            session=db,
            assembly_id=assembly_id,
        )
        return AssemblyDetailResponse.model_validate(assembly)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put(
    "/assemblies/{assembly_id}",
    response_model=AssemblyDetailResponse,
)
async def update_assembly(
    assembly_id: uuid.UUID,
    request: AssemblyUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an assembly."""
    service = get_assembly_service()

    try:
        assembly = await service.update_assembly(
            session=db,
            assembly_id=assembly_id,
            **request.model_dump(exclude_unset=True),
        )
        return AssemblyDetailResponse.model_validate(assembly)
    except ValueError as e:
        detail = str(e)
        code = status.HTTP_400_BAD_REQUEST
        if "not found" in detail.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=detail)


@router.delete(
    "/assemblies/{assembly_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_assembly(
    assembly_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an assembly."""
    service = get_assembly_service()

    try:
        await service.delete_assembly(session=db, assembly_id=assembly_id)
    except ValueError as e:
        detail = str(e)
        code = status.HTTP_400_BAD_REQUEST
        if "not found" in detail.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=detail)


# ---------------------------------------------------------------------------
# Assembly actions
# ---------------------------------------------------------------------------


@router.post(
    "/assemblies/{assembly_id}/calculate",
    response_model=AssemblyDetailResponse,
)
async def calculate_assembly(
    assembly_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Recalculate all component quantities and costs."""
    service = get_assembly_service()

    try:
        assembly = await service.calculate_assembly(
            session=db,
            assembly_id=assembly_id,
        )
        return AssemblyDetailResponse.model_validate(assembly)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/assemblies/{assembly_id}/lock",
    response_model=AssemblyDetailResponse,
)
async def lock_assembly(
    assembly_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    locked_by: str = Query(default="system"),
):
    """Lock an assembly to prevent modifications."""
    service = get_assembly_service()

    try:
        assembly = await service.lock_assembly(
            session=db,
            assembly_id=assembly_id,
            locked_by=locked_by,
        )
        return AssemblyDetailResponse.model_validate(assembly)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/assemblies/{assembly_id}/unlock",
    response_model=AssemblyDetailResponse,
)
async def unlock_assembly(
    assembly_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Unlock an assembly."""
    service = get_assembly_service()

    try:
        assembly = await service.unlock_assembly(
            session=db,
            assembly_id=assembly_id,
        )
        return AssemblyDetailResponse.model_validate(assembly)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ---------------------------------------------------------------------------
# Component CRUD
# ---------------------------------------------------------------------------


@router.post(
    "/assemblies/{assembly_id}/components",
    response_model=ComponentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_component(
    assembly_id: uuid.UUID,
    request: ComponentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add a component to an assembly."""
    service = get_assembly_service()

    try:
        component = await service.add_component(
            session=db,
            assembly_id=assembly_id,
            **request.model_dump(),
        )
        return ComponentResponse.model_validate(component)
    except ValueError as e:
        detail = str(e)
        code = status.HTTP_400_BAD_REQUEST
        if "not found" in detail.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=detail)


@router.put(
    "/components/{component_id}",
    response_model=ComponentResponse,
)
async def update_component(
    component_id: uuid.UUID,
    request: ComponentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a component."""
    service = get_assembly_service()

    try:
        component = await service.update_component(
            session=db,
            component_id=component_id,
            **request.model_dump(exclude_unset=True),
        )
        return ComponentResponse.model_validate(component)
    except ValueError as e:
        detail = str(e)
        code = status.HTTP_400_BAD_REQUEST
        if "not found" in detail.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=detail)


@router.delete(
    "/components/{component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_component(
    component_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a component."""
    service = get_assembly_service()

    try:
        await service.delete_component(session=db, component_id=component_id)
    except ValueError as e:
        detail = str(e)
        code = status.HTTP_400_BAD_REQUEST
        if "not found" in detail.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=detail)


@router.put(
    "/assemblies/{assembly_id}/components/reorder",
    status_code=status.HTTP_200_OK,
)
async def reorder_components(
    assembly_id: uuid.UUID,
    component_ids: list[uuid.UUID],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reorder components by the provided ID list."""
    service = get_assembly_service()

    try:
        await service.reorder_components(
            session=db,
            assembly_id=assembly_id,
            component_ids=component_ids,
        )
        return {"status": "ok"}
    except ValueError as e:
        detail = str(e)
        code = status.HTTP_400_BAD_REQUEST
        if "not found" in detail.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=detail)


# ---------------------------------------------------------------------------
# Formula utilities
# ---------------------------------------------------------------------------


@router.post(
    "/formulas/validate",
    response_model=FormulaValidateResponse,
)
async def validate_formula(request: FormulaValidateRequest):
    """Validate a formula and optionally test it with sample values."""
    engine = get_formula_engine()

    is_valid, error = engine.validate_formula(request.formula)
    if not is_valid:
        return FormulaValidateResponse(is_valid=False, error=error)

    # If test values provided, evaluate the formula
    test_result: float | None = None
    if request.test_qty is not None:
        context = FormulaContext(
            qty=request.test_qty,
            depth=request.test_depth or 0.0,
            thickness=request.test_thickness or 0.0,
            perimeter=request.test_perimeter or 0.0,
            count=request.test_count or 0,
        )
        try:
            test_result = engine.evaluate(request.formula, context)
        except ValueError as e:
            return FormulaValidateResponse(is_valid=False, error=str(e))

    return FormulaValidateResponse(is_valid=True, test_result=test_result)


@router.get("/formulas/presets")
async def get_formula_presets() -> dict[str, Any]:
    """List available formula presets."""
    return FORMULA_PRESETS


@router.get("/formulas/help")
async def get_formula_help() -> dict[str, Any]:
    """Get formula documentation including variables, functions, and examples."""
    engine = get_formula_engine()
    return engine.get_formula_help()


# ---------------------------------------------------------------------------
# Project cost summary
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/cost-summary",
    response_model=ProjectCostSummaryResponse,
)
async def get_project_cost_summary(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get aggregated cost summary across all assemblies in a project."""
    service = get_assembly_service()

    summary = await service.get_project_cost_summary(
        session=db,
        project_id=project_id,
    )
    return ProjectCostSummaryResponse(**summary)
