"""Measurement engine service."""

import uuid
from typing import Any

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.condition import Condition
from app.models.measurement import Measurement
from app.models.page import Page
from app.utils.geometry import MeasurementCalculator

logger = structlog.get_logger()


class MeasurementEngine:
    """Service for creating and managing measurements."""
    
    GEOMETRY_TYPES = ["line", "polyline", "polygon", "rectangle", "circle", "point"]
    MEASUREMENT_TYPES = ["linear", "area", "volume", "count"]
    
    UNIT_MAP = {
        "linear": "LF",
        "area": "SF",
        "volume": "CY",
        "count": "EA",
    }

    async def create_measurement(
        self,
        session: AsyncSession,
        condition_id: uuid.UUID,
        page_id: uuid.UUID,
        geometry_type: str,
        geometry_data: dict[str, Any],
        is_ai_generated: bool = False,
        ai_confidence: float | None = None,
        notes: str | None = None,
    ) -> Measurement:
        """Create a new measurement.
        
        Args:
            session: Database session
            condition_id: Parent condition ID
            page_id: Page where measurement is drawn
            geometry_type: Type of geometry
            geometry_data: Geometry coordinates
            is_ai_generated: Whether created by AI
            ai_confidence: AI confidence score
            notes: Optional notes
            
        Returns:
            Created Measurement
        """
        # Validate geometry type
        if geometry_type not in self.GEOMETRY_TYPES:
            raise ValueError(f"Invalid geometry type: {geometry_type}")
        
        # Get condition and page
        condition = await session.get(Condition, condition_id)
        if not condition:
            raise ValueError(f"Condition not found: {condition_id}")
        
        page = await session.get(Page, page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        if not page.scale_calibrated or not page.scale_value:
            raise ValueError("Page scale not calibrated")
        
        # Calculate measurement
        calculator = MeasurementCalculator(page.scale_value)
        calculation = self._calculate_geometry(
            calculator,
            geometry_type,
            geometry_data,
            condition.depth,
        )
        
        # Determine quantity based on measurement type
        quantity = self._extract_quantity(
            calculation,
            condition.measurement_type,
        )
        
        # Create measurement
        measurement = Measurement(
            condition_id=condition_id,
            page_id=page_id,
            geometry_type=geometry_type,
            geometry_data=geometry_data,
            quantity=quantity,
            unit=condition.unit,
            pixel_length=calculation.get("pixel_length"),
            pixel_area=calculation.get("pixel_area"),
            is_ai_generated=is_ai_generated,
            ai_confidence=ai_confidence,
            notes=notes,
            extra_metadata={"calculation": calculation},
        )
        
        session.add(measurement)
        
        # Update condition totals
        await self._update_condition_totals(session, condition)
        
        await session.commit()
        await session.refresh(measurement)
        
        return measurement

    async def update_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        geometry_data: dict[str, Any] | None = None,
        notes: str | None = None,
    ) -> Measurement:
        """Update an existing measurement.
        
        Args:
            session: Database session
            measurement_id: Measurement to update
            geometry_data: New geometry (optional)
            notes: New notes (optional)
            
        Returns:
            Updated Measurement
        """
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        if geometry_data:
            # Get page for scale
            page = await session.get(Page, measurement.page_id)
            condition = await session.get(Condition, measurement.condition_id)
            
            if not page.scale_value:
                raise ValueError("Page scale not calibrated")
            
            # Recalculate
            calculator = MeasurementCalculator(page.scale_value)
            calculation = self._calculate_geometry(
                calculator,
                measurement.geometry_type,
                geometry_data,
                condition.depth,
            )
            
            measurement.geometry_data = geometry_data
            measurement.quantity = self._extract_quantity(
                calculation,
                condition.measurement_type,
            )
            measurement.unit = condition.unit
            measurement.pixel_length = calculation.get("pixel_length")
            measurement.pixel_area = calculation.get("pixel_area")
            measurement.extra_metadata = {"calculation": calculation}
            measurement.is_modified = True
        
        if notes is not None:
            measurement.notes = notes
        
        # Update condition totals
        condition = await session.get(Condition, measurement.condition_id)
        await self._update_condition_totals(session, condition)
        
        await session.commit()
        await session.refresh(measurement)
        
        return measurement

    async def delete_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
    ) -> None:
        """Delete a measurement."""
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        condition_id = measurement.condition_id
        
        await session.delete(measurement)
        
        # Update condition totals
        condition = await session.get(Condition, condition_id)
        if condition:
            await self._update_condition_totals(session, condition)
        
        await session.commit()

    async def recalculate_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
    ) -> Measurement:
        """Recalculate a measurement (e.g., after scale change)."""
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        page = await session.get(Page, measurement.page_id)
        condition = await session.get(Condition, measurement.condition_id)
        
        if not page.scale_value:
            raise ValueError("Page scale not calibrated")
        
        calculator = MeasurementCalculator(page.scale_value)
        calculation = self._calculate_geometry(
            calculator,
            measurement.geometry_type,
            measurement.geometry_data,
            condition.depth,
        )
        
        measurement.quantity = self._extract_quantity(
            calculation,
            condition.measurement_type,
        )
        measurement.unit = condition.unit
        measurement.pixel_length = calculation.get("pixel_length")
        measurement.pixel_area = calculation.get("pixel_area")
        measurement.extra_metadata = {"calculation": calculation}
        
        await self._update_condition_totals(session, condition)
        
        await session.commit()
        await session.refresh(measurement)
        
        return measurement

    def _calculate_geometry(
        self,
        calculator: MeasurementCalculator,
        geometry_type: str,
        geometry_data: dict[str, Any],
        depth: float | None,
    ) -> dict[str, Any]:
        """Calculate measurements for a geometry."""
        if geometry_type == "line":
            return calculator.calculate_line(
                geometry_data["start"],
                geometry_data["end"],
            )
        elif geometry_type == "polyline":
            return calculator.calculate_polyline(geometry_data["points"])
        elif geometry_type == "polygon":
            return calculator.calculate_polygon(
                geometry_data["points"],
                depth,
            )
        elif geometry_type == "rectangle":
            return calculator.calculate_rectangle(
                geometry_data["x"],
                geometry_data["y"],
                geometry_data["width"],
                geometry_data["height"],
                depth,
            )
        elif geometry_type == "circle":
            return calculator.calculate_circle(
                geometry_data["center"],
                geometry_data["radius"],
                depth,
            )
        elif geometry_type == "point":
            return calculator.calculate_count(
                geometry_data["x"],
                geometry_data["y"],
            )
        else:
            raise ValueError(f"Unknown geometry type: {geometry_type}")

    def _extract_quantity(
        self,
        calculation: dict[str, Any],
        measurement_type: str,
    ) -> float:
        """Extract the relevant quantity from calculation results."""
        if measurement_type == "linear":
            return calculation.get("length_feet", calculation.get("perimeter_lf", 0))
        elif measurement_type == "area":
            return calculation.get("area_sf", 0)
        elif measurement_type == "volume":
            return calculation.get("volume_cy", 0)
        elif measurement_type == "count":
            return calculation.get("count", 1)
        else:
            raise ValueError(f"Unknown measurement type: {measurement_type}")

    async def _update_condition_totals(
        self,
        session: AsyncSession,
        condition: Condition,
    ) -> None:
        """Update condition's denormalized totals."""
        result = await session.execute(
            select(
                func.sum(Measurement.quantity),
                func.count(Measurement.id),
            ).where(
                Measurement.condition_id == condition.id,
                Measurement.is_rejected == False,
            )
        )
        row = result.one()
        
        condition.total_quantity = row[0] or 0.0
        condition.measurement_count = row[1] or 0


# Singleton
_engine: MeasurementEngine | None = None


def get_measurement_engine() -> MeasurementEngine:
    """Get the measurement engine singleton."""
    global _engine
    if _engine is None:
        _engine = MeasurementEngine()
    return _engine
