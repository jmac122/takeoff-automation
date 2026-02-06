# Phase 4B Enhanced: Review Interface
## Human QA Workflow with Efficiency Optimizations

> **Duration**: Weeks 20-26
> **Prerequisites**: AI takeoff generation working (Phase 4A)
> **Outcome**: Efficient review interface with keyboard navigation, auto-accept, and productivity tools

---

## Context for LLM Assistant

You are implementing an enhanced review interface for AI-generated measurements. This builds on the base review workflow with efficiency features inspired by professional takeoff tools like Kreo.net.

### Review Workflow Overview

AI generates measurements with confidence scores. Humans review them:

```
AI Detection (75% accurate)
    ↓
┌─────────────────────────────────────────────────────┐
│  REVIEW QUEUE                                        │
│  ┌─────────────────────────────────────────────────┐│
│  │ High Confidence (>90%)  → Auto-Accept Option    ││
│  │ Medium Confidence (70-90%) → Quick Review       ││
│  │ Low Confidence (<70%)   → Detailed Review       ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  REVIEWER ACTIONS                                    │
│  [A] Approve  [R] Reject  [E] Edit  [N] Next [P] Prev│
│  [1-9] Quick confidence override                     │
│  [Space] Toggle selection  [Enter] Confirm batch     │
└─────────────────────────────────────────────────────┘
    ↓
Verified Measurements → Export
```

### Key Enhancement Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Auto-Accept Threshold** | Auto-approve detections >90% confidence | Reduce review time 50%+ |
| **Keyboard Shortcuts** | A/R/E/N/P for rapid navigation | 3x faster than mouse |
| **Confidence Filtering** | Show lowest confidence first | Focus on problem areas |
| **Quick Adjust Tools** | Nudge, snap, extend with keys | Precise edits without dialogs |
| **Batch Operations** | Select multiple, apply action | Handle groups efficiently |
| **Split View Comparison** | AI vs Final side-by-side | Verify changes visually |
| **Measurement History** | Full audit trail | Track who changed what |

---

## Database Model Enhancements

### Task 9.1: Enhanced Measurement Model

Update `backend/app/models/measurement.py`:

```python
"""Enhanced measurement model with review tracking."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    String, Float, Integer, Boolean, ForeignKey, Text,
    Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.condition import Condition
    from app.models.page import Page


class ReviewStatus(str):
    """Review status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    MODIFIED = "modified"
    REJECTED = "rejected"
    VERIFIED = "verified"
    FLAGGED = "flagged"


class Measurement(Base, UUIDMixin, TimestampMixin):
    """
    A measurement taken from a construction plan.
    
    Enhanced with comprehensive review tracking fields.
    """

    __tablename__ = "measurements"
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_measurements_review_status', 'review_status'),
        Index('ix_measurements_ai_confidence', 'ai_confidence'),
        Index('ix_measurements_condition_status', 'condition_id', 'review_status'),
    )

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
    geometry_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Calculated values
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # AI generation info
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # ===== REVIEW FIELDS (Enhanced) =====
    
    # Review status
    review_status: Mapped[str] = mapped_column(
        String(50),
        default=ReviewStatus.PENDING,
        index=True,
    )
    
    # Who reviewed and when
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Second-level verification (QA)
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Store original AI geometry before human edits
    original_geometry: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    original_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Rejection/flag info
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    flag_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    flag_priority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Review notes
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Auto-accept tracking
    was_auto_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_accept_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Edit tracking
    edit_count: Mapped[int] = mapped_column(Integer, default=0)
    last_edited_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_edited_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Geometry change tracking
    geometry_changes: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    
    # Display properties
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    condition: Mapped["Condition"] = relationship("Condition", back_populates="measurements")
    page: Mapped["Page"] = relationship("Page", back_populates="measurements")
    history: Mapped[list["MeasurementHistory"]] = relationship(
        "MeasurementHistory",
        back_populates="measurement",
        cascade="all, delete-orphan",
        order_by="MeasurementHistory.created_at.desc()",
    )


class MeasurementHistory(Base, UUIDMixin, TimestampMixin):
    """
    Audit trail for measurement changes.
    
    Records every change to a measurement for compliance and debugging.
    """

    __tablename__ = "measurement_history"

    measurement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("measurements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # What changed
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    # created, approved, rejected, modified, verified, flagged, unflagged
    
    # Who made the change
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(50), default="user")
    # user, system, auto_accept
    
    # Previous and new values
    previous_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # For geometry changes
    previous_geometry: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_geometry: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    previous_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Change details
    change_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Context
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Metadata
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    measurement: Mapped["Measurement"] = relationship(
        "Measurement",
        back_populates="history",
    )


class ReviewSession(Base, UUIDMixin, TimestampMixin):
    """
    A review session for tracking reviewer productivity.
    
    Groups review actions into sessions for analytics.
    """

    __tablename__ = "review_sessions"

    # Session info
    reviewer: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Statistics
    measurements_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    measurements_approved: Mapped[int] = mapped_column(Integer, default=0)
    measurements_rejected: Mapped[int] = mapped_column(Integer, default=0)
    measurements_modified: Mapped[int] = mapped_column(Integer, default=0)
    measurements_flagged: Mapped[int] = mapped_column(Integer, default=0)
    
    # Auto-accept stats
    auto_accepted_count: Mapped[int] = mapped_column(Integer, default=0)
    auto_accept_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Time tracking
    total_review_time_seconds: Mapped[int] = mapped_column(Integer, default=0)
    avg_time_per_measurement_seconds: Mapped[float] = mapped_column(Float, default=0)
    
    # Session settings used
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

---

### Task 9.2: Review Service

Create `backend/app/services/review_service.py`:

```python
"""Review service for measurement QA workflow."""

import uuid
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.measurement import (
    Measurement, MeasurementHistory, ReviewSession, ReviewStatus
)
from app.models.condition import Condition
from app.models.page import Page

