# Phase 4B: Review Interface
## Human Review and Refinement UI

> **Duration**: Weeks 20-26
> **Prerequisites**: AI takeoff generation working (Phase 4A)
> **Outcome**: Complete review workflow with approval, rejection, editing, and QA verification

---

## Context for LLM Assistant

You are implementing the human review interface for a construction takeoff platform. This phase enables:
- Side-by-side comparison of AI-generated measurements with original drawings
- Approve/reject individual measurements
- Edit and refine AI-generated geometry
- QA verification workflow for quality control
- Bulk operations for efficient review

### Review Workflow

```
1. AI generates measurements (Phase 4A)
2. Estimator reviews each measurement
   - Approve: Mark as verified
   - Reject: Delete measurement
   - Edit: Modify geometry/quantity
3. QA reviewer verifies estimator's work
4. Export approved takeoff
```

### Measurement States

| State | Description | Who Sets |
|-------|-------------|----------|
| `pending` | AI-generated, not reviewed | System |
| `approved` | Estimator approved | Estimator |
| `rejected` | Estimator rejected (deleted) | Estimator |
| `modified` | Estimator edited geometry | Estimator |
| `verified` | QA reviewer verified | QA Reviewer |
| `flagged` | QA flagged for re-review | QA Reviewer |

---

## Database Updates

### Task 9.1: Add Review Fields to Models

Update `backend/app/models/measurement.py`:

```python
"""Updated Measurement model with review fields."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import String, Float, Integer, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.condition import Condition
    from app.models.page import Page


class Measurement(Base, UUIDMixin, TimestampMixin):
    """Individual measurement (geometric shape) on a page."""

    __tablename__ = "measurements"

    # Foreign keys
    condition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conditions.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Geometry
    geometry_type: Mapped[str] = mapped_column(String(50), nullable=False)
    geometry_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    # Calculated values
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    pixel_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    pixel_area: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # AI generation tracking
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Review status
    review_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )  # pending, approved, modified, verified, flagged
    
    # Estimator review
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # QA verification
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Original geometry (for tracking changes)
    original_geometry: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    original_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Flags
    is_modified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    condition: Mapped["Condition"] = relationship("Condition", back_populates="measurements")
    page: Mapped["Page"] = relationship("Page", back_populates="measurements")
```

Create migration:

```bash
alembic revision --autogenerate -m "add_review_fields_to_measurements"
alembic upgrade head
```

---

### Task 9.2: Review Statistics Model

Create `backend/app/models/review_session.py`:

```python
"""Review session tracking model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ReviewSession(Base, UUIDMixin, TimestampMixin):
    """Tracks a review session for analytics and audit."""

    __tablename__ = "review_sessions"

    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Session info
    reviewer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reviewer_role: Mapped[str] = mapped_column(
        String(50),
        default="estimator",
    )  # estimator, qa_reviewer
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Statistics
    measurements_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    measurements_approved: Mapped[int] = mapped_column(Integer, default=0)
    measurements_rejected: Mapped[int] = mapped_column(Integer, default=0)
    measurements_modified: Mapped[int] = mapped_column(Integer, default=0)
    measurements_flagged: Mapped[int] = mapped_column(Integer, default=0)
    
    # AI accuracy tracking
    ai_measurements_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    ai_measurements_accepted: Mapped[int] = mapped_column(Integer, default=0)
    ai_accuracy_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    session_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
```

---

## Review Service

### Task 9.3: Review Service Implementation

Create `backend/app/services/review_service.py`:

