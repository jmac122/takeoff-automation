"""Pydantic schemas for the assembly system."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Component schemas
# ---------------------------------------------------------------------------


class ComponentCreate(BaseModel):
    """Schema for creating an assembly component."""

    name: str
    description: str | None = None
    component_type: str = Field(
        default="material",
        pattern=r"^(material|labor|equipment|subcontract|other)$",
    )
    quantity_formula: str = Field(default="{qty}", max_length=500)
    unit: str
    unit_cost: Decimal = Decimal("0")
    waste_percent: float = Field(default=0, ge=0, le=100)
    cost_item_id: uuid.UUID | None = None
    sort_order: int = 0
    labor_hours: float | None = None
    labor_rate: Decimal | None = None
    crew_size: int | None = None
    duration_hours: float | None = None
    hourly_rate: Decimal | None = None
    daily_rate: Decimal | None = None
    is_included: bool = True
    is_optional: bool = False
    notes: str | None = None


class ComponentUpdate(BaseModel):
    """Schema for updating an assembly component."""

    name: str | None = None
    description: str | None = None
    component_type: str | None = None
    quantity_formula: str | None = None
    unit: str | None = None
    unit_cost: Decimal | None = None
    waste_percent: float | None = None
    cost_item_id: uuid.UUID | None = None
    sort_order: int | None = None
    labor_hours: float | None = None
    labor_rate: Decimal | None = None
    crew_size: int | None = None
    duration_hours: float | None = None
    hourly_rate: Decimal | None = None
    daily_rate: Decimal | None = None
    is_included: bool | None = None
    is_optional: bool | None = None
    notes: str | None = None


class ComponentResponse(BaseModel):
    """Schema for an assembly component response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assembly_id: uuid.UUID
    cost_item_id: uuid.UUID | None
    name: str
    description: str | None
    component_type: str
    sort_order: int
    quantity_formula: str
    calculated_quantity: float
    unit: str
    unit_cost: Decimal
    waste_percent: float
    quantity_with_waste: float
    extended_cost: Decimal
    labor_hours: float | None
    labor_rate: Decimal | None
    crew_size: int | None
    duration_hours: float | None
    hourly_rate: Decimal | None
    daily_rate: Decimal | None
    is_included: bool
    is_optional: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Assembly schemas
# ---------------------------------------------------------------------------


class AssemblyCreate(BaseModel):
    """Schema for creating an assembly."""

    name: str | None = None
    template_id: uuid.UUID | None = None
    description: str | None = None


class AssemblyUpdate(BaseModel):
    """Schema for updating an assembly."""

    name: str | None = None
    description: str | None = None
    csi_code: str | None = None
    csi_description: str | None = None
    default_waste_percent: float | None = None
    overhead_percent: float | None = None
    profit_percent: float | None = None
    productivity_rate: float | None = None
    productivity_unit: str | None = None
    crew_size: int | None = None
    notes: str | None = None


class AssemblyResponse(BaseModel):
    """Schema for an assembly response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    condition_id: uuid.UUID
    template_id: uuid.UUID | None
    name: str
    description: str | None
    csi_code: str | None
    csi_description: str | None
    default_waste_percent: float
    productivity_rate: float | None
    productivity_unit: str | None
    crew_size: int | None
    material_cost: Decimal
    labor_cost: Decimal
    equipment_cost: Decimal
    subcontract_cost: Decimal
    other_cost: Decimal
    total_cost: Decimal
    unit_cost: Decimal
    total_labor_hours: float
    overhead_percent: float
    profit_percent: float
    total_with_markup: Decimal
    is_locked: bool
    locked_at: datetime | None
    locked_by: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AssemblyDetailResponse(AssemblyResponse):
    """Assembly response with nested components."""

    components: list[ComponentResponse] = []


# ---------------------------------------------------------------------------
# Template schemas
# ---------------------------------------------------------------------------


class AssemblyTemplateResponse(BaseModel):
    """Schema for an assembly template response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    scope: str
    category: str | None
    subcategory: str | None
    csi_code: str | None
    csi_description: str | None
    measurement_type: str
    expected_unit: str
    default_waste_percent: float
    productivity_rate: float | None
    productivity_unit: str | None
    crew_size: int | None
    is_system: bool
    is_active: bool
    version: int
    component_definitions: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Formula schemas
# ---------------------------------------------------------------------------


class FormulaValidateRequest(BaseModel):
    """Schema for formula validation request."""

    formula: str
    test_qty: float | None = None
    test_depth: float | None = None
    test_thickness: float | None = None
    test_perimeter: float | None = None
    test_count: int | None = None


class FormulaValidateResponse(BaseModel):
    """Schema for formula validation response."""

    is_valid: bool
    error: str | None = None
    test_result: float | None = None


# ---------------------------------------------------------------------------
# Project cost summary
# ---------------------------------------------------------------------------


class ProjectCostSummaryResponse(BaseModel):
    """Schema for aggregated project cost summary."""

    project_id: uuid.UUID
    total_conditions: int
    conditions_with_assemblies: int
    material_cost: Decimal
    labor_cost: Decimal
    equipment_cost: Decimal
    subcontract_cost: Decimal
    other_cost: Decimal
    total_cost: Decimal
    total_with_markup: Decimal
