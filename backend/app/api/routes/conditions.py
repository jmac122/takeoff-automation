"""Condition (takeoff line item) endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.condition import Condition
from app.models.project import Project
from app.schemas.condition import (
    ConditionCreate,
    ConditionUpdate,
    ConditionResponse,
    ConditionListResponse,
)

router = APIRouter()


@router.get("/projects/{project_id}/conditions", response_model=ConditionListResponse)
async def list_project_conditions(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all conditions for a project."""
    result = await db.execute(
        select(Condition)
        .where(Condition.project_id == project_id)
        .order_by(Condition.sort_order, Condition.created_at)
    )
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
        sort_order=request.sort_order,
        extra_metadata=request.extra_metadata,
    )
    
    db.add(condition)
    await db.commit()
    await db.refresh(condition)
    
    return ConditionResponse.model_validate(condition)


@router.get("/conditions/{condition_id}", response_model=ConditionResponse)
async def get_condition(
    condition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get condition details."""
    condition = await db.get(Condition, condition_id)
    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )
    
    return ConditionResponse.model_validate(condition)


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