```python
"""Review service for measurement approval and verification."""

import uuid
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.measurement import Measurement
from app.models.condition import Condition
from app.models.review_session import ReviewSession
from app.services.measurement_engine import get_measurement_engine

logger = structlog.get_logger()


class ReviewService:
    """Service for reviewing and verifying measurements."""

    async def approve_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        reviewer_name: str,
        notes: str | None = None,
    ) -> Measurement:
        """Approve a measurement (estimator review).
        
        Args:
            session: Database session
            measurement_id: Measurement to approve
            reviewer_name: Name of reviewer
            notes: Optional review notes
            
        Returns:
            Updated measurement
        """
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        measurement.review_status = "approved"
        measurement.reviewed_by = reviewer_name
        measurement.reviewed_at = datetime.utcnow()
        measurement.review_notes = notes
        
        await session.commit()
        await session.refresh(measurement)
        
        logger.info(
            "Measurement approved",
            measurement_id=str(measurement_id),
            reviewer=reviewer_name,
        )
        
        return measurement

    async def reject_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        reviewer_name: str,
        reason: str | None = None,
    ) -> None:
        """Reject and delete a measurement.
        
        Args:
            session: Database session
            measurement_id: Measurement to reject
            reviewer_name: Name of reviewer
            reason: Reason for rejection
        """
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        condition_id = measurement.condition_id
        
        logger.info(
            "Measurement rejected",
            measurement_id=str(measurement_id),
            reviewer=reviewer_name,
            reason=reason,
        )
        
        await session.delete(measurement)
        
        # Update condition totals
        condition = await session.get(Condition, condition_id)
        if condition:
            await self._update_condition_totals(session, condition)
        
        await session.commit()

    async def modify_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        geometry_data: dict[str, Any],
        reviewer_name: str,
        notes: str | None = None,
    ) -> Measurement:
        """Modify a measurement's geometry.
        
        Args:
            session: Database session
            measurement_id: Measurement to modify
            geometry_data: New geometry data
            reviewer_name: Name of reviewer
            notes: Optional notes
            
        Returns:
            Updated measurement
        """
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        # Store original if not already stored
        if not measurement.original_geometry:
            measurement.original_geometry = measurement.geometry_data
            measurement.original_quantity = measurement.quantity
        
        # Use measurement engine to recalculate
        engine = get_measurement_engine()
        measurement = await engine.update_measurement(
            session=session,
            measurement_id=measurement_id,
            geometry_data=geometry_data,
            notes=notes,
        )
        
        # Update review status
        measurement.review_status = "modified"
        measurement.is_modified = True
        measurement.reviewed_by = reviewer_name
        measurement.reviewed_at = datetime.utcnow()
        measurement.review_notes = notes
        
        await session.commit()
        await session.refresh(measurement)
        
        logger.info(
            "Measurement modified",
            measurement_id=str(measurement_id),
            reviewer=reviewer_name,
        )
        
        return measurement

    async def verify_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        verifier_name: str,
        notes: str | None = None,
    ) -> Measurement:
        """QA verify a measurement.
        
        Args:
            session: Database session
            measurement_id: Measurement to verify
            verifier_name: Name of QA verifier
            notes: Optional verification notes
            
        Returns:
            Updated measurement
        """
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        if measurement.review_status not in ("approved", "modified"):
            raise ValueError("Measurement must be approved before verification")
        
        measurement.review_status = "verified"
        measurement.is_verified = True
        measurement.verified_by = verifier_name
        measurement.verified_at = datetime.utcnow()
        measurement.verification_notes = notes
        
        await session.commit()
        await session.refresh(measurement)
        
        logger.info(
            "Measurement verified",
            measurement_id=str(measurement_id),
            verifier=verifier_name,
        )
        
        return measurement

    async def flag_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        verifier_name: str,
        reason: str,
    ) -> Measurement:
        """Flag a measurement for re-review.
        
        Args:
            session: Database session
            measurement_id: Measurement to flag
            verifier_name: Name of QA verifier
            reason: Reason for flagging
            
        Returns:
            Updated measurement
        """
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        measurement.review_status = "flagged"
        measurement.is_flagged = True
        measurement.flag_reason = reason
        measurement.verified_by = verifier_name
        measurement.verified_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(measurement)
        
        logger.info(
            "Measurement flagged",
            measurement_id=str(measurement_id),
            verifier=verifier_name,
            reason=reason,
        )
        
        return measurement

    async def bulk_approve(
        self,
        session: AsyncSession,
        measurement_ids: list[uuid.UUID],
        reviewer_name: str,
    ) -> dict[str, Any]:
        """Bulk approve multiple measurements.
        
        Returns:
            Summary of operation
        """
        approved_count = 0
        errors = []
        
        for mid in measurement_ids:
            try:
                await self.approve_measurement(session, mid, reviewer_name)
                approved_count += 1
            except Exception as e:
                errors.append({"measurement_id": str(mid), "error": str(e)})
        
        return {
            "approved_count": approved_count,
            "error_count": len(errors),
            "errors": errors,
        }

    async def bulk_verify(
        self,
        session: AsyncSession,
        measurement_ids: list[uuid.UUID],
        verifier_name: str,
    ) -> dict[str, Any]:
        """Bulk verify multiple measurements.
        
        Returns:
            Summary of operation
        """
        verified_count = 0
        errors = []
        
        for mid in measurement_ids:
            try:
                await self.verify_measurement(session, mid, verifier_name)
                verified_count += 1
            except Exception as e:
                errors.append({"measurement_id": str(mid), "error": str(e)})
        
        return {
            "verified_count": verified_count,
            "error_count": len(errors),
            "errors": errors,
        }

    async def get_review_statistics(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Get review statistics for a project.
        
        Returns:
            Statistics dictionary
        """
        # Get counts by status
        result = await session.execute(
            select(
                Measurement.review_status,
                func.count(Measurement.id),
            )
            .join(Condition)
            .where(Condition.project_id == project_id)
            .group_by(Measurement.review_status)
        )
        status_counts = {row[0]: row[1] for row in result.all()}
        
        # Get AI accuracy stats
        result = await session.execute(
            select(
                func.count(Measurement.id).filter(Measurement.is_ai_generated == True),
                func.count(Measurement.id).filter(
                    and_(
                        Measurement.is_ai_generated == True,
                        Measurement.review_status.in_(["approved", "verified"]),
                    )
                ),
                func.count(Measurement.id).filter(
                    and_(
                        Measurement.is_ai_generated == True,
                        Measurement.is_modified == True,
                    )
                ),
            )
            .join(Condition)
            .where(Condition.project_id == project_id)
        )
        ai_stats = result.one()
        
        ai_total = ai_stats[0]
        ai_accepted = ai_stats[1]
        ai_modified = ai_stats[2]
        
        return {
            "status_counts": status_counts,
            "total_measurements": sum(status_counts.values()),
            "pending_review": status_counts.get("pending", 0),
            "approved": status_counts.get("approved", 0),
            "modified": status_counts.get("modified", 0),
            "verified": status_counts.get("verified", 0),
            "flagged": status_counts.get("flagged", 0),
            "ai_statistics": {
                "total_ai_generated": ai_total,
                "ai_accepted_as_is": ai_accepted - ai_modified,
                "ai_modified": ai_modified,
                "ai_accuracy_rate": (ai_accepted / ai_total * 100) if ai_total > 0 else 0,
            },
        }

    async def get_pending_review_items(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
        page_id: uuid.UUID | None = None,
        condition_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[Measurement]:
        """Get measurements pending review.
        
        Args:
            session: Database session
            project_id: Project ID
            page_id: Optional filter by page
            condition_id: Optional filter by condition
            limit: Maximum items to return
            
        Returns:
            List of pending measurements
        """
        query = (
            select(Measurement)
            .join(Condition)
            .where(Condition.project_id == project_id)
            .where(Measurement.review_status == "pending")
        )
        
        if page_id:
            query = query.where(Measurement.page_id == page_id)
        if condition_id:
            query = query.where(Measurement.condition_id == condition_id)
        
        query = query.order_by(Measurement.created_at).limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_flagged_items(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
    ) -> list[Measurement]:
        """Get all flagged measurements for a project."""
        result = await session.execute(
            select(Measurement)
            .join(Condition)
            .where(Condition.project_id == project_id)
            .where(Measurement.is_flagged == True)
            .order_by(Measurement.verified_at.desc())
        )
        return list(result.scalars().all())

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
            ).where(Measurement.condition_id == condition.id)
        )
        row = result.one()
        
        condition.total_quantity = row[0] or 0.0
        condition.measurement_count = row[1] or 0


# Singleton
_service: ReviewService | None = None


def get_review_service() -> ReviewService:
    """Get the review service singleton."""
    global _service
    if _service is None:
        _service = ReviewService()
    return _service
```

