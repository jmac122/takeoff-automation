# Phase 3B: Condition Management
## Takeoff Line Items and Condition UI

> **Duration**: Weeks 14-18
> **Prerequisites**: Measurement engine working (Phase 3A)
> **Outcome**: Full condition management with templates and organization

---

## Current Implementation Status

> **Important:** Some components already exist from earlier phases. This guide focuses on **extending** existing code rather than creating from scratch.

### Backend - Already Implemented
| Component | Status | Notes |
|-----------|--------|-------|
| `models/condition.py` | ✅ Complete | Includes additional fields: `line_width`, `fill_opacity`, `extra_metadata` |
| `models/measurement.py` | ✅ Complete | Full geometry and AI tracking support |
| `schemas/condition.py` | ⚠️ Partial | Has `ConditionCreate`, `ConditionUpdate`, `ConditionResponse`, `ConditionListResponse` |
| `routes/conditions.py` | ⚠️ Partial | Has basic CRUD, missing templates/duplicate/reorder endpoints |
| `routes/measurements.py` | ✅ Complete | Full CRUD with recalculate support |

### Backend - Needs to be Added
- `GET /condition-templates` endpoint
- `POST /projects/{id}/conditions/from-template` endpoint
- `POST /conditions/{id}/duplicate` endpoint
- `PUT /projects/{id}/conditions/reorder` endpoint
- Query filters (`scope`, `category`) on list endpoint
- `ConditionWithMeasurementsResponse`, `ConditionTemplateResponse`, `MeasurementSummary` schemas

### Frontend - Already Implemented
| Component | Status | Notes |
|-----------|--------|-------|
| `viewer/ConditionsPanel.tsx` | ⚠️ Basic | Simple list display, needs upgrade to full-featured panel |
| `viewer/MeasurementsPanel.tsx` | ✅ Complete | - |

### Frontend - Needs to be Added
- Upgrade `ConditionsPanel.tsx` with grouping, drag-and-drop, context menus
- `CreateConditionModal.tsx`
- `EditConditionModal.tsx`
- `hooks/useConditions.ts`

---

## Context for LLM Assistant

You are implementing the condition management system for a construction takeoff platform. Conditions are "line items" that group related measurements:

- **Condition** = A takeoff item (e.g., "4" Concrete Slab", "Foundation Wall 12\"", "Concrete Piers")
- **Measurement** = Individual shapes drawn on pages, linked to a condition

### Condition Properties

| Property | Description | Example |
|----------|-------------|---------|
| **Name** | Descriptive name | "4\" Concrete Slab on Grade" |
| **Scope** | Work category | "Concrete", "Site Work" |
| **Category** | Sub-category | "Slabs", "Foundations", "Paving" |
| **Measurement Type** | How to measure | Linear, Area, Volume, Count |
| **Unit** | Output unit | LF, SF, CY, EA |
| **Depth/Thickness** | For volume calc | 4", 6", 8" |
| **Color** | Display color | #3B82F6 |

### Common Concrete Conditions

```
Foundations:
- Strip Footing 24"x12"
- Spread Footing 36"x36"x12"
- Foundation Wall 8"
- Grade Beam 12"x24"

Slabs:
- 4" SOG (Slab on Grade)
- 6" SOG Reinforced
- Concrete Paving 4"
- Sidewalk 4"

Vertical:
- Concrete Column 12"x12"
- Concrete Wall 8"
- CMU Wall 8" (concrete masonry)

Site:
- Curb & Gutter
- Concrete Paving
- Catch Basin (count)
```

---

## API Endpoints

### Task 7.1: Condition API Routes

> **Note:** Basic CRUD endpoints already exist in `backend/app/api/routes/conditions.py`.
> This task focuses on:
> - Adding the `CONDITION_TEMPLATES` list
> - Adding `scope` and `category` query filters to `list_project_conditions`
> - Adding new endpoints: `/condition-templates`, `/from-template`, `/duplicate`, `/reorder`
> - Updating `get_condition` to include measurements via `selectinload`

Extend `backend/app/api/routes/conditions.py`:

