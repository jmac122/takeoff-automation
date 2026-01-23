"""Condition (takeoff line item) endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.condition import Condition
from app.models.project import Project
from app.schemas.condition import (
    ConditionCreate,
    ConditionUpdate,
    ConditionResponse,
    ConditionListResponse,
    ConditionTemplateResponse,
    ConditionWithMeasurementsResponse,
)

router = APIRouter()

# ============== Condition Templates ==============

CONDITION_TEMPLATES = [
    # Foundations
    {
        "name": "Strip Footing",
        "scope": "concrete",
        "category": "foundations",
        "measurement_type": "linear",
        "unit": "LF",
        "depth": 12,
        "color": "#EF4444",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    {
        "name": "Spread Footing",
        "scope": "concrete",
        "category": "foundations",
        "measurement_type": "count",
        "unit": "EA",
        "depth": 12,
        "color": "#F97316",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    {
        "name": "Foundation Wall",
        "scope": "concrete",
        "category": "foundations",
        "measurement_type": "area",
        "unit": "SF",
        "thickness": 8,
        "color": "#F59E0B",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    {
        "name": "Grade Beam",
        "scope": "concrete",
        "category": "foundations",
        "measurement_type": "linear",
        "unit": "LF",
        "depth": 24,
        "color": "#EAB308",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    # Slabs
    {
        "name": '4" SOG',
        "scope": "concrete",
        "category": "slabs",
        "measurement_type": "area",
        "unit": "SF",
        "depth": 4,
        "color": "#22C55E",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    {
        "name": '6" SOG Reinforced',
        "scope": "concrete",
        "category": "slabs",
        "measurement_type": "area",
        "unit": "SF",
        "depth": 6,
        "color": "#10B981",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    {
        "name": '4" Sidewalk',
        "scope": "concrete",
        "category": "slabs",
        "measurement_type": "area",
        "unit": "SF",
        "depth": 4,
        "color": "#14B8A6",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    # Paving
    {
        "name": '6" Concrete Paving',
        "scope": "concrete",
        "category": "paving",
        "measurement_type": "area",
        "unit": "SF",
        "depth": 6,
        "color": "#06B6D4",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    {
        "name": "Curb & Gutter",
        "scope": "concrete",
        "category": "paving",
        "measurement_type": "linear",
        "unit": "LF",
        "color": "#0EA5E9",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    # Vertical
    {
        "name": "Concrete Column",
        "scope": "concrete",
        "category": "vertical",
        "measurement_type": "count",
        "unit": "EA",
        "color": "#3B82F6",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    {
        "name": '8" Concrete Wall',
        "scope": "concrete",
        "category": "vertical",
        "measurement_type": "area",
        "unit": "SF",
        "thickness": 8,
        "color": "#6366F1",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    # Miscellaneous
    {
        "name": "Concrete Pier",
        "scope": "concrete",
        "category": "miscellaneous",
        "measurement_type": "count",
        "unit": "EA",
        "color": "#8B5CF6",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    {
        "name": "Catch Basin",
        "scope": "concrete",
        "category": "miscellaneous",
        "measurement_type": "count",
        "unit": "EA",
        "color": "#A855F7",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
]


@router.get("/condition-templates", response_model=list[ConditionTemplateResponse])
async def list_condition_templates(
    scope: str | None = None,
    category: str | None = None,
):
    """List available condition templates."""
    templates = CONDITION_TEMPLATES

    if scope:
        templates = [t for t in templates if t["scope"] == scope]
    if category:
        templates = [t for t in templates if t.get("category") == category]

    return templates


@router.get("/projects/{project_id}/conditions", response_model=ConditionListResponse)
async def list_project_conditions(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    scope: str | None = Query(None),
    category: str | None = Query(None),
):
    """List all conditions for a project."""
    query = select(Condition).where(Condition.project_id == project_id)

    if scope:
        query = query.where(Condition.scope == scope)
    if category:
        query = query.where(Condition.category == category)

    result = await db.execute(query.order_by(Condition.sort_order, Condition.name))
    conditions = result.scalars().all()
    
    return ConditionListResponse(
        conditions=[ConditionResponse.model_validate(c) for c in conditions],
        total=len(conditions),
    )


@router.post(
    "/projects/{project_id}/conditions",
    response_model=ConditionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_condition(
    project_id: uuid.UUID,
    request: ConditionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new condition."""
    # Verify project exists
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    result = await db.execute(
        select(func.max(Condition.sort_order)).where(Condition.project_id == project_id)
    )
    max_order = result.scalar() or 0

    condition = Condition(
        project_id=project_id,
        name=request.name,
        description=request.description,
        scope=request.scope,
        category=request.category,
        measurement_type=request.measurement_type,
        color=request.color,
        line_width=request.line_width,
        fill_opacity=request.fill_opacity,
        unit=request.unit,
        depth=request.depth,
        thickness=request.thickness,
        sort_order=max_order + 1,
        extra_metadata=request.extra_metadata,
    )
    
    db.add(condition)
    await db.commit()
    await db.refresh(condition)
    
    return ConditionResponse.model_validate(condition)


