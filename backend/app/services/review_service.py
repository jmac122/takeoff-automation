"""Review service for measurement review workflow."""

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.condition import Condition
from app.models.measurement import Measurement
from app.models.measurement_history import MeasurementHistory
from app.models.page import Page
from app.services.measurement_engine import get_measurement_engine
from app.utils.geometry import MeasurementCalculator

logger = structlog.get_logger()


class ReviewService:
    """Service for reviewing AI-generated measurements."""

    def _derive_status(self, measurement: Measurement) -> str:
        """Derive the review status string from measurement booleans."""
        if measurement.is_rejected:
            return "rejected"
        if measurement.is_verified and measurement.is_modified:
            return "modified"
        if measurement.is_verified:
            return "approved"
        return "pending"

    async def approve_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        reviewer: str,
        notes: str | None = None,
    ) -> Measurement:
        """Approve a measurement.

        Args:
            session: Database session
            measurement_id: Measurement to approve
            reviewer: Name of the reviewer
            notes: Optional review notes

        Returns:
            Updated Measurement
        """
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")

        previous_status = self._derive_status(measurement)

        # Set approved state
        measurement.is_verified = True
        measurement.is_rejected = False
        measurement.rejection_reason = None
        measurement.reviewed_at = datetime.now(timezone.utc)
        if notes:
            measurement.review_notes = notes

        # Create history record
        history = MeasurementHistory(
            measurement_id=measurement_id,
            action="approved",
            actor=reviewer,
            actor_type="user",
            previous_status=previous_status,
            new_status="approved",
            notes=notes,
            change_description=f"Measurement approved by {reviewer}",
        )
        session.add(history)

        # Update condition totals (in case it was previously rejected)
        condition = await session.get(Condition, measurement.condition_id)
        engine = get_measurement_engine()
        await engine._update_condition_totals(session, condition)

        await session.commit()
        await session.refresh(measurement)

        logger.info(
            "measurement_approved",
            measurement_id=str(measurement_id),
            reviewer=reviewer,
        )

        return measurement

    async def reject_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        reviewer: str,
        reason: str,
    ) -> Measurement:
        """Reject a measurement (soft-delete).

        Args:
            session: Database session
            measurement_id: Measurement to reject
            reviewer: Name of the reviewer
            reason: Reason for rejection (required)

        Returns:
            Updated Measurement
        """
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")

        previous_status = self._derive_status(measurement)

        # Set rejected state
        measurement.is_rejected = True
        measurement.is_verified = False
        measurement.rejection_reason = reason
        measurement.reviewed_at = datetime.now(timezone.utc)

        # Create history record
        history = MeasurementHistory(
            measurement_id=measurement_id,
            action="rejected",
            actor=reviewer,
            actor_type="user",
            previous_status=previous_status,
            new_status="rejected",
            notes=reason,
            change_description=f"Measurement rejected by {reviewer}: {reason}",
        )
        session.add(history)

        # Update condition totals to exclude rejected measurement
        condition = await session.get(Condition, measurement.condition_id)
        engine = get_measurement_engine()
        await engine._update_condition_totals(session, condition)

        await session.commit()
        await session.refresh(measurement)

        logger.info(
            "measurement_rejected",
            measurement_id=str(measurement_id),
            reviewer=reviewer,
            reason=reason,
        )

        return measurement

    async def modify_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        reviewer: str,
        geometry_data: dict[str, Any],
        notes: str | None = None,
    ) -> Measurement:
        """Modify a measurement's geometry during review.

        Args:
            session: Database session
            measurement_id: Measurement to modify
            reviewer: Name of the reviewer
            geometry_data: New geometry data
            notes: Optional notes

        Returns:
            Updated Measurement with recalculated quantity
        """
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")

        previous_status = self._derive_status(measurement)
        previous_quantity = measurement.quantity
        previous_geometry = measurement.geometry_data

        # Store originals on first modification only
        if measurement.original_geometry is None:
            measurement.original_geometry = measurement.geometry_data
            measurement.original_quantity = measurement.quantity

        # Get page and condition for recalculation
        page = await session.get(Page, measurement.page_id)
        condition = await session.get(Condition, measurement.condition_id)

        if not page or not page.scale_value:
            raise ValueError("Page scale not calibrated")
        if not condition:
            raise ValueError(f"Condition not found: {measurement.condition_id}")

        # Recalculate with new geometry
        engine = get_measurement_engine()
        calculator = MeasurementCalculator(page.scale_value)
        calculation = engine._calculate_geometry(
            calculator,
            measurement.geometry_type,
            geometry_data,
            condition.depth,
        )
        new_quantity = engine._extract_quantity(calculation, condition.measurement_type)

        # Update measurement
        measurement.geometry_data = geometry_data
        measurement.quantity = new_quantity
        measurement.pixel_length = calculation.get("pixel_length")
        measurement.pixel_area = calculation.get("pixel_area")
        measurement.extra_metadata = {"calculation": calculation}
        measurement.is_modified = True
        measurement.is_verified = True
        measurement.is_rejected = False
        measurement.reviewed_at = datetime.now(timezone.utc)
        if notes:
            measurement.review_notes = notes

        # Create history record
        history = MeasurementHistory(
            measurement_id=measurement_id,
            action="modified",
            actor=reviewer,
            actor_type="user",
            previous_status=previous_status,
            new_status="modified",
            previous_geometry=previous_geometry,
            new_geometry=geometry_data,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            notes=notes,
            change_description=f"Measurement modified by {reviewer}: quantity {previous_quantity:.2f} -> {new_quantity:.2f}",
        )
        session.add(history)

        # Update condition totals
        await engine._update_condition_totals(session, condition)

        await session.commit()
        await session.refresh(measurement)

        logger.info(
            "measurement_modified",
            measurement_id=str(measurement_id),
            reviewer=reviewer,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
        )

        return measurement

    async def auto_accept_batch(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
        threshold: float = 0.90,
        reviewer: str | None = None,
    ) -> int:
        """Auto-accept high-confidence AI measurements for a project.

        Args:
            session: Database session
            project_id: Project to process
            threshold: Minimum confidence threshold (default 0.90)
            reviewer: Optional reviewer name

        Returns:
            Count of auto-accepted measurements
        """
        actor = reviewer or "system"

        # Find eligible measurements
        result = await session.execute(
            select(Measurement)
            .join(Condition, Measurement.condition_id == Condition.id)
            .where(
                and_(
                    Condition.project_id == project_id,
                    Measurement.is_ai_generated == True,
                    Measurement.ai_confidence >= threshold,
                    Measurement.is_verified == False,
                    Measurement.is_rejected == False,
                )
            )
        )
        measurements = result.scalars().all()

        count = 0
        condition_ids = set()

        for measurement in measurements:
            previous_status = self._derive_status(measurement)

            measurement.is_verified = True
            measurement.reviewed_at = datetime.now(timezone.utc)

            history = MeasurementHistory(
                measurement_id=measurement.id,
                action="auto_accepted",
                actor=actor,
                actor_type="auto_accept",
                previous_status=previous_status,
                new_status="approved",
                change_description=f"Auto-accepted with confidence {measurement.ai_confidence:.2f} >= {threshold:.2f}",
            )
            session.add(history)
            condition_ids.add(measurement.condition_id)
            count += 1

        # Update condition totals for all affected conditions
        engine = get_measurement_engine()
        for condition_id in condition_ids:
            condition = await session.get(Condition, condition_id)
            if condition:
                await engine._update_condition_totals(session, condition)

        await session.commit()

        logger.info(
            "measurements_auto_accepted",
            project_id=str(project_id),
            threshold=threshold,
            count=count,
        )

        return count

    async def get_review_stats(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Get review statistics for a project.

        Args:
            session: Database session
            project_id: Project ID

        Returns:
            Dictionary with review statistics
        """
        # Base query: all measurements for this project
        base = (
            select(Measurement)
            .join(Condition, Measurement.condition_id == Condition.id)
            .where(Condition.project_id == project_id)
        )

        # Aggregate counts using case expressions
        result = await session.execute(
            select(
                func.count(Measurement.id).label("total"),
                func.sum(
                    case(
                        (
                            and_(
                                Measurement.is_verified == False,
                                Measurement.is_rejected == False,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("pending"),
                func.sum(
                    case(
                        (
                            and_(
                                Measurement.is_verified == True,
                                Measurement.is_rejected == False,
                                Measurement.is_modified == False,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("approved"),
                func.sum(case((Measurement.is_rejected == True, 1), else_=0)).label(
                    "rejected"
                ),
                func.sum(
                    case(
                        (
                            and_(
                                Measurement.is_modified == True,
                                Measurement.is_verified == True,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("modified"),
                func.sum(case((Measurement.is_ai_generated == True, 1), else_=0)).label(
                    "ai_generated_count"
                ),
                # AI accuracy: approved AI measurements / total AI measurements
                func.sum(
                    case(
                        (
                            and_(
                                Measurement.is_ai_generated == True,
                                Measurement.is_verified == True,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("ai_approved"),
                # Confidence distribution
                func.sum(
                    case(
                        (
                            and_(
                                Measurement.is_ai_generated == True,
                                Measurement.ai_confidence >= 0.9,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("confidence_high"),
                func.sum(
                    case(
                        (
                            and_(
                                Measurement.is_ai_generated == True,
                                Measurement.ai_confidence >= 0.7,
                                Measurement.ai_confidence < 0.9,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("confidence_medium"),
                func.sum(
                    case(
                        (
                            and_(
                                Measurement.is_ai_generated == True,
                                Measurement.ai_confidence < 0.7,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("confidence_low"),
            )
            .join(Condition, Measurement.condition_id == Condition.id)
            .where(Condition.project_id == project_id)
        )

        row = result.one()

        total = row.total or 0
        ai_generated = row.ai_generated_count or 0
        ai_approved = row.ai_approved or 0
        ai_accuracy = (ai_approved / ai_generated * 100) if ai_generated > 0 else 0.0

        return {
            "total": total,
            "pending": row.pending or 0,
            "approved": row.approved or 0,
            "rejected": row.rejected or 0,
            "modified": row.modified or 0,
            "ai_generated_count": ai_generated,
            "ai_accuracy_percent": round(ai_accuracy, 1),
            "confidence_distribution": {
                "high": row.confidence_high or 0,
                "medium": row.confidence_medium or 0,
                "low": row.confidence_low or 0,
            },
        }

    async def get_next_unreviewed(
        self,
        session: AsyncSession,
        page_id: uuid.UUID,
        after_id: uuid.UUID | None = None,
    ) -> tuple[Measurement | None, int]:
        """Get the next unreviewed measurement on a page.

        Args:
            session: Database session
            page_id: Page to search
            after_id: Skip past this measurement ID

        Returns:
            Tuple of (next measurement or None, remaining unreviewed count)
        """
        # Base filter for unreviewed measurements on this page
        base_filter = and_(
            Measurement.page_id == page_id,
            Measurement.is_verified == False,
            Measurement.is_rejected == False,
        )

        # Count remaining
        count_result = await session.execute(
            select(func.count(Measurement.id)).where(base_filter)
        )
        remaining_count = count_result.scalar() or 0

        # Build query for next measurement, ordered by confidence ASC (lowest first)
        query = (
            select(Measurement)
            .where(base_filter)
            .order_by(
                Measurement.ai_confidence.asc().nulls_last(),
                Measurement.created_at.asc(),
            )
            .limit(1)
        )

        # If after_id specified, skip past it by finding its position
        if after_id:
            after_measurement = await session.get(Measurement, after_id)
            if after_measurement and after_measurement.ai_confidence is not None:
                # Get measurements after the current one
                query = (
                    select(Measurement)
                    .where(
                        and_(
                            base_filter,
                            Measurement.id != after_id,
                        )
                    )
                    .order_by(
                        Measurement.ai_confidence.asc().nulls_last(),
                        Measurement.created_at.asc(),
                    )
                    .limit(1)
                )
            else:
                query = (
                    select(Measurement)
                    .where(
                        and_(
                            base_filter,
                            Measurement.id != after_id,
                        )
                    )
                    .order_by(
                        Measurement.ai_confidence.asc().nulls_last(),
                        Measurement.created_at.asc(),
                    )
                    .limit(1)
                )

        result = await session.execute(query)
        next_measurement = result.scalar_one_or_none()

        return next_measurement, remaining_count

    async def get_measurement_history(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
    ) -> list[MeasurementHistory]:
        """Get the audit history for a measurement.

        Args:
            session: Database session
            measurement_id: Measurement ID

        Returns:
            List of history entries, newest first
        """
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")

        result = await session.execute(
            select(MeasurementHistory)
            .where(MeasurementHistory.measurement_id == measurement_id)
            .order_by(MeasurementHistory.created_at.desc())
        )

        return list(result.scalars().all())


# Singleton
_service: ReviewService | None = None


def get_review_service() -> ReviewService:
    """Get the review service singleton."""
    global _service
    if _service is None:
        _service = ReviewService()
    return _service