```python
"""Condition endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.condition import Condition
from app.models.measurement import Measurement
from app.models.project import Project
from app.schemas.condition import (
    ConditionCreate,
    ConditionUpdate,
    ConditionResponse,
    ConditionListResponse,
    ConditionWithMeasurementsResponse,
    ConditionTemplateResponse,
)

router = APIRouter()


# ============== Condition Templates ==============

CONDITION_TEMPLATES = [
    # Foundations
    {
        "name": "Strip Footing 24\"x12\"",
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
        "name": "Spread Footing 36\"x36\"x12\"",
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
        "name": "Foundation Wall 8\"",
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
        "name": "Grade Beam 12\"x24\"",
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
        "name": "4\" Concrete Slab on Grade",
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
        "name": "6\" Concrete Slab Reinforced",
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
        "name": "4\" Sidewalk",
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
        "name": "6\" Concrete Paving",
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
        "name": "Concrete Column 12\"x12\"",
        "scope": "concrete",
        "category": "vertical",
        "measurement_type": "count",
        "unit": "EA",
        "color": "#3B82F6",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    {
        "name": "8\" Concrete Wall",
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
        "category": "foundations",
        "measurement_type": "count",
        "unit": "EA",
        "color": "#8B5CF6",
        "line_width": 2,
        "fill_opacity": 0.3,
    },
    {
        "name": "Catch Basin",
        "scope": "site",
        "category": "drainage",
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


# ============== Project Conditions ==============

@router.get("/projects/{project_id}/conditions", response_model=ConditionListResponse)
async def list_project_conditions(
    project_id: uuid.UUID,
    scope: str | None = None,
    category: str | None = None,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all conditions for a project."""
    query = select(Condition).where(Condition.project_id == project_id)
    
    if scope:
        query = query.where(Condition.scope == scope)
    if category:
        query = query.where(Condition.category == category)
    
    query = query.order_by(Condition.sort_order, Condition.name)
    
    result = await db.execute(query)
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
    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Get max sort order
    result = await db.execute(
        select(func.max(Condition.sort_order))
        .where(Condition.project_id == project_id)
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
        unit=request.unit,
        depth=request.depth,
        thickness=request.thickness,
        sort_order=max_order + 1,
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
    template_name: str = Query(...),
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a condition from a template."""
    # Find template
    template = next(
        (t for t in CONDITION_TEMPLATES if t["name"] == template_name),
        None,
    )
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Get max sort order
    result = await db.execute(
        select(func.max(Condition.sort_order))
        .where(Condition.project_id == project_id)
    )
    max_order = result.scalar() or 0
    
    condition = Condition(
        project_id=project_id,
        name=template["name"],
        scope=template["scope"],
        category=template.get("category"),
        measurement_type=template["measurement_type"],
        color=template["color"],
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
    """Get condition details with measurements."""
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
    result = await db.execute(
        select(Condition).where(Condition.id == condition_id)
    )
    condition = result.scalar_one_or_none()
    
    if not condition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )
    
    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(condition, field, value)
    
    await db.commit()
    await db.refresh(condition)
    
    return ConditionResponse.model_validate(condition)


@router.delete("/conditions/{condition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_condition(
    condition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a condition and all its measurements."""
    result = await db.execute(
        select(Condition).where(Condition.id == condition_id)
    )
    condition = result.scalar_one_or_none()
    
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
    result = await db.execute(
        select(Condition).where(Condition.id == condition_id)
    )
    original = result.scalar_one_or_none()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found",
        )
    
    # Get max sort order
    result = await db.execute(
        select(func.max(Condition.sort_order))
        .where(Condition.project_id == original.project_id)
    )
    max_order = result.scalar() or 0
    
    duplicate = Condition(
        project_id=original.project_id,
        name=f"{original.name} (Copy)",
        description=original.description,
        scope=original.scope,
        category=original.category,
        measurement_type=original.measurement_type,
        color=original.color,
        unit=original.unit,
        depth=original.depth,
        thickness=original.thickness,
        sort_order=max_order + 1,
    )
    
    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)
    
    return ConditionResponse.model_validate(duplicate)


@router.post("/projects/{project_id}/conditions/reorder")
async def reorder_conditions(
    project_id: uuid.UUID,
    condition_ids: list[uuid.UUID],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reorder conditions by providing ordered list of IDs."""
    for i, cid in enumerate(condition_ids):
        await db.execute(
            select(Condition)
            .where(Condition.id == cid)
            .where(Condition.project_id == project_id)
        )
        result = await db.execute(
            select(Condition).where(Condition.id == cid)
        )
        condition = result.scalar_one_or_none()
        if condition:
            condition.sort_order = i
    
    await db.commit()
    
    return {"status": "success", "reordered_count": len(condition_ids)}
```