---

## API Endpoints

### Task 9.4: Review API Routes

Create `backend/app/api/routes/review.py`:

```python
"""Review endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.measurement import Measurement
from app.models.condition import Condition
from app.models.project import Project
from app.schemas.review import (
    ApproveRequest,
    RejectRequest,
    ModifyRequest,
    VerifyRequest,
    FlagRequest,
    BulkApproveRequest,
    BulkVerifyRequest,
    ReviewStatisticsResponse,
    PendingReviewResponse,
)
from app.services.review_service import get_review_service

router = APIRouter()


@router.post("/measurements/{measurement_id}/approve")
async def approve_measurement(
    measurement_id: uuid.UUID,
    request: ApproveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Approve a measurement (estimator review)."""
    service = get_review_service()
    
    try:
        measurement = await service.approve_measurement(
            session=db,
            measurement_id=measurement_id,
            reviewer_name=request.reviewer_name,
            notes=request.notes,
        )
        return {
            "status": "approved",
            "measurement_id": str(measurement_id),
            "reviewed_by": measurement.reviewed_by,
            "reviewed_at": measurement.reviewed_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/measurements/{measurement_id}/reject")
async def reject_measurement(
    measurement_id: uuid.UUID,
    request: RejectRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reject and delete a measurement."""
    service = get_review_service()
    
    try:
        await service.reject_measurement(
            session=db,
            measurement_id=measurement_id,
            reviewer_name=request.reviewer_name,
            reason=request.reason,
        )
        return {
            "status": "rejected",
            "measurement_id": str(measurement_id),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/measurements/{measurement_id}/modify")
async def modify_measurement(
    measurement_id: uuid.UUID,
    request: ModifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Modify a measurement's geometry."""
    service = get_review_service()
    
    try:
        measurement = await service.modify_measurement(
            session=db,
            measurement_id=measurement_id,
            geometry_data=request.geometry_data,
            reviewer_name=request.reviewer_name,
            notes=request.notes,
        )
        return {
            "status": "modified",
            "measurement_id": str(measurement_id),
            "new_quantity": measurement.quantity,
            "reviewed_by": measurement.reviewed_by,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/measurements/{measurement_id}/verify")
async def verify_measurement(
    measurement_id: uuid.UUID,
    request: VerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """QA verify a measurement."""
    service = get_review_service()
    
    try:
        measurement = await service.verify_measurement(
            session=db,
            measurement_id=measurement_id,
            verifier_name=request.verifier_name,
            notes=request.notes,
        )
        return {
            "status": "verified",
            "measurement_id": str(measurement_id),
            "verified_by": measurement.verified_by,
            "verified_at": measurement.verified_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/measurements/{measurement_id}/flag")
async def flag_measurement(
    measurement_id: uuid.UUID,
    request: FlagRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Flag a measurement for re-review."""
    service = get_review_service()
    
    try:
        measurement = await service.flag_measurement(
            session=db,
            measurement_id=measurement_id,
            verifier_name=request.verifier_name,
            reason=request.reason,
        )
        return {
            "status": "flagged",
            "measurement_id": str(measurement_id),
            "flag_reason": measurement.flag_reason,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/projects/{project_id}/bulk-approve")
async def bulk_approve_measurements(
    project_id: uuid.UUID,
    request: BulkApproveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Bulk approve multiple measurements."""
    service = get_review_service()
    
    result = await service.bulk_approve(
        session=db,
        measurement_ids=request.measurement_ids,
        reviewer_name=request.reviewer_name,
    )
    
    return result


@router.post("/projects/{project_id}/bulk-verify")
async def bulk_verify_measurements(
    project_id: uuid.UUID,
    request: BulkVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Bulk verify multiple measurements."""
    service = get_review_service()
    
    result = await service.bulk_verify(
        session=db,
        measurement_ids=request.measurement_ids,
        verifier_name=request.verifier_name,
    )
    
    return result


@router.get("/projects/{project_id}/review-statistics", response_model=ReviewStatisticsResponse)
async def get_review_statistics(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get review statistics for a project."""
    # Verify project exists
    result = await db.execute(select(Project.id).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    service = get_review_service()
    stats = await service.get_review_statistics(db, project_id)
    
    return stats


@router.get("/projects/{project_id}/pending-review", response_model=PendingReviewResponse)
async def get_pending_review(
    project_id: uuid.UUID,
    page_id: uuid.UUID | None = None,
    condition_id: uuid.UUID | None = None,
    limit: int = 50,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get measurements pending review."""
    service = get_review_service()
    
    measurements = await service.get_pending_review_items(
        session=db,
        project_id=project_id,
        page_id=page_id,
        condition_id=condition_id,
        limit=limit,
    )
    
    return {
        "measurements": measurements,
        "total": len(measurements),
    }


@router.get("/projects/{project_id}/flagged")
async def get_flagged_measurements(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all flagged measurements for a project."""
    service = get_review_service()
    
    measurements = await service.get_flagged_items(db, project_id)
    
    return {
        "measurements": [
            {
                "id": str(m.id),
                "condition_id": str(m.condition_id),
                "page_id": str(m.page_id),
                "quantity": m.quantity,
                "unit": m.unit,
                "flag_reason": m.flag_reason,
                "flagged_by": m.verified_by,
                "flagged_at": m.verified_at.isoformat() if m.verified_at else None,
            }
            for m in measurements
        ],
        "total": len(measurements),
    }
```