@router.post(
    "/projects/{project_id}/conditions/from-template",
    response_model=ConditionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_condition_from_template(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    template_name: str = Query(...),
):
    """Create a condition from a template."""
    template = next((t for t in CONDITION_TEMPLATES if t["name"] == template_name), None)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    result = await db.execute(
        select(func.max(Condition.sort_order)).where(Condition.project_id == project_id)
    )
    max_order = result.scalar() or 0

    condition = Condition(
        project_id=project_id,
        name=template["name"],
        scope=template["scope"],
        category=template.get("category"),
        measurement_type=template["measurement_type"],
        color=template["color"],
        line_width=template.get("line_width", 2),
        fill_opacity=template.get("fill_opacity", 0.3),
        unit=template["unit"],
        depth=template.get("depth"),
        thickness=template.get("thickness"),
        sort_order=max_order + 1,
    )

    db.add(condition)
    await db.commit()
    await db.refresh(condition)

    return ConditionResponse.model_validate(condition)


@router.get("/conditions/{condition_id}", response_model=ConditionWithMeasurementsResponse)
async def get_condition(
    condition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get condition details."""
    result = await db.execute(
        select(Condition)
        .options(selectinload(Condition.measurements))
        .where(Condition.id == condition_id)
    )
    condition = result.scalar_one_or_none()
    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )
    
    return ConditionWithMeasurementsResponse.model_validate(condition)


@router.put("/conditions/{condition_id}", response_model=ConditionResponse)
async def update_condition(
    condition_id: uuid.UUID,
    request: ConditionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a condition."""
    condition = await db.get(Condition, condition_id)
    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )
    
    # Update fields if provided
    if request.name is not None:
        condition.name = request.name
    if request.description is not None:
        condition.description = request.description
    if request.scope is not None:
        condition.scope = request.scope
    if request.category is not None:
        condition.category = request.category
    if request.measurement_type is not None:
        condition.measurement_type = request.measurement_type
    if request.color is not None:
        condition.color = request.color
    if request.line_width is not None:
        condition.line_width = request.line_width
    if request.fill_opacity is not None:
        condition.fill_opacity = request.fill_opacity
    if request.unit is not None:
        condition.unit = request.unit
    if request.depth is not None:
        condition.depth = request.depth
    if request.thickness is not None:
        condition.thickness = request.thickness
    if request.sort_order is not None:
        condition.sort_order = request.sort_order
    if request.extra_metadata is not None:
        condition.extra_metadata = request.extra_metadata
    
    await db.commit()
    await db.refresh(condition)
    
    return ConditionResponse.model_validate(condition)


@router.delete("/conditions/{condition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_condition(
    condition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a condition and all its measurements."""
    condition = await db.get(Condition, condition_id)
    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )
    
    await db.delete(condition)
    await db.commit()


@router.post("/conditions/{condition_id}/duplicate", response_model=ConditionResponse)
async def duplicate_condition(
    condition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Duplicate a condition (without measurements)."""
    condition = await db.get(Condition, condition_id)
    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )

    result = await db.execute(
        select(func.max(Condition.sort_order)).where(Condition.project_id == condition.project_id)
    )
    max_order = result.scalar() or 0

    duplicate = Condition(
        project_id=condition.project_id,
        name=f"{condition.name} (Copy)",
        description=condition.description,
        scope=condition.scope,
        category=condition.category,
        measurement_type=condition.measurement_type,
        color=condition.color,
        line_width=condition.line_width,
        fill_opacity=condition.fill_opacity,
        unit=condition.unit,
        depth=condition.depth,
        thickness=condition.thickness,
        sort_order=max_order + 1,
        extra_metadata=condition.extra_metadata,
    )

    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)

    return ConditionResponse.model_validate(duplicate)


@router.put("/projects/{project_id}/conditions/reorder")
async def reorder_conditions(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    condition_ids: list[uuid.UUID] = Body(...),
):
    """Reorder conditions by providing ordered list of IDs."""
    if not condition_ids:
        return {"status": "success", "reordered_count": 0}

    result = await db.execute(
        select(Condition).where(
            Condition.project_id == project_id,
            Condition.id.in_(condition_ids),
        )
    )
    conditions = result.scalars().all()
    condition_map = {c.id: c for c in conditions}

    missing = [cid for cid in condition_ids if cid not in condition_map]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more conditions not found for project",
        )

    for index, condition_id in enumerate(condition_ids):
        condition_map[condition_id].sort_order = index

    await db.commit()

    return {"status": "success", "reordered_count": len(condition_ids)}
