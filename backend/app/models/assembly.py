"""Assembly system models for cost estimation."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.condition import Condition


class AssemblyTemplate(Base, UUIDMixin, TimestampMixin):
    """Reusable assembly template with component definitions."""

    __tablename__ = "assembly_templates"

    # Template info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    scope: Mapped[str] = mapped_column(String(100), default="concrete")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # CSI MasterFormat
    csi_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    csi_description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Configuration
    measurement_type: Mapped[str] = mapped_column(String(50), default="area")
    expected_unit: Mapped[str] = mapped_column(String(50), default="SF")
    default_waste_percent: Mapped[float] = mapped_column(Float, default=5.0)
    productivity_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    productivity_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    crew_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Flags
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Content
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    component_definitions: Mapped[list] = mapped_column(JSONB, default=list)

    # Relationships
    instances: Mapped[list["Assembly"]] = relationship(
        "Assembly", back_populates="template"
    )


class CostItem(Base, UUIDMixin, TimestampMixin):
    """Master cost database item."""

    __tablename__ = "cost_items"

    # Identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    item_type: Mapped[str] = mapped_column(
        String(50), default="material"
    )  # material, labor, equipment, etc.
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Primary unit & cost
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)

    # Alternative unit
    alt_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    alt_unit_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True
    )
    conversion_factor: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Labor rates
    labor_rate_regular: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    labor_rate_overtime: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    burden_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Equipment rates
    hourly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    daily_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    weekly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    monthly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    # Vendor
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Validity
    effective_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expiration_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class Assembly(Base, UUIDMixin, TimestampMixin):
    """Cost assembly attached to a condition (one-to-one)."""

    __tablename__ = "assemblies"

    # Foreign keys
    condition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conditions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assembly_templates.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Assembly info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # CSI MasterFormat
    csi_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    csi_description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Configuration
    default_waste_percent: Mapped[float] = mapped_column(Float, default=5.0)
    productivity_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    productivity_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    crew_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Calculated cost totals
    material_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    labor_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    equipment_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    subcontract_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    other_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)

    # Labor
    total_labor_hours: Mapped[float] = mapped_column(Float, default=0)

    # Markup
    overhead_percent: Mapped[float] = mapped_column(Float, default=0)
    profit_percent: Mapped[float] = mapped_column(Float, default=0)
    total_with_markup: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # Lock
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    locked_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Extra
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    condition: Mapped["Condition"] = relationship(
        "Condition", back_populates="assembly"
    )
    components: Mapped[list["AssemblyComponent"]] = relationship(
        "AssemblyComponent",
        back_populates="assembly",
        cascade="all, delete-orphan",
        order_by="AssemblyComponent.sort_order",
    )
    template: Mapped["AssemblyTemplate | None"] = relationship(
        "AssemblyTemplate", back_populates="instances"
    )


class AssemblyComponent(Base, UUIDMixin, TimestampMixin):
    """Individual line item in an assembly (material, labor, equipment, etc.)."""

    __tablename__ = "assembly_components"

    # Foreign keys
    assembly_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assemblies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cost_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cost_items.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Component info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    component_type: Mapped[str] = mapped_column(
        String(50), default="material"
    )  # material, labor, equipment, subcontract, other
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Formula & quantity
    quantity_formula: Mapped[str] = mapped_column(String(500), default="{qty}")
    calculated_quantity: Mapped[float] = mapped_column(Float, default=0)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)

    # Waste
    waste_percent: Mapped[float] = mapped_column(Float, default=0)
    quantity_with_waste: Mapped[float] = mapped_column(Float, default=0)
    extended_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # Labor-specific
    labor_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    labor_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    crew_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Equipment-specific
    duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    daily_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Flags
    is_included: Mapped[bool] = mapped_column(Boolean, default=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)

    # Extra
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    assembly: Mapped["Assembly"] = relationship("Assembly", back_populates="components")