---

### Task 9.5: Review Schemas

Create `backend/app/schemas/review.py`:

```python
"""Review schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ApproveRequest(BaseModel):
    """Request to approve a measurement."""
    
    reviewer_name: str = Field(..., min_length=1)
    notes: str | None = None


class RejectRequest(BaseModel):
    """Request to reject a measurement."""
    
    reviewer_name: str = Field(..., min_length=1)
    reason: str | None = None


class ModifyRequest(BaseModel):
    """Request to modify a measurement."""
    
    reviewer_name: str = Field(..., min_length=1)
    geometry_data: dict[str, Any]
    notes: str | None = None


class VerifyRequest(BaseModel):
    """Request to verify a measurement (QA)."""
    
    verifier_name: str = Field(..., min_length=1)
    notes: str | None = None


class FlagRequest(BaseModel):
    """Request to flag a measurement for re-review."""
    
    verifier_name: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class BulkApproveRequest(BaseModel):
    """Request for bulk approval."""
    
    measurement_ids: list[uuid.UUID]
    reviewer_name: str = Field(..., min_length=1)


class BulkVerifyRequest(BaseModel):
    """Request for bulk verification."""
    
    measurement_ids: list[uuid.UUID]
    verifier_name: str = Field(..., min_length=1)


class AIStatistics(BaseModel):
    """AI accuracy statistics."""
    
    total_ai_generated: int
    ai_accepted_as_is: int
    ai_modified: int
    ai_accuracy_rate: float


class ReviewStatisticsResponse(BaseModel):
    """Review statistics response."""
    
    status_counts: dict[str, int]
    total_measurements: int
    pending_review: int
    approved: int
    modified: int
    verified: int
    flagged: int
    ai_statistics: AIStatistics


class MeasurementReviewItem(BaseModel):
    """Measurement item for review lists."""
    
    id: uuid.UUID
    condition_id: uuid.UUID
    page_id: uuid.UUID
    geometry_type: str
    quantity: float
    unit: str
    is_ai_generated: bool
    ai_confidence: float | None
    review_status: str
    created_at: datetime


class PendingReviewResponse(BaseModel):
    """Pending review items response."""
    
    measurements: list[MeasurementReviewItem]
    total: int
```

---

## Frontend Components

### Task 9.6: Side-by-Side Review Panel

Create `frontend/src/components/review/ReviewPanel.tsx`:

```tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Check,
  X,
  Flag,
  ChevronLeft,
  ChevronRight,
  Edit,
  Eye,
  AlertTriangle,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { apiClient } from '@/api/client';
import { cn } from '@/lib/utils';

interface ReviewPanelProps {
  projectId: string;
  pageId: string;
  conditionId?: string;
  reviewerName: string;
  mode: 'estimator' | 'qa';
  onMeasurementSelect: (id: string) => void;
}

interface PendingMeasurement {
  id: string;
  condition_id: string;
  page_id: string;
  geometry_type: string;
  quantity: number;
  unit: string;
  is_ai_generated: boolean;
  ai_confidence: number | null;
  review_status: string;
}

export function ReviewPanel({
  projectId,
  pageId,
  conditionId,
  reviewerName,
  mode,
  onMeasurementSelect,
}: ReviewPanelProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showFlagDialog, setShowFlagDialog] = useState(false);
  const [flagReason, setFlagReason] = useState('');
  const [notes, setNotes] = useState('');

  const queryClient = useQueryClient();

  const { data: pendingData, isLoading } = useQuery({
    queryKey: ['pending-review', projectId, pageId, conditionId],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (pageId) params.append('page_id', pageId);
      if (conditionId) params.append('condition_id', conditionId);
      
      const response = await apiClient.get(
        `/projects/${projectId}/pending-review?${params}`
      );
      return response.data as { measurements: PendingMeasurement[]; total: number };
    },
  });

  const { data: statsData } = useQuery({
    queryKey: ['review-stats', projectId],
    queryFn: async () => {
      const response = await apiClient.get(
        `/projects/${projectId}/review-statistics`
      );
      return response.data;
    },
  });

  const approveMutation = useMutation({
    mutationFn: async (measurementId: string) => {
      await apiClient.post(`/measurements/${measurementId}/approve`, {
        reviewer_name: reviewerName,
        notes: notes || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-review'] });
      queryClient.invalidateQueries({ queryKey: ['review-stats'] });
      queryClient.invalidateQueries({ queryKey: ['measurements'] });
      setNotes('');
      goToNext();
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async (measurementId: string) => {
      await apiClient.post(`/measurements/${measurementId}/reject`, {
        reviewer_name: reviewerName,
        reason: notes || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-review'] });
      queryClient.invalidateQueries({ queryKey: ['review-stats'] });
      queryClient.invalidateQueries({ queryKey: ['measurements'] });
      setNotes('');
      goToNext();
    },
  });

  const verifyMutation = useMutation({
    mutationFn: async (measurementId: string) => {
      await apiClient.post(`/measurements/${measurementId}/verify`, {
        verifier_name: reviewerName,
        notes: notes || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-review'] });
      queryClient.invalidateQueries({ queryKey: ['review-stats'] });
      setNotes('');
      goToNext();
    },
  });

  const flagMutation = useMutation({
    mutationFn: async (measurementId: string) => {
      await apiClient.post(`/measurements/${measurementId}/flag`, {
        verifier_name: reviewerName,
        reason: flagReason,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-review'] });
      queryClient.invalidateQueries({ queryKey: ['review-stats'] });
      setShowFlagDialog(false);
      setFlagReason('');
      goToNext();
    },
  });

  const measurements = pendingData?.measurements || [];
  const currentMeasurement = measurements[currentIndex];

  const goToNext = () => {
    if (currentIndex < measurements.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const goToPrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  // Select measurement for highlighting
  if (currentMeasurement) {
    onMeasurementSelect(currentMeasurement.id);
  }

  if (isLoading) {
    return <div className="p-4 text-center">Loading review items...</div>;
  }

  if (measurements.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <Check className="h-8 w-8 mx-auto mb-2 text-green-500" />
        <p>All measurements reviewed!</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Statistics Header */}
      {statsData && (
        <div className="p-3 border-b bg-muted/50">
          <div className="grid grid-cols-4 gap-2 text-center text-sm">
            <div>
              <div className="font-semibold">{statsData.pending_review}</div>
              <div className="text-xs text-muted-foreground">Pending</div>
            </div>
            <div>
              <div className="font-semibold text-green-600">{statsData.approved}</div>
              <div className="text-xs text-muted-foreground">Approved</div>
            </div>
            <div>
              <div className="font-semibold text-blue-600">{statsData.verified}</div>
              <div className="text-xs text-muted-foreground">Verified</div>
            </div>
            <div>
              <div className="font-semibold text-amber-600">{statsData.flagged}</div>
              <div className="text-xs text-muted-foreground">Flagged</div>
            </div>
          </div>
          
          {statsData.ai_statistics && statsData.ai_statistics.total_ai_generated > 0 && (
            <div className="mt-2 text-xs text-center text-muted-foreground">
              AI Accuracy: {statsData.ai_statistics.ai_accuracy_rate.toFixed(1)}%
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between p-2 border-b">
        <Button
          variant="ghost"
          size="icon"
          onClick={goToPrevious}
          disabled={currentIndex === 0}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="text-sm">
          {currentIndex + 1} of {measurements.length}
        </span>
        <Button
          variant="ghost"
          size="icon"
          onClick={goToNext}
          disabled={currentIndex === measurements.length - 1}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Current Measurement Details */}
      {currentMeasurement && (
        <div className="flex-1 overflow-auto p-3 space-y-3">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant={currentMeasurement.is_ai_generated ? 'secondary' : 'outline'}>
                {currentMeasurement.is_ai_generated ? 'AI Generated' : 'Manual'}
              </Badge>
              {currentMeasurement.ai_confidence && (
                <Badge variant="outline">
                  {(currentMeasurement.ai_confidence * 100).toFixed(0)}% confidence
                </Badge>
              )}
            </div>

            <div className="bg-muted p-3 rounded-lg space-y-1">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Type</span>
                <span className="font-medium">{currentMeasurement.geometry_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Quantity</span>
                <span className="font-medium">
                  {currentMeasurement.quantity.toFixed(2)} {currentMeasurement.unit}
                </span>
              </div>
            </div>

            <div>
              <label className="text-sm text-muted-foreground">Notes (optional)</label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add review notes..."
                className="mt-1"
                rows={2}
              />
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {currentMeasurement && (
        <div className="p-3 border-t space-y-2">
          {mode === 'estimator' ? (
            <>
              <div className="flex gap-2">
                <Button
                  className="flex-1"
                  variant="default"
                  onClick={() => approveMutation.mutate(currentMeasurement.id)}
                  disabled={approveMutation.isPending}
                >
                  <Check className="h-4 w-4 mr-1" />
                  Approve
                </Button>
                <Button
                  className="flex-1"
                  variant="destructive"
                  onClick={() => rejectMutation.mutate(currentMeasurement.id)}
                  disabled={rejectMutation.isPending}
                >
                  <X className="h-4 w-4 mr-1" />
                  Reject
                </Button>
              </div>
              <Button
                className="w-full"
                variant="outline"
                onClick={() => {
                  // TODO: Open edit mode
                }}
              >
                <Edit className="h-4 w-4 mr-1" />
                Edit Geometry
              </Button>
            </>
          ) : (
            <>
              <div className="flex gap-2">
                <Button
                  className="flex-1"
                  variant="default"
                  onClick={() => verifyMutation.mutate(currentMeasurement.id)}
                  disabled={verifyMutation.isPending}
                >
                  <Check className="h-4 w-4 mr-1" />
                  Verify
                </Button>
                <Button
                  className="flex-1"
                  variant="outline"
                  onClick={() => setShowFlagDialog(true)}
                >
                  <Flag className="h-4 w-4 mr-1" />
                  Flag
                </Button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Flag Dialog */}
      <Dialog open={showFlagDialog} onOpenChange={setShowFlagDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Flag for Re-Review</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <label className="text-sm font-medium">Reason</label>
            <Textarea
              value={flagReason}
              onChange={(e) => setFlagReason(e.target.value)}
              placeholder="Why does this need re-review?"
              className="mt-1"
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFlagDialog(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => currentMeasurement && flagMutation.mutate(currentMeasurement.id)}
              disabled={!flagReason || flagMutation.isPending}
            >
              Flag Measurement
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
```

