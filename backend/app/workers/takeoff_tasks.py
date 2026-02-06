"""Celery tasks for AI takeoff generation.

IMPORTANT: This module uses SYNCHRONOUS SQLAlchemy (psycopg2 driver)
because Celery workers run in a multiprocessing context where async
database connections (asyncpg) cause InterfaceError.

FastAPI routes use ASYNC SQLAlchemy - this is the correct pattern.
"""

import traceback as tb_module
import uuid

from celery.exceptions import MaxRetriesExceededError
import structlog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.page import Page
from app.models.document import Document
from app.models.condition import Condition
from app.models.measurement import Measurement
from app.services.ai_takeoff import get_ai_takeoff_service, AITakeoffResult, DetectedElement
from app.services.task_tracker import TaskTracker
from app.utils.storage import get_storage_service
from app.utils.geometry import MeasurementCalculator
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()

# Create SYNC engine for Celery workers (remove +asyncpg from URL)
sync_database_url = str(settings.database_url).replace("+asyncpg", "")
sync_engine = create_engine(
    sync_database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SyncSession = sessionmaker(bind=sync_engine)


def _report_progress(task, db, percent: float, step: str) -> None:
    """Send progress updates to Celery and the DB."""
    task.update_state(state="PROGRESS", meta={"percent": percent, "step": step})
    TaskTracker.update_progress_sync(db, task.request.id, percent, step)


def create_measurement_from_element(
    page: Page,
    condition: Condition,
    element: DetectedElement,
    calculator: MeasurementCalculator,
    result: AITakeoffResult,
) -> Measurement | None:
    """Create a Measurement record from a detected element.
    
    Uses the condition's unit as the source of truth to ensure measurements
    sum correctly. If AI draws a linear element (LF) as a polygon, we use
    the perimeter. If AI draws an area element (SF) as a polyline, we skip it.
    
    Calculates both SF (square feet) and CY (cubic yards) for area elements.
    """
    extra_metadata = {
        "ai_provider": result.llm_provider,
        "ai_latency_ms": result.llm_latency_ms,
    }
    
    # Use condition's unit as source of truth to ensure totals are consistent
    condition_unit = condition.unit or "SF"
    
    # Calculate based on geometry type, but assign quantity based on condition unit
    if element.geometry_type == "polygon":
        points = element.geometry_data.get("points", [])
        if len(points) < 3:
            return None
        
        # Use element depth if available, otherwise condition depth
        # Note: condition.depth is already stored in inches (e.g., 4 for "4" SOG")
        depth_inches = element.depth_inches or condition.depth
        
        calculation = calculator.calculate_polygon(points, depth_inches)
        pixel_area = calculation.get("pixel_area")
        pixel_length = calculation.get("pixel_perimeter")
        
        # Store all calculated values in metadata
        area_sf = calculation.get("area_sf", 0)
        perimeter_lf = calculation.get("perimeter_lf", 0)
        volume_cy = calculation.get("volume_cy")
        
        if volume_cy:
            extra_metadata["volume_cy"] = round(volume_cy, 2)
            extra_metadata["depth_inches"] = depth_inches
        extra_metadata["area_sf"] = round(area_sf, 2)
        extra_metadata["perimeter_lf"] = round(perimeter_lf, 2)
        
        # Assign quantity based on condition's expected unit
        if condition_unit == "LF":
            # Condition expects linear - use perimeter of polygon
            quantity = perimeter_lf
            unit = "LF"
        elif condition_unit == "EA":
            # Condition expects count - treat polygon as 1 item
            quantity = 1
            unit = "EA"
        elif condition_unit == "CY":
            # Condition expects volume - use cubic yards
            if volume_cy:
                quantity = volume_cy
                unit = "CY"
            else:
                # No depth available to calculate volume, skip
                logger.warning(
                    "Skipping polygon measurement for CY condition - no depth available",
                    condition_name=condition.name,
                    condition_unit=condition_unit,
                )
                return None
        else:
            # Default: use area (SF)
            quantity = area_sf
            unit = "SF"

    elif element.geometry_type == "polyline":
        # Note: "line" geometry_type is normalized to "polyline" in ai_takeoff.py
        # to ensure consistent {points} format handling
        points = element.geometry_data.get("points", [])
        if len(points) < 2:
            return None
        calculation = calculator.calculate_polyline(points)
        length_lf = calculation.get("length_feet", 0)
        pixel_length = calculation.get("pixel_length")
        pixel_area = None
        extra_metadata["length_lf"] = round(length_lf, 2)
        
        # Assign quantity based on condition's expected unit
        if condition_unit == "SF":
            # Condition expects area but AI drew a line - skip this measurement
            # (can't derive area from a line without width)
            logger.warning(
                "Skipping polyline measurement for area condition",
                condition_name=condition.name,
                condition_unit=condition_unit,
                geometry_type=element.geometry_type,
            )
            return None
        elif condition_unit == "CY":
            # Condition expects volume but AI drew a line - skip
            # (can't derive volume from a line)
            logger.warning(
                "Skipping polyline measurement for volume condition",
                condition_name=condition.name,
                condition_unit=condition_unit,
                geometry_type=element.geometry_type,
            )
            return None
        elif condition_unit == "EA":
            # Condition expects count - treat polyline as 1 item
            quantity = 1
            unit = "EA"
        else:
            # Default: use length (LF)
            quantity = length_lf
            unit = "LF"

    elif element.geometry_type == "point":
        pixel_length = None
        pixel_area = None
        extra_metadata["count"] = 1
        
        # Points are always count=1, but respect condition unit
        if condition_unit in ("SF", "LF", "CY"):
            # Condition expects area/length/volume but AI drew a point - skip
            logger.warning(
                "Skipping point measurement for non-count condition",
                condition_name=condition.name,
                condition_unit=condition_unit,
                geometry_type=element.geometry_type,
            )
            return None
        else:
            quantity = 1
            unit = "EA"

    else:
        return None

    return Measurement(
        id=uuid.uuid4(),
        page_id=page.id,
        condition_id=condition.id,
        geometry_type=element.geometry_type,
        geometry_data=element.geometry_data,
        quantity=quantity,
        unit=unit,
        pixel_length=pixel_length,
        pixel_area=pixel_area,
        notes=element.description,
        is_ai_generated=True,
        ai_confidence=element.confidence,
        ai_model=result.llm_model,
        extra_metadata=extra_metadata,
    )


@celery_app.task(bind=True, max_retries=3)
def generate_ai_takeoff_task(
    self,
    page_id: str,
    condition_id: str,
    provider: str | None = None,
) -> dict:
    """Generate AI takeoff for a page and condition.

    Args:
        page_id: Page UUID as string
        condition_id: Condition UUID as string
        provider: Optional LLM provider override

    Returns:
        Result summary dict
    """
    logger.info(
        "Starting AI takeoff generation",
        page_id=page_id,
        condition_id=condition_id,
        provider=provider,
    )

    try:
        with SyncSession() as db:
            # Mark task as started
            TaskTracker.mark_started_sync(db, self.request.id)

            _report_progress(self, db, 10, "Loading page data")

            page_uuid = uuid.UUID(page_id)
            condition_uuid = uuid.UUID(condition_id)

            # Get page with document for project validation
            page = db.query(Page).filter(Page.id == page_uuid).one_or_none()
            condition = db.query(Condition).filter(Condition.id == condition_uuid).one_or_none()

            if not page:
                raise ValueError(f"Page not found: {page_id}")
            if not condition:
                raise ValueError(f"Condition not found: {condition_id}")

            # Verify page and condition belong to the same project
            document = db.query(Document).filter(Document.id == page.document_id).one()
            if document.project_id != condition.project_id:
                raise ValueError("Page and condition must belong to the same project")

            # Verify page is calibrated
            if not page.scale_calibrated or not page.scale_value:
                raise ValueError("Page must be calibrated before AI takeoff")

            # Get page image
            storage = get_storage_service()
            image_bytes = storage.download_file(page.image_key)

            # Get AI takeoff service
            _report_progress(self, db, 30, "Running AI analysis")

            ai_service = get_ai_takeoff_service(provider=provider)

            # Analyze page
            result = ai_service.analyze_page(
                image_bytes=image_bytes,
                width=page.width,
                height=page.height,
                element_type=condition.name,
                measurement_type=condition.measurement_type,
                scale_text=page.scale_text,
                ocr_text=page.ocr_text,
            )

            # Create measurements from detected elements
            _report_progress(self, db, 70, "Creating measurements")

            calculator = MeasurementCalculator(
                pixels_per_foot=page.scale_value
            )

            measurements_created = 0
            for elem in result.elements:
                measurement = create_measurement_from_element(
                    page, condition, elem, calculator, result
                )
                if measurement:
                    db.add(measurement)
                    measurements_created += 1

            # Update condition totals with row lock to prevent race conditions
            # when multiple tasks update the same condition concurrently
            if measurements_created > 0:
                from sqlalchemy import func

                # Lock the condition row to prevent concurrent updates
                locked_condition = db.query(Condition).filter(
                    Condition.id == condition.id
                ).with_for_update().one()

                totals = db.query(
                    func.sum(Measurement.quantity),
                    func.count(Measurement.id),
                ).filter(Measurement.condition_id == condition.id).one()

                locked_condition.total_quantity = totals[0] or 0.0
                locked_condition.measurement_count = totals[1] or 0

            _report_progress(self, db, 90, "Finalizing")

            result_summary = {
                "page_id": page_id,
                "condition_id": condition_id,
                "elements_detected": len(result.elements),
                "measurements_created": measurements_created,
                "page_description": result.page_description,
                "analysis_notes": result.analysis_notes,
                "llm_provider": result.llm_provider,
                "llm_model": result.llm_model,
                "llm_latency_ms": result.llm_latency_ms,
            }

            TaskTracker.mark_completed_sync(
                db,
                self.request.id,
                result_summary,
                commit=False,
            )
            db.commit()

            logger.info(
                "AI takeoff complete",
                page_id=page_id,
                condition_id=condition_id,
                elements_detected=len(result.elements),
                measurements_created=measurements_created,
                provider=result.llm_provider,
                model=result.llm_model,
                latency_ms=result.llm_latency_ms,
            )

            return result_summary

    except ValueError as e:
        # Validation errors (not found, not calibrated, etc.) should fail immediately
        # without retrying - they won't succeed on retry
        logger.error(
            "AI takeoff validation failed (not retrying)",
            page_id=page_id,
            condition_id=condition_id,
            error=str(e),
        )
        with SyncSession() as db:
            TaskTracker.mark_failed_sync(db, self.request.id, str(e), tb_module.format_exc())
        raise
    except Exception as e:
        # Transient errors (network, API rate limits, etc.) can be retried
        logger.error(
            "AI takeoff failed (will retry)",
            page_id=page_id,
            condition_id=condition_id,
            error=str(e),
        )
        original_traceback = tb_module.format_exc()
        try:
            raise self.retry(exc=e, countdown=60)
        except MaxRetriesExceededError:
            with SyncSession() as db:
                TaskTracker.mark_failed_sync(
                    db, self.request.id, str(e), original_traceback
                )
            raise


@celery_app.task(bind=True)
def compare_providers_task(
    self,
    page_id: str,
    condition_id: str,
    providers: list[str] | None = None,
) -> dict:
    """Run AI takeoff with multiple providers for comparison.

    Useful for benchmarking provider accuracy.

    Args:
        page_id: Page UUID as string
        condition_id: Condition UUID as string
        providers: List of providers to compare (default: all available)

    Returns:
        Comparison results
    """
    if providers is None:
        providers = settings.available_providers

    logger.info(
        "Starting multi-provider comparison",
        page_id=page_id,
        condition_id=condition_id,
        providers=providers,
    )

    try:
        with SyncSession() as db:
            TaskTracker.mark_started_sync(db, self.request.id)

            _report_progress(self, db, 10, "Loading page data")

            page_uuid = uuid.UUID(page_id)
            condition_uuid = uuid.UUID(condition_id)

            page = db.query(Page).filter(Page.id == page_uuid).one_or_none()
            condition = db.query(Condition).filter(Condition.id == condition_uuid).one_or_none()

            if not page:
                raise ValueError(f"Page not found: {page_id}")
            if not condition:
                raise ValueError(f"Condition not found: {condition_id}")

            if not page.scale_calibrated:
                raise ValueError("Page must be calibrated before AI takeoff")

            storage = get_storage_service()
            image_bytes = storage.download_file(page.image_key)

            _report_progress(self, db, 20, "Running multi-provider analysis")

            ai_service = get_ai_takeoff_service()

            results = ai_service.analyze_page_multi_provider(
                image_bytes=image_bytes,
                width=page.width,
                height=page.height,
                element_type=condition.name,
                measurement_type=condition.measurement_type,
                scale_text=page.scale_text,
                ocr_text=page.ocr_text,
                providers=providers,
            )

            _report_progress(self, db, 90, "Compiling results")

            comparison = {}
            for provider_name, result in results.items():
                comparison[provider_name] = {
                    "elements_detected": len(result.elements),
                    "latency_ms": result.llm_latency_ms,
                    "input_tokens": result.llm_input_tokens,
                    "output_tokens": result.llm_output_tokens,
                    "model": result.llm_model,
                    "elements": [e.to_dict() for e in result.elements],
                }

            logger.info(
                "Multi-provider comparison complete",
                page_id=page_id,
                providers_compared=len(results),
            )

            result_summary = {
                "page_id": page_id,
                "condition_id": condition_id,
                "providers_compared": list(results.keys()),
                "results": comparison,
            }

            TaskTracker.mark_completed_sync(db, self.request.id, result_summary)

            return result_summary

    except ValueError as e:
        logger.error(
            "Multi-provider comparison validation failed (not retrying)",
            page_id=page_id,
            condition_id=condition_id,
            error=str(e),
        )
        with SyncSession() as db:
            TaskTracker.mark_failed_sync(db, self.request.id, str(e), tb_module.format_exc())
        raise

    except Exception as e:
        logger.error(
            "Multi-provider comparison failed",
            page_id=page_id,
            condition_id=condition_id,
            error=str(e),
        )
        with SyncSession() as db:
            TaskTracker.mark_failed_sync(db, self.request.id, str(e), tb_module.format_exc())
        raise


@celery_app.task(bind=True)
def batch_ai_takeoff_task(
    self,
    page_ids: list[str],
    condition_id: str,
    provider: str | None = None,
) -> dict:
    """Generate AI takeoff for multiple pages.

    Args:
        page_ids: List of page UUIDs as strings
        condition_id: Condition UUID as string
        provider: Optional LLM provider override

    Returns:
        Batch result summary
    """
    logger.info(
        "Starting batch AI takeoff",
        page_count=len(page_ids),
        condition_id=condition_id,
        provider=provider,
    )

    try:
        with SyncSession() as db:
            TaskTracker.mark_started_sync(db, self.request.id)
            _report_progress(self, db, 10, "Starting batch")

        results = []
        total_pages = len(page_ids)
        for i, page_id in enumerate(page_ids):
            try:
                task = generate_ai_takeoff_task.delay(
                    page_id=page_id,
                    condition_id=condition_id,
                    provider=provider,
                )
                results.append({
                    "page_id": page_id,
                    "task_id": task.id,
                    "status": "queued",
                })
            except Exception as e:
                logger.error(
                    "Failed to queue AI takeoff for page",
                    page_id=page_id,
                    error=str(e),
                )
                results.append({
                    "page_id": page_id,
                    "task_id": None,
                    "status": "error",
                    "error": str(e),
                })

            # Report per-page progress (10-90% range)
            percent = 10 + int(80 * (i + 1) / total_pages)
            with SyncSession() as db:
                _report_progress(self, db, percent, f"Queued {i + 1}/{total_pages} pages")

        result_summary = {
            "condition_id": condition_id,
            "pages_queued": len([r for r in results if r["status"] == "queued"]),
            "pages_failed": len([r for r in results if r["status"] == "error"]),
            "results": results,
        }

        with SyncSession() as db:
            TaskTracker.mark_completed_sync(db, self.request.id, result_summary)

        return result_summary

    except Exception as e:
        logger.error(
            "Batch AI takeoff failed",
            page_count=len(page_ids),
            condition_id=condition_id,
            error=str(e),
        )
        with SyncSession() as db:
            TaskTracker.mark_failed_sync(db, self.request.id, str(e), tb_module.format_exc())
        raise


# Mapping from AI-detected element types to condition categories
ELEMENT_TYPE_MAPPING = {
    "slab_on_grade": {"category": "slabs", "measurement_type": "area", "unit": "SF"},
    "slab": {"category": "slabs", "measurement_type": "area", "unit": "SF"},
    "concrete_slab": {"category": "slabs", "measurement_type": "area", "unit": "SF"},
    "strip_footing": {"category": "foundations", "measurement_type": "linear", "unit": "LF"},
    "continuous_footing": {"category": "foundations", "measurement_type": "linear", "unit": "LF"},
    "spread_footing": {"category": "foundations", "measurement_type": "area", "unit": "SF"},
    "column_footing": {"category": "foundations", "measurement_type": "count", "unit": "EA"},
    "foundation_wall": {"category": "foundations", "measurement_type": "linear", "unit": "LF"},
    "grade_beam": {"category": "foundations", "measurement_type": "linear", "unit": "LF"},
    "retaining_wall": {"category": "walls", "measurement_type": "linear", "unit": "LF"},
    "concrete_wall": {"category": "walls", "measurement_type": "area", "unit": "SF"},
    "column": {"category": "columns", "measurement_type": "count", "unit": "EA"},
    "pier": {"category": "columns", "measurement_type": "count", "unit": "EA"},
    "curb": {"category": "sitework", "measurement_type": "linear", "unit": "LF"},
    "curb_and_gutter": {"category": "sitework", "measurement_type": "linear", "unit": "LF"},
    "sidewalk": {"category": "sitework", "measurement_type": "area", "unit": "SF"},
    "concrete_paving": {"category": "sitework", "measurement_type": "area", "unit": "SF"},
}


def get_or_create_condition_for_element(
    db,
    project_id: uuid.UUID,
    element_type: str,
) -> tuple[Condition, bool]:
    """Get or create a condition for an AI-detected element type.
    
    Uses SELECT FOR UPDATE on the project row to prevent race conditions
    when multiple concurrent tasks try to create the same condition.
    
    Returns:
        Tuple of (condition, was_created)
    """
    from sqlalchemy import func
    from sqlalchemy.exc import IntegrityError
    from app.models.project import Project
    
    # Handle null element_type from AI (explicit null, not missing key)
    if not element_type:
        element_type = "unknown"
    
    # Normalize element type
    normalized = element_type.lower().replace(" ", "_").replace("-", "_")
    
    # Get mapping or use defaults
    mapping = ELEMENT_TYPE_MAPPING.get(normalized, {
        "category": "other",
        "measurement_type": "area",
        "unit": "SF",
    })
    
    # Normalize name for display
    display_name = element_type.replace("_", " ").title()
    
    # Lock the project row to serialize condition creation for this project
    # This prevents race conditions where concurrent tasks both see no condition
    # and both try to create one with the same name
    db.query(Project).filter(Project.id == project_id).with_for_update().one()
    
    # Check if condition exists (by name or normalized name)
    condition = db.query(Condition).filter(
        Condition.project_id == project_id,
        Condition.name == display_name,
    ).one_or_none()
    
    if condition:
        return condition, False
    
    # Get max sort_order for this project to place new condition at end
    max_order = db.query(func.max(Condition.sort_order)).filter(
        Condition.project_id == project_id
    ).scalar() or 0
    
    # Create new condition using a savepoint to avoid rolling back the entire transaction
    # if there's an IntegrityError (which would lose all previous work in the transaction)
    savepoint = db.begin_nested()
    try:
        condition = Condition(
            id=uuid.uuid4(),
            project_id=project_id,
            name=display_name,
            scope="concrete",
            category=mapping["category"],
            measurement_type=mapping["measurement_type"],
            unit=mapping["unit"],
            color="#4CAF50",  # Default green
            is_ai_generated=True,
            sort_order=max_order + 1,
        )
        db.add(condition)
        db.flush()  # Get the ID
        
        return condition, True
    except IntegrityError:
        # Another transaction created the condition between our check and insert
        # (shouldn't happen with row locking, but handle defensively)
        # Roll back only the savepoint, not the entire transaction
        savepoint.rollback()
        condition = db.query(Condition).filter(
            Condition.project_id == project_id,
            Condition.name == display_name,
        ).one()
        return condition, False


@celery_app.task(bind=True, max_retries=3)
def autonomous_ai_takeoff_task(
    self,
    page_id: str,
    provider: str | None = None,
    project_id: str | None = None,
) -> dict:
    """Autonomous AI takeoff - AI identifies ALL concrete elements on its own.

    This is the true AI takeoff test - no pre-defined conditions or element
    types. The AI must independently identify what concrete elements exist
    on the drawing.

    Args:
        page_id: Page UUID as string
        provider: Optional LLM provider override
        project_id: Optional project ID for auto-creating conditions

    Returns:
        Result summary with all detected elements grouped by type
    """
    logger.info(
        "Starting AUTONOMOUS AI takeoff",
        page_id=page_id,
        provider=provider,
        project_id=project_id,
    )

    try:
        with SyncSession() as db:
            TaskTracker.mark_started_sync(db, self.request.id)

            _report_progress(self, db, 10, "Loading page data")

            page_uuid = uuid.UUID(page_id)
            project_uuid = uuid.UUID(project_id) if project_id else None

            # Get page
            page = db.query(Page).filter(Page.id == page_uuid).one_or_none()

            if not page:
                raise ValueError(f"Page not found: {page_id}")

            if not page.scale_calibrated or not page.scale_value:
                raise ValueError("Page must be calibrated before AI takeoff")

            # Verify project_id matches the page's project (if provided)
            document = db.query(Document).filter(Document.id == page.document_id).one()
            if project_uuid and project_uuid != document.project_id:
                raise ValueError("Provided project_id does not match the page's project")

            # Use the page's actual project if not provided
            if not project_uuid:
                project_uuid = document.project_id

            # Get page image
            storage = get_storage_service()
            image_bytes = storage.download_file(page.image_key)

            # Get AI takeoff service
            _report_progress(self, db, 30, "Running AI analysis")
            ai_service = get_ai_takeoff_service(provider=provider)

            # Run AUTONOMOUS analysis - AI determines what elements exist
            result = ai_service.analyze_page_autonomous(
                image_bytes=image_bytes,
                width=page.width,
                height=page.height,
                scale_text=page.scale_text,
                ocr_text=page.ocr_text,
            )

            # Group elements by type
            elements_by_type = {}
            for elem in result.elements:
                elem_type = elem.element_type
                if elem_type not in elements_by_type:
                    elements_by_type[elem_type] = []
                elements_by_type[elem_type].append(elem)

            # Create measurements if project_id provided
            _report_progress(self, db, 70, "Creating measurements")
            measurements_created = 0
            conditions_created = 0
            calculator = MeasurementCalculator(pixels_per_foot=page.scale_value)

            if project_uuid:
                for element_type, elements in elements_by_type.items():
                    # Get or create condition for this element type
                    condition, was_created = get_or_create_condition_for_element(
                        db, project_uuid, element_type
                    )
                    if was_created:
                        conditions_created += 1

                    # Create measurements
                    for elem in elements:
                        measurement = create_measurement_from_element(
                            page, condition, elem, calculator, result
                        )
                        if measurement:
                            db.add(measurement)
                            measurements_created += 1

                    # Update condition totals with row lock to prevent race conditions
                    from sqlalchemy import func
                    
                    # Lock the condition row to prevent concurrent updates
                    locked_condition = db.query(Condition).filter(
                        Condition.id == condition.id
                    ).with_for_update().one()
                    
                    totals = db.query(
                        func.sum(Measurement.quantity),
                        func.count(Measurement.id),
                    ).filter(Measurement.condition_id == condition.id).one()

                    locked_condition.total_quantity = totals[0] or 0.0
                    locked_condition.measurement_count = totals[1] or 0

            _report_progress(self, db, 90, "Finalizing")

            result_summary = {
                "page_id": page_id,
                "autonomous": True,
                "element_types_found": list(elements_by_type.keys()),
                "elements_by_type": {
                    et: [e.to_dict() for e in elems]
                    for et, elems in elements_by_type.items()
                },
                "total_elements": len(result.elements),
                "measurements_created": measurements_created,
                "conditions_created": conditions_created,
                "page_description": result.page_description,
                "analysis_notes": result.analysis_notes,
                "llm_provider": result.llm_provider,
                "llm_model": result.llm_model,
                "llm_latency_ms": result.llm_latency_ms,
            }

            TaskTracker.mark_completed_sync(
                db,
                self.request.id,
                result_summary,
                commit=False,
            )
            db.commit()

            logger.info(
                "AUTONOMOUS AI takeoff complete",
                page_id=page_id,
                element_types_found=list(elements_by_type.keys()),
                total_elements=len(result.elements),
                measurements_created=measurements_created,
                conditions_created=conditions_created,
                provider=result.llm_provider,
                model=result.llm_model,
                latency_ms=result.llm_latency_ms,
            )

            return result_summary

    except ValueError as e:
        # Validation errors (not found, not calibrated, etc.) should fail immediately
        # without retrying - they won't succeed on retry
        logger.error(
            "AUTONOMOUS AI takeoff validation failed (not retrying)",
            page_id=page_id,
            error=str(e),
        )
        with SyncSession() as db:
            TaskTracker.mark_failed_sync(db, self.request.id, str(e), tb_module.format_exc())
        raise
    except Exception as e:
        # Transient errors (network, API rate limits, etc.) can be retried
        logger.error(
            "AUTONOMOUS AI takeoff failed (will retry)",
            page_id=page_id,
            error=str(e),
        )
        original_traceback = tb_module.format_exc()
        try:
            raise self.retry(exc=e, countdown=60)
        except MaxRetriesExceededError:
            with SyncSession() as db:
                TaskTracker.mark_failed_sync(
                    db, self.request.id, str(e), original_traceback
                )
            raise
