# Phase 3C: Assembly System
## Cost Assemblies with Components, Formulas, and Pricing

> **Duration**: Weeks 18-22
> **Prerequisites**: Condition management working (Phase 3B)
> **Outcome**: Full assembly system with nested components, formula engine, and cost calculations

---

## Context for LLM Assistant

You are implementing a professional-grade assembly system for construction takeoff. This transforms simple "conditions" into complete cost assemblies that match how concrete contractors actually estimate work.

### What is an Assembly?

An **Assembly** is a complete work item that bundles:
- **Takeoff measurement** (the quantity from drawings)
- **Multiple components** (materials, labor, equipment)
- **Formulas** that derive component quantities from the takeoff
- **Unit costs** for pricing
- **Waste factors** and productivity rates

### Real-World Example

When an estimator takes off "4-inch Slab on Grade", they don't just measure square footage. They need:

```
Assembly: 4" SOG Reinforced w/ #4 Bars @ 18" O.C.
├── Takeoff: 10,000 SF (from measurements)
│
├── Materials
│   ├── Concrete 4000 PSI: 10,000 × 0.333 ÷ 27 = 123.5 CY @ $145/CY = $17,907
│   ├── #4 Rebar: 10,000 × 0.89 = 8,900 LBS @ $0.85/LB = $7,565
│   ├── Rebar Chairs: 10,000 ÷ 4 = 2,500 EA @ $0.45/EA = $1,125
│   ├── Vapor Barrier 10mil: 10,000 × 1.1 = 11,000 SF @ $0.08/SF = $880
│   ├── Cure & Seal: 10,000 ÷ 200 = 50 GAL @ $28/GAL = $1,400
│   └── Expansion Joint: 500 LF @ $2.50/LF = $1,250
│
├── Labor
│   ├── Fine Grade: 10,000 SF @ $0.35/SF = $3,500
│   ├── Vapor Barrier Install: 10,000 SF @ $0.12/SF = $1,200
│   ├── Rebar Install: 8,900 LBS @ $0.25/LB = $2,225
│   ├── Place Concrete: 123.5 CY @ $45/CY = $5,558
│   ├── Finish (Broom): 10,000 SF @ $0.65/SF = $6,500
│   └── Cure & Seal Apply: 10,000 SF @ $0.15/SF = $1,500
│
├── Equipment
│   ├── Concrete Pump: 123.5 CY ÷ 80 = 1.5 days @ $1,800/day = $2,700
│   ├── Laser Screed: 10,000 ÷ 3000 = 3.3 days @ $850/day = $2,833
│   └── Power Trowels (2): 10,000 ÷ 2000 = 5 hrs × 2 @ $45/hr = $450
│
├── Waste Factor: 5% on materials
├── Productivity: 150 SF/crew-hour
│
└── TOTAL: $56,593 ($5.66/SF)
```

### Assembly Hierarchy

```
Project
└── Condition (linked to measurements)
    └── Assembly (cost breakdown)
        ├── Component (material/labor/equipment)
        │   ├── Formula (derives quantity)
        │   ├── Unit Cost
        │   └── Waste Factor
        └── Assembly Settings
            ├── Default Waste %
            ├── Productivity Rate
            └── Crew Size
```

### Formula Engine

Components use formulas to calculate quantities from the takeoff measurement:

| Formula Variable | Description | Example |
|------------------|-------------|---------|
| `{qty}` | Takeoff quantity (SF, LF, CY, EA) | 10000 |
| `{depth}` | Condition depth in inches | 4 |
| `{thickness}` | Condition thickness in inches | 8 |
| `{perimeter}` | Sum of linear measurements | 500 |
| `{count}` | Number of count measurements | 25 |