---

### Task 7.2: Condition Schemas

> **Note:** `ConditionCreate`, `ConditionUpdate`, `ConditionResponse`, and `ConditionListResponse` already exist in `backend/app/schemas/condition.py` with the additional fields (`line_width`, `fill_opacity`, `extra_metadata`).
> 
> This task focuses on adding the missing schemas:
> - `ConditionWithMeasurementsResponse`
> - `ConditionTemplateResponse`
> - `MeasurementSummary`

Extend `backend/app/schemas/condition.py` with the missing schemas:

```python
"""Condition schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConditionCreate(BaseModel):
    """Request to create a condition."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    scope: str = "concrete"
    category: str | None = None
    measurement_type: str = Field(..., pattern="^(linear|area|volume|count)$")
    color: str = "#3B82F6"
    line_width: int = 2          # Display line width
    fill_opacity: float = 0.3    # Display fill opacity
    unit: str = "SF"
    depth: float | None = None
    thickness: float | None = None
    sort_order: int = 0
    extra_metadata: dict[str, Any] | None = None


class ConditionUpdate(BaseModel):
    """Request to update a condition."""
    
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    scope: str | None = None
    category: str | None = None
    measurement_type: str | None = None
    color: str | None = None
    line_width: int | None = None
    fill_opacity: float | None = None
    unit: str | None = None
    depth: float | None = None
    thickness: float | None = None
    sort_order: int | None = None
    extra_metadata: dict[str, Any] | None = None


class ConditionResponse(BaseModel):
    """Condition response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None = None
    scope: str
    category: str | None = None
    measurement_type: str
    color: str
    line_width: int
    fill_opacity: float
    unit: str
    depth: float | None = None
    thickness: float | None = None
    total_quantity: float
    measurement_count: int
    sort_order: int
    extra_metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class ConditionListResponse(BaseModel):
    """Response for listing conditions."""
    
    conditions: list[ConditionResponse]
    total: int


# ============== ADD THESE MISSING SCHEMAS ==============

class MeasurementSummary(BaseModel):
    """Brief measurement info for condition details."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    page_id: uuid.UUID
    geometry_type: str
    quantity: float
    unit: str
    is_ai_generated: bool
    is_verified: bool


class ConditionWithMeasurementsResponse(ConditionResponse):
    """Condition with its measurements."""
    
    measurements: list[MeasurementSummary] = []


class ConditionTemplateResponse(BaseModel):
    """Condition template response."""
    
    name: str
    scope: str
    category: str | None = None
    measurement_type: str
    unit: str
    depth: float | None = None
    thickness: float | None = None
    color: str
    line_width: int = 2
    fill_opacity: float = 0.3
```

---

### Task 7.3: Frontend Condition Panel

> **Note:** A basic `ConditionsPanel.tsx` already exists at `frontend/src/components/viewer/ConditionsPanel.tsx`.
> It displays conditions with color swatches and totals but lacks:
> - Category grouping with expand/collapse
> - Drag-and-drop reordering
> - Context menu (edit, duplicate, delete)
> - "Add Condition" button
>
> This task **replaces** the existing basic panel with the full-featured version below.

Replace `frontend/src/components/viewer/ConditionsPanel.tsx`:

```tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  ChevronDown,
  ChevronRight,
  MoreVertical,
  Trash2,
  Copy,
  Edit,
  GripVertical,
} from 'lucide-react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { apiClient } from '@/api/client';
import type { Condition } from '@/types';
import { cn } from '@/lib/utils';

import { CreateConditionModal } from './CreateConditionModal';
import { EditConditionModal } from './EditConditionModal';

interface ConditionPanelProps {
  projectId: string;
  selectedConditionId: string | null;
  onConditionSelect: (id: string | null) => void;
}

export function ConditionPanel({
  projectId,
  selectedConditionId,
  onConditionSelect,
}: ConditionPanelProps) {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingCondition, setEditingCondition] = useState<Condition | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['foundations', 'slabs', 'paving', 'vertical'])
  );

  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['conditions', projectId],
    queryFn: async () => {
      const response = await apiClient.get<{ conditions: Condition[]; total: number }>(
        `/projects/${projectId}/conditions`
      );
      return response.data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (conditionId: string) => {
      await apiClient.delete(`/conditions/${conditionId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
      if (selectedConditionId) {
        onConditionSelect(null);
      }
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: async (conditionId: string) => {
      const response = await apiClient.post(`/conditions/${conditionId}/duplicate`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
    },
  });

  const reorderMutation = useMutation({
    mutationFn: async (conditionIds: string[]) => {
      await apiClient.post(`/projects/${projectId}/conditions/reorder`, conditionIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
    },
  });

  const conditions = data?.conditions || [];

  // Group conditions by category
  const groupedConditions = conditions.reduce((acc, condition) => {
    const category = condition.category || 'other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(condition);
    return acc;
  }, {} as Record<string, Condition[]>);

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: any) => {
    const { active, over } = event;

    if (active.id !== over.id) {
      const oldIndex = conditions.findIndex((c) => c.id === active.id);
      const newIndex = conditions.findIndex((c) => c.id === over.id);
      const newOrder = arrayMove(conditions, oldIndex, newIndex);
      reorderMutation.mutate(newOrder.map((c) => c.id));
    }
  };

  // Calculate totals
  const totalQuantityByUnit = conditions.reduce((acc, c) => {
    acc[c.unit] = (acc[c.unit] || 0) + c.total_quantity;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b">
        <h3 className="font-semibold">Conditions</h3>
        <Button size="sm" onClick={() => setIsCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-1" />
          Add
        </Button>
      </div>

      {/* Condition List */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="p-4 text-center text-muted-foreground">Loading...</div>
        ) : conditions.length === 0 ? (
          <div className="p-4 text-center text-muted-foreground">
            <p>No conditions yet.</p>
            <Button
              variant="link"
              size="sm"
              onClick={() => setIsCreateOpen(true)}
            >
              Add your first condition
            </Button>
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={conditions.map((c) => c.id)}
              strategy={verticalListSortingStrategy}
            >
              {Object.entries(groupedConditions).map(([category, items]) => (
                <Collapsible
                  key={category}
                  open={expandedCategories.has(category)}
                  onOpenChange={() => toggleCategory(category)}
                >
                  <CollapsibleTrigger className="flex items-center w-full p-2 hover:bg-muted text-sm font-medium capitalize">
                    {expandedCategories.has(category) ? (
                      <ChevronDown className="h-4 w-4 mr-1" />
                    ) : (
                      <ChevronRight className="h-4 w-4 mr-1" />
                    )}
                    {category}
                    <span className="ml-auto text-muted-foreground">
                      {items.length}
                    </span>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    {items.map((condition) => (
                      <SortableConditionItem
                        key={condition.id}
                        condition={condition}
                        isSelected={condition.id === selectedConditionId}
                        onSelect={() => onConditionSelect(condition.id)}
                        onEdit={() => setEditingCondition(condition)}
                        onDuplicate={() => duplicateMutation.mutate(condition.id)}
                        onDelete={() => deleteMutation.mutate(condition.id)}
                      />
                    ))}
                  </CollapsibleContent>
                </Collapsible>
              ))}
            </SortableContext>
          </DndContext>
        )}
      </div>

      {/* Totals */}
      {conditions.length > 0 && (
        <div className="border-t p-3 space-y-1">
          <h4 className="text-sm font-medium">Totals</h4>
          {Object.entries(totalQuantityByUnit).map(([unit, total]) => (
            <div key={unit} className="flex justify-between text-sm">
              <span className="text-muted-foreground">{unit}</span>
              <span className="font-mono">{total.toFixed(1)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Modals */}
      <CreateConditionModal
        projectId={projectId}
        open={isCreateOpen}
        onOpenChange={setIsCreateOpen}
      />

      {editingCondition && (
        <EditConditionModal
          condition={editingCondition}
          open={!!editingCondition}
          onOpenChange={(open) => !open && setEditingCondition(null)}
        />
      )}
    </div>
  );
}

// Sortable condition item component
function SortableConditionItem({
  condition,
  isSelected,
  onSelect,
  onEdit,
  onDuplicate,
  onDelete,
}: {
  condition: Condition;
  isSelected: boolean;
  onSelect: () => void;
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id: condition.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'flex items-center gap-2 px-2 py-1.5 ml-4 mr-2 rounded cursor-pointer',
        isSelected ? 'bg-primary/10' : 'hover:bg-muted'
      )}
      onClick={onSelect}
    >
      <button
        className="cursor-grab hover:bg-muted-foreground/20 rounded p-0.5"
        {...attributes}
        {...listeners}
      >
        <GripVertical className="h-3 w-3 text-muted-foreground" />
      </button>

      <div
        className="w-3 h-3 rounded-sm flex-shrink-0"
        style={{ backgroundColor: condition.color }}
      />

      <div className="flex-1 min-w-0">
        <div className="text-sm truncate">{condition.name}</div>
        <div className="text-xs text-muted-foreground">
          {condition.total_quantity.toFixed(1)} {condition.unit}
          {condition.measurement_count > 0 && (
            <span className="ml-1">({condition.measurement_count})</span>
          )}
        </div>
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="icon" className="h-6 w-6">
            <MoreVertical className="h-3 w-3" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={onEdit}>
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </DropdownMenuItem>
          <DropdownMenuItem onClick={onDuplicate}>
            <Copy className="h-4 w-4 mr-2" />
            Duplicate
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={onDelete}
            className="text-destructive"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
```

---

### Task 7.4: Create Condition Modal

Create `frontend/src/components/viewer/CreateConditionModal.tsx`:

```tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { apiClient } from '@/api/client';

interface CreateConditionModalProps {
  projectId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ConditionTemplate {
  name: string;
  scope: string;
  category: string | null;
  measurement_type: string;
  unit: string;
  depth: number | null;
  thickness: number | null;
  color: string;
  line_width: number;
  fill_opacity: number;
}

const COLORS = [
  '#EF4444', '#F97316', '#F59E0B', '#EAB308',
  '#22C55E', '#10B981', '#14B8A6', '#06B6D4',
  '#0EA5E9', '#3B82F6', '#6366F1', '#8B5CF6',
  '#A855F7', '#D946EF', '#EC4899', '#F43F5E',
];

const MEASUREMENT_TYPES = [
  { value: 'linear', label: 'Linear (LF)', unit: 'LF' },
  { value: 'area', label: 'Area (SF)', unit: 'SF' },
  { value: 'volume', label: 'Volume (CY)', unit: 'CY' },
  { value: 'count', label: 'Count (EA)', unit: 'EA' },
];

export function CreateConditionModal({
  projectId,
  open,
  onOpenChange,
}: CreateConditionModalProps) {
  const [tab, setTab] = useState<'template' | 'custom'>('template');
  const [name, setName] = useState('');
  const [measurementType, setMeasurementType] = useState('area');
  const [depth, setDepth] = useState('');
  const [color, setColor] = useState(COLORS[0]);

  const queryClient = useQueryClient();

  const { data: templates } = useQuery({
    queryKey: ['condition-templates'],
    queryFn: async () => {
      const response = await apiClient.get<ConditionTemplate[]>('/condition-templates');
      return response.data;
    },
  });

  const createFromTemplateMutation = useMutation({
    mutationFn: async (templateName: string) => {
      const response = await apiClient.post(
        `/projects/${projectId}/conditions/from-template?template_name=${encodeURIComponent(templateName)}`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
      onOpenChange(false);
    },
  });

  const createCustomMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiClient.post(
        `/projects/${projectId}/conditions`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conditions', projectId] });
      onOpenChange(false);
      resetForm();
    },
  });

  const resetForm = () => {
    setName('');
    setMeasurementType('area');
    setDepth('');
    setColor(COLORS[0]);
  };

  const handleCreateCustom = () => {
    const mt = MEASUREMENT_TYPES.find((t) => t.value === measurementType);
    createCustomMutation.mutate({
      name,
      measurement_type: measurementType,
      unit: mt?.unit || 'SF',
      depth: depth ? parseFloat(depth) : null,
      color,
      scope: 'concrete',
    });
  };

  // Group templates by category
  const groupedTemplates = (templates || []).reduce((acc, t) => {
    const category = t.category || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(t);
    return acc;
  }, {} as Record<string, ConditionTemplate[]>);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Add Condition</DialogTitle>
        </DialogHeader>

        <Tabs value={tab} onValueChange={(v) => setTab(v as any)}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="template">From Template</TabsTrigger>
            <TabsTrigger value="custom">Custom</TabsTrigger>
          </TabsList>

          <TabsContent value="template" className="space-y-4 mt-4">
            <div className="max-h-80 overflow-auto space-y-4">
              {Object.entries(groupedTemplates).map(([category, items]) => (
                <div key={category}>
                  <h4 className="text-sm font-medium capitalize mb-2">
                    {category}
                  </h4>
                  <div className="space-y-1">
                    {items.map((template) => (
                      <button
                        key={template.name}
                        onClick={() => createFromTemplateMutation.mutate(template.name)}
                        disabled={createFromTemplateMutation.isPending}
                        className="w-full flex items-center gap-3 p-2 rounded hover:bg-muted text-left"
                      >
                        <div
                          className="w-4 h-4 rounded"
                          style={{ backgroundColor: template.color }}
                        />
                        <div className="flex-1">
                          <div className="text-sm">{template.name}</div>
                          <div className="text-xs text-muted-foreground">
                            {template.measurement_type} • {template.unit}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="custom" className="space-y-4 mt-4">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., 4&quot; Concrete Slab"
              />
            </div>

            <div>
              <Label htmlFor="type">Measurement Type</Label>
              <Select value={measurementType} onValueChange={setMeasurementType}>
                <SelectTrigger id="type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MEASUREMENT_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {(measurementType === 'area' || measurementType === 'volume') && (
              <div>
                <Label htmlFor="depth">Depth/Thickness (inches)</Label>
                <Input
                  id="depth"
                  type="number"
                  value={depth}
                  onChange={(e) => setDepth(e.target.value)}
                  placeholder="e.g., 4"
                />
              </div>
            )}

            <div>
              <Label>Color</Label>
              <div className="flex flex-wrap gap-2 mt-2">
                {COLORS.map((c) => (
                  <button
                    key={c}
                    onClick={() => setColor(c)}
                    className={cn(
                      'w-6 h-6 rounded border-2',
                      color === c ? 'border-foreground' : 'border-transparent'
                    )}
                    style={{ backgroundColor: c }}
                  />
                ))}
              </div>
            </div>

            <Button
              onClick={handleCreateCustom}
              disabled={!name || createCustomMutation.isPending}
              className="w-full"
            >
              {createCustomMutation.isPending ? 'Creating...' : 'Create Condition'}
            </Button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] Can create conditions from templates
- [ ] Can create custom conditions
- [ ] Condition list shows grouped by category
- [ ] Conditions can be selected (highlights in panel)
- [ ] Conditions can be edited
- [ ] Conditions can be duplicated
- [ ] Conditions can be deleted (with measurements)
- [ ] Conditions can be reordered via drag-and-drop
- [ ] Condition totals update when measurements change
- [ ] Project-level totals display correctly
- [ ] Color picker works
- [ ] Depth/thickness stored correctly

### Test Cases

1. Create condition from "4\" Concrete Slab" template → appears in list
2. Create custom linear condition → correct unit (LF) assigned
3. Add measurements to condition → total updates
4. Delete condition with measurements → both removed
5. Drag condition to reorder → new order persists

---
## Next Phase

Once verified, proceed to **`13-ASSEMBLY-SYSTEM.md`** for implementing the assembly and cost estimation system.

The Assembly System extends conditions with:
- **Component Breakdown**: Material, labor, equipment, and subcontract components
- **Formula Engine**: Calculate quantities dynamically (e.g., `{quantity} * 1.1` for 10% waste)
- **Cost Database**: Unit costs for materials and labor rates
- **Assembly Templates**: Pre-built assemblies for common concrete work (slabs, footings, walls)
- **Markup & Pricing**: Apply overhead, profit, and contingency percentages

This creates a complete estimating workflow where conditions track what you're measuring and assemblies track what it costs.

After Assembly System, continue to **`08-AI-TAKEOFF-GENERATION.md`** for AI-assisted automatic measurement detection.