logger = structlog.get_logger()


class ReviewService:
    """Service for managing measurement review workflow."""
    
    async def get_review_queue(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
        filters: dict[str, Any] | None = None,
        sort_by: str = "confidence_asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Measurement], int]:
        """
        Get measurements pending review.
        
        Args:
            session: Database session
            project_id: Project to get measurements for
            filters: Optional filters (status, confidence_range, page_id, etc.)
            sort_by: Sort order (confidence_asc, confidence_desc, created_at, page_order)
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            Tuple of (measurements, total_count)
        """
        filters = filters or {}
        
        # Base query - join through condition to get project measurements
        query = (
            select(Measurement)
            .join(Condition)
            .where(Condition.project_id == project_id)
        )
        
        # Apply filters
        if filters.get("status"):
            if isinstance(filters["status"], list):
                query = query.where(Measurement.review_status.in_(filters["status"]))
            else:
                query = query.where(Measurement.review_status == filters["status"])
        
        if filters.get("min_confidence") is not None:
            query = query.where(Measurement.ai_confidence >= filters["min_confidence"])
        
        if filters.get("max_confidence") is not None:
            query = query.where(Measurement.ai_confidence <= filters["max_confidence"])
        
        if filters.get("page_id"):
            query = query.where(Measurement.page_id == filters["page_id"])
        
        if filters.get("condition_id"):
            query = query.where(Measurement.condition_id == filters["condition_id"])
        
        if filters.get("is_ai_generated") is not None:
            query = query.where(Measurement.is_ai_generated == filters["is_ai_generated"])
        
        if filters.get("is_flagged"):
            query = query.where(Measurement.review_status == ReviewStatus.FLAGGED)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_query)).scalar()
        
        # Apply sorting
        if sort_by == "confidence_asc":
            query = query.order_by(Measurement.ai_confidence.asc().nulls_last())
        elif sort_by == "confidence_desc":
            query = query.order_by(Measurement.ai_confidence.desc().nulls_first())
        elif sort_by == "created_at":
            query = query.order_by(Measurement.created_at.desc())
        elif sort_by == "page_order":
            query = query.join(Page).order_by(Page.page_number, Measurement.sort_order)
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        # Execute
        result = await session.execute(query)
        measurements = result.scalars().all()
        
        return list(measurements), total
    
    async def approve_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        reviewer: str,
        notes: str | None = None,
    ) -> Measurement:
        """Approve a measurement."""
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        previous_status = measurement.review_status
        
        measurement.review_status = ReviewStatus.APPROVED
        measurement.reviewed_by = reviewer
        measurement.reviewed_at = datetime.utcnow()
        measurement.review_notes = notes
        
        # Record history
        history = MeasurementHistory(
            measurement_id=measurement_id,
            action="approved",
            actor=reviewer,
            actor_type="user",
            previous_status=previous_status,
            new_status=ReviewStatus.APPROVED,
            change_description="Measurement approved by reviewer",
        )
        session.add(history)
        
        await session.commit()
        await session.refresh(measurement)
        
        logger.info(
            "Measurement approved",
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
        """Reject a measurement."""
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        previous_status = measurement.review_status
        
        measurement.review_status = ReviewStatus.REJECTED
        measurement.reviewed_by = reviewer
        measurement.reviewed_at = datetime.utcnow()
        measurement.rejection_reason = reason
        
        # Record history
        history = MeasurementHistory(
            measurement_id=measurement_id,
            action="rejected",
            actor=reviewer,
            actor_type="user",
            previous_status=previous_status,
            new_status=ReviewStatus.REJECTED,
            change_description=f"Measurement rejected: {reason}",
            change_reason=reason,
        )
        session.add(history)
        
        await session.commit()
        await session.refresh(measurement)
        
        return measurement
    
    async def modify_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        reviewer: str,
        new_geometry: dict,
        new_quantity: float | None = None,
        notes: str | None = None,
    ) -> Measurement:
        """Modify a measurement's geometry."""
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        previous_status = measurement.review_status
        previous_geometry = measurement.geometry_data.copy()
        previous_quantity = measurement.quantity
        
        # Store original if first modification
        if measurement.original_geometry is None:
            measurement.original_geometry = previous_geometry
            measurement.original_quantity = previous_quantity
        
        # Track geometry changes
        change_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "actor": reviewer,
            "previous": previous_geometry,
            "new": new_geometry,
        }
        
        if measurement.geometry_changes:
            measurement.geometry_changes.append(change_record)
        else:
            measurement.geometry_changes = [change_record]
        
        # Update measurement
        measurement.geometry_data = new_geometry
        if new_quantity is not None:
            measurement.quantity = new_quantity
        
        measurement.review_status = ReviewStatus.MODIFIED
        measurement.reviewed_by = reviewer
        measurement.reviewed_at = datetime.utcnow()
        measurement.edit_count += 1
        measurement.last_edited_by = reviewer
        measurement.last_edited_at = datetime.utcnow()
        measurement.review_notes = notes
        
        # Record history
        history = MeasurementHistory(
            measurement_id=measurement_id,
            action="modified",
            actor=reviewer,
            actor_type="user",
            previous_status=previous_status,
            new_status=ReviewStatus.MODIFIED,
            previous_geometry=previous_geometry,
            new_geometry=new_geometry,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity or measurement.quantity,
            change_description="Geometry modified by reviewer",
            change_reason=notes,
        )
        session.add(history)
        
        await session.commit()
        await session.refresh(measurement)
        
        return measurement
    
    async def verify_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        verifier: str,
        notes: str | None = None,
    ) -> Measurement:
        """Second-level verification of a measurement."""
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        if measurement.review_status not in (ReviewStatus.APPROVED, ReviewStatus.MODIFIED):
            raise ValueError("Can only verify approved or modified measurements")
        
        previous_status = measurement.review_status
        
        measurement.review_status = ReviewStatus.VERIFIED
        measurement.verified_by = verifier
        measurement.verified_at = datetime.utcnow()
        if notes:
            measurement.review_notes = (measurement.review_notes or "") + f"\nVerification: {notes}"
        
        # Record history
        history = MeasurementHistory(
            measurement_id=measurement_id,
            action="verified",
            actor=verifier,
            actor_type="user",
            previous_status=previous_status,
            new_status=ReviewStatus.VERIFIED,
            change_description="Measurement verified by QA",
        )
        session.add(history)
        
        await session.commit()
        await session.refresh(measurement)
        
        return measurement
    
    async def flag_measurement(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
        flagger: str,
        reason: str,
        priority: str = "normal",
    ) -> Measurement:
        """Flag a measurement for additional review."""
        measurement = await session.get(Measurement, measurement_id)
        if not measurement:
            raise ValueError(f"Measurement not found: {measurement_id}")
        
        previous_status = measurement.review_status
        
        measurement.review_status = ReviewStatus.FLAGGED
        measurement.flag_reason = reason
        measurement.flag_priority = priority
        measurement.reviewed_by = flagger
        measurement.reviewed_at = datetime.utcnow()
        
        # Record history
        history = MeasurementHistory(
            measurement_id=measurement_id,
            action="flagged",
            actor=flagger,
            actor_type="user",
            previous_status=previous_status,
            new_status=ReviewStatus.FLAGGED,
            change_description=f"Flagged ({priority}): {reason}",
            change_reason=reason,
        )
        session.add(history)
        
        await session.commit()
        await session.refresh(measurement)
        
        return measurement
    
    async def auto_accept_high_confidence(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
        threshold: float = 0.90,
        reviewer: str = "system",
    ) -> int:
        """
        Auto-accept all measurements above confidence threshold.
        
        Returns count of auto-accepted measurements.
        """
        # Get pending high-confidence measurements
        query = (
            select(Measurement)
            .join(Condition)
            .where(
                and_(
                    Condition.project_id == project_id,
                    Measurement.review_status == ReviewStatus.PENDING,
                    Measurement.ai_confidence >= threshold,
                )
            )
        )
        
        result = await session.execute(query)
        measurements = result.scalars().all()
        
        count = 0
        for measurement in measurements:
            measurement.review_status = ReviewStatus.APPROVED
            measurement.reviewed_by = reviewer
            measurement.reviewed_at = datetime.utcnow()
            measurement.was_auto_accepted = True
            measurement.auto_accept_threshold = threshold
            
            # Record history
            history = MeasurementHistory(
                measurement_id=measurement.id,
                action="approved",
                actor=reviewer,
                actor_type="auto_accept",
                previous_status=ReviewStatus.PENDING,
                new_status=ReviewStatus.APPROVED,
                change_description=f"Auto-accepted (confidence {measurement.ai_confidence:.1%} >= {threshold:.1%})",
                metadata={"threshold": threshold, "confidence": measurement.ai_confidence},
            )
            session.add(history)
            count += 1
        
        await session.commit()
        
        logger.info(
            "Auto-accepted measurements",
            project_id=str(project_id),
            threshold=threshold,
            count=count,
        )
        
        return count
    
    async def bulk_approve(
        self,
        session: AsyncSession,
        measurement_ids: list[uuid.UUID],
        reviewer: str,
    ) -> int:
        """Bulk approve multiple measurements."""
        count = 0
        for mid in measurement_ids:
            try:
                await self.approve_measurement(session, mid, reviewer)
                count += 1
            except ValueError:
                continue
        return count
    
    async def bulk_reject(
        self,
        session: AsyncSession,
        measurement_ids: list[uuid.UUID],
        reviewer: str,
        reason: str,
    ) -> int:
        """Bulk reject multiple measurements."""
        count = 0
        for mid in measurement_ids:
            try:
                await self.reject_measurement(session, mid, reviewer, reason)
                count += 1
            except ValueError:
                continue
        return count
    
    async def get_review_statistics(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Get review statistics for a project."""
        # Count by status
        status_query = (
            select(
                Measurement.review_status,
                func.count(Measurement.id).label("count"),
            )
            .join(Condition)
            .where(Condition.project_id == project_id)
            .group_by(Measurement.review_status)
        )
        
        status_result = await session.execute(status_query)
        status_counts = {row.review_status: row.count for row in status_result}
        
        # AI accuracy (approved vs total AI)
        ai_query = (
            select(
                func.count(Measurement.id).label("total"),
                func.count(Measurement.id).filter(
                    Measurement.review_status.in_([
                        ReviewStatus.APPROVED,
                        ReviewStatus.VERIFIED,
                    ])
                ).label("approved"),
                func.count(Measurement.id).filter(
                    Measurement.review_status == ReviewStatus.REJECTED
                ).label("rejected"),
                func.count(Measurement.id).filter(
                    Measurement.review_status == ReviewStatus.MODIFIED
                ).label("modified"),
            )
            .join(Condition)
            .where(
                and_(
                    Condition.project_id == project_id,
                    Measurement.is_ai_generated == True,
                )
            )
        )
        
        ai_result = (await session.execute(ai_query)).one()
        
        total_ai = ai_result.total
        if total_ai > 0:
            ai_accuracy = (ai_result.approved / total_ai) * 100
            ai_rejection_rate = (ai_result.rejected / total_ai) * 100
            ai_modification_rate = (ai_result.modified / total_ai) * 100
        else:
            ai_accuracy = ai_rejection_rate = ai_modification_rate = 0
        
        # Auto-accept stats
        auto_query = (
            select(func.count(Measurement.id))
            .join(Condition)
            .where(
                and_(
                    Condition.project_id == project_id,
                    Measurement.was_auto_accepted == True,
                )
            )
        )
        auto_accepted = (await session.execute(auto_query)).scalar()
        
        # Confidence distribution
        conf_query = (
            select(
                func.count(Measurement.id).filter(Measurement.ai_confidence >= 0.9).label("high"),
                func.count(Measurement.id).filter(
                    and_(Measurement.ai_confidence >= 0.7, Measurement.ai_confidence < 0.9)
                ).label("medium"),
                func.count(Measurement.id).filter(Measurement.ai_confidence < 0.7).label("low"),
            )
            .join(Condition)
            .where(
                and_(
                    Condition.project_id == project_id,
                    Measurement.is_ai_generated == True,
                )
            )
        )
        
        conf_result = (await session.execute(conf_query)).one()
        
        return {
            "status_counts": status_counts,
            "total_measurements": sum(status_counts.values()),
            "pending_count": status_counts.get(ReviewStatus.PENDING, 0),
            "ai_statistics": {
                "total_ai_generated": total_ai,
                "accuracy_percent": round(ai_accuracy, 1),
                "rejection_rate_percent": round(ai_rejection_rate, 1),
                "modification_rate_percent": round(ai_modification_rate, 1),
            },
            "auto_accept": {
                "count": auto_accepted,
                "percent_of_ai": round((auto_accepted / total_ai * 100) if total_ai > 0 else 0, 1),
            },
            "confidence_distribution": {
                "high_confidence": conf_result.high,
                "medium_confidence": conf_result.medium,
                "low_confidence": conf_result.low,
            },
        }
    
    async def get_measurement_history(
        self,
        session: AsyncSession,
        measurement_id: uuid.UUID,
    ) -> list[MeasurementHistory]:
        """Get full history for a measurement."""
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
```

---

### Task 9.3: Review API Endpoints

Create `backend/app/api/routes/review.py`:

```python
"""Review workflow API endpoints."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.review import (
    ReviewQueueResponse,
    ApproveRequest,
    RejectRequest,
    ModifyRequest,
    VerifyRequest,
    FlagRequest,
    BulkActionRequest,
    AutoAcceptRequest,
    ReviewStatisticsResponse,
    MeasurementHistoryResponse,
)
from app.services.review_service import get_review_service