**Example Formulas:**
- Concrete CY: `{qty} * {depth} / 12 / 27`
- Rebar LBS: `{qty} * 0.89` (for #4 @ 18" O.C.)
- Form SF: `{perimeter} * {depth} / 12 * 2` (both sides)
- Dowels EA: `{count} * 4` (4 dowels per footing)

---

## Database Models

### Task 13.1: Assembly and Component Models

Create `backend/app/models/assembly.py`:

```python
"""Assembly and component models for cost estimation."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    String, Float, Integer, Boolean, ForeignKey, Text, 
    Numeric, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.condition import Condition
    from app.models.project import Project


class ComponentType(str):
    """Component type enumeration."""
    MATERIAL = "material"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    SUBCONTRACT = "subcontract"
    OTHER = "other"


class Assembly(Base, UUIDMixin, TimestampMixin):
    """
    Cost assembly that breaks down a condition into components.
    
    An assembly represents a complete work item with all materials,
    labor, and equipment needed to perform the work.
    """

    __tablename__ = "assemblies"

    # Foreign keys
    condition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conditions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One assembly per condition
    )
    
    # Optional: link to assembly template
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assembly_templates.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Assembly info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # CSI MasterFormat code (e.g., "03 30 00" for Cast-in-Place Concrete)
    csi_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    csi_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Default settings
    default_waste_percent: Mapped[float] = mapped_column(Float, default=5.0)
    productivity_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    productivity_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    crew_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Calculated totals (denormalized for performance)
    material_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    labor_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    equipment_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    subcontract_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    other_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    
    # Labor hours
    total_labor_hours: Mapped[float] = mapped_column(Float, default=0)
    
    # Markup and pricing
    overhead_percent: Mapped[float] = mapped_column(Float, default=0)
    profit_percent: Mapped[float] = mapped_column(Float, default=0)
    total_with_markup: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    
    # Status
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    locked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Notes and metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    condition: Mapped["Condition"] = relationship(
        "Condition", 
        back_populates="assembly"
    )
    components: Mapped[list["AssemblyComponent"]] = relationship(
        "AssemblyComponent",
        back_populates="assembly",
        cascade="all, delete-orphan",
        order_by="AssemblyComponent.sort_order",
    )
    template: Mapped["AssemblyTemplate | None"] = relationship(
        "AssemblyTemplate",
        back_populates="instances",
    )


class AssemblyComponent(Base, UUIDMixin, TimestampMixin):
    """
    Individual component within an assembly.
    
    Components can be materials, labor, equipment, or subcontracts.
    Each has a formula that derives quantity from the takeoff.
    """

    __tablename__ = "assembly_components"

    # Foreign keys
    assembly_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assemblies.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Optional: link to cost item in cost database
    cost_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cost_items.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Component identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    component_type: Mapped[str] = mapped_column(
        String(50), 
        default=ComponentType.MATERIAL
    )  # material, labor, equipment, subcontract, other
    
    # Ordering
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Formula for quantity calculation
    # Uses variables: {qty}, {depth}, {thickness}, {perimeter}, {count}
    quantity_formula: Mapped[str] = mapped_column(String(500), default="{qty}")
    
    # Calculated quantity (after formula evaluation)
    calculated_quantity: Mapped[float] = mapped_column(Float, default=0)
    
    # Unit of measure
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Pricing
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    
    # Waste factor (percentage, e.g., 5 for 5%)
    waste_percent: Mapped[float] = mapped_column(Float, default=0)
    
    # Quantity after waste
    quantity_with_waste: Mapped[float] = mapped_column(Float, default=0)
    
    # Extended cost (quantity_with_waste × unit_cost)
    extended_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    
    # Labor-specific fields
    labor_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    labor_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    crew_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Equipment-specific fields
    duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    daily_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Flags
    is_included: Mapped[bool] = mapped_column(Boolean, default=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    assembly: Mapped["Assembly"] = relationship(
        "Assembly", 
        back_populates="components"
    )
    cost_item: Mapped["CostItem | None"] = relationship("CostItem")


class AssemblyTemplate(Base, UUIDMixin, TimestampMixin):
    """
    Reusable assembly template that can be applied to conditions.
    
    Templates store the component structure and formulas without
    specific quantities or costs, which are calculated when applied.
    """

    __tablename__ = "assembly_templates"

    # Template identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Classification
    scope: Mapped[str] = mapped_column(String(100), default="concrete")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # CSI code
    csi_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    csi_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Expected measurement type (area, linear, volume, count)
    measurement_type: Mapped[str] = mapped_column(String(50), default="area")
    expected_unit: Mapped[str] = mapped_column(String(50), default="SF")
    
    # Default settings
    default_waste_percent: Mapped[float] = mapped_column(Float, default=5.0)
    productivity_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    productivity_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    crew_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Template is system-provided vs user-created
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Ownership (for user-created templates)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Version tracking
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Component definitions stored as JSON
    # (Denormalized for easy template copying)
    component_definitions: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    # Relationships
    instances: Mapped[list["Assembly"]] = relationship(
        "Assembly",
        back_populates="template",
    )


class CostItem(Base, UUIDMixin, TimestampMixin):
    """
    Cost database item for materials, labor rates, and equipment.
    
    This is the master cost database that components reference.
    """

    __tablename__ = "cost_items"

    # Item identification
    code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Classification
    item_type: Mapped[str] = mapped_column(String(50), default="material")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Unit and pricing
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    
    # Alternative units and conversions
    alt_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    alt_unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    conversion_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Labor-specific
    labor_rate_regular: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    labor_rate_overtime: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    burden_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Equipment-specific
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    daily_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    weekly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    monthly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Vendor/supplier info
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Effective dates
    effective_date: Mapped[datetime | None] = mapped_column(nullable=True)
    expiration_date: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Region/location
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
```

Update `backend/app/models/condition.py` to add assembly relationship:

```python
# Add to Condition model:

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.assembly import Assembly

class Condition(Base, UUIDMixin, TimestampMixin):
    # ... existing fields ...
    
    # Add assembly relationship
    assembly: Mapped["Assembly | None"] = relationship(
        "Assembly",
        back_populates="condition",
        uselist=False,
        cascade="all, delete-orphan",
    )
```

Create migration:

```bash
alembic revision --autogenerate -m "add_assembly_system"
alembic upgrade head
```

---

### Task 13.2: Formula Engine Service

Create `backend/app/services/formula_engine.py`:

```python
"""Formula engine for calculating assembly component quantities."""

import re
import math
from decimal import Decimal
from typing import Any
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class FormulaContext:
    """Context variables available for formula evaluation."""
    
    qty: float  # Primary takeoff quantity (SF, LF, CY, EA)
    depth: float = 0  # Depth in inches
    thickness: float = 0  # Thickness in inches
    perimeter: float = 0  # Perimeter in LF (sum of linear measurements)
    count: int = 0  # Number of count measurements
    height: float = 0  # Height in feet (for walls)
    width: float = 0  # Width in feet (for elements)
    length: float = 0  # Total length in feet
    
    # Computed helpers
    @property
    def depth_ft(self) -> float:
        """Depth in feet."""
        return self.depth / 12
    
    @property
    def thickness_ft(self) -> float:
        """Thickness in feet."""
        return self.thickness / 12
    
    @property
    def volume_cf(self) -> float:
        """Volume in cubic feet (qty as SF × depth)."""
        return self.qty * self.depth / 12
    
    @property
    def volume_cy(self) -> float:
        """Volume in cubic yards."""
        return self.volume_cf / 27


class FormulaEngine:
    """
    Engine for evaluating quantity formulas.
    
    Formulas use variables like {qty}, {depth}, etc. and support
    basic math operations.
    
    Examples:
        - "{qty}"  → direct quantity
        - "{qty} * {depth} / 12 / 27"  → SF to CY conversion
        - "{qty} * 0.89"  → rebar weight factor
        - "{perimeter} * {depth} / 12 * 2"  → form area (both sides)
        - "math.ceil({qty} / 100) * 100"  → round up to nearest 100
    """
    
    # Valid variable names
    VALID_VARIABLES = {
        'qty', 'depth', 'thickness', 'perimeter', 'count',
        'height', 'width', 'length', 'depth_ft', 'thickness_ft',
        'volume_cf', 'volume_cy'
    }
    
    # Allowed functions and constants
    ALLOWED_NAMES = {
        'math': math,
        'ceil': math.ceil,
        'floor': math.floor,
        'round': round,
        'min': min,
        'max': max,
        'abs': abs,
        'pow': pow,
        'sqrt': math.sqrt,
        'pi': math.pi,
    }
    
    def __init__(self):
        self._variable_pattern = re.compile(r'\{(\w+)\}')
    
    def evaluate(
        self,
        formula: str,
        context: FormulaContext,
    ) -> float:
        """
        Evaluate a formula with the given context.
        
        Args:
            formula: Formula string with {variables}
            context: Context containing variable values
            
        Returns:
            Calculated quantity
            
        Raises:
            ValueError: If formula is invalid
        """
        if not formula or not formula.strip():
            return context.qty
        
        # Replace {variables} with actual values
        def replace_var(match):
            var_name = match.group(1)
            if var_name not in self.VALID_VARIABLES:
                raise ValueError(f"Unknown variable: {var_name}")
            
            value = getattr(context, var_name, 0)
            return str(value)
        
        expression = self._variable_pattern.sub(replace_var, formula)
        
        # Validate expression for safety
        self._validate_expression(expression)
        
        # Evaluate
        try:
            result = eval(expression, {"__builtins__": {}}, self.ALLOWED_NAMES)
            return float(result)
        except Exception as e:
            logger.error(
                "Formula evaluation failed",
                formula=formula,
                expression=expression,
                error=str(e),
            )
            raise ValueError(f"Formula evaluation failed: {e}")
    
    def _validate_expression(self, expression: str) -> None:
        """Validate expression for safety before evaluation."""
        # Remove allowed content
        cleaned = expression
        
        # Remove numbers (including decimals and scientific notation)
        cleaned = re.sub(r'[\d.]+(?:e[+-]?\d+)?', '', cleaned, flags=re.IGNORECASE)
        
        # Remove operators
        cleaned = re.sub(r'[+\-*/().,\s]', '', cleaned)
        
        # Remove allowed function names
        for name in self.ALLOWED_NAMES:
            cleaned = cleaned.replace(name, '')
        
        # Anything remaining is suspicious
        if cleaned:
            raise ValueError(f"Invalid characters in formula: {cleaned}")
    
    def validate_formula(self, formula: str) -> tuple[bool, str | None]:
        """
        Validate a formula without evaluating it.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check variable names
            variables = self._variable_pattern.findall(formula)
            for var in variables:
                if var not in self.VALID_VARIABLES:
                    return False, f"Unknown variable: {var}"
            
            # Try evaluation with dummy context
            dummy_context = FormulaContext(
                qty=100,
                depth=4,
                thickness=8,
                perimeter=50,
                count=10,
                height=8,
                width=12,
                length=100,
            )
            self.evaluate(formula, dummy_context)
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def get_formula_help(self) -> dict[str, Any]:
        """Get help information for formula writing."""
        return {
            "variables": {
                "qty": "Primary takeoff quantity (SF, LF, CY, or EA)",
                "depth": "Condition depth in inches",
                "thickness": "Condition thickness in inches",
                "perimeter": "Sum of perimeter/linear measurements in LF",
                "count": "Number of count measurements",
                "height": "Height in feet",
                "width": "Width in feet",
                "length": "Total length in feet",
                "depth_ft": "Computed: depth / 12",
                "thickness_ft": "Computed: thickness / 12",
                "volume_cf": "Computed: qty × depth / 12",
                "volume_cy": "Computed: volume_cf / 27",
            },
            "functions": {
                "ceil(x)": "Round up to nearest integer",
                "floor(x)": "Round down to nearest integer",
                "round(x, n)": "Round to n decimal places",
                "min(a, b)": "Minimum of two values",
                "max(a, b)": "Maximum of two values",
                "abs(x)": "Absolute value",
                "sqrt(x)": "Square root",
                "pow(x, y)": "x raised to power y",
            },
            "constants": {
                "pi": "3.14159...",
            },
            "examples": [
                {
                    "description": "Direct quantity (no conversion)",
                    "formula": "{qty}",
                },
                {
                    "description": "SF to CY (area × depth)",
                    "formula": "{qty} * {depth} / 12 / 27",
                },
                {
                    "description": "Rebar weight (#4 @ 18\" O.C.)",
                    "formula": "{qty} * 0.89",
                },
                {
                    "description": "Vapor barrier with 10% overlap",
                    "formula": "{qty} * 1.1",
                },
                {
                    "description": "Form area (both sides)",
                    "formula": "{perimeter} * {depth} / 12 * 2",
                },
                {
                    "description": "Round up to nearest 100",
                    "formula": "ceil({qty} / 100) * 100",
                },
                {
                    "description": "Dowels per footing (4 each)",
                    "formula": "{count} * 4",
                },
            ],
        }


# Common formula presets
FORMULA_PRESETS = {
    # Concrete
    "concrete_cy_from_sf": {
        "name": "Concrete CY from SF",
        "formula": "{qty} * {depth} / 12 / 27",
        "description": "Convert SF × depth to cubic yards",
    },
    "concrete_cy_from_lf": {
        "name": "Concrete CY from LF",
        "formula": "{qty} * {width} * {depth} / 144 / 27",
        "description": "Convert LF × width × depth to CY",
    },
    
    # Rebar
    "rebar_lbs_4_at_12": {
        "name": "Rebar #4 @ 12\" O.C.",
        "formula": "{qty} * 1.33",
        "description": "#4 rebar at 12\" on center, lbs per SF",
    },
    "rebar_lbs_4_at_18": {
        "name": "Rebar #4 @ 18\" O.C.",
        "formula": "{qty} * 0.89",
        "description": "#4 rebar at 18\" on center, lbs per SF",
    },
    "rebar_lbs_5_at_12": {
        "name": "Rebar #5 @ 12\" O.C.",
        "formula": "{qty} * 2.08",
        "description": "#5 rebar at 12\" on center, lbs per SF",
    },
    
    # Forms
    "sfca_wall_both_sides": {
        "name": "SFCA Wall (Both Sides)",
        "formula": "{qty} * 2",
        "description": "Form area for wall, both sides",
    },
    "sfca_footing_perimeter": {
        "name": "SFCA Footing (Perimeter)",
        "formula": "{perimeter} * {depth} / 12",
        "description": "Form area from perimeter × depth",
    },
    
    # Miscellaneous
    "with_waste_5": {
        "name": "With 5% Waste",
        "formula": "{qty} * 1.05",
        "description": "Add 5% waste factor",
    },
    "with_waste_10": {
        "name": "With 10% Waste",
        "formula": "{qty} * 1.10",
        "description": "Add 10% waste factor",
    },
    "vapor_barrier_overlap": {
        "name": "Vapor Barrier with Overlap",
        "formula": "{qty} * 1.1",
        "description": "Add 10% for overlaps",
    },
    "cure_compound_gallons": {
        "name": "Cure Compound Gallons",
        "formula": "{qty} / 200",
        "description": "1 gallon per 200 SF coverage",
    },
    "expansion_joint_lf": {
        "name": "Expansion Joint LF",
        "formula": "sqrt({qty}) * 4",
        "description": "Approximate joint LF for slab",
    },
}


# Singleton
_engine: FormulaEngine | None = None

def get_formula_engine() -> FormulaEngine:
    """Get the formula engine singleton."""
    global _engine
    if _engine is None:
        _engine = FormulaEngine()
    return _engine
```

---

### Task 13.3: Assembly Calculation Service

Create `backend/app/services/assembly_service.py`:

```python
"""Assembly calculation and management service."""

import uuid
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assembly import (
    Assembly, AssemblyComponent, AssemblyTemplate, CostItem, ComponentType
)
from app.models.condition import Condition
from app.models.measurement import Measurement
from app.services.formula_engine import (
    FormulaEngine, FormulaContext, get_formula_engine, FORMULA_PRESETS
)

logger = structlog.get_logger()


class AssemblyService:
    """Service for managing assemblies and calculating costs."""
    
    def __init__(self):
        self.formula_engine = get_formula_engine()
    
    async def create_assembly_for_condition(
        self,
        session: AsyncSession,
        condition_id: uuid.UUID,
        name: str | None = None,
        template_id: uuid.UUID | None = None,
    ) -> Assembly:
        """
        Create a new assembly for a condition.
        
        Args:
            session: Database session
            condition_id: Condition to create assembly for
            name: Optional assembly name (defaults to condition name)
            template_id: Optional template to apply
            
        Returns:
            Created assembly
        """
        # Get condition
        condition = await session.get(Condition, condition_id)
        if not condition:
            raise ValueError(f"Condition not found: {condition_id}")
        
        # Check if assembly already exists
        if condition.assembly:
            raise ValueError(f"Condition already has an assembly")
        
        # Create assembly
        assembly = Assembly(
            condition_id=condition_id,
            name=name or condition.name,
            template_id=template_id,
        )
        
        session.add(assembly)
        await session.flush()
        
        # Apply template if specified
        if template_id:
            template = await session.get(AssemblyTemplate, template_id)
            if template:
                await self._apply_template(session, assembly, template)
        
        await session.commit()
        await session.refresh(assembly)
        
        logger.info(
            "Assembly created",
            assembly_id=str(assembly.id),
            condition_id=str(condition_id),
        )
        
        return assembly
    
    async def _apply_template(
        self,
        session: AsyncSession,
        assembly: Assembly,
        template: AssemblyTemplate,
    ) -> None:
        """Apply a template's component definitions to an assembly."""
        assembly.csi_code = template.csi_code
        assembly.csi_description = template.csi_description
        assembly.default_waste_percent = template.default_waste_percent
        assembly.productivity_rate = template.productivity_rate
        assembly.productivity_unit = template.productivity_unit
        assembly.crew_size = template.crew_size
        
        # Create components from template definitions
        for idx, comp_def in enumerate(template.component_definitions):
            component = AssemblyComponent(
                assembly_id=assembly.id,
                name=comp_def["name"],
                description=comp_def.get("description"),
                component_type=comp_def.get("component_type", "material"),
                sort_order=idx,
                quantity_formula=comp_def.get("quantity_formula", "{qty}"),
                unit=comp_def.get("unit", "EA"),
                unit_cost=Decimal(str(comp_def.get("unit_cost", 0))),
                waste_percent=comp_def.get("waste_percent", 0),
            )
            session.add(component)
    
    async def add_component(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
        name: str,
        component_type: str,
        unit: str,
        quantity_formula: str = "{qty}",
        unit_cost: Decimal = Decimal("0"),
        waste_percent: float = 0,
        cost_item_id: uuid.UUID | None = None,
        **kwargs,
    ) -> AssemblyComponent:
        """Add a component to an assembly."""
        assembly = await session.get(Assembly, assembly_id)
        if not assembly:
            raise ValueError(f"Assembly not found: {assembly_id}")
        
        if assembly.is_locked:
            raise ValueError("Cannot modify locked assembly")
        
        # Validate formula
        is_valid, error = self.formula_engine.validate_formula(quantity_formula)
        if not is_valid:
            raise ValueError(f"Invalid formula: {error}")
        
        # Get max sort order
        result = await session.execute(
            select(func.coalesce(func.max(AssemblyComponent.sort_order), -1))
            .where(AssemblyComponent.assembly_id == assembly_id)
        )
        max_order = result.scalar()
        
        # Get unit cost from cost item if specified
        if cost_item_id:
            cost_item = await session.get(CostItem, cost_item_id)
            if cost_item:
                unit_cost = cost_item.unit_cost
        
        component = AssemblyComponent(
            assembly_id=assembly_id,
            cost_item_id=cost_item_id,
            name=name,
            component_type=component_type,
            sort_order=max_order + 1,
            quantity_formula=quantity_formula,
            unit=unit,
            unit_cost=unit_cost,
            waste_percent=waste_percent,
            **kwargs,
        )
        
        session.add(component)
        await session.commit()
        await session.refresh(component)
        
        # Recalculate assembly
        await self.calculate_assembly(session, assembly_id)
        
        return component
    
    async def calculate_assembly(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
    ) -> Assembly:
        """
        Calculate all component quantities and costs for an assembly.
        
        This is the main calculation method that:
        1. Gets the takeoff quantity from the condition's measurements
        2. Evaluates each component's formula
        3. Applies waste factors
        4. Calculates extended costs
        5. Sums up totals by type
        """
        # Load assembly with components and condition
        result = await session.execute(
            select(Assembly)
            .options(
                selectinload(Assembly.components),
                selectinload(Assembly.condition).selectinload(Condition.measurements),
            )
            .where(Assembly.id == assembly_id)
        )
        assembly = result.scalar_one_or_none()
        
        if not assembly:
            raise ValueError(f"Assembly not found: {assembly_id}")
        
        condition = assembly.condition
        
        # Build formula context from condition and measurements
        context = await self._build_formula_context(condition)
        
        # Calculate each component
        material_total = Decimal("0")
        labor_total = Decimal("0")
        equipment_total = Decimal("0")
        subcontract_total = Decimal("0")
        other_total = Decimal("0")
        total_labor_hours = 0.0
        
        for component in assembly.components:
            if not component.is_included:
                continue
            
            # Evaluate formula
            try:
                calculated_qty = self.formula_engine.evaluate(
                    component.quantity_formula,
                    context,
                )
            except Exception as e:
                logger.warning(
                    "Formula evaluation failed",
                    component_id=str(component.id),
                    formula=component.quantity_formula,
                    error=str(e),
                )
                calculated_qty = 0
            
            component.calculated_quantity = calculated_qty
            
            # Apply waste factor
            waste_factor = 1 + (component.waste_percent / 100)
            component.quantity_with_waste = calculated_qty * waste_factor
            
            # Calculate extended cost
            extended = Decimal(str(component.quantity_with_waste)) * component.unit_cost
            component.extended_cost = extended
            
            # Calculate labor hours if applicable
            if component.component_type == ComponentType.LABOR:
                if component.labor_hours:
                    component_hours = component.quantity_with_waste * component.labor_hours
                    total_labor_hours += component_hours
            
            # Sum by type
            if component.component_type == ComponentType.MATERIAL:
                material_total += extended
            elif component.component_type == ComponentType.LABOR:
                labor_total += extended
            elif component.component_type == ComponentType.EQUIPMENT:
                equipment_total += extended
            elif component.component_type == ComponentType.SUBCONTRACT:
                subcontract_total += extended
            else:
                other_total += extended
        
        # Update assembly totals
        assembly.material_cost = material_total
        assembly.labor_cost = labor_total
        assembly.equipment_cost = equipment_total
        assembly.subcontract_cost = subcontract_total
        assembly.other_cost = other_total
        assembly.total_cost = (
            material_total + labor_total + equipment_total + 
            subcontract_total + other_total
        )
        assembly.total_labor_hours = total_labor_hours
        
        # Calculate unit cost
        if context.qty > 0:
            assembly.unit_cost = assembly.total_cost / Decimal(str(context.qty))
        else:
            assembly.unit_cost = Decimal("0")
        
        # Calculate total with markup
        markup_factor = 1 + (assembly.overhead_percent / 100) + (assembly.profit_percent / 100)
        assembly.total_with_markup = assembly.total_cost * Decimal(str(markup_factor))
        
        await session.commit()
        await session.refresh(assembly)
        
        logger.info(
            "Assembly calculated",
            assembly_id=str(assembly_id),
            total_cost=str(assembly.total_cost),
            unit_cost=str(assembly.unit_cost),
        )
        
        return assembly
    
    async def _build_formula_context(self, condition: Condition) -> FormulaContext:
        """Build formula context from condition and its measurements."""
        measurements = condition.measurements
        
        # Calculate aggregates from measurements
        total_qty = condition.total_quantity or 0
        total_perimeter = 0
        total_count = 0
        total_length = 0
        
        for m in measurements:
            if m.geometry_type in ('polygon', 'rectangle', 'circle'):
                # For area measurements, perimeter might be stored
                if m.metadata and 'perimeter' in m.metadata:
                    total_perimeter += m.metadata['perimeter']
            elif m.geometry_type in ('line', 'polyline'):
                total_length += m.quantity
                total_perimeter += m.quantity
            elif m.geometry_type == 'point':
                total_count += 1
        
        # If condition is count type, use the quantity as count
        if condition.measurement_type == 'count':
            total_count = int(total_qty)
        
        return FormulaContext(
            qty=total_qty,
            depth=condition.depth or 0,
            thickness=condition.thickness or 0,
            perimeter=total_perimeter,
            count=total_count,
            height=condition.height or 0,
            width=condition.width or 0,
            length=total_length,
        )
    
    async def get_assembly_summary(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Get a summary of assembly costs."""
        assembly = await session.get(Assembly, assembly_id)
        if not assembly:
            raise ValueError(f"Assembly not found: {assembly_id}")
        
        return {
            "id": str(assembly.id),
            "name": assembly.name,
            "condition_id": str(assembly.condition_id),
            "takeoff_quantity": assembly.condition.total_quantity if assembly.condition else 0,
            "takeoff_unit": assembly.condition.unit if assembly.condition else "",
            "costs": {
                "material": float(assembly.material_cost),
                "labor": float(assembly.labor_cost),
                "equipment": float(assembly.equipment_cost),
                "subcontract": float(assembly.subcontract_cost),
                "other": float(assembly.other_cost),
                "total": float(assembly.total_cost),
                "unit_cost": float(assembly.unit_cost),
            },
            "labor_hours": assembly.total_labor_hours,
            "markup": {
                "overhead_percent": assembly.overhead_percent,
                "profit_percent": assembly.profit_percent,
                "total_with_markup": float(assembly.total_with_markup),
            },
            "component_count": len(assembly.components) if assembly.components else 0,
        }
    
    async def duplicate_assembly(
        self,
        session: AsyncSession,
        assembly_id: uuid.UUID,
        new_condition_id: uuid.UUID,
    ) -> Assembly:
        """Duplicate an assembly to a new condition."""
        # Load source assembly with components
        result = await session.execute(
            select(Assembly)
            .options(selectinload(Assembly.components))
            .where(Assembly.id == assembly_id)
        )
        source = result.scalar_one_or_none()
        
        if not source:
            raise ValueError(f"Assembly not found: {assembly_id}")
        
        # Create new assembly
        new_assembly = Assembly(
            condition_id=new_condition_id,
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
        )
        
        session.add(new_assembly)
        await session.flush()
        
        # Duplicate components
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
        
        # Calculate the new assembly
        return await self.calculate_assembly(session, new_assembly.id)


# Singleton
_service: AssemblyService | None = None

def get_assembly_service() -> AssemblyService:
    """Get the assembly service singleton."""
    global _service
    if _service is None:
        _service = AssemblyService()
    return _service
```

---

### Task 13.4: Assembly API Endpoints

Create `backend/app/api/routes/assemblies.py`:

```python
"""Assembly API endpoints."""

import uuid
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.assembly import (
    Assembly, AssemblyComponent, AssemblyTemplate, CostItem
)
from app.models.condition import Condition
from app.schemas.assembly import (
    AssemblyCreate,
    AssemblyUpdate,
    AssemblyResponse,
    AssemblyDetailResponse,
    ComponentCreate,
    ComponentUpdate,
    ComponentResponse,
    AssemblyTemplateResponse,
    CostItemCreate,
    CostItemResponse,
    CostItemListResponse,
    FormulaValidateRequest,
    FormulaValidateResponse,
    AssemblyCalculateResponse,
)
from app.services.assembly_service import get_assembly_service
from app.services.formula_engine import get_formula_engine, FORMULA_PRESETS

router = APIRouter()


# ============== Assembly Templates ==============

@router.get("/assembly-templates", response_model=list[AssemblyTemplateResponse])
async def list_assembly_templates(
    scope: str | None = Query(None),
    category: str | None = Query(None),
    measurement_type: str | None = Query(None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """List available assembly templates."""
    query = select(AssemblyTemplate).where(AssemblyTemplate.is_active == True)
    
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


@router.get("/assembly-templates/{template_id}", response_model=AssemblyTemplateResponse)
async def get_assembly_template(
    template_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific assembly template."""
    template = await db.get(AssemblyTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    return AssemblyTemplateResponse.model_validate(template)


# ============== Condition Assemblies ==============

@router.post(
    "/conditions/{condition_id}/assembly",
    response_model=AssemblyResponse,
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
        )
        return AssemblyResponse.model_validate(assembly)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/conditions/{condition_id}/assembly", response_model=AssemblyDetailResponse)
async def get_condition_assembly(
    condition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the assembly for a condition with all components."""
    result = await db.execute(
        select(Assembly)
        .options(selectinload(Assembly.components))
        .where(Assembly.condition_id == condition_id)
    )
    assembly = result.scalar_one_or_none()
    
    if not assembly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assembly not found for this condition",
        )
    
    return AssemblyDetailResponse.model_validate(assembly)


@router.get("/assemblies/{assembly_id}", response_model=AssemblyDetailResponse)
async def get_assembly(
    assembly_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get an assembly with all components."""
    result = await db.execute(
        select(Assembly)
        .options(selectinload(Assembly.components))
        .where(Assembly.id == assembly_id)
    )
    assembly = result.scalar_one_or_none()
    
    if not assembly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assembly not found",
        )
    
    return AssemblyDetailResponse.model_validate(assembly)


@router.put("/assemblies/{assembly_id}", response_model=AssemblyResponse)
async def update_assembly(
    assembly_id: uuid.UUID,
    request: AssemblyUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update assembly settings."""
    assembly = await db.get(Assembly, assembly_id)
    if not assembly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assembly not found",
        )
    
    if assembly.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify locked assembly",
        )
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(assembly, key, value)
    
    await db.commit()
    await db.refresh(assembly)
    
    # Recalculate if markup changed
    if 'overhead_percent' in update_data or 'profit_percent' in update_data:
        service = get_assembly_service()
        assembly = await service.calculate_assembly(db, assembly_id)
    
    return AssemblyResponse.model_validate(assembly)


@router.post("/assemblies/{assembly_id}/calculate", response_model=AssemblyCalculateResponse)
async def calculate_assembly(
    assembly_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Recalculate assembly quantities and costs."""
    service = get_assembly_service()
    
    try:
        assembly = await service.calculate_assembly(db, assembly_id)
        summary = await service.get_assembly_summary(db, assembly_id)
        return AssemblyCalculateResponse(**summary)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/assemblies/{assembly_id}/lock")
async def lock_assembly(
    assembly_id: uuid.UUID,
    locked_by: str = Query(...),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Lock an assembly to prevent modifications."""
    from datetime import datetime
    
    assembly = await db.get(Assembly, assembly_id)
    if not assembly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assembly not found",
        )
    
    assembly.is_locked = True
    assembly.locked_at = datetime.utcnow()
    assembly.locked_by = locked_by
    
    await db.commit()
    
    return {"status": "locked", "locked_by": locked_by}


@router.post("/assemblies/{assembly_id}/unlock")
async def unlock_assembly(
    assembly_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Unlock an assembly to allow modifications."""
    assembly = await db.get(Assembly, assembly_id)
    if not assembly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assembly not found",
        )
    
    assembly.is_locked = False
    assembly.locked_at = None
    assembly.locked_by = None
    
    await db.commit()
    
    return {"status": "unlocked"}


@router.delete("/assemblies/{assembly_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assembly(
    assembly_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an assembly."""
    assembly = await db.get(Assembly, assembly_id)
    if not assembly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assembly not found",
        )
    
    if assembly.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete locked assembly",
        )
    
    await db.delete(assembly)
    await db.commit()


# ============== Assembly Components ==============

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/components/{component_id}", response_model=ComponentResponse)
async def update_component(
    component_id: uuid.UUID,
    request: ComponentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a component."""
    component = await db.get(AssemblyComponent, component_id)
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found",
        )
    
    # Check assembly lock
    assembly = await db.get(Assembly, component.assembly_id)
    if assembly and assembly.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify component in locked assembly",
        )
    
    # Validate formula if provided
    if request.quantity_formula:
        engine = get_formula_engine()
        is_valid, error = engine.validate_formula(request.quantity_formula)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid formula: {error}",
            )
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(component, key, value)
    
    await db.commit()
    await db.refresh(component)
    
    # Recalculate assembly
    service = get_assembly_service()
    await service.calculate_assembly(db, component.assembly_id)
    
    return ComponentResponse.model_validate(component)


@router.delete("/components/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_component(
    component_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a component."""
    component = await db.get(AssemblyComponent, component_id)
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found",
        )
    
    assembly_id = component.assembly_id
    
    # Check assembly lock
    assembly = await db.get(Assembly, assembly_id)
    if assembly and assembly.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete component in locked assembly",
        )
    
    await db.delete(component)
    await db.commit()
    
    # Recalculate assembly
    service = get_assembly_service()
    await service.calculate_assembly(db, assembly_id)


@router.put("/assemblies/{assembly_id}/components/reorder")
async def reorder_components(
    assembly_id: uuid.UUID,
    component_ids: list[uuid.UUID],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reorder components within an assembly."""
    assembly = await db.get(Assembly, assembly_id)
    if not assembly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assembly not found",
        )
    
    if assembly.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reorder components in locked assembly",
        )
    
    for idx, comp_id in enumerate(component_ids):
        component = await db.get(AssemblyComponent, comp_id)
        if component and component.assembly_id == assembly_id:
            component.sort_order = idx
    
    await db.commit()
    
    return {"status": "reordered"}


# ============== Cost Database ==============

@router.get("/cost-items", response_model=CostItemListResponse)
async def list_cost_items(
    item_type: str | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """List cost items from the cost database."""
    query = select(CostItem).where(CostItem.is_active == True)
    
    if item_type:
        query = query.where(CostItem.item_type == item_type)
    if category:
        query = query.where(CostItem.category == category)
    if search:
        query = query.where(
            CostItem.name.ilike(f"%{search}%") |
            CostItem.code.ilike(f"%{search}%")
        )
    
    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()
    
    # Get items
    query = query.order_by(CostItem.category, CostItem.name)
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return CostItemListResponse(
        items=[CostItemResponse.model_validate(i) for i in items],
        total=total,
    )


@router.post(
    "/cost-items",
    response_model=CostItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cost_item(
    request: CostItemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new cost item."""
    item = CostItem(**request.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return CostItemResponse.model_validate(item)


@router.get("/cost-items/{item_id}", response_model=CostItemResponse)
async def get_cost_item(
    item_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific cost item."""
    item = await db.get(CostItem, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost item not found",
        )
    return CostItemResponse.model_validate(item)


# ============== Formula Utilities ==============

@router.post("/formulas/validate", response_model=FormulaValidateResponse)
async def validate_formula(
    request: FormulaValidateRequest,
):
    """Validate a formula without saving it."""
    engine = get_formula_engine()
    is_valid, error = engine.validate_formula(request.formula)
    
    # If valid and test values provided, evaluate
    result = None
    if is_valid and request.test_qty is not None:
        from app.services.formula_engine import FormulaContext
        context = FormulaContext(
            qty=request.test_qty,
            depth=request.test_depth or 0,
            thickness=request.test_thickness or 0,
            perimeter=request.test_perimeter or 0,
            count=request.test_count or 0,
        )
        try:
            result = engine.evaluate(request.formula, context)
        except Exception as e:
            is_valid = False
            error = str(e)
    
    return FormulaValidateResponse(
        is_valid=is_valid,
        error=error,
        test_result=result,
    )


@router.get("/formulas/presets")
async def get_formula_presets():
    """Get available formula presets."""
    return FORMULA_PRESETS


@router.get("/formulas/help")
async def get_formula_help():
    """Get formula writing help and documentation."""
    engine = get_formula_engine()
    return engine.get_formula_help()
```

---

### Task 13.5: Assembly Schemas

Create `backend/app/schemas/assembly.py`:

```python
"""Assembly schemas."""

import uuid
from decimal import Decimal
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ============== Component Schemas ==============

class ComponentCreate(BaseModel):
    """Request to create a component."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    component_type: str = Field(default="material")
    quantity_formula: str = Field(default="{qty}")
    unit: str = Field(..., min_length=1, max_length=50)
    unit_cost: Decimal = Field(default=Decimal("0"))
    waste_percent: float = Field(default=0, ge=0, le=100)
    cost_item_id: uuid.UUID | None = None
    labor_hours: float | None = None
    labor_rate: Decimal | None = None
    crew_size: int | None = None
    duration_hours: float | None = None
    hourly_rate: Decimal | None = None
    daily_rate: Decimal | None = None
    is_optional: bool = False
    notes: str | None = None


class ComponentUpdate(BaseModel):
    """Request to update a component."""
    
    name: str | None = None
    description: str | None = None
    component_type: str | None = None
    quantity_formula: str | None = None
    unit: str | None = None
    unit_cost: Decimal | None = None
    waste_percent: float | None = None
    cost_item_id: uuid.UUID | None = None
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
    """Component response."""
    
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
    
    model_config = {"from_attributes": True}


# ============== Assembly Schemas ==============

class AssemblyCreate(BaseModel):
    """Request to create an assembly."""
    
    name: str | None = None
    template_id: uuid.UUID | None = None


class AssemblyUpdate(BaseModel):
    """Request to update an assembly."""
    
    name: str | None = None
    description: str | None = None
    csi_code: str | None = None
    csi_description: str | None = None
    default_waste_percent: float | None = None
    productivity_rate: float | None = None
    productivity_unit: str | None = None
    crew_size: int | None = None
    overhead_percent: float | None = None
    profit_percent: float | None = None
    notes: str | None = None


class AssemblyResponse(BaseModel):
    """Basic assembly response."""
    
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
    
    model_config = {"from_attributes": True}


class AssemblyDetailResponse(AssemblyResponse):
    """Assembly response with components."""
    
    components: list[ComponentResponse] = []


class AssemblyCalculateResponse(BaseModel):
    """Response after calculating an assembly."""
    
    id: str
    name: str
    condition_id: str
    takeoff_quantity: float
    takeoff_unit: str
    costs: dict[str, float]
    labor_hours: float
    markup: dict[str, float]
    component_count: int


# ============== Template Schemas ==============

class ComponentDefinition(BaseModel):
    """Component definition within a template."""
    
    name: str
    description: str | None = None
    component_type: str = "material"
    quantity_formula: str = "{qty}"
    unit: str
    unit_cost: float = 0
    waste_percent: float = 0


class AssemblyTemplateResponse(BaseModel):
    """Assembly template response."""
    
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
    version: int
    component_definitions: list[dict]
    
    model_config = {"from_attributes": True}


# ============== Cost Item Schemas ==============

class CostItemCreate(BaseModel):
    """Request to create a cost item."""
    
    code: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    item_type: str = "material"
    category: str | None = None
    subcategory: str | None = None
    unit: str = Field(..., min_length=1, max_length=50)
    unit_cost: Decimal = Field(default=Decimal("0"))
    alt_unit: str | None = None
    alt_unit_cost: Decimal | None = None
    conversion_factor: float | None = None
    labor_rate_regular: Decimal | None = None
    labor_rate_overtime: Decimal | None = None
    burden_percent: float | None = None
    hourly_rate: Decimal | None = None
    daily_rate: Decimal | None = None
    weekly_rate: Decimal | None = None
    monthly_rate: Decimal | None = None
    vendor: str | None = None
    vendor_code: str | None = None
    region: str | None = None
    notes: str | None = None


class CostItemResponse(BaseModel):
    """Cost item response."""
    
    id: uuid.UUID
    code: str | None
    name: str
    description: str | None
    item_type: str
    category: str | None
    subcategory: str | None
    unit: str
    unit_cost: Decimal
    alt_unit: str | None
    alt_unit_cost: Decimal | None
    conversion_factor: float | None
    labor_rate_regular: Decimal | None
    labor_rate_overtime: Decimal | None
    burden_percent: float | None
    hourly_rate: Decimal | None
    daily_rate: Decimal | None
    weekly_rate: Decimal | None
    monthly_rate: Decimal | None
    vendor: str | None
    vendor_code: str | None
    region: str | None
    is_active: bool
    notes: str | None
    
    model_config = {"from_attributes": True}


class CostItemListResponse(BaseModel):
    """Cost item list response."""
    
    items: list[CostItemResponse]
    total: int


# ============== Formula Schemas ==============

class FormulaValidateRequest(BaseModel):
    """Request to validate a formula."""
    
    formula: str
    test_qty: float | None = None
    test_depth: float | None = None
    test_thickness: float | None = None
    test_perimeter: float | None = None
    test_count: int | None = None


class FormulaValidateResponse(BaseModel):
    """Formula validation response."""
    
    is_valid: bool
    error: str | None = None
    test_result: float | None = None
```

---

### Task 13.6: Assembly Templates Data

Create `backend/app/data/assembly_templates.py`:

```python
"""
Concrete assembly templates for common work items.

These templates define the standard components and formulas
for typical concrete construction work.
"""

CONCRETE_ASSEMBLY_TEMPLATES = [
    # ============== SLABS ==============
    {
        "name": "4\" Slab on Grade - Standard",
        "description": "4-inch concrete slab on grade with vapor barrier and wire mesh",
        "scope": "concrete",
        "category": "slabs",
        "subcategory": "slab_on_grade",
        "csi_code": "03 30 00",
        "csi_description": "Cast-in-Place Concrete",
        "measurement_type": "area",
        "expected_unit": "SF",
        "default_waste_percent": 5,
        "productivity_rate": 150,
        "productivity_unit": "SF/crew-hour",
        "crew_size": 6,
        "component_definitions": [
            # Materials
            {
                "name": "Concrete 3000 PSI",
                "component_type": "material",
                "quantity_formula": "{qty} * {depth} / 12 / 27",
                "unit": "CY",
                "unit_cost": 135.00,
                "waste_percent": 5,
            },
            {
                "name": "6x6 W2.9xW2.9 WWF",
                "component_type": "material",
                "quantity_formula": "{qty} / 750",
                "unit": "ROLL",
                "unit_cost": 89.00,
                "waste_percent": 10,
            },
            {
                "name": "Vapor Barrier 10 mil",
                "component_type": "material",
                "quantity_formula": "{qty} * 1.1",
                "unit": "SF",
                "unit_cost": 0.08,
                "waste_percent": 10,
            },
            {
                "name": "Cure & Seal Compound",
                "component_type": "material",
                "quantity_formula": "{qty} / 200",
                "unit": "GAL",
                "unit_cost": 28.00,
                "waste_percent": 5,
            },
            # Labor
            {
                "name": "Fine Grade",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.35,
            },
            {
                "name": "Vapor Barrier Install",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.12,
            },
            {
                "name": "WWF Install",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.18,
            },
            {
                "name": "Place Concrete",
                "component_type": "labor",
                "quantity_formula": "{qty} * {depth} / 12 / 27",
                "unit": "CY",
                "unit_cost": 42.00,
            },
            {
                "name": "Finish - Broom",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.55,
            },
            {
                "name": "Cure & Seal Apply",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.12,
            },
            # Equipment
            {
                "name": "Concrete Pump (Line)",
                "component_type": "equipment",
                "quantity_formula": "ceil({qty} * {depth} / 12 / 27 / 80)",
                "unit": "DAY",
                "unit_cost": 1200.00,
            },
        ],
    },
    
    {
        "name": "4\" Slab on Grade - Reinforced #4 @ 18\" O.C.",
        "description": "4-inch reinforced concrete slab with #4 rebar at 18\" on center both ways",
        "scope": "concrete",
        "category": "slabs",
        "subcategory": "slab_on_grade",
        "csi_code": "03 30 00",
        "csi_description": "Cast-in-Place Concrete",
        "measurement_type": "area",
        "expected_unit": "SF",
        "default_waste_percent": 5,
        "productivity_rate": 120,
        "productivity_unit": "SF/crew-hour",
        "crew_size": 7,
        "component_definitions": [
            # Materials
            {
                "name": "Concrete 4000 PSI",
                "component_type": "material",
                "quantity_formula": "{qty} * {depth} / 12 / 27",
                "unit": "CY",
                "unit_cost": 145.00,
                "waste_percent": 5,
            },
            {
                "name": "#4 Rebar",
                "component_type": "material",
                "quantity_formula": "{qty} * 0.89",
                "unit": "LBS",
                "unit_cost": 0.85,
                "waste_percent": 5,
            },
            {
                "name": "Rebar Chairs",
                "component_type": "material",
                "quantity_formula": "{qty} / 4",
                "unit": "EA",
                "unit_cost": 0.45,
                "waste_percent": 10,
            },
            {
                "name": "Tie Wire",
                "component_type": "material",
                "quantity_formula": "{qty} / 100",
                "unit": "ROLL",
                "unit_cost": 45.00,
                "waste_percent": 10,
            },
            {
                "name": "Vapor Barrier 10 mil",
                "component_type": "material",
                "quantity_formula": "{qty} * 1.1",
                "unit": "SF",
                "unit_cost": 0.08,
                "waste_percent": 10,
            },
            {
                "name": "Cure & Seal Compound",
                "component_type": "material",
                "quantity_formula": "{qty} / 200",
                "unit": "GAL",
                "unit_cost": 28.00,
                "waste_percent": 5,
            },
            # Labor
            {
                "name": "Fine Grade",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.35,
            },
            {
                "name": "Vapor Barrier Install",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.12,
            },
            {
                "name": "Rebar Install",
                "component_type": "labor",
                "quantity_formula": "{qty} * 0.89",
                "unit": "LBS",
                "unit_cost": 0.25,
            },
            {
                "name": "Place Concrete",
                "component_type": "labor",
                "quantity_formula": "{qty} * {depth} / 12 / 27",
                "unit": "CY",
                "unit_cost": 45.00,
            },
            {
                "name": "Finish - Broom",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.65,
            },
            {
                "name": "Cure & Seal Apply",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.15,
            },
            # Equipment
            {
                "name": "Concrete Pump (Line)",
                "component_type": "equipment",
                "quantity_formula": "ceil({qty} * {depth} / 12 / 27 / 80)",
                "unit": "DAY",
                "unit_cost": 1200.00,
            },
            {
                "name": "Power Trowels",
                "component_type": "equipment",
                "quantity_formula": "ceil({qty} / 2000)",
                "unit": "DAY",
                "unit_cost": 150.00,
            },
        ],
    },
    
    {
        "name": "6\" Slab on Grade - Heavy Duty",
        "description": "6-inch heavy-duty concrete slab with #5 rebar at 12\" on center",
        "scope": "concrete",
        "category": "slabs",
        "subcategory": "slab_on_grade",
        "csi_code": "03 30 00",
        "csi_description": "Cast-in-Place Concrete",
        "measurement_type": "area",
        "expected_unit": "SF",
        "default_waste_percent": 5,
        "productivity_rate": 100,
        "productivity_unit": "SF/crew-hour",
        "crew_size": 8,
        "component_definitions": [
            {
                "name": "Concrete 4000 PSI",
                "component_type": "material",
                "quantity_formula": "{qty} * {depth} / 12 / 27",
                "unit": "CY",
                "unit_cost": 145.00,
                "waste_percent": 5,
            },
            {
                "name": "#5 Rebar",
                "component_type": "material",
                "quantity_formula": "{qty} * 2.08",
                "unit": "LBS",
                "unit_cost": 0.85,
                "waste_percent": 5,
            },
            {
                "name": "Rebar Chairs (High)",
                "component_type": "material",
                "quantity_formula": "{qty} / 4",
                "unit": "EA",
                "unit_cost": 0.65,
                "waste_percent": 10,
            },
            {
                "name": "Vapor Barrier 15 mil",
                "component_type": "material",
                "quantity_formula": "{qty} * 1.1",
                "unit": "SF",
                "unit_cost": 0.12,
                "waste_percent": 10,
            },
            {
                "name": "Cure & Seal Compound",
                "component_type": "material",
                "quantity_formula": "{qty} / 200",
                "unit": "GAL",
                "unit_cost": 28.00,
                "waste_percent": 5,
            },
            {
                "name": "Fine Grade",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.40,
            },
            {
                "name": "Vapor Barrier Install",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.15,
            },
            {
                "name": "Rebar Install",
                "component_type": "labor",
                "quantity_formula": "{qty} * 2.08",
                "unit": "LBS",
                "unit_cost": 0.28,
            },
            {
                "name": "Place Concrete",
                "component_type": "labor",
                "quantity_formula": "{qty} * {depth} / 12 / 27",
                "unit": "CY",
                "unit_cost": 48.00,
            },
            {
                "name": "Finish - Trowel",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.85,
            },
            {
                "name": "Concrete Pump (Boom)",
                "component_type": "equipment",
                "quantity_formula": "ceil({qty} * {depth} / 12 / 27 / 100)",
                "unit": "DAY",
                "unit_cost": 2200.00,
            },
            {
                "name": "Laser Screed",
                "component_type": "equipment",
                "quantity_formula": "ceil({qty} / 3000)",
                "unit": "DAY",
                "unit_cost": 850.00,
            },
        ],
    },
    
    # ============== FOUNDATIONS ==============
    {
        "name": "Strip Footing 24\"x12\"",
        "description": "24-inch wide by 12-inch deep continuous strip footing",
        "scope": "concrete",
        "category": "foundations",
        "subcategory": "footings",
        "csi_code": "03 30 00",
        "csi_description": "Cast-in-Place Concrete",
        "measurement_type": "linear",
        "expected_unit": "LF",
        "default_waste_percent": 5,
        "productivity_rate": 80,
        "productivity_unit": "LF/crew-hour",
        "crew_size": 5,
        "component_definitions": [
            {
                "name": "Concrete 3000 PSI",
                "component_type": "material",
                "quantity_formula": "{qty} * 2 * 1 / 27",
                "unit": "CY",
                "unit_cost": 135.00,
                "waste_percent": 5,
            },
            {
                "name": "#4 Rebar (Longitudinal)",
                "component_type": "material",
                "quantity_formula": "{qty} * 3 * 0.668",
                "unit": "LBS",
                "unit_cost": 0.85,
                "waste_percent": 8,
            },
            {
                "name": "#4 Stirrups",
                "component_type": "material",
                "quantity_formula": "{qty} / 2 * 4 * 0.668",
                "unit": "LBS",
                "unit_cost": 0.95,
                "waste_percent": 10,
            },
            {
                "name": "Form Lumber",
                "component_type": "material",
                "quantity_formula": "{qty} * 2",
                "unit": "LF",
                "unit_cost": 1.20,
                "waste_percent": 15,
            },
            {
                "name": "Form Stakes",
                "component_type": "material",
                "quantity_formula": "{qty} / 4",
                "unit": "EA",
                "unit_cost": 0.85,
            },
            {
                "name": "Excavation",
                "component_type": "labor",
                "quantity_formula": "{qty} * 2.5 * 1.5 / 27",
                "unit": "CY",
                "unit_cost": 12.00,
            },
            {
                "name": "Form & Strip",
                "component_type": "labor",
                "quantity_formula": "{qty} * 2",
                "unit": "SFCA",
                "unit_cost": 4.50,
            },
            {
                "name": "Rebar Install",
                "component_type": "labor",
                "quantity_formula": "{qty} * 3 * 0.668 + {qty} / 2 * 4 * 0.668",
                "unit": "LBS",
                "unit_cost": 0.30,
            },
            {
                "name": "Place Concrete",
                "component_type": "labor",
                "quantity_formula": "{qty} * 2 * 1 / 27",
                "unit": "CY",
                "unit_cost": 55.00,
            },
            {
                "name": "Backfill",
                "component_type": "labor",
                "quantity_formula": "{qty} * 0.5 * 1.5 / 27",
                "unit": "CY",
                "unit_cost": 8.00,
            },
        ],
    },
    
    {
        "name": "Spread Footing 4'x4'x12\"",
        "description": "4-foot square by 12-inch deep spread footing",
        "scope": "concrete",
        "category": "foundations",
        "subcategory": "footings",
        "csi_code": "03 30 00",
        "csi_description": "Cast-in-Place Concrete",
        "measurement_type": "count",
        "expected_unit": "EA",
        "default_waste_percent": 5,
        "productivity_rate": 8,
        "productivity_unit": "EA/crew-day",
        "crew_size": 4,
        "component_definitions": [
            {
                "name": "Concrete 3000 PSI",
                "component_type": "material",
                "quantity_formula": "{count} * 4 * 4 * 1 / 27",
                "unit": "CY",
                "unit_cost": 135.00,
                "waste_percent": 5,
            },
            {
                "name": "#5 Rebar (Both Ways)",
                "component_type": "material",
                "quantity_formula": "{count} * 10 * 4.5 * 1.043",
                "unit": "LBS",
                "unit_cost": 0.85,
                "waste_percent": 8,
            },
            {
                "name": "#6 Dowels",
                "component_type": "material",
                "quantity_formula": "{count} * 4",
                "unit": "EA",
                "unit_cost": 8.50,
            },
            {
                "name": "Form Lumber",
                "component_type": "material",
                "quantity_formula": "{count} * 16",
                "unit": "LF",
                "unit_cost": 1.20,
                "waste_percent": 15,
            },
            {
                "name": "Excavation",
                "component_type": "labor",
                "quantity_formula": "{count} * 5 * 5 * 2 / 27",
                "unit": "CY",
                "unit_cost": 12.00,
            },
            {
                "name": "Form & Strip",
                "component_type": "labor",
                "quantity_formula": "{count} * 16",
                "unit": "SFCA",
                "unit_cost": 5.50,
            },
            {
                "name": "Rebar Install",
                "component_type": "labor",
                "quantity_formula": "{count} * 10 * 4.5 * 1.043",
                "unit": "LBS",
                "unit_cost": 0.32,
            },
            {
                "name": "Place Concrete",
                "component_type": "labor",
                "quantity_formula": "{count} * 4 * 4 * 1 / 27",
                "unit": "CY",
                "unit_cost": 58.00,
            },
            {
                "name": "Backfill",
                "component_type": "labor",
                "quantity_formula": "{count} * 1 * 5 * 2 / 27",
                "unit": "CY",
                "unit_cost": 8.00,
            },
        ],
    },
    
    {
        "name": "Foundation Wall 8\" x 8' Tall",
        "description": "8-inch thick foundation wall, 8 feet tall",
        "scope": "concrete",
        "category": "foundations",
        "subcategory": "walls",
        "csi_code": "03 30 00",
        "csi_description": "Cast-in-Place Concrete",
        "measurement_type": "linear",
        "expected_unit": "LF",
        "default_waste_percent": 5,
        "productivity_rate": 40,
        "productivity_unit": "LF/crew-day",
        "crew_size": 6,
        "component_definitions": [
            {
                "name": "Concrete 3000 PSI",
                "component_type": "material",
                "quantity_formula": "{qty} * 0.667 * 8 / 27",
                "unit": "CY",
                "unit_cost": 140.00,
                "waste_percent": 3,
            },
            {
                "name": "#5 Vertical Rebar",
                "component_type": "material",
                "quantity_formula": "{qty} * 8.5 * 1.043",
                "unit": "LBS",
                "unit_cost": 0.85,
                "waste_percent": 5,
            },
            {
                "name": "#4 Horizontal Rebar",
                "component_type": "material",
                "quantity_formula": "{qty} * 9 * 0.668",
                "unit": "LBS",
                "unit_cost": 0.85,
                "waste_percent": 5,
            },
            {
                "name": "Snap Ties",
                "component_type": "material",
                "quantity_formula": "{qty} * 8 / 2",
                "unit": "EA",
                "unit_cost": 1.25,
            },
            {
                "name": "Form Rental",
                "component_type": "material",
                "quantity_formula": "{qty} * 8 * 2",
                "unit": "SFCA",
                "unit_cost": 1.50,
            },
            {
                "name": "Form Release Agent",
                "component_type": "material",
                "quantity_formula": "{qty} * 8 * 2 / 400",
                "unit": "GAL",
                "unit_cost": 22.00,
            },
            {
                "name": "Waterstop",
                "component_type": "material",
                "quantity_formula": "{qty}",
                "unit": "LF",
                "unit_cost": 3.50,
                "waste_percent": 5,
            },
            {
                "name": "Set & Strip Forms",
                "component_type": "labor",
                "quantity_formula": "{qty} * 8 * 2",
                "unit": "SFCA",
                "unit_cost": 6.50,
            },
            {
                "name": "Rebar Install",
                "component_type": "labor",
                "quantity_formula": "{qty} * 8.5 * 1.043 + {qty} * 9 * 0.668",
                "unit": "LBS",
                "unit_cost": 0.35,
            },
            {
                "name": "Place Concrete",
                "component_type": "labor",
                "quantity_formula": "{qty} * 0.667 * 8 / 27",
                "unit": "CY",
                "unit_cost": 65.00,
            },
            {
                "name": "Concrete Pump (Boom)",
                "component_type": "equipment",
                "quantity_formula": "ceil({qty} * 0.667 * 8 / 27 / 80)",
                "unit": "DAY",
                "unit_cost": 2200.00,
            },
            {
                "name": "Vibrator",
                "component_type": "equipment",
                "quantity_formula": "ceil({qty} / 100)",
                "unit": "DAY",
                "unit_cost": 75.00,
            },
        ],
    },
    
    # ============== SITE CONCRETE ==============
    {
        "name": "4\" Sidewalk",
        "description": "4-inch concrete sidewalk with broom finish",
        "scope": "concrete",
        "category": "paving",
        "subcategory": "sidewalks",
        "csi_code": "32 13 13",
        "csi_description": "Concrete Paving",
        "measurement_type": "area",
        "expected_unit": "SF",
        "default_waste_percent": 5,
        "productivity_rate": 200,
        "productivity_unit": "SF/crew-hour",
        "crew_size": 4,
        "component_definitions": [
            {
                "name": "Concrete 3000 PSI",
                "component_type": "material",
                "quantity_formula": "{qty} * {depth} / 12 / 27",
                "unit": "CY",
                "unit_cost": 135.00,
                "waste_percent": 5,
            },
            {
                "name": "6x6 W2.1xW2.1 WWF",
                "component_type": "material",
                "quantity_formula": "{qty} / 750",
                "unit": "ROLL",
                "unit_cost": 75.00,
                "waste_percent": 10,
            },
            {
                "name": "Expansion Joint Material",
                "component_type": "material",
                "quantity_formula": "sqrt({qty}) * 2",
                "unit": "LF",
                "unit_cost": 2.50,
                "waste_percent": 10,
            },
            {
                "name": "Cure & Seal",
                "component_type": "material",
                "quantity_formula": "{qty} / 200",
                "unit": "GAL",
                "unit_cost": 28.00,
                "waste_percent": 5,
            },
            {
                "name": "Grade & Compact",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.25,
            },
            {
                "name": "Form & Strip",
                "component_type": "labor",
                "quantity_formula": "sqrt({qty}) * 4",
                "unit": "LF",
                "unit_cost": 3.00,
            },
            {
                "name": "Place Concrete",
                "component_type": "labor",
                "quantity_formula": "{qty} * {depth} / 12 / 27",
                "unit": "CY",
                "unit_cost": 42.00,
            },
            {
                "name": "Finish - Broom",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "SF",
                "unit_cost": 0.45,
            },
            {
                "name": "Saw Cut Joints",
                "component_type": "labor",
                "quantity_formula": "sqrt({qty}) * 2.5",
                "unit": "LF",
                "unit_cost": 1.50,
            },
        ],
    },
    
    {
        "name": "Curb & Gutter - Standard",
        "description": "Standard 6-inch curb with 18-inch gutter",
        "scope": "concrete",
        "category": "paving",
        "subcategory": "curb_gutter",
        "csi_code": "32 16 13",
        "csi_description": "Curbs and Gutters",
        "measurement_type": "linear",
        "expected_unit": "LF",
        "default_waste_percent": 5,
        "productivity_rate": 150,
        "productivity_unit": "LF/crew-day",
        "crew_size": 5,
        "component_definitions": [
            {
                "name": "Concrete 3500 PSI",
                "component_type": "material",
                "quantity_formula": "{qty} * 0.055",
                "unit": "CY",
                "unit_cost": 140.00,
                "waste_percent": 5,
            },
            {
                "name": "#4 Rebar",
                "component_type": "material",
                "quantity_formula": "{qty} * 2 * 0.668",
                "unit": "LBS",
                "unit_cost": 0.85,
                "waste_percent": 8,
            },
            {
                "name": "Expansion Joint",
                "component_type": "material",
                "quantity_formula": "{qty} / 20",
                "unit": "EA",
                "unit_cost": 4.50,
            },
            {
                "name": "Cure Compound",
                "component_type": "material",
                "quantity_formula": "{qty} / 150",
                "unit": "GAL",
                "unit_cost": 24.00,
            },
            {
                "name": "Grade Subbase",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "LF",
                "unit_cost": 0.85,
            },
            {
                "name": "Set String Line",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "LF",
                "unit_cost": 0.25,
            },
            {
                "name": "Place & Finish",
                "component_type": "labor",
                "quantity_formula": "{qty}",
                "unit": "LF",
                "unit_cost": 8.50,
            },
            {
                "name": "Curb Machine",
                "component_type": "equipment",
                "quantity_formula": "ceil({qty} / 500)",
                "unit": "DAY",
                "unit_cost": 450.00,
            },
        ],
    },
    
    # ============== VERTICAL ==============
    {
        "name": "Concrete Column 12\"x12\"",
        "description": "12-inch square concrete column",
        "scope": "concrete",
        "category": "vertical",
        "subcategory": "columns",
        "csi_code": "03 30 00",
        "csi_description": "Cast-in-Place Concrete",
        "measurement_type": "count",
        "expected_unit": "EA",
        "default_waste_percent": 5,
        "productivity_rate": 4,
        "productivity_unit": "EA/crew-day",
        "crew_size": 4,
        "component_definitions": [
            {
                "name": "Concrete 4000 PSI",
                "component_type": "material",
                "quantity_formula": "{count} * 1 * 1 * {height} / 27",
                "unit": "CY",
                "unit_cost": 155.00,
                "waste_percent": 5,
            },
            {
                "name": "#8 Vertical Rebar",
                "component_type": "material",
                "quantity_formula": "{count} * 4 * ({height} + 3) * 2.67",
                "unit": "LBS",
                "unit_cost": 0.90,
                "waste_percent": 5,
            },
            {
                "name": "#3 Ties @ 12\" O.C.",
                "component_type": "material",
                "quantity_formula": "{count} * {height} * 4 * 0.376",
                "unit": "LBS",
                "unit_cost": 0.95,
                "waste_percent": 10,
            },
            {
                "name": "Column Forms (Fiber)",
                "component_type": "material",
                "quantity_formula": "{count}",
                "unit": "EA",
                "unit_cost": 85.00,
            },
            {
                "name": "Form Bracing",
                "component_type": "material",
                "quantity_formula": "{count} * 4",
                "unit": "EA",
                "unit_cost": 12.00,
            },
            {
                "name": "Set Column Forms",
                "component_type": "labor",
                "quantity_formula": "{count}",
                "unit": "EA",
                "unit_cost": 125.00,
            },
            {
                "name": "Rebar Install",
                "component_type": "labor",
                "quantity_formula": "{count} * 4 * ({height} + 3) * 2.67 + {count} * {height} * 4 * 0.376",
                "unit": "LBS",
                "unit_cost": 0.40,
            },
            {
                "name": "Place Concrete",
                "component_type": "labor",
                "quantity_formula": "{count} * 1 * 1 * {height} / 27",
                "unit": "CY",
                "unit_cost": 85.00,
            },
            {
                "name": "Strip Forms",
                "component_type": "labor",
                "quantity_formula": "{count}",
                "unit": "EA",
                "unit_cost": 45.00,
            },
            {
                "name": "Concrete Bucket",
                "component_type": "equipment",
                "quantity_formula": "ceil({count} / 8)",
                "unit": "DAY",
                "unit_cost": 125.00,
            },
        ],
    },
    
    {
        "name": "Concrete Pier 24\" Diameter",
        "description": "24-inch diameter drilled concrete pier",
        "scope": "concrete",
        "category": "foundations",
        "subcategory": "piers",
        "csi_code": "31 63 00",
        "csi_description": "Bored Piles",
        "measurement_type": "count",
        "expected_unit": "EA",
        "default_waste_percent": 8,
        "productivity_rate": 6,
        "productivity_unit": "EA/day",
        "crew_size": 3,
        "component_definitions": [
            {
                "name": "Concrete 4000 PSI",
                "component_type": "material",
                "quantity_formula": "{count} * 3.14159 * 1 * 1 * {depth} / 4 / 27",
                "unit": "CY",
                "unit_cost": 155.00,
                "waste_percent": 8,
            },
            {
                "name": "#8 Vertical Rebar",
                "component_type": "material",
                "quantity_formula": "{count} * 6 * ({depth} + 4) * 2.67",
                "unit": "LBS",
                "unit_cost": 0.90,
                "waste_percent": 5,
            },
            {
                "name": "#4 Spiral",
                "component_type": "material",
                "quantity_formula": "{count} * {depth} * 3 * 0.668",
                "unit": "LBS",
                "unit_cost": 0.95,
                "waste_percent": 10,
            },
            {
                "name": "Sonotube 24\"",
                "component_type": "material",
                "quantity_formula": "{count} * 2",
                "unit": "LF",
                "unit_cost": 18.00,
            },
            {
                "name": "Drill Pier",
                "component_type": "labor",
                "quantity_formula": "{count}",
                "unit": "EA",
                "unit_cost": 350.00,
            },
            {
                "name": "Rebar Cage Fabricate",
                "component_type": "labor",
                "quantity_formula": "{count}",
                "unit": "EA",
                "unit_cost": 185.00,
            },
            {
                "name": "Set Cage & Pour",
                "component_type": "labor",
                "quantity_formula": "{count}",
                "unit": "EA",
                "unit_cost": 125.00,
            },
            {
                "name": "Auger Drill Rig",
                "component_type": "equipment",
                "quantity_formula": "ceil({count} / 6)",
                "unit": "DAY",
                "unit_cost": 1800.00,
            },
            {
                "name": "Crane (Support)",
                "component_type": "equipment",
                "quantity_formula": "ceil({count} / 6)",
                "unit": "DAY",
                "unit_cost": 1200.00,
            },
        ],
    },
]


def get_assembly_templates() -> list[dict]:
    """Get all assembly templates."""
    return CONCRETE_ASSEMBLY_TEMPLATES


def get_templates_by_category(category: str) -> list[dict]:
    """Get templates filtered by category."""
    return [t for t in CONCRETE_ASSEMBLY_TEMPLATES if t["category"] == category]


def get_templates_by_measurement_type(measurement_type: str) -> list[dict]:
    """Get templates filtered by measurement type."""
    return [t for t in CONCRETE_ASSEMBLY_TEMPLATES if t["measurement_type"] == measurement_type]
```

---

### Task 13.7: Frontend Assembly Components

Create `frontend/src/components/assembly/AssemblyPanel.tsx`:

```tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Calculator,
  Plus,
  ChevronDown,
  ChevronRight,
  Lock,
  Unlock,
  Trash2,
  Copy,
  DollarSign,
  Clock,
  Package,
  Wrench,
  HardHat,
  Truck,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { apiClient } from '@/api/client';
import { cn, formatCurrency, formatNumber } from '@/lib/utils';

interface AssemblyPanelProps {
  conditionId: string;
  conditionName: string;
  takeoffQuantity: number;
  takeoffUnit: string;
}

interface Component {
  id: string;
  name: string;
  component_type: string;
  quantity_formula: string;
  calculated_quantity: number;
  unit: string;
  unit_cost: number;
  waste_percent: number;
  quantity_with_waste: number;
  extended_cost: number;
  is_included: boolean;
  is_optional: boolean;
}

interface Assembly {
  id: string;
  name: string;
  material_cost: number;
  labor_cost: number;
  equipment_cost: number;
  total_cost: number;
  unit_cost: number;
  total_labor_hours: number;
  overhead_percent: number;
  profit_percent: number;
  total_with_markup: number;
  is_locked: boolean;
  components: Component[];
}

const COMPONENT_ICONS = {
  material: Package,
  labor: HardHat,
  equipment: Truck,
  subcontract: Wrench,
  other: DollarSign,
};

const COMPONENT_COLORS = {
  material: 'text-blue-600',
  labor: 'text-green-600',
  equipment: 'text-orange-600',
  subcontract: 'text-purple-600',
  other: 'text-gray-600',
};

export function AssemblyPanel({
  conditionId,
  conditionName,
  takeoffQuantity,
  takeoffUnit,
}: AssemblyPanelProps) {
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(
    new Set(['material', 'labor', 'equipment'])
  );
  
  const queryClient = useQueryClient();

  // Fetch assembly for condition
  const { data: assembly, isLoading } = useQuery({
    queryKey: ['assembly', conditionId],
    queryFn: async () => {
      try {
        const response = await apiClient.get<Assembly>(
          `/conditions/${conditionId}/assembly`
        );
        return response.data;
      } catch (error: any) {
        if (error.response?.status === 404) {
          return null;
        }
        throw error;
      }
    },
  });

  // Create assembly mutation
  const createAssemblyMutation = useMutation({
    mutationFn: async (templateId?: string) => {
      const response = await apiClient.post(`/conditions/${conditionId}/assembly`, {
        template_id: templateId,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assembly', conditionId] });
    },
  });

  // Calculate assembly mutation
  const calculateMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/assemblies/${assembly?.id}/calculate`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assembly', conditionId] });
    },
  });

  const toggleType = (type: string) => {
    const newExpanded = new Set(expandedTypes);
    if (newExpanded.has(type)) {
      newExpanded.delete(type);
    } else {
      newExpanded.add(type);
    }
    setExpandedTypes(newExpanded);
  };

  // Group components by type
  const groupedComponents = assembly?.components.reduce((acc, comp) => {
    const type = comp.component_type;
    if (!acc[type]) acc[type] = [];
    acc[type].push(comp);
    return acc;
  }, {} as Record<string, Component[]>) || {};

  if (isLoading) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        Loading assembly...
      </div>
    );
  }

  if (!assembly) {
    return (
      <div className="p-4 space-y-4">
        <div className="text-center text-muted-foreground">
          <Calculator className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>No assembly defined for this condition</p>
        </div>
        <Button
          className="w-full"
          onClick={() => createAssemblyMutation.mutate()}
          disabled={createAssemblyMutation.isPending}
        >
          <Plus className="h-4 w-4 mr-2" />
          Create Assembly
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b bg-muted/50">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-sm truncate">{assembly.name}</h3>
          {assembly.is_locked ? (
            <Badge variant="secondary" className="gap-1">
              <Lock className="h-3 w-3" />
              Locked
            </Badge>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => calculateMutation.mutate()}
              disabled={calculateMutation.isPending}
            >
              <Calculator className="h-4 w-4" />
            </Button>
          )}
        </div>
        
        <div className="text-xs text-muted-foreground">
          Takeoff: {formatNumber(takeoffQuantity)} {takeoffUnit}
        </div>
      </div>

      {/* Cost Summary */}
      <div className="p-3 border-b space-y-2">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-muted-foreground">Material:</span>
            <span className="float-right font-medium">
              {formatCurrency(assembly.material_cost)}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Labor:</span>
            <span className="float-right font-medium">
              {formatCurrency(assembly.labor_cost)}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Equipment:</span>
            <span className="float-right font-medium">
              {formatCurrency(assembly.equipment_cost)}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Labor Hrs:</span>
            <span className="float-right font-medium">
              {formatNumber(assembly.total_labor_hours, 1)}
            </span>
          </div>
        </div>
        
        <div className="pt-2 border-t">
          <div className="flex justify-between text-sm font-semibold">
            <span>Total Cost:</span>
            <span>{formatCurrency(assembly.total_cost)}</span>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Unit Cost:</span>
            <span>{formatCurrency(assembly.unit_cost)}/{takeoffUnit}</span>
          </div>
        </div>
        
        {(assembly.overhead_percent > 0 || assembly.profit_percent > 0) && (
          <div className="pt-2 border-t">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>
                O&P ({assembly.overhead_percent}% + {assembly.profit_percent}%):
              </span>
              <span>
                +{formatCurrency(assembly.total_with_markup - assembly.total_cost)}
              </span>
            </div>
            <div className="flex justify-between text-sm font-semibold text-green-600">
              <span>Sell Price:</span>
              <span>{formatCurrency(assembly.total_with_markup)}</span>
            </div>
          </div>
        )}
      </div>

      {/* Components */}
      <div className="flex-1 overflow-auto">
        {['material', 'labor', 'equipment', 'subcontract', 'other'].map((type) => {
          const components = groupedComponents[type] || [];
          if (components.length === 0) return null;
          
          const Icon = COMPONENT_ICONS[type as keyof typeof COMPONENT_ICONS];
          const colorClass = COMPONENT_COLORS[type as keyof typeof COMPONENT_COLORS];
          const typeTotal = components.reduce((sum, c) => sum + c.extended_cost, 0);
          
          return (
            <Collapsible
              key={type}
              open={expandedTypes.has(type)}
              onOpenChange={() => toggleType(type)}
            >
              <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-muted/50 border-b">
                <div className="flex items-center gap-2">
                  {expandedTypes.has(type) ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  <Icon className={cn('h-4 w-4', colorClass)} />
                  <span className="text-sm font-medium capitalize">{type}</span>
                  <Badge variant="secondary" className="text-xs">
                    {components.length}
                  </Badge>
                </div>
                <span className="text-sm font-medium">
                  {formatCurrency(typeTotal)}
                </span>
              </CollapsibleTrigger>
              
              <CollapsibleContent>
                <div className="divide-y">
                  {components.map((comp) => (
                    <ComponentRow
                      key={comp.id}
                      component={comp}
                      isLocked={assembly.is_locked}
                    />
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          );
        })}
      </div>

      {/* Footer Actions */}
      {!assembly.is_locked && (
        <div className="p-2 border-t bg-muted/50">
          <Button variant="outline" size="sm" className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            Add Component
          </Button>
        </div>
      )}
    </div>
  );
}

function ComponentRow({
  component,
  isLocked,
}: {
  component: Component;
  isLocked: boolean;
}) {
  return (
    <div
      className={cn(
        'px-3 py-2 text-sm',
        !component.is_included && 'opacity-50',
        component.is_optional && 'bg-muted/30'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="font-medium truncate">{component.name}</div>
          <div className="text-xs text-muted-foreground">
            {formatNumber(component.quantity_with_waste, 2)} {component.unit} @{' '}
            {formatCurrency(component.unit_cost)}/{component.unit}
          </div>
          {component.waste_percent > 0 && (
            <div className="text-xs text-orange-600">
              +{component.waste_percent}% waste
            </div>
          )}
        </div>
        <div className="text-right">
          <div className="font-medium">{formatCurrency(component.extended_cost)}</div>
        </div>
      </div>
    </div>
  );
}
```

Create `frontend/src/components/assembly/AssemblyTemplateSelector.tsx`:

```tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Package, Check } from 'lucide-react';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { apiClient } from '@/api/client';
import { cn } from '@/lib/utils';

interface AssemblyTemplate {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  subcategory: string | null;
  measurement_type: string;
  expected_unit: string;
  component_definitions: any[];
}

interface AssemblyTemplateSelectorProps {
  conditionId: string;
  measurementType: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (templateId: string) => void;
}

export function AssemblyTemplateSelector({
  conditionId,
  measurementType,
  open,
  onOpenChange,
  onSelect,
}: AssemblyTemplateSelectorProps) {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const { data: templates } = useQuery({
    queryKey: ['assembly-templates', measurementType],
    queryFn: async () => {
      const response = await apiClient.get<AssemblyTemplate[]>(
        '/assembly-templates',
        { params: { measurement_type: measurementType } }
      );
      return response.data;
    },
    enabled: open,
  });

  // Filter templates
  const filteredTemplates = (templates || []).filter((t) => {
    if (search && !t.name.toLowerCase().includes(search.toLowerCase())) {
      return false;
    }
    if (selectedCategory && t.category !== selectedCategory) {
      return false;
    }
    return true;
  });

  // Get unique categories
  const categories = [...new Set((templates || []).map((t) => t.category).filter(Boolean))];

  // Group by category
  const groupedTemplates = filteredTemplates.reduce((acc, t) => {
    const cat = t.category || 'Other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(t);
    return acc;
  }, {} as Record<string, AssemblyTemplate[]>);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Select Assembly Template</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search templates..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Category filters */}
          <div className="flex flex-wrap gap-2">
            <Badge
              variant={selectedCategory === null ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setSelectedCategory(null)}
            >
              All
            </Badge>
            {categories.map((cat) => (
              <Badge
                key={cat}
                variant={selectedCategory === cat ? 'default' : 'outline'}
                className="cursor-pointer capitalize"
                onClick={() => setSelectedCategory(cat as string)}
              >
                {cat}
              </Badge>
            ))}
          </div>

          {/* Template list */}
          <ScrollArea className="h-[400px]">
            <div className="space-y-4">
              {Object.entries(groupedTemplates).map(([category, categoryTemplates]) => (
                <div key={category}>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2 capitalize">
                    {category}
                  </h4>
                  <div className="space-y-2">
                    {categoryTemplates.map((template) => (
                      <button
                        key={template.id}
                        onClick={() => {
                          onSelect(template.id);
                          onOpenChange(false);
                        }}
                        className="w-full p-3 rounded-lg border hover:border-primary hover:bg-muted/50 text-left transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="font-medium">{template.name}</div>
                            {template.description && (
                              <div className="text-sm text-muted-foreground mt-1">
                                {template.description}
                              </div>
                            )}
                          </div>
                          <Badge variant="secondary">
                            {template.component_definitions.length} items
                          </Badge>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}

              {filteredTemplates.length === 0 && (
                <div className="text-center text-muted-foreground py-8">
                  No templates found
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

---

### Task 13.8: Seed Assembly Templates

Create `backend/app/scripts/seed_assembly_templates.py`:

```python
"""Seed assembly templates into the database."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.assembly import AssemblyTemplate
from app.data.assembly_templates import CONCRETE_ASSEMBLY_TEMPLATES


async def seed_templates():
    """Seed assembly templates into the database."""
    settings = get_settings()
    
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        for template_data in CONCRETE_ASSEMBLY_TEMPLATES:
            # Check if template already exists
            existing = await session.execute(
                select(AssemblyTemplate).where(
                    AssemblyTemplate.name == template_data["name"],
                    AssemblyTemplate.is_system == True,
                )
            )
            if existing.scalar_one_or_none():
                print(f"Template already exists: {template_data['name']}")
                continue
            
            template = AssemblyTemplate(
                name=template_data["name"],
                description=template_data.get("description"),
                scope=template_data.get("scope", "concrete"),
                category=template_data.get("category"),
                subcategory=template_data.get("subcategory"),
                csi_code=template_data.get("csi_code"),
                csi_description=template_data.get("csi_description"),
                measurement_type=template_data.get("measurement_type", "area"),
                expected_unit=template_data.get("expected_unit", "SF"),
                default_waste_percent=template_data.get("default_waste_percent", 5),
                productivity_rate=template_data.get("productivity_rate"),
                productivity_unit=template_data.get("productivity_unit"),
                crew_size=template_data.get("crew_size"),
                is_system=True,
                component_definitions=template_data.get("component_definitions", []),
            )
            
            session.add(template)
            print(f"Added template: {template_data['name']}")
        
        await session.commit()
        print("Done seeding templates!")


if __name__ == "__main__":
    asyncio.run(seed_templates())
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] Assembly model created with all fields
- [ ] Component model created with formula support
- [ ] Formula engine evaluates expressions correctly
- [ ] Assembly service calculates quantities and costs
- [ ] Assembly templates seeded in database
- [ ] API endpoints work for CRUD operations
- [ ] Frontend displays assembly with grouped components
- [ ] Cost summary shows correct totals
- [ ] Waste factors applied correctly
- [ ] Markup (O&P) calculations work
- [ ] Assembly can be locked/unlocked
- [ ] Components can be added/removed/reordered
- [ ] Formula presets available
- [ ] Template selector shows relevant templates

### Test Cases

1. Create assembly from template → components created with formulas
2. Change takeoff quantity → recalculate → all component quantities update
3. Add waste factor → extended cost increases proportionally
4. Add overhead and profit → sell price calculated correctly
5. Lock assembly → editing blocked
6. Validate formula with test values → correct result
7. Invalid formula → validation error returned
8. Duplicate assembly → new assembly created with same components

---

## Next Phase

Once verified, proceed to **`14-AUTO-COUNT.md`** for implementing similarity-based object counting.