---

### Task 9.7: Side-by-Side Comparison View

Create `frontend/src/components/review/SideBySideView.tsx`:

```tsx
import { useState, useRef, useEffect } from 'react';
import { Stage, Layer, Image as KonvaImage, Rect } from 'react-konva';
import { ZoomIn, ZoomOut, Move, Maximize2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { MeasurementLayer } from '@/components/viewer/MeasurementLayer';

interface SideBySideViewProps {
  pageImageUrl: string;
  pageWidth: number;
  pageHeight: number;
  measurements: any[];
  conditions: Map<string, any>;
  highlightedMeasurementId: string | null;
  onMeasurementClick: (id: string) => void;
}

export function SideBySideView({
  pageImageUrl,
  pageWidth,
  pageHeight,
  measurements,
  conditions,
  highlightedMeasurementId,
  onMeasurementClick,
}: SideBySideViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ width: 800, height: 600 });
  const [zoom, setZoom] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [syncedPosition, setSyncedPosition] = useState({ x: 0, y: 0 });

  // Load image
  useEffect(() => {
    const img = new window.Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => setImage(img);
    img.src = pageImageUrl;
  }, [pageImageUrl]);

  // Resize observer
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setContainerSize({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Calculate scale to fit
  const halfWidth = containerSize.width / 2 - 10;
  const scaleToFit = Math.min(
    halfWidth / pageWidth,
    containerSize.height / pageHeight
  );

  // Sync positions between panels
  const handleDragEnd = (e: any) => {
    const newPos = { x: e.target.x(), y: e.target.y() };
    setPosition(newPos);
    setSyncedPosition(newPos);
  };

  const handleWheel = (e: any) => {
    e.evt.preventDefault();
    const scaleBy = 1.1;
    const newZoom = e.evt.deltaY > 0 ? zoom / scaleBy : zoom * scaleBy;
    setZoom(Math.max(0.1, Math.min(5, newZoom)));
  };

  const resetView = () => {
    setZoom(1);
    setPosition({ x: 0, y: 0 });
    setSyncedPosition({ x: 0, y: 0 });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-2 p-2 border-b">
        <Button variant="outline" size="icon" onClick={() => setZoom(zoom * 1.2)}>
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button variant="outline" size="icon" onClick={() => setZoom(zoom / 1.2)}>
          <ZoomOut className="h-4 w-4" />
        </Button>
        <div className="w-32">
          <Slider
            value={[zoom * 100]}
            min={10}
            max={500}
            step={10}
            onValueChange={([value]) => setZoom(value / 100)}
          />
        </div>
        <span className="text-sm text-muted-foreground w-16">
          {(zoom * 100).toFixed(0)}%
        </span>
        <Button variant="outline" size="icon" onClick={resetView}>
          <Maximize2 className="h-4 w-4" />
        </Button>
      </div>

      {/* Side by side panels */}
      <div ref={containerRef} className="flex-1 flex">
        {/* Left panel - Original drawing */}
        <div className="flex-1 border-r relative">
          <div className="absolute top-2 left-2 z-10 bg-background/80 px-2 py-1 rounded text-sm">
            Original Drawing
          </div>
          <Stage
            width={halfWidth}
            height={containerSize.height}
            scaleX={scaleToFit * zoom}
            scaleY={scaleToFit * zoom}
            x={syncedPosition.x}
            y={syncedPosition.y}
            draggable
            onDragEnd={handleDragEnd}
            onWheel={handleWheel}
          >
            <Layer>
              {image && (
                <KonvaImage
                  image={image}
                  width={pageWidth}
                  height={pageHeight}
                />
              )}
            </Layer>
          </Stage>
        </div>

        {/* Right panel - With measurements */}
        <div className="flex-1 relative">
          <div className="absolute top-2 left-2 z-10 bg-background/80 px-2 py-1 rounded text-sm">
            With Measurements
          </div>
          <Stage
            width={halfWidth}
            height={containerSize.height}
            scaleX={scaleToFit * zoom}
            scaleY={scaleToFit * zoom}
            x={syncedPosition.x}
            y={syncedPosition.y}
            draggable
            onDragEnd={handleDragEnd}
            onWheel={handleWheel}
          >
            <Layer>
              {image && (
                <KonvaImage
                  image={image}
                  width={pageWidth}
                  height={pageHeight}
                />
              )}
            </Layer>
            <MeasurementLayer
              measurements={measurements}
              conditions={conditions}
              selectedMeasurementId={highlightedMeasurementId}
              onMeasurementSelect={onMeasurementClick}
              onMeasurementUpdate={() => {}}
              isEditing={false}
              scale={scaleToFit * zoom}
            />
            {/* Highlight box for current measurement */}
            {highlightedMeasurementId && (
              <Layer>
                <HighlightBox
                  measurement={measurements.find(m => m.id === highlightedMeasurementId)}
                />
              </Layer>
            )}
          </Stage>
        </div>
      </div>
    </div>
  );
}

function HighlightBox({ measurement }: { measurement: any }) {
  if (!measurement) return null;

  // Calculate bounding box based on geometry
  const bbox = calculateBoundingBox(measurement.geometry_data, measurement.geometry_type);
  if (!bbox) return null;

  const padding = 20;

  return (
    <Rect
      x={bbox.x - padding}
      y={bbox.y - padding}
      width={bbox.width + padding * 2}
      height={bbox.height + padding * 2}
      stroke="#FFD700"
      strokeWidth={3}
      dash={[10, 5]}
      fill="rgba(255, 215, 0, 0.1)"
    />
  );
}

function calculateBoundingBox(geometryData: any, geometryType: string) {
  let points: { x: number; y: number }[] = [];

  if (geometryType === 'polygon' || geometryType === 'polyline') {
    points = geometryData.points || [];
  } else if (geometryType === 'line') {
    points = [geometryData.start, geometryData.end];
  } else if (geometryType === 'rectangle') {
    return {
      x: geometryData.x,
      y: geometryData.y,
      width: geometryData.width,
      height: geometryData.height,
    };
  } else if (geometryType === 'circle') {
    return {
      x: geometryData.center.x - geometryData.radius,
      y: geometryData.center.y - geometryData.radius,
      width: geometryData.radius * 2,
      height: geometryData.radius * 2,
    };
  } else if (geometryType === 'point') {
    return {
      x: geometryData.x - 10,
      y: geometryData.y - 10,
      width: 20,
      height: 20,
    };
  }

  if (points.length === 0) return null;

  const xs = points.map(p => p.x);
  const ys = points.map(p => p.y);

  return {
    x: Math.min(...xs),
    y: Math.min(...ys),
    width: Math.max(...xs) - Math.min(...xs),
    height: Math.max(...ys) - Math.min(...ys),
  };
}
```