router = APIRouter()


@router.get("/projects/{project_id}/review-queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    project_id: uuid.UUID,
    status_filter: list[str] | None = Query(None, alias="status"),
    min_confidence: float | None = Query(None),
    max_confidence: float | None = Query(None),
    page_id: uuid.UUID | None = Query(None),
    condition_id: uuid.UUID | None = Query(None),
    is_flagged: bool | None = Query(None),
    sort_by: str = Query("confidence_asc"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    Get measurements pending review.
    
    Sort options:
    - confidence_asc: Lowest confidence first (recommended for review)
    - confidence_desc: Highest confidence first
    - created_at: Newest first
    - page_order: By page number and position
    """
    service = get_review_service()
    
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if min_confidence is not None:
        filters["min_confidence"] = min_confidence
    if max_confidence is not None:
        filters["max_confidence"] = max_confidence
    if page_id:
        filters["page_id"] = page_id
    if condition_id:
        filters["condition_id"] = condition_id
    if is_flagged is not None:
        filters["is_flagged"] = is_flagged
    
    measurements, total = await service.get_review_queue(
        session=db,
        project_id=project_id,
        filters=filters,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )
    
    return ReviewQueueResponse(
        measurements=measurements,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/measurements/{measurement_id}/approve")
async def approve_measurement(
    measurement_id: uuid.UUID,
    request: ApproveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Approve a measurement."""
    service = get_review_service()
    
    try:
        measurement = await service.approve_measurement(
            session=db,
            measurement_id=measurement_id,
            reviewer=request.reviewer,
            notes=request.notes,
        )
        return {"status": "approved", "measurement_id": str(measurement_id)}
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
    """Reject a measurement."""
    service = get_review_service()
    
    try:
        measurement = await service.reject_measurement(
            session=db,
            measurement_id=measurement_id,
            reviewer=request.reviewer,
            reason=request.reason,
        )
        return {"status": "rejected", "measurement_id": str(measurement_id)}
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
            reviewer=request.reviewer,
            new_geometry=request.geometry,
            new_quantity=request.quantity,
            notes=request.notes,
        )
        return {
            "status": "modified",
            "measurement_id": str(measurement_id),
            "new_quantity": measurement.quantity,
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
    """Second-level verification of a measurement."""
    service = get_review_service()
    
    try:
        measurement = await service.verify_measurement(
            session=db,
            measurement_id=measurement_id,
            verifier=request.verifier,
            notes=request.notes,
        )
        return {"status": "verified", "measurement_id": str(measurement_id)}
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
    """Flag a measurement for additional review."""
    service = get_review_service()
    
    try:
        measurement = await service.flag_measurement(
            session=db,
            measurement_id=measurement_id,
            flagger=request.flagger,
            reason=request.reason,
            priority=request.priority,
        )
        return {"status": "flagged", "measurement_id": str(measurement_id)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/projects/{project_id}/review/bulk-approve")
async def bulk_approve(
    project_id: uuid.UUID,
    request: BulkActionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Bulk approve multiple measurements."""
    service = get_review_service()
    
    count = await service.bulk_approve(
        session=db,
        measurement_ids=request.measurement_ids,
        reviewer=request.reviewer,
    )
    
    return {"approved_count": count}


@router.post("/projects/{project_id}/review/bulk-reject")
async def bulk_reject(
    project_id: uuid.UUID,
    request: BulkActionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Bulk reject multiple measurements."""
    service = get_review_service()
    
    if not request.reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reason is required for bulk rejection",
        )
    
    count = await service.bulk_reject(
        session=db,
        measurement_ids=request.measurement_ids,
        reviewer=request.reviewer,
        reason=request.reason,
    )
    
    return {"rejected_count": count}


@router.post("/projects/{project_id}/review/auto-accept")
async def auto_accept_high_confidence(
    project_id: uuid.UUID,
    request: AutoAcceptRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Auto-accept all measurements above confidence threshold."""
    service = get_review_service()
    
    count = await service.auto_accept_high_confidence(
        session=db,
        project_id=project_id,
        threshold=request.threshold,
        reviewer=request.reviewer or "system",
    )
    
    return {
        "auto_accepted_count": count,
        "threshold": request.threshold,
    }


@router.get(
    "/projects/{project_id}/review/statistics",
    response_model=ReviewStatisticsResponse,
)
async def get_review_statistics(
    project_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get review statistics for a project."""
    service = get_review_service()
    
    stats = await service.get_review_statistics(
        session=db,
        project_id=project_id,
    )
    
    return ReviewStatisticsResponse(**stats)


@router.get(
    "/measurements/{measurement_id}/history",
    response_model=list[MeasurementHistoryResponse],
)
async def get_measurement_history(
    measurement_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get full change history for a measurement."""
    service = get_review_service()
    
    history = await service.get_measurement_history(
        session=db,
        measurement_id=measurement_id,
    )
    
    return [MeasurementHistoryResponse.model_validate(h) for h in history]
```

---

### Task 9.4: Review Schemas

Create `backend/app/schemas/review.py`:

```python
"""Review workflow schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MeasurementReviewItem(BaseModel):
    """Measurement item in review queue."""
    
    id: uuid.UUID
    condition_id: uuid.UUID
    page_id: uuid.UUID
    geometry_type: str
    geometry_data: dict
    quantity: float
    unit: str
    is_ai_generated: bool
    ai_confidence: float | None
    review_status: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    original_geometry: dict | None
    was_auto_accepted: bool
    edit_count: int
    
    # Condition info
    condition_name: str | None = None
    condition_color: str | None = None
    
    # Page info
    page_number: int | None = None
    
    model_config = {"from_attributes": True}


class ReviewQueueResponse(BaseModel):
    """Review queue response."""
    
    measurements: list[MeasurementReviewItem]
    total: int
    limit: int
    offset: int


class ApproveRequest(BaseModel):
    """Request to approve a measurement."""
    
    reviewer: str = Field(..., min_length=1)
    notes: str | None = None


class RejectRequest(BaseModel):
    """Request to reject a measurement."""
    
    reviewer: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class ModifyRequest(BaseModel):
    """Request to modify a measurement."""
    
    reviewer: str = Field(..., min_length=1)
    geometry: dict = Field(...)
    quantity: float | None = None
    notes: str | None = None


class VerifyRequest(BaseModel):
    """Request to verify a measurement."""
    
    verifier: str = Field(..., min_length=1)
    notes: str | None = None


class FlagRequest(BaseModel):
    """Request to flag a measurement."""
    
    flagger: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    priority: str = Field(default="normal")  # low, normal, high, urgent


class BulkActionRequest(BaseModel):
    """Request for bulk review actions."""
    
    measurement_ids: list[uuid.UUID] = Field(..., min_length=1)
    reviewer: str = Field(..., min_length=1)
    reason: str | None = None


class AutoAcceptRequest(BaseModel):
    """Request to auto-accept high confidence measurements."""
    
    threshold: float = Field(default=0.90, ge=0.5, le=1.0)
    reviewer: str | None = None


class AIStatistics(BaseModel):
    """AI generation statistics."""
    
    total_ai_generated: int
    accuracy_percent: float
    rejection_rate_percent: float
    modification_rate_percent: float


class AutoAcceptStats(BaseModel):
    """Auto-accept statistics."""
    
    count: int
    percent_of_ai: float


class ConfidenceDistribution(BaseModel):
    """Confidence score distribution."""
    
    high_confidence: int  # >= 90%
    medium_confidence: int  # 70-89%
    low_confidence: int  # < 70%


class ReviewStatisticsResponse(BaseModel):
    """Review statistics response."""
    
    status_counts: dict[str, int]
    total_measurements: int
    pending_count: int
    ai_statistics: AIStatistics
    auto_accept: AutoAcceptStats
    confidence_distribution: ConfidenceDistribution


class MeasurementHistoryResponse(BaseModel):
    """Measurement history item."""
    
    id: uuid.UUID
    measurement_id: uuid.UUID
    action: str
    actor: str
    actor_type: str
    previous_status: str | None
    new_status: str | None
    previous_quantity: float | None
    new_quantity: float | None
    change_description: str | None
    change_reason: str | None
    created_at: datetime
    
    model_config = {"from_attributes": True}
```

---

### Task 9.5: Frontend Review Workspace

Create `frontend/src/pages/ReviewWorkspace.tsx`:

```tsx
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useHotkeys } from 'react-hotkeys-hook';
import {
  Check,
  X,
  Edit,
  ChevronLeft,
  ChevronRight,
  Flag,
  CheckCircle2,
  Zap,
  Filter,
  BarChart3,
  History,
  Keyboard,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Slider } from '@/components/ui/slider';
import { SplitView } from '@/components/review/SplitView';
import { ReviewPanel } from '@/components/review/ReviewPanel';
import { StatisticsPanel } from '@/components/review/StatisticsPanel';
import { MeasurementCanvas } from '@/components/canvas/MeasurementCanvas';
import { apiClient } from '@/api/client';
import { cn } from '@/lib/utils';

interface Measurement {
  id: string;
  condition_id: string;
  page_id: string;
  geometry_type: string;
  geometry_data: any;
  quantity: number;
  unit: string;
  ai_confidence: number | null;
  review_status: string;
  original_geometry: any | null;
  condition_name?: string;
  condition_color?: string;
  page_number?: number;
}

const REVIEWER_NAME = 'Estimator'; // TODO: Get from auth

export function ReviewWorkspace() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();

  // State
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState('confidence_asc');
  const [statusFilter, setStatusFilter] = useState<string[]>(['pending']);
  const [confidenceRange, setConfidenceRange] = useState([0, 100]);
  const [showStats, setShowStats] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [autoAcceptThreshold, setAutoAcceptThreshold] = useState(90);

  // Fetch review queue
  const { data: queueData, isLoading } = useQuery({
    queryKey: ['review-queue', projectId, sortBy, statusFilter, confidenceRange],
    queryFn: async () => {
      const params = new URLSearchParams();
      statusFilter.forEach(s => params.append('status', s));
      params.set('sort_by', sortBy);
      params.set('min_confidence', String(confidenceRange[0] / 100));
      params.set('max_confidence', String(confidenceRange[1] / 100));
      params.set('limit', '200');

      const response = await apiClient.get(
        `/projects/${projectId}/review-queue?${params}`
      );
      return response.data;
    },
    enabled: !!projectId,
  });

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['review-stats', projectId],
    queryFn: async () => {
      const response = await apiClient.get(
        `/projects/${projectId}/review/statistics`
      );
      return response.data;
    },
    enabled: !!projectId,
  });

  const measurements = queueData?.measurements || [];
  const currentMeasurement = measurements[currentIndex];

  // Mutations
  const approveMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.post(`/measurements/${id}/approve`, {
        reviewer: REVIEWER_NAME,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] });
      queryClient.invalidateQueries({ queryKey: ['review-stats'] });
      goToNext();
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      await apiClient.post(`/measurements/${id}/reject`, {
        reviewer: REVIEWER_NAME,
        reason,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] });
      queryClient.invalidateQueries({ queryKey: ['review-stats'] });
      goToNext();
    },
  });

  const flagMutation = useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      await apiClient.post(`/measurements/${id}/flag`, {
        flagger: REVIEWER_NAME,
        reason,
        priority: 'normal',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] });
      goToNext();
    },
  });

  const autoAcceptMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(
        `/projects/${projectId}/review/auto-accept`,
        {
          threshold: autoAcceptThreshold / 100,
          reviewer: REVIEWER_NAME,
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] });
      queryClient.invalidateQueries({ queryKey: ['review-stats'] });
      alert(`Auto-accepted ${data.auto_accepted_count} measurements`);
    },
  });

  const bulkApproveMutation = useMutation({
    mutationFn: async (ids: string[]) => {
      await apiClient.post(`/projects/${projectId}/review/bulk-approve`, {
        measurement_ids: ids,
        reviewer: REVIEWER_NAME,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] });
      queryClient.invalidateQueries({ queryKey: ['review-stats'] });
      setSelectedIds(new Set());
    },
  });

  // Navigation
  const goToNext = useCallback(() => {
    if (currentIndex < measurements.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  }, [currentIndex, measurements.length]);

  const goToPrevious = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  }, [currentIndex]);

  // Keyboard shortcuts
  useHotkeys('a', () => {
    if (currentMeasurement) {
      approveMutation.mutate(currentMeasurement.id);
    }
  }, { enabled: !!currentMeasurement });

  useHotkeys('r', () => {
    if (currentMeasurement) {
      const reason = prompt('Rejection reason:');
      if (reason) {
        rejectMutation.mutate({ id: currentMeasurement.id, reason });
      }
    }
  }, { enabled: !!currentMeasurement });

  useHotkeys('e', () => {
    // Open edit mode
    console.log('Edit mode');
  }, { enabled: !!currentMeasurement });

  useHotkeys('f', () => {
    if (currentMeasurement) {
      const reason = prompt('Flag reason:');
      if (reason) {
        flagMutation.mutate({ id: currentMeasurement.id, reason });
      }
    }
  }, { enabled: !!currentMeasurement });

  useHotkeys('n', goToNext);
  useHotkeys('right', goToNext);
  useHotkeys('p', goToPrevious);
  useHotkeys('left', goToPrevious);

  useHotkeys('space', () => {
    if (currentMeasurement) {
      const newSelected = new Set(selectedIds);
      if (newSelected.has(currentMeasurement.id)) {
        newSelected.delete(currentMeasurement.id);
      } else {
        newSelected.add(currentMeasurement.id);
      }
      setSelectedIds(newSelected);
    }
  }, { enabled: !!currentMeasurement });

  useHotkeys('enter', () => {
    if (selectedIds.size > 0) {
      bulkApproveMutation.mutate(Array.from(selectedIds));
    }
  });

  useHotkeys('?', () => setShowShortcuts(true));

  // Progress
  const reviewedCount = stats?.total_measurements - stats?.pending_count || 0;
  const totalCount = stats?.total_measurements || 0;
  const progressPercent = totalCount > 0 ? (reviewedCount / totalCount) * 100 : 0;

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="h-14 border-b px-4 flex items-center justify-between bg-card">
        <div className="flex items-center gap-4">
          <h1 className="font-semibold">Review Workspace</h1>
          
          {/* Progress */}
          <div className="flex items-center gap-2">
            <Progress value={progressPercent} className="w-32 h-2" />
            <span className="text-sm text-muted-foreground">
              {reviewedCount}/{totalCount} reviewed
            </span>
          </div>

          {/* Current position */}
          {measurements.length > 0 && (
            <Badge variant="outline">
              {currentIndex + 1} of {measurements.length}
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Filters */}
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="confidence_asc">Lowest Confidence</SelectItem>
              <SelectItem value="confidence_desc">Highest Confidence</SelectItem>
              <SelectItem value="page_order">Page Order</SelectItem>
              <SelectItem value="created_at">Newest First</SelectItem>
            </SelectContent>
          </Select>

          {/* Auto-accept */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                onClick={() => autoAcceptMutation.mutate()}
                disabled={autoAcceptMutation.isPending}
              >
                <Zap className="h-4 w-4 mr-2" />
                Auto-Accept ≥{autoAcceptThreshold}%
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              Auto-approve all measurements with confidence ≥{autoAcceptThreshold}%
            </TooltipContent>
          </Tooltip>

          {/* Stats */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowStats(true)}
          >
            <BarChart3 className="h-4 w-4" />
          </Button>

          {/* Shortcuts help */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowShortcuts(true)}
          >
            <Keyboard className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex">
        {/* Left: Measurement list */}
        <div className="w-64 border-r overflow-auto">
          <div className="p-2 border-b bg-muted/50">
            <div className="text-sm font-medium">Review Queue</div>
            <div className="text-xs text-muted-foreground">
              Sorted by {sortBy.replace('_', ' ')}
            </div>
          </div>
          
          <div className="divide-y">
            {measurements.map((m, idx) => (
              <button
                key={m.id}
                onClick={() => setCurrentIndex(idx)}
                className={cn(
                  'w-full p-2 text-left hover:bg-muted/50 transition-colors',
                  idx === currentIndex && 'bg-muted',
                  selectedIds.has(m.id) && 'ring-2 ring-primary ring-inset'
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: m.condition_color || '#888' }}
                    />
                    <span className="text-sm truncate max-w-[120px]">
                      {m.condition_name || 'Unknown'}
                    </span>
                  </div>
                  <ConfidenceBadge confidence={m.ai_confidence} />
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Page {m.page_number} • {m.quantity.toFixed(1)} {m.unit}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Center: Canvas with measurement */}
        <div className="flex-1 flex flex-col">
          {currentMeasurement ? (
            <>
              {/* Canvas */}
              <div className="flex-1 relative">
                <MeasurementCanvas
                  pageId={currentMeasurement.page_id}
                  measurements={[currentMeasurement]}
                  highlightedId={currentMeasurement.id}
                  showOriginal={!!currentMeasurement.original_geometry}
                />
                
                {/* AI vs Modified indicator */}
                {currentMeasurement.original_geometry && (
                  <div className="absolute top-4 left-4 flex gap-2">
                    <Badge variant="outline" className="bg-blue-500/20">
                      <div className="w-2 h-2 rounded-full bg-blue-500 mr-1" />
                      AI Original
                    </Badge>
                    <Badge variant="outline" className="bg-green-500/20">
                      <div className="w-2 h-2 rounded-full bg-green-500 mr-1" />
                      Current
                    </Badge>
                  </div>
                )}
              </div>

              {/* Action bar */}
              <div className="h-16 border-t bg-card px-4 flex items-center justify-between">
                {/* Navigation */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={goToPrevious}
                    disabled={currentIndex === 0}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={goToNext}
                    disabled={currentIndex === measurements.length - 1}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>

                {/* Measurement info */}
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {currentMeasurement.quantity.toFixed(2)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {currentMeasurement.unit}
                    </div>
                  </div>
                  <ConfidenceBadge
                    confidence={currentMeasurement.ai_confidence}
                    size="lg"
                  />
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        onClick={() => setShowHistory(true)}
                      >
                        <History className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>View History</TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        onClick={() => {
                          const reason = prompt('Flag reason:');
                          if (reason) {
                            flagMutation.mutate({
                              id: currentMeasurement.id,
                              reason,
                            });
                          }
                        }}
                      >
                        <Flag className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>[F] Flag for review</TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="destructive"
                        onClick={() => {
                          const reason = prompt('Rejection reason:');
                          if (reason) {
                            rejectMutation.mutate({
                              id: currentMeasurement.id,
                              reason,
                            });
                          }
                        }}
                        disabled={rejectMutation.isPending}
                      >
                        <X className="h-4 w-4 mr-2" />
                        Reject
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>[R] Reject measurement</TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="default"
                        className="bg-green-600 hover:bg-green-700"
                        onClick={() => approveMutation.mutate(currentMeasurement.id)}
                        disabled={approveMutation.isPending}
                      >
                        <Check className="h-4 w-4 mr-2" />
                        Approve
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>[A] Approve measurement</TooltipContent>
                  </Tooltip>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              {isLoading ? 'Loading...' : 'No measurements to review'}
            </div>
          )}
        </div>

        {/* Right: Review panel */}
        <div className="w-80 border-l">
          <ReviewPanel
            measurement={currentMeasurement}
            onApprove={() => approveMutation.mutate(currentMeasurement?.id)}
            onReject={(reason) =>
              rejectMutation.mutate({ id: currentMeasurement?.id, reason })
            }
          />
        </div>
      </div>

      {/* Keyboard shortcuts dialog */}
      <Dialog open={showShortcuts} onOpenChange={setShowShortcuts}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Keyboard Shortcuts</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex justify-between">
              <kbd className="px-2 py-1 bg-muted rounded">A</kbd>
              <span>Approve</span>
            </div>
            <div className="flex justify-between">
              <kbd className="px-2 py-1 bg-muted rounded">R</kbd>
              <span>Reject</span>
            </div>
            <div className="flex justify-between">
              <kbd className="px-2 py-1 bg-muted rounded">E</kbd>
              <span>Edit</span>
            </div>
            <div className="flex justify-between">
              <kbd className="px-2 py-1 bg-muted rounded">F</kbd>
              <span>Flag</span>
            </div>
            <div className="flex justify-between">
              <kbd className="px-2 py-1 bg-muted rounded">N</kbd> / <kbd className="px-2 py-1 bg-muted rounded">→</kbd>
              <span>Next</span>
            </div>
            <div className="flex justify-between">
              <kbd className="px-2 py-1 bg-muted rounded">P</kbd> / <kbd className="px-2 py-1 bg-muted rounded">←</kbd>
              <span>Previous</span>
            </div>
            <div className="flex justify-between">
              <kbd className="px-2 py-1 bg-muted rounded">Space</kbd>
              <span>Toggle select</span>
            </div>
            <div className="flex justify-between">
              <kbd className="px-2 py-1 bg-muted rounded">Enter</kbd>
              <span>Approve selected</span>
            </div>
            <div className="flex justify-between">
              <kbd className="px-2 py-1 bg-muted rounded">?</kbd>
              <span>Show shortcuts</span>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Statistics dialog */}
      <Dialog open={showStats} onOpenChange={setShowStats}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Review Statistics</DialogTitle>
          </DialogHeader>
          {stats && <StatisticsPanel stats={stats} />}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ConfidenceBadge({
  confidence,
  size = 'sm',
}: {
  confidence: number | null;
  size?: 'sm' | 'lg';
}) {
  if (confidence === null) return null;

  const percent = Math.round(confidence * 100);
  const variant =
    percent >= 90 ? 'default' : percent >= 70 ? 'secondary' : 'destructive';

  return (
    <Badge
      variant={variant}
      className={cn(
        size === 'lg' && 'text-lg px-3 py-1',
        percent >= 90 && 'bg-green-600',
        percent >= 70 && percent < 90 && 'bg-yellow-600',
        percent < 70 && 'bg-red-600'
      )}
    >
      {percent}%
    </Badge>
  );
}
```

---

### Task 9.6: Statistics Panel Component

Create `frontend/src/components/review/StatisticsPanel.tsx`:

```tsx
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface Statistics {
  status_counts: Record<string, number>;
  total_measurements: number;
  pending_count: number;
  ai_statistics: {
    total_ai_generated: number;
    accuracy_percent: number;
    rejection_rate_percent: number;
    modification_rate_percent: number;
  };
  auto_accept: {
    count: number;
    percent_of_ai: number;
  };
  confidence_distribution: {
    high_confidence: number;
    medium_confidence: number;
    low_confidence: number;
  };
}

const STATUS_COLORS: Record<string, string> = {
  pending: '#FFA500',
  approved: '#22C55E',
  modified: '#3B82F6',
  rejected: '#EF4444',
  verified: '#10B981',
  flagged: '#8B5CF6',
};

export function StatisticsPanel({ stats }: { stats: Statistics }) {
  // Prepare status data for pie chart
  const statusData = Object.entries(stats.status_counts).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
    color: STATUS_COLORS[status] || '#888',
  }));

  // Confidence distribution for bar chart
  const confidenceData = [
    {
      name: 'High (≥90%)',
      count: stats.confidence_distribution.high_confidence,
      color: '#22C55E',
    },
    {
      name: 'Medium (70-89%)',
      count: stats.confidence_distribution.medium_confidence,
      color: '#FFA500',
    },
    {
      name: 'Low (<70%)',
      count: stats.confidence_distribution.low_confidence,
      color: '#EF4444',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Total Measurements"
          value={stats.total_measurements}
        />
        <StatCard
          label="Pending Review"
          value={stats.pending_count}
          color="orange"
        />
        <StatCard
          label="AI Accuracy"
          value={`${stats.ai_statistics.accuracy_percent}%`}
          color="green"
        />
        <StatCard
          label="Auto-Accepted"
          value={stats.auto_accept.count}
          subtitle={`${stats.auto_accept.percent_of_ai}% of AI`}
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Status distribution */}
        <div>
          <h4 className="text-sm font-medium mb-4">Review Status</h4>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={statusData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={({ name, value }) => `${name}: ${value}`}
              >
                {statusData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Confidence distribution */}
        <div>
          <h4 className="text-sm font-medium mb-4">AI Confidence Distribution</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={confidenceData}>
              <XAxis dataKey="name" fontSize={12} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count">
                {confidenceData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* AI Statistics */}
      <div>
        <h4 className="text-sm font-medium mb-4">AI Performance</h4>
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 bg-green-500/10 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {stats.ai_statistics.accuracy_percent}%
            </div>
            <div className="text-sm text-muted-foreground">
              Approved without changes
            </div>
          </div>
          <div className="p-4 bg-blue-500/10 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {stats.ai_statistics.modification_rate_percent}%
            </div>
            <div className="text-sm text-muted-foreground">
              Required modification
            </div>
          </div>
          <div className="p-4 bg-red-500/10 rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              {stats.ai_statistics.rejection_rate_percent}%
            </div>
            <div className="text-sm text-muted-foreground">
              Rejected
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  subtitle,
  color,
}: {
  label: string;
  value: string | number;
  subtitle?: string;
  color?: 'green' | 'orange' | 'red';
}) {
  const colorClasses = {
    green: 'text-green-600',
    orange: 'text-orange-600',
    red: 'text-red-600',
  };

  return (
    <div className="p-4 bg-muted/50 rounded-lg">
      <div className={`text-2xl font-bold ${color ? colorClasses[color] : ''}`}>
        {value}
      </div>
      <div className="text-sm text-muted-foreground">{label}</div>
      {subtitle && <div className="text-xs text-muted-foreground">{subtitle}</div>}
    </div>
  );
}
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] Review queue loads with filters
- [ ] Sorting by confidence works (lowest first)
- [ ] Keyboard shortcuts A/R/E/N/P function
- [ ] Approve updates status correctly
- [ ] Reject stores reason
- [ ] Modify preserves original geometry
- [ ] Verify requires prior approval
- [ ] Flag marks for re-review
- [ ] Auto-accept approves above threshold
- [ ] Bulk operations work
- [ ] Statistics show accurate counts
- [ ] History tracks all changes
- [ ] AI vs Modified overlay displays
- [ ] Progress bar updates
- [ ] Batch selection with Space/Enter

### Test Cases

1. Press A → measurement approved, advances to next
2. Press R → prompts reason, rejects, advances
3. Sort by confidence_asc → lowest confidence first
4. Auto-accept at 90% → high confidence approved
5. Verify approved measurement → status becomes verified
6. Flag measurement → appears in flagged queue
7. View history → shows all status changes
8. Bulk select 5 + Enter → all 5 approved

---

## Next Phase

Once verified, proceed to **`10-EXPORT-SYSTEM.md`** for implementing takeoff exports.
