"""Assembly service for cost estimation and management."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assembly import Assembly, AssemblyComponent, AssemblyTemplate
from app.models.condition import Condition
from app.services.formula_engine import FormulaContext, get_formula_engine

logger = structlog.get_logger()


class AssemblyService:
    """Service for managing assemblies and calculating costs."""

    def __init__(self) -> None:
        self.formula_engine = get_formula_engine()

    # ------------------------------------------------------------------
    # Assembly CRUD
    # ------------------------------------------------------------------

    async def create_assembly_for_condition(
        self,
        session: AsyncSession,
        condition_id: uuid.UUID,
        name: str | None = None,
        template_id: uuid.UUID | None = None,
        description: str | None = None,
    ) -> Assembly:
        """Create an assembly for a condition, optionally from a template."""
        # Verify condition exists
        result = await session.execute(
            select(Condition).where(Condition.id == condition_id)
        )
        condition = result.scalar_one_or_none()
        if condition is None:
            raise ValueError(f"Condition {condition_id} not found")

        # Check if condition already has an assembly
        result = await session.execute(
            select(Assembly).where(Assembly.condition_id == condition_id)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise ValueError(f"Condition {condition_id} already has an assembly")

        assembly_name = name or condition.name

        # Load template if specified
        template: AssemblyTemplate | None = None
        if template_id:
            result = await session.execute(
                select(AssemblyTemplate).where(AssemblyTemplate.id == template_id)
            )
            template = result.scalar_one_or_none()
            if template is None:
                raise ValueError(f"Template {template_id} not found")
            if not assembly_name or assembly_name == condition.name:
                assembly_name = template.name

        assembly = Assembly(
            condition_id=condition_id,
            template_id=template_id,
            name=assembly_name,
            description=description,
            csi_code=template.csi_code if template else None,
            csi_description=template.csi_description if template else None,
            default_waste_percent=template.default_waste_percent if template else 5.0,
            productivity_rate=template.productivity_rate if template else None,
            productivity_unit=template.productivity_unit if template else None,
            crew_size=template.crew_size if template else None,
        )
        session.add(assembly)
        await session.flush()

        # Apply template components if template was provided
        if template:
            await self._apply_template(session, assembly, template)

        await session.commit()
        await session.refresh(assembly)

        # Reload with components
        result = await session.execute(
            select(Assembly)
            .options(selectinload(Assembly.components))
            .where(Assembly.id == assembly.id)
        )
        return result.scalar_one()

    async def _apply_template(
        self,
        session: AsyncSession,
        assembly: Assembly,
        template: AssemblyTemplate,
    ) -> None:
        """Copy component definitions from a template into assembly components."""
        for idx, comp_def in enumerate(template.component_definitions):
            component = AssemblyComponent(
                assembly_id=assembly.id,
                name=comp_def.get("name", "Unnamed"),
                description=comp_def.get("description"),
                component_type=comp_def.get("component_type", "material"),
                sort_order=idx,
                quantity_formula=comp_def.get("quantity_formula", "{qty}"),
                unit=comp_def.get("unit", "EA"),
                unit_cost=Decimal(str(comp_def.get("unit_cost", 0))),
                waste_percent=comp_def.get("waste_percent", 0),
                labor_hours=comp_def.get("labor_hours"),
                labor_rate=(
                    Decimal(str(comp_def["labor_rate"]))
                    if comp_def.get("labor_rate") is not None
                    else None
                ),
                crew_size=comp_def.get("crew_size"),
                duration_hours=comp_def.get("duration_hours"),
                hourly_rate=(
                    Decimal(str(comp_def["hourly_rate"]))
                    if comp_def.get("hourly_rate") is not None
                    else None
                ),
                daily_rate=(
                    Decimal(str(comp_def["daily_rate"]))
                    if comp_def.get("daily_rate") is not None
                    else None
                ),
                is_included=comp_def.get("is_included", True),
                is_optional=comp_def.get("is_optional", False),
                notes=comp_def.get("notes"),
            )
            session.add(component)

    async def get_assembly(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
    ) -> Assembly:
        """Get an assembly by ID with components."""
        result = await session.execute(
            select(Assembly)
            .options(selectinload(Assembly.components))
            .where(Assembly.id == assembly_id)
        )
        assembly = result.scalar_one_or_none()
        if assembly is None:
            raise ValueError(f"Assembly {assembly_id} not found")
        return assembly

    async def get_condition_assembly(
        self,
        session: AsyncSession,
        condition_id: uuid.UUID,
    ) -> Assembly | None:
        """Get the assembly for a condition, or None if none exists."""
        result = await session.execute(
            select(Assembly)
            .options(selectinload(Assembly.components))
            .where(Assembly.condition_id == condition_id)
        )
        return result.scalar_one_or_none()

    async def update_assembly(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
        **kwargs: Any,
    ) -> Assembly:
        """Update assembly fields."""
        assembly = await self.get_assembly(session, assembly_id)
        if assembly.is_locked:
            raise ValueError("Assembly is locked and cannot be modified")

        for key, value in kwargs.items():
            if value is not None and hasattr(assembly, key):
                setattr(assembly, key, value)

        await session.commit()
        await session.refresh(assembly)
        return assembly

    async def delete_assembly(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
    ) -> None:
        """Delete an assembly."""
        assembly = await self.get_assembly(session, assembly_id)
        if assembly.is_locked:
            raise ValueError("Assembly is locked and cannot be deleted")
        await session.delete(assembly)
        await session.commit()

    # ------------------------------------------------------------------
    # Component CRUD
    # ------------------------------------------------------------------

    async def add_component(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
        **kwargs: Any,
    ) -> AssemblyComponent:
        """Add a component to an assembly."""
        assembly = await self.get_assembly(session, assembly_id)
        if assembly.is_locked:
            raise ValueError("Assembly is locked and cannot be modified")

        # Auto-set sort_order if not provided
        if "sort_order" not in kwargs or kwargs["sort_order"] is None:
            max_order = max((c.sort_order for c in assembly.components), default=-1)
            kwargs["sort_order"] = max_order + 1

        # Convert unit_cost to Decimal if present
        if "unit_cost" in kwargs and kwargs["unit_cost"] is not None:
            kwargs["unit_cost"] = Decimal(str(kwargs["unit_cost"]))

        component = AssemblyComponent(assembly_id=assembly_id, **kwargs)
        session.add(component)
        await session.commit()
        await session.refresh(component)
        return component

    async def update_component(
        self,
        session: AsyncSession,
        component_id: uuid.UUID,
        **kwargs: Any,
    ) -> AssemblyComponent:
        """Update a component."""
        result = await session.execute(
            select(AssemblyComponent)
            .options(selectinload(AssemblyComponent.assembly))
            .where(AssemblyComponent.id == component_id)
        )
        component = result.scalar_one_or_none()
        if component is None:
            raise ValueError(f"Component {component_id} not found")
        if component.assembly.is_locked:
            raise ValueError("Assembly is locked and cannot be modified")

        for key, value in kwargs.items():
            if value is not None and hasattr(component, key):
                if key == "unit_cost":
                    value = Decimal(str(value))
                setattr(component, key, value)

        await session.commit()
        await session.refresh(component)
        return component

    async def delete_component(
        self,
        session: AsyncSession,
        component_id: uuid.UUID,
    ) -> None:
        """Delete a component."""
        result = await session.execute(
            select(AssemblyComponent)
            .options(selectinload(AssemblyComponent.assembly))
            .where(AssemblyComponent.id == component_id)
        )
        component = result.scalar_one_or_none()
        if component is None:
            raise ValueError(f"Component {component_id} not found")
        if component.assembly.is_locked:
            raise ValueError("Assembly is locked and cannot be modified")

        await session.delete(component)
        await session.commit()

    async def reorder_components(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
        component_ids: list[uuid.UUID],
    ) -> None:
        """Reorder components by the provided ID list."""
        assembly = await self.get_assembly(session, assembly_id)
        if assembly.is_locked:
            raise ValueError("Assembly is locked and cannot be modified")

        id_to_component = {c.id: c for c in assembly.components}
        for idx, cid in enumerate(component_ids):
            if cid in id_to_component:
                id_to_component[cid].sort_order = idx

        await session.commit()

    # ------------------------------------------------------------------
    # Calculation
    # ------------------------------------------------------------------

    async def calculate_assembly(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
    ) -> Assembly:
        """Recalculate all component quantities and costs for an assembly."""
        # Load assembly with components and condition
        result = await session.execute(
            select(Assembly)
            .options(
                selectinload(Assembly.components),
                selectinload(Assembly.condition),
            )
            .where(Assembly.id == assembly_id)
        )
        assembly = result.scalar_one_or_none()
        if assembly is None:
            raise ValueError(f"Assembly {assembly_id} not found")

        condition = assembly.condition
        context = self._build_formula_context(condition)

        # Reset cost accumulators
        cost_by_type: dict[str, Decimal] = {
            "material": Decimal("0"),
            "labor": Decimal("0"),
            "equipment": Decimal("0"),
            "subcontract": Decimal("0"),
            "other": Decimal("0"),
        }
        total_labor_hours = 0.0

        for component in assembly.components:
            if not component.is_included:
                component.calculated_quantity = 0
                component.quantity_with_waste = 0
                component.extended_cost = Decimal("0")
                continue

            try:
                calc_qty = self.formula_engine.evaluate(
                    component.quantity_formula, context
                )
            except ValueError as e:
                logger.warning(
                    "Formula evaluation failed",
                    component_id=str(component.id),
                    formula=component.quantity_formula,
                    error=str(e),
                )
                calc_qty = 0.0

            component.calculated_quantity = calc_qty
            component.quantity_with_waste = calc_qty * (
                1 + component.waste_percent / 100
            )
            component.extended_cost = (
                Decimal(str(component.quantity_with_waste)) * component.unit_cost
            )

            # Accumulate by type
            ctype = component.component_type
            if ctype in cost_by_type:
                cost_by_type[ctype] += component.extended_cost
            else:
                cost_by_type["other"] += component.extended_cost

            # Accumulate labor hours
            if component.labor_hours is not None:
                total_labor_hours += (
                    component.labor_hours * component.quantity_with_waste
                )

        # Update assembly totals
        assembly.material_cost = cost_by_type["material"]
        assembly.labor_cost = cost_by_type["labor"]
        assembly.equipment_cost = cost_by_type["equipment"]
        assembly.subcontract_cost = cost_by_type["subcontract"]
        assembly.other_cost = cost_by_type["other"]
        assembly.total_cost = sum(cost_by_type.values())
        assembly.total_labor_hours = total_labor_hours

        # Unit cost (guard against division by zero)
        qty = context.qty
        if qty > 0:
            assembly.unit_cost = assembly.total_cost / Decimal(str(qty))
        else:
            assembly.unit_cost = Decimal("0")

        # Markup
        markup_factor = (
            Decimal("1")
            + Decimal(str(assembly.overhead_percent / 100))
            + Decimal(str(assembly.profit_percent / 100))
        )
        assembly.total_with_markup = assembly.total_cost * markup_factor

        await session.commit()

        # Reload with components
        result = await session.execute(
            select(Assembly)
            .options(selectinload(Assembly.components))
            .where(Assembly.id == assembly.id)
        )
        return result.scalar_one()

    def _build_formula_context(self, condition: Condition) -> FormulaContext:
        """Build a FormulaContext from condition data."""
        return FormulaContext(
            qty=condition.total_quantity or 0.0,
            depth=condition.depth or 0.0,
            thickness=condition.thickness or 0.0,
            count=condition.measurement_count or 0,
            # TODO: Add the following fields to Condition model to support template formulas:
            # - perimeter: Float (for perimeter-based calculations like sidewalks)
            # - height: Float (for height-based volume calculations)
            # - width: Float (for width-based area calculations)
            # - length: Float (for length-based linear calculations)
            # Currently these are placeholders set to 0 and will be used once model is extended.
            perimeter=0.0,
            height=0.0,
            width=0.0,
            length=0.0,
        )

    # ------------------------------------------------------------------
    # Lock / Unlock
    # ------------------------------------------------------------------

    async def lock_assembly(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
        locked_by: str,
    ) -> Assembly:
        """Lock an assembly to prevent modifications."""
        assembly = await self.get_assembly(session, assembly_id)
        assembly.is_locked = True
        assembly.locked_at = datetime.now(timezone.utc)
        assembly.locked_by = locked_by
        await session.commit()
        await session.refresh(assembly)
        return assembly

    async def unlock_assembly(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
    ) -> Assembly:
        """Unlock an assembly."""
        assembly = await self.get_assembly(session, assembly_id)
        assembly.is_locked = False
        assembly.locked_at = None
        assembly.locked_by = None
        await session.commit()
        await session.refresh(assembly)
        return assembly

    # ------------------------------------------------------------------
    # Duplication
    # ------------------------------------------------------------------

    async def duplicate_assembly(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
        new_condition_id: uuid.UUID,
    ) -> Assembly:
        """Deep-copy an assembly and all its components to a new condition."""
        source = await self.get_assembly(session, assembly_id)

        new_assembly = Assembly(
            condition_id=new_condition_id,
            template_id=source.template_id,
            name=source.name,
            description=source.description,
            csi_code=source.csi_code,
            csi_description=source.csi_description,
            default_waste_percent=source.default_waste_percent,
            productivity_rate=source.productivity_rate,
            productivity_unit=source.productivity_unit,
            crew_size=source.crew_size,
            overhead_percent=source.overhead_percent,
            profit_percent=source.profit_percent,
            notes=source.notes,
        )
        session.add(new_assembly)
        await session.flush()

        for comp in source.components:
            new_comp = AssemblyComponent(
                assembly_id=new_assembly.id,
                cost_item_id=comp.cost_item_id,
                name=comp.name,
                description=comp.description,
                component_type=comp.component_type,
                sort_order=comp.sort_order,
                quantity_formula=comp.quantity_formula,
                unit=comp.unit,
                unit_cost=comp.unit_cost,
                waste_percent=comp.waste_percent,
                labor_hours=comp.labor_hours,
                labor_rate=comp.labor_rate,
                crew_size=comp.crew_size,
                duration_hours=comp.duration_hours,
                hourly_rate=comp.hourly_rate,
                daily_rate=comp.daily_rate,
                is_included=comp.is_included,
                is_optional=comp.is_optional,
                notes=comp.notes,
            )
            session.add(new_comp)

        await session.commit()

        result = await session.execute(
            select(Assembly)
            .options(selectinload(Assembly.components))
            .where(Assembly.id == new_assembly.id)
        )
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Project cost summary
    # ------------------------------------------------------------------

    async def get_project_cost_summary(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Get aggregated costs across all assemblies in a project."""
        result = await session.execute(
            select(
                func.count(Condition.id).label("total_conditions"),
                func.count(Assembly.id).label("conditions_with_assemblies"),
                func.coalesce(func.sum(Assembly.material_cost), 0).label(
                    "material_cost"
                ),
                func.coalesce(func.sum(Assembly.labor_cost), 0).label("labor_cost"),
                func.coalesce(func.sum(Assembly.equipment_cost), 0).label(
                    "equipment_cost"
                ),
                func.coalesce(func.sum(Assembly.subcontract_cost), 0).label(
                    "subcontract_cost"
                ),
                func.coalesce(func.sum(Assembly.other_cost), 0).label("other_cost"),
                func.coalesce(func.sum(Assembly.total_cost), 0).label("total_cost"),
                func.coalesce(func.sum(Assembly.total_with_markup), 0).label(
                    "total_with_markup"
                ),
            )
            .select_from(Condition)
            .outerjoin(Assembly, Assembly.condition_id == Condition.id)
            .where(Condition.project_id == project_id)
        )
        row = result.one()

        return {
            "project_id": project_id,
            "total_conditions": row.total_conditions,
            "conditions_with_assemblies": row.conditions_with_assemblies,
            "material_cost": row.material_cost,
            "labor_cost": row.labor_cost,
            "equipment_cost": row.equipment_cost,
            "subcontract_cost": row.subcontract_cost,
            "other_cost": row.other_cost,
            "total_cost": row.total_cost,
            "total_with_markup": row.total_with_markup,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_service: AssemblyService | None = None


def get_assembly_service() -> AssemblyService:
    """Get the assembly service singleton."""
    global _service
    if _service is None:
        _service = AssemblyService()
    return _service
