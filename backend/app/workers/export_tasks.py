"""Export generation Celery tasks.

Uses SYNCHRONOUS SQLAlchemy (psycopg2 driver) because Celery workers
run in a multiprocessing context where async database connections
(asyncpg) cause InterfaceError.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings
from app.models.export_job import ExportJob
from app.services.export.base import ExportData, ConditionData, MeasurementData
from app.services.export.excel_exporter import ExcelExporter
from app.services.export.ost_exporter import OSTExporter
from app.services.export.csv_exporter import CSVExporter
from app.services.export.pdf_exporter import PDFExporter
from app.services.task_tracker import TaskTracker
from app.utils.storage import get_storage_service
from app.workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()

# Sync engine for Celery workers
sync_database_url = str(settings.database_url).replace("+asyncpg", "")
sync_engine = create_engine(
    sync_database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SyncSession = sessionmaker(bind=sync_engine)

# Format → Exporter mapping
EXPORTERS = {
    "excel": ExcelExporter,
    "ost": OSTExporter,
    "csv": CSVExporter,
    "pdf": PDFExporter,
}


def _fetch_export_data_sync(db: Session, project_id: uuid.UUID, options: dict | None = None) -> ExportData:
    """Fetch project export data using sync SQLAlchemy queries."""
    from app.models.project import Project
    from app.models.condition import Condition
    from app.models.measurement import Measurement
    from app.models.page import Page

    project = db.query(Project).filter(Project.id == project_id).one_or_none()
    if not project:
        raise ValueError(f"Project not found: {project_id}")

    include_unverified = True
    if options and not options.get("include_unverified", True):
        include_unverified = False

    conditions = (
        db.query(Condition)
        .filter(Condition.project_id == project_id)
        .order_by(Condition.sort_order, Condition.name)
        .all()
    )

    condition_data_list = []
    for cond in conditions:
        measurements_query = (
            db.query(Measurement)
            .filter(Measurement.condition_id == cond.id)
        )
        if not include_unverified:
            measurements_query = measurements_query.filter(Measurement.is_verified == True)

        measurements = measurements_query.all()
        measurement_data_list = []
        for m in measurements:
            page = db.query(Page).filter(Page.id == m.page_id).one_or_none()
            measurement_data_list.append(
                MeasurementData(
                    id=m.id,
                    condition_name=cond.name,
                    condition_id=cond.id,
                    page_id=m.page_id,
                    page_number=page.page_number if page else 0,
                    sheet_number=page.sheet_number if page else None,
                    sheet_title=page.sheet_title if page else None,
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
                measurements=measurement_data_list,
            )
        )

    return ExportData(
        project_id=project.id,
        project_name=project.name,
        project_description=project.description,
        client_name=project.client_name,
        conditions=condition_data_list,
    )


@celery_app.task(bind=True, max_retries=2)
def generate_export_task(
    self,
    export_job_id: str,
    project_id: str,
    export_format: str,
    task_id: str,
    options: dict | None = None,
) -> dict:
    """Generate an export file for a project.

    Args:
        export_job_id: ExportJob UUID as string
        project_id: Project UUID as string
        export_format: Export format (excel, ost, csv, pdf)
        task_id: Pre-generated TaskRecord ID for tracking
        options: Format-specific options

    Returns:
        Result dictionary with file_key and status
    """
    logger.info(
        "Starting export generation",
        export_job_id=export_job_id,
        project_id=project_id,
        format=export_format,
        task_id=task_id,
    )

    with SyncSession() as db:
        try:
            # Mark started
            TaskTracker.mark_started_sync(db, task_id)
            TaskTracker.update_progress_sync(db, task_id, 10.0, "Initializing export")

            # Update ExportJob status
            export_job = db.get(ExportJob, uuid.UUID(export_job_id))
            if export_job:
                export_job.status = "processing"
                export_job.started_at = datetime.now(timezone.utc)
                db.commit()

            # Fetch data
            TaskTracker.update_progress_sync(db, task_id, 20.0, "Fetching project data")
            proj_uuid = uuid.UUID(project_id)
            export_data = _fetch_export_data_sync(db, proj_uuid, options)

            # Generate export
            TaskTracker.update_progress_sync(db, task_id, 50.0, f"Generating {export_format} file")
            exporter_cls = EXPORTERS.get(export_format)
            if not exporter_cls:
                raise ValueError(f"Unsupported export format: {export_format}")

            exporter = exporter_cls()
            file_bytes = exporter.generate(export_data, options)

            # Upload to storage
            TaskTracker.update_progress_sync(db, task_id, 90.0, "Uploading file")
            storage = get_storage_service()
            file_key = f"exports/{project_id}/{export_job_id}{exporter.file_extension}"
            storage.upload_bytes(file_bytes, file_key, exporter.content_type)

            # Update ExportJob
            export_job = db.get(ExportJob, uuid.UUID(export_job_id))
            if export_job:
                export_job.status = "completed"
                export_job.file_key = file_key
                export_job.file_size = len(file_bytes)
                export_job.completed_at = datetime.now(timezone.utc)

            # Mark completed
            TaskTracker.mark_completed_sync(
                db,
                task_id,
                result_summary={
                    "file_key": file_key,
                    "file_size": len(file_bytes),
                    "format": export_format,
                },
                commit=False,
            )
            db.commit()

            logger.info(
                "Export generation complete",
                export_job_id=export_job_id,
                file_key=file_key,
                file_size=len(file_bytes),
            )

            return {
                "status": "completed",
                "export_job_id": export_job_id,
                "file_key": file_key,
                "file_size": len(file_bytes),
            }

        except Exception as e:
            logger.error(
                "Export generation failed",
                export_job_id=export_job_id,
                error=str(e),
            )

            # Update ExportJob
            try:
                export_job = db.get(ExportJob, uuid.UUID(export_job_id))
                if export_job:
                    export_job.status = "failed"
                    export_job.error_message = str(e)
                    export_job.completed_at = datetime.now(timezone.utc)
                    db.commit()
            except Exception:
                pass

            # Mark task failed
            TaskTracker.mark_failed_sync(db, task_id, str(e))

            raise
