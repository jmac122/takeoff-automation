"""add assembly system tables

Revision ID: p4q5r6s7t8u9
Revises: o3p4q5r6s7t8
Create Date: 2026-02-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "p4q5r6s7t8u9"
down_revision: Union[str, None] = "o3p4q5r6s7t8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create assembly_templates table first (referenced by assemblies FK)
    op.create_table(
        "assembly_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("scope", sa.String(100), server_default="concrete"),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("subcategory", sa.String(100), nullable=True),
        sa.Column("csi_code", sa.String(20), nullable=True),
        sa.Column("csi_description", sa.String(255), nullable=True),
        sa.Column("measurement_type", sa.String(50), server_default="area"),
        sa.Column("expected_unit", sa.String(50), server_default="SF"),
        sa.Column("default_waste_percent", sa.Float, server_default="5.0"),
        sa.Column("productivity_rate", sa.Float, nullable=True),
        sa.Column("productivity_unit", sa.String(50), nullable=True),
        sa.Column("crew_size", sa.Integer, nullable=True),
        sa.Column("is_system", sa.Boolean, server_default="false"),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("component_definitions", postgresql.JSONB, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Create cost_items table (referenced by assembly_components FK)
    op.create_table(
        "cost_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("item_type", sa.String(50), server_default="material"),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("subcategory", sa.String(100), nullable=True),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("unit_cost", sa.Numeric(10, 4), server_default="0"),
        sa.Column("alt_unit", sa.String(50), nullable=True),
        sa.Column("alt_unit_cost", sa.Numeric(10, 4), nullable=True),
        sa.Column("conversion_factor", sa.Float, nullable=True),
        sa.Column("labor_rate_regular", sa.Numeric(10, 2), nullable=True),
        sa.Column("labor_rate_overtime", sa.Numeric(10, 2), nullable=True),
        sa.Column("burden_percent", sa.Float, nullable=True),
        sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("daily_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("weekly_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("monthly_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("vendor", sa.String(255), nullable=True),
        sa.Column("vendor_code", sa.String(100), nullable=True),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiration_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_cost_items_code", "cost_items", ["code"])

    # Create assemblies table
    op.create_table(
        "assemblies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "condition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conditions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assembly_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("csi_code", sa.String(20), nullable=True),
        sa.Column("csi_description", sa.String(255), nullable=True),
        sa.Column("default_waste_percent", sa.Float, server_default="5.0"),
        sa.Column("productivity_rate", sa.Float, nullable=True),
        sa.Column("productivity_unit", sa.String(50), nullable=True),
        sa.Column("crew_size", sa.Integer, nullable=True),
        sa.Column("material_cost", sa.Numeric(12, 2), server_default="0"),
        sa.Column("labor_cost", sa.Numeric(12, 2), server_default="0"),
        sa.Column("equipment_cost", sa.Numeric(12, 2), server_default="0"),
        sa.Column("subcontract_cost", sa.Numeric(12, 2), server_default="0"),
        sa.Column("other_cost", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total_cost", sa.Numeric(12, 2), server_default="0"),
        sa.Column("unit_cost", sa.Numeric(10, 4), server_default="0"),
        sa.Column("total_labor_hours", sa.Float, server_default="0"),
        sa.Column("overhead_percent", sa.Float, server_default="0"),
        sa.Column("profit_percent", sa.Float, server_default="0"),
        sa.Column("total_with_markup", sa.Numeric(12, 2), server_default="0"),
        sa.Column("is_locked", sa.Boolean, server_default="false"),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_assemblies_condition_id", "assemblies", ["condition_id"], unique=True)

    # Create assembly_components table
    op.create_table(
        "assembly_components",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "assembly_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assemblies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cost_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cost_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("component_type", sa.String(50), server_default="material"),
        sa.Column("sort_order", sa.Integer, server_default="0"),
        sa.Column("quantity_formula", sa.String(500), server_default="{qty}"),
        sa.Column("calculated_quantity", sa.Float, server_default="0"),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("unit_cost", sa.Numeric(10, 4), server_default="0"),
        sa.Column("waste_percent", sa.Float, server_default="0"),
        sa.Column("quantity_with_waste", sa.Float, server_default="0"),
        sa.Column("extended_cost", sa.Numeric(12, 2), server_default="0"),
        sa.Column("labor_hours", sa.Float, nullable=True),
        sa.Column("labor_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("crew_size", sa.Integer, nullable=True),
        sa.Column("duration_hours", sa.Float, nullable=True),
        sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("daily_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_included", sa.Boolean, server_default="true"),
        sa.Column("is_optional", sa.Boolean, server_default="false"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_assembly_components_assembly_id",
        "assembly_components",
        ["assembly_id"],
    )


def downgrade() -> None:
    op.drop_table("assembly_components")
    op.drop_table("assemblies")
    op.drop_index("ix_cost_items_code", table_name="cost_items")
    op.drop_table("cost_items")
    op.drop_table("assembly_templates")
