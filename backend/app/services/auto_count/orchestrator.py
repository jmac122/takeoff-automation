"""Auto Count orchestrator — combines template matching and LLM detection."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auto_count import AutoCountDetection, AutoCountSession
from app.models.condition import Condition
from app.models.measurement import Measurement
from app.models.page import Page
from app.services.auto_count.llm_similarity import LLMSimilarityService
from app.services.auto_count.template_matcher import MatchResult, TemplateMatchingService

logger = structlog.get_logger()


class AutoCountService:
    """Orchestrates template matching + LLM detection for auto-counting."""

    def __init__(self) -> None:
        self.template_matcher = TemplateMatchingService()

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    async def create_session(
        self,
        db: AsyncSession,
        page_id: uuid.UUID,
        condition_id: uuid.UUID,
        template_bbox: dict,
        confidence_threshold: float = 0.80,
        scale_tolerance: float = 0.20,
        rotation_tolerance: float = 15.0,
        detection_method: str = "hybrid",
    ) -> AutoCountSession:
        """Create a new auto-count session."""
        # Verify page and condition exist
        page = await db.get(Page, page_id)
        if page is None:
            raise ValueError(f"Page {page_id} not found")

        condition = await db.get(Condition, condition_id)
        if condition is None:
            raise ValueError(f"Condition {condition_id} not found")

        session = AutoCountSession(
            page_id=page_id,
            condition_id=condition_id,
            template_bbox=template_bbox,
            confidence_threshold=confidence_threshold,
            scale_tolerance=scale_tolerance,
            rotation_tolerance=rotation_tolerance,
            detection_method=detection_method,
            status="pending",
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
    ) -> AutoCountSession:
        """Get a session with detections loaded."""
        result = await db.execute(
            select(AutoCountSession)
            .options(selectinload(AutoCountSession.detections))
            .where(AutoCountSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise ValueError(f"AutoCountSession {session_id} not found")
        return session

    async def list_sessions(
        self,
        db: AsyncSession,
        page_id: uuid.UUID | None = None,
        condition_id: uuid.UUID | None = None,
    ) -> list[AutoCountSession]:
        """List sessions, optionally filtered."""
        query = select(AutoCountSession).order_by(
            AutoCountSession.created_at.desc()
        )
        if page_id:
            query = query.where(AutoCountSession.page_id == page_id)
        if condition_id:
            query = query.where(AutoCountSession.condition_id == condition_id)

        result = await db.execute(query)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Detection execution
    # ------------------------------------------------------------------

    async def run_detection(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        page_image_bytes: bytes,
        image_width: int,
        image_height: int,
        llm_provider: str | None = None,
    ) -> AutoCountSession:
        """Execute the auto-count detection pipeline.

        This is the core method that runs template matching and/or LLM
        detection, deduplicates results, and stores detections.
        """
        session = await self.get_session(db, session_id)
        session.status = "processing"
        await db.commit()

        start_time = time.time()
        all_matches: list[MatchResult] = []
        template_count = 0
        llm_count = 0

        try:
            method = session.detection_method

            # Step 1: Template matching (OpenCV)
            if method in ("template", "hybrid"):
                self.template_matcher.confidence_threshold = (
                    session.confidence_threshold
                )
                self.template_matcher.scale_tolerance = session.scale_tolerance
                self.template_matcher.rotation_tolerance = (
                    session.rotation_tolerance
                )

                template_matches = self.template_matcher.find_matches(
                    page_image_bytes=page_image_bytes,
                    template_bbox=session.template_bbox,
                    confidence_threshold=session.confidence_threshold,
                )
                template_count = len(template_matches)
                for m in template_matches:
                    all_matches.append(m)

                logger.info(
                    "Template matching phase complete",
                    session_id=str(session_id),
                    matches=template_count,
                )

            # Step 2: LLM similarity detection
            if method in ("llm", "hybrid"):
                llm_service = LLMSimilarityService(provider=llm_provider)
                llm_matches = await llm_service.find_similar(
                    page_image_bytes=page_image_bytes,
                    template_bbox=session.template_bbox,
                    image_width=image_width,
                    image_height=image_height,
                )
                llm_count = len(llm_matches)

                # In hybrid mode, merge LLM matches with template matches
                if method == "hybrid":
                    all_matches = self._merge_detections(
                        all_matches, llm_matches
                    )
                else:
                    all_matches = llm_matches

                logger.info(
                    "LLM detection phase complete",
                    session_id=str(session_id),
                    matches=llm_count,
                )

            # Step 3: Store detections
            for match in all_matches:
                source = "template"
                if method == "llm":
                    source = "llm"
                elif method == "hybrid":
                    # Determine if this came from both sources
                    source = self._determine_source(
                        match, template_count, llm_count
                    )

                detection = AutoCountDetection(
                    session_id=session.id,
                    bbox={
                        "x": match.x,
                        "y": match.y,
                        "w": match.w,
                        "h": match.h,
                    },
                    center_x=match.center_x,
                    center_y=match.center_y,
                    confidence=match.confidence,
                    detection_source=source,
                    status="pending",
                )
                db.add(detection)

            elapsed_ms = (time.time() - start_time) * 1000

            session.status = "completed"
            session.total_detections = len(all_matches)
            session.template_match_count = template_count
            session.llm_match_count = llm_count
            session.processing_time_ms = elapsed_ms
            await db.commit()

            # Reload with detections
            return await self.get_session(db, session_id)

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            session.status = "failed"
            session.error_message = str(e)
            session.processing_time_ms = elapsed_ms
            await db.commit()

            logger.error(
                "Auto count detection failed",
                session_id=str(session_id),
                error=str(e),
            )
            raise

    def _merge_detections(
        self,
        template_matches: list[MatchResult],
        llm_matches: list[MatchResult],
    ) -> list[MatchResult]:
        """Merge template and LLM matches, deduplicating overlaps.

        When both sources detect the same element, keep the higher-confidence one.
        LLM matches that don't overlap with template matches are added as new.
        """
        merged = list(template_matches)

        for llm_match in llm_matches:
            is_duplicate = False
            for i, existing in enumerate(merged):
                iou = self.template_matcher._compute_iou(llm_match, existing)
                if iou > 0.30:
                    # Overlapping — keep the higher confidence
                    if llm_match.confidence > existing.confidence:
                        merged[i] = llm_match
                    is_duplicate = True
                    break
            if not is_duplicate:
                merged.append(llm_match)

        return merged

    def _determine_source(
        self,
        match: MatchResult,
        template_count: int,
        llm_count: int,
    ) -> str:
        """Determine the source label for a merged match."""
        if template_count > 0 and llm_count > 0:
            return "both"
        elif template_count > 0:
            return "template"
        return "llm"

    # ------------------------------------------------------------------
    # Detection review
    # ------------------------------------------------------------------

    async def confirm_detection(
        self,
        db: AsyncSession,
        detection_id: uuid.UUID,
    ) -> AutoCountDetection:
        """Mark a detection as confirmed."""
        detection = await db.get(AutoCountDetection, detection_id)
        if detection is None:
            raise ValueError(f"Detection {detection_id} not found")

        detection.status = "confirmed"
        await db.commit()
        await db.refresh(detection)

        # Update session counts
        await self._update_session_counts(db, detection.session_id)
        return detection

    async def reject_detection(
        self,
        db: AsyncSession,
        detection_id: uuid.UUID,
    ) -> AutoCountDetection:
        """Mark a detection as rejected."""
        detection = await db.get(AutoCountDetection, detection_id)
        if detection is None:
            raise ValueError(f"Detection {detection_id} not found")

        detection.status = "rejected"
        await db.commit()
        await db.refresh(detection)

        await self._update_session_counts(db, detection.session_id)
        return detection

    async def bulk_confirm_above_threshold(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        threshold: float,
    ) -> int:
        """Auto-confirm all pending detections above a confidence threshold."""
        session = await self.get_session(db, session_id)
        count = 0

        for detection in session.detections:
            if (
                detection.status == "pending"
                and detection.confidence >= threshold
            ):
                detection.status = "confirmed"
                detection.is_auto_confirmed = True
                count += 1

        await db.commit()
        await self._update_session_counts(db, session_id)

        logger.info(
            "Bulk confirmed detections",
            session_id=str(session_id),
            threshold=threshold,
            confirmed=count,
        )
        return count

    async def create_measurements_from_confirmed(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
    ) -> int:
        """Create point measurements for all confirmed detections that don't yet have one."""
        session = await self.get_session(db, session_id)

        count = 0
        for detection in session.detections:
            if detection.status != "confirmed" or detection.measurement_id is not None:
                continue

            measurement = Measurement(
                condition_id=session.condition_id,
                page_id=session.page_id,
                geometry_type="point",
                geometry_data={
                    "x": detection.center_x,
                    "y": detection.center_y,
                },
                quantity=1.0,
                unit="EA",
                is_ai_generated=True,
                ai_confidence=detection.confidence,
                ai_model="auto_count",
                notes=f"Auto-counted (confidence: {detection.confidence:.0%})",
            )
            db.add(measurement)
            await db.flush()

            detection.measurement_id = measurement.id
            count += 1

        if count > 0:
            # Update condition total_quantity
            condition = await db.get(Condition, session.condition_id)
            if condition is not None:
                condition.total_quantity = (condition.total_quantity or 0) + count

        await db.commit()

        logger.info(
            "Created measurements from confirmed detections",
            session_id=str(session_id),
            measurements_created=count,
        )
        return count

    async def _update_session_counts(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
    ) -> None:
        """Refresh confirmed/rejected counts on a session."""
        session = await self.get_session(db, session_id)
        confirmed = sum(1 for d in session.detections if d.status == "confirmed")
        rejected = sum(1 for d in session.detections if d.status == "rejected")
        session.confirmed_count = confirmed
        session.rejected_count = rejected
        await db.commit()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_service: AutoCountService | None = None


def get_auto_count_service() -> AutoCountService:
    """Get the auto count service singleton."""
    global _service
    if _service is None:
        _service = AutoCountService()
    return _service
