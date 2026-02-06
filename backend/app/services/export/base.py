"""Base export service with shared query logic."""

import abc
import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.condition import Condition
from app.models.measurement import Measurement
from app.models.page import Page
from app.models.project import Project

logger = structlog.get_logger()


@dataclass
class MeasurementData:
    """Flat measurement data for export."""

    id: uuid.UUID
    condition_name: str
    condition_id: uuid.UUID
    page_id: uuid.UUID
    page_number: int
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


async def fetch_export_data(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    include_unverified: bool = True,
) -> ExportData:
    """Fetch all project data needed for export.

    Args:
        db: Async database session
        project_id: Project UUID
        include_unverified: Whether to include unverified measurements

    Returns:
        ExportData with all conditions and measurements
    """
    # Fetch project
    proj_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        raise ValueError(f"Project not found: {project_id}")

    # Fetch conditions with measurements and their pages
    cond_query = (
        select(Condition)
        .where(Condition.project_id == project_id)
        .options(
            selectinload(Condition.measurements).joinedload(Measurement.page)
        )
        .order_by(Condition.sort_order, Condition.name)
    )
    cond_result = await db.execute(cond_query)
    conditions = cond_result.scalars().unique().all()

    condition_data_list = []
    for cond in conditions:
        measurements = []
        for m in cond.measurements:
            if not include_unverified and not m.is_verified:
                continue
            measurements.append(
                MeasurementData(
                    id=m.id,
                    condition_name=cond.name,
                    condition_id=cond.id,
                    page_id=m.page_id,
                    page_number=m.page.page_number if m.page else 0,
                    sheet_number=m.page.sheet_number if m.page else None,
                    sheet_title=m.page.sheet_title if m.page else None,
                    geometry_type=m.geometry_type,
                    geometry_data=m.geometry_data,
                    quantity=m.quantity,
                    unit=m.unit,
                    pixel_length=m.pixel_length,
                    pixel_area=m.pixel_area,
                    is_ai_generated=m.is_ai_generated,
                    is_verified=m.is_verified,
                    notes=m.notes,
                )
            )

        condition_data_list.append(
            ConditionData(
                id=cond.id,
                name=cond.name,
                description=cond.description,
                scope=cond.scope,
                category=cond.category,
                measurement_type=cond.measurement_type,
                color=cond.color,
                unit=cond.unit,
                depth=cond.depth,
                thickness=cond.thickness,
                total_quantity=cond.total_quantity,
                measurement_count=cond.measurement_count,
                building=cond.building,
                area=cond.area,
                elevation=cond.elevation,
                measurements=measurements,
            )
        )

    return ExportData(
        project_id=project.id,
        project_name=project.name,
        project_description=project.description,
        client_name=project.client_name,
        conditions=condition_data_list,
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
