"""Base export service with shared query logic."""

import abc
import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class MeasurementData:
    """Flat measurement data for export."""

    id: uuid.UUID
    condition_name: str
    condition_id: uuid.UUID
    page_id: uuid.UUID
    page_number: int | None
    sheet_number: str | None
    sheet_title: str | None
    geometry_type: str
    geometry_data: dict[str, Any]
    quantity: float
    unit: str
    pixel_length: float | None
    pixel_area: float | None
    is_ai_generated: bool
    is_verified: bool
    notes: str | None


@dataclass
class AssemblyCostData:
    """Assembly cost summary for export."""

    material_cost: float
    labor_cost: float
    equipment_cost: float
    subcontract_cost: float
    other_cost: float
    total_cost: float
    unit_cost: float
    total_labor_hours: float
    overhead_percent: float
    profit_percent: float
    total_with_markup: float


@dataclass
class ConditionData:
    """Condition with its measurements for export."""

    id: uuid.UUID
    name: str
    description: str | None
    scope: str
    category: str | None
    measurement_type: str
    color: str
    unit: str
    depth: float | None
    thickness: float | None
    total_quantity: float
    measurement_count: int
    building: str | None
    area: str | None
    elevation: str | None
    assembly_cost: AssemblyCostData | None = None
    measurements: list[MeasurementData] = field(default_factory=list)


@dataclass
class ExportData:
    """All project data needed for export."""

    project_id: uuid.UUID
    project_name: str
    project_description: str | None
    client_name: str | None
    conditions: list[ConditionData]

    @property
    def all_measurements(self) -> list[MeasurementData]:
        """Get all measurements across all conditions."""
        result = []
        for condition in self.conditions:
            result.extend(condition.measurements)
        return result

    @property
    def total_project_cost(self) -> float:
        """Sum of total_with_markup across all conditions with assemblies."""
        return sum(
            c.assembly_cost.total_with_markup
            for c in self.conditions
            if c.assembly_cost
        )


# Unit abbreviation map
UNIT_DISPLAY = {
    "LF": "LF",
    "SF": "SF",
    "CY": "CY",
    "EA": "EA",
}


def format_unit(unit: str) -> str:
    """Return display abbreviation for a unit."""
    return UNIT_DISPLAY.get(unit, unit)


_FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')


def sanitize_field(value: str) -> str:
    """Prefix fields that could be interpreted as formulas by spreadsheet software."""
    if value and value[0] in _FORMULA_PREFIXES:
        return "'" + value
    return value


class BaseExporter(abc.ABC):
    """Abstract base class for export format implementations."""

    @abc.abstractmethod
    def generate(self, data: ExportData, options: dict | None = None) -> bytes:
        """Generate export file bytes from project data.

        Args:
            data: Export data containing conditions and measurements
            options: Format-specific options

        Returns:
            Generated file content as bytes
        """
        ...

    @property
    @abc.abstractmethod
    def content_type(self) -> str:
        """MIME content type for the export format."""
        ...

    @property
    @abc.abstractmethod
    def file_extension(self) -> str:
        """File extension for the export format."""
        ...