---

### Task 9.8: Review Workspace Page

Create `frontend/src/pages/ReviewWorkspace.tsx`:

```tsx
import { useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

import { Layout } from '@/components/layout/Layout';
import { PageBrowser } from '@/components/document/PageBrowser';
import { ReviewPanel } from '@/components/review/ReviewPanel';
import { SideBySideView } from '@/components/review/SideBySideView';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { apiClient } from '@/api/client';

export function ReviewWorkspace() {
  const { projectId, documentId } = useParams();
  const [searchParams] = useSearchParams();
  
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null);
  const [selectedConditionId, setSelectedConditionId] = useState<string | null>(null);
  const [highlightedMeasurementId, setHighlightedMeasurementId] = useState<string | null>(null);
  const [reviewMode, setReviewMode] = useState<'estimator' | 'qa'>('estimator');
  const [reviewerName, setReviewerName] = useState('Estimator'); // TODO: Get from auth

  // Fetch page data
  const { data: pageData } = useQuery({
    queryKey: ['page', selectedPageId],
    queryFn: async () => {
      if (!selectedPageId) return null;
      const response = await apiClient.get(`/pages/${selectedPageId}`);
      return response.data;
    },
    enabled: !!selectedPageId,
  });

  // Fetch measurements for page
  const { data: measurementsData } = useQuery({
    queryKey: ['measurements', selectedPageId],
    queryFn: async () => {
      if (!selectedPageId) return { measurements: [] };
      const response = await apiClient.get(`/pages/${selectedPageId}/measurements`);
      return response.data;
    },
    enabled: !!selectedPageId,
  });

  // Fetch conditions for project
  const { data: conditionsData } = useQuery({
    queryKey: ['conditions', projectId],
    queryFn: async () => {
      const response = await apiClient.get(`/projects/${projectId}/conditions`);
      return response.data;
    },
    enabled: !!projectId,
  });

  const conditions = new Map(
    (conditionsData?.conditions || []).map((c: any) => [c.id, c])
  );

  return (
    <Layout>
      <div className="flex h-[calc(100vh-64px)]">
        {/* Left sidebar - Page browser */}
        <div className="w-64 border-r flex flex-col">
          <div className="p-3 border-b">
            <h2 className="font-semibold">Pages</h2>
          </div>
          {documentId && (
            <PageBrowser
              documentId={documentId}
              onPageSelect={setSelectedPageId}
              selectedPageId={selectedPageId || undefined}
            />
          )}
        </div>

        {/* Main content - Side by side view */}
        <div className="flex-1 flex flex-col">
          {/* Toolbar */}
          <div className="flex items-center gap-4 p-3 border-b">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Mode:</span>
              <Select
                value={reviewMode}
                onValueChange={(v) => setReviewMode(v as any)}
              >
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="estimator">Estimator</SelectItem>
                  <SelectItem value="qa">QA Review</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Condition:</span>
              <Select
                value={selectedConditionId || 'all'}
                onValueChange={(v) => setSelectedConditionId(v === 'all' ? null : v)}
              >
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="All conditions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All conditions</SelectItem>
                  {(conditionsData?.conditions || []).map((c: any) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Side by side viewer */}
          {selectedPageId && pageData ? (
            <SideBySideView
              pageImageUrl={pageData.image_url}
              pageWidth={pageData.width}
              pageHeight={pageData.height}
              measurements={measurementsData?.measurements || []}
              conditions={conditions}
              highlightedMeasurementId={highlightedMeasurementId}
              onMeasurementClick={setHighlightedMeasurementId}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              Select a page to begin review
            </div>
          )}
        </div>

        {/* Right sidebar - Review panel */}
        <div className="w-80 border-l">
          {projectId && selectedPageId && (
            <ReviewPanel
              projectId={projectId}
              pageId={selectedPageId}
              conditionId={selectedConditionId || undefined}
              reviewerName={reviewerName}
              mode={reviewMode}
              onMeasurementSelect={setHighlightedMeasurementId}
            />
          )}
        </div>
      </div>
    </Layout>
  );
}
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] Approve measurement updates status to "approved"
- [ ] Reject measurement deletes it from database
- [ ] Modify measurement stores original and updates geometry
- [ ] Verify measurement (QA) updates status to "verified"
- [ ] Flag measurement marks for re-review with reason
- [ ] Bulk approve works for multiple measurements
- [ ] Bulk verify works for multiple measurements
- [ ] Review statistics calculated correctly
- [ ] AI accuracy tracking works
- [ ] Side-by-side view syncs pan/zoom between panels
- [ ] Highlighted measurement shows bounding box
- [ ] Review panel navigates through pending items
- [ ] Estimator and QA modes show appropriate actions

### Test Cases

1. Generate AI measurements â†’ review panel shows them as pending
2. Approve a measurement â†’ status changes, statistics update
3. Reject a measurement â†’ deleted from list
4. Modify geometry â†’ original stored, new quantity calculated
5. QA verify approved measurement â†’ status changes to verified
6. QA flag measurement â†’ appears in flagged list
7. Check AI accuracy after reviewing 10 AI measurements

---

## Next Phase

Once verified, proceed to **`10-EXPORT-SYSTEM.md`** for implementing Excel and OST export functionality.
