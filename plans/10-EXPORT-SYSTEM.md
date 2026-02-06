# Phase 5A: Export System
## Excel and OST Export Functionality

> **Duration**: Weeks 24-28
> **Prerequisites**: Review interface complete (Phase 4B), measurements approved/verified
> **Outcome**: Complete export system supporting Excel spreadsheets and On Screen Takeoff-compatible formats

---

## Context for LLM Assistant

You are implementing the export system for a construction takeoff platform. This phase enables:
- Excel export with detailed takeoff data, summaries, and formatting
- On Screen Takeoff (OST) XML format export for industry compatibility
- PDF report generation with measurement overlays
- CSV export for simple data exchange
- Export job queue for large exports
- Export history and re-download capability

### Export Workflow

```
1. User selects project/conditions to export
2. User chooses export format and options
3. System queues export job
4. Worker generates export file(s)
5. User downloads or receives notification
6. Export stored for future re-download
```

### Supported Export Formats

| Format | Extension | Use Case |
|--------|-----------|----------|
| Excel | `.xlsx` | Primary export for estimators, includes formulas |
| OST XML | `.xml` | Import into On Screen Takeoff software |
| CSV | `.csv` | Simple data exchange, database import |
| PDF Report | `.pdf` | Client-facing summary with images |
| JSON | `.json` | API/integration use |

---

## Database Models

### Task 10.1: Export Job Model

Create `backend/app/models/export.py`:

```python
"""Export job tracking model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.project import Project


class ExportJob(Base, UUIDMixin, TimestampMixin):
    """Tracks an export job and its output."""

    __tablename__ = "export_jobs"

    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Export configuration
    export_format: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # xlsx, ost_xml, csv, pdf, json
    
    export_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Scope - what to export
    scope_type: Mapped[str] = mapped_column(
        String(50),
        default="project",
    )  # project, conditions, pages
    
    condition_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    page_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    
    # Options
    include_images: Mapped[bool] = mapped_column(Boolean, default=False)
    include_summary: Mapped[bool] = mapped_column(Boolean, default=True)
    include_details: Mapped[bool] = mapped_column(Boolean, default=True)
    include_unverified: Mapped[bool] = mapped_column(Boolean, default=False)
    group_by: Mapped[str] = mapped_column(
        String(50),
        default="condition",
    )  # condition, page, csi_code
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
    )  # pending, processing, completed, failed
    
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    
    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Output
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    download_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    download_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Statistics
    conditions_exported: Mapped[int] = mapped_column(Integer, default=0)
    measurements_exported: Mapped[int] = mapped_column(Integer, default=0)
    pages_exported: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    requested_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    export_options: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="exports")


class ExportTemplate(Base, UUIDMixin, TimestampMixin):
    """Saved export templates for reuse."""

    __tablename__ = "export_templates"

    # Ownership
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,  # Null = global template
    )
    
    # Template info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Configuration
    export_format: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Column mappings for Excel/CSV
    column_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    
    # Styling for Excel
    style_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    
    # Options
    options: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
```

Update `backend/app/models/project.py` to add relationship:

```python
# Add to imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.export import ExportJob

# Add to Project class
exports: Mapped[list["ExportJob"]] = relationship(
    "ExportJob",
    back_populates="project",
    cascade="all, delete-orphan",
)
```

Create migration:

```bash
alembic revision --autogenerate -m "add_export_models"
alembic upgrade head
```

---

## Export Service

### Task 10.2: Base Export Service

Create `backend/app/services/export_service.py`:

```python
"""Export service for generating takeoff exports."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.export import ExportJob, ExportTemplate
from app.models.project import Project
from app.models.condition import Condition
from app.models.measurement import Measurement
from app.models.page import Page
from app.utils.storage import storage_client

logger = structlog.get_logger()


class ExportServiceError(Exception):
    """Base exception for export service."""
    pass


class BaseExporter(ABC):
    """Abstract base class for export implementations."""

    def __init__(self, session: AsyncSession, job: ExportJob):
        self.session = session
        self.job = job
        self.logger = logger.bind(
            export_job_id=str(job.id),
            export_format=job.export_format,
        )

    @abstractmethod
    async def generate(self) -> Path:
        """Generate the export file. Returns path to generated file."""
        pass

    async def get_export_data(self) -> dict[str, Any]:
        """Fetch all data needed for export."""
        # Get project
        project_result = await self.session.execute(
            select(Project).where(Project.id == self.job.project_id)
        )
        project = project_result.scalar_one()

        # Build condition query
        condition_query = (
            select(Condition)
            .where(Condition.project_id == self.job.project_id)
            .options(
                selectinload(Condition.measurements).selectinload(Measurement.page)
            )
        )

        # Filter by specific conditions if provided
        if self.job.condition_ids:
            condition_ids = [uuid.UUID(cid) for cid in self.job.condition_ids]
            condition_query = condition_query.where(Condition.id.in_(condition_ids))

        conditions_result = await self.session.execute(condition_query)
        conditions = list(conditions_result.scalars().all())

        # Filter measurements
        export_data = {
            "project": project,
            "conditions": [],
            "summary": {
                "total_conditions": 0,
                "total_measurements": 0,
                "by_unit": {},
                "by_csi_code": {},
            },
        }

        for condition in conditions:
            measurements = []
            for m in condition.measurements:
                # Skip unverified if not included
                if not self.job.include_unverified:
                    if m.review_status not in ("approved", "verified"):
                        continue
                
                # Filter by pages if specified
                if self.job.page_ids:
                    page_ids = [uuid.UUID(pid) for pid in self.job.page_ids]
                    if m.page_id not in page_ids:
                        continue
                
                measurements.append(m)

            if measurements:
                export_data["conditions"].append({
                    "condition": condition,
                    "measurements": measurements,
                })

                # Update summary
                export_data["summary"]["total_conditions"] += 1
                export_data["summary"]["total_measurements"] += len(measurements)

                # Aggregate by unit
                unit = condition.unit
                if unit not in export_data["summary"]["by_unit"]:
                    export_data["summary"]["by_unit"][unit] = {
                        "count": 0,
                        "total_quantity": 0,
                    }
                export_data["summary"]["by_unit"][unit]["count"] += len(measurements)
                export_data["summary"]["by_unit"][unit]["total_quantity"] += sum(
                    m.quantity for m in measurements
                )

                # Aggregate by CSI code
                csi = condition.csi_code or "Uncategorized"
                if csi not in export_data["summary"]["by_csi_code"]:
                    export_data["summary"]["by_csi_code"][csi] = {
                        "conditions": [],
                        "total_quantity": 0,
                    }
                export_data["summary"]["by_csi_code"][csi]["conditions"].append(
                    condition.name
                )
                export_data["summary"]["by_csi_code"][csi]["total_quantity"] += sum(
                    m.quantity for m in measurements
                )

        return export_data


class ExportService:
    """Main export service for managing export jobs."""

    EXPORTERS: dict[str, type[BaseExporter]] = {}  # Registered in submodules

    @classmethod
    def register_exporter(cls, format_name: str, exporter_class: type[BaseExporter]):
        """Register an exporter class for a format."""
        cls.EXPORTERS[format_name] = exporter_class

    async def create_export_job(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
        export_format: str,
        *,
        export_name: str | None = None,
        condition_ids: list[str] | None = None,
        page_ids: list[str] | None = None,
        include_images: bool = False,
        include_summary: bool = True,
        include_details: bool = True,
        include_unverified: bool = False,
        group_by: str = "condition",
        requested_by: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> ExportJob:
        """Create a new export job."""
        # Validate format
        if export_format not in self.EXPORTERS:
            raise ExportServiceError(f"Unsupported export format: {export_format}")

        # Get project for naming
        project_result = await session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise ExportServiceError(f"Project not found: {project_id}")

        # Generate export name if not provided
        if not export_name:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            export_name = f"{project.name}_takeoff_{timestamp}"

        job = ExportJob(
            project_id=project_id,
            export_format=export_format,
            export_name=export_name,
            condition_ids=condition_ids,
            page_ids=page_ids,
            include_images=include_images,
            include_summary=include_summary,
            include_details=include_details,
            include_unverified=include_unverified,
            group_by=group_by,
            requested_by=requested_by,
            export_options=options,
            status="pending",
        )

        session.add(job)
        await session.commit()
        await session.refresh(job)

        self.logger = logger.bind(export_job_id=str(job.id))
        self.logger.info("export_job_created", format=export_format)

        return job

    async def process_export(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
    ) -> ExportJob:
        """Process an export job."""
        # Get job
        job_result = await session.execute(
            select(ExportJob).where(ExportJob.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        if not job:
            raise ExportServiceError(f"Export job not found: {job_id}")

        log = logger.bind(export_job_id=str(job_id))

        try:
            # Update status
            job.status = "processing"
            job.started_at = datetime.utcnow()
            await session.commit()

            log.info("export_processing_started")

            # Get exporter
            exporter_class = self.EXPORTERS.get(job.export_format)
            if not exporter_class:
                raise ExportServiceError(f"No exporter for format: {job.export_format}")

            exporter = exporter_class(session, job)

            # Generate export
            output_path = await exporter.generate()

            # Upload to storage
            storage_path = f"exports/{job.project_id}/{job.id}/{output_path.name}"
            download_url = await storage_client.upload_file(
                output_path,
                storage_path,
            )

            # Update job
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.file_path = storage_path
            job.file_size = output_path.stat().st_size
            job.download_url = download_url
            job.download_expires_at = datetime.utcnow() + timedelta(days=7)

            await session.commit()
            await session.refresh(job)

            log.info(
                "export_completed",
                file_size=job.file_size,
                conditions=job.conditions_exported,
                measurements=job.measurements_exported,
            )

            # Cleanup temp file
            output_path.unlink(missing_ok=True)

        except Exception as e:
            log.error("export_failed", error=str(e))
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            await session.commit()
            raise

        return job

    async def get_export_job(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
    ) -> ExportJob | None:
        """Get an export job by ID."""
        result = await session.execute(
            select(ExportJob).where(ExportJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_export_jobs(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
        *,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ExportJob], int]:
        """List export jobs for a project."""
        query = (
            select(ExportJob)
            .where(ExportJob.project_id == project_id)
            .order_by(ExportJob.created_at.desc())
        )

        if status:
            query = query.where(ExportJob.status == status)

        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Get page
        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        jobs = list(result.scalars().all())

        return jobs, total

    async def refresh_download_url(
        self,
        session: AsyncSession,
        job_id: uuid.UUID,
    ) -> str:
        """Refresh the download URL for an export job."""
        job = await self.get_export_job(session, job_id)
        if not job:
            raise ExportServiceError(f"Export job not found: {job_id}")

        if job.status != "completed":
            raise ExportServiceError("Export job not completed")

        if not job.file_path:
            raise ExportServiceError("Export file not found")

        # Generate new presigned URL
        download_url = await storage_client.generate_presigned_url(
            job.file_path,
            expires_in=3600 * 24 * 7,  # 7 days
        )

        job.download_url = download_url
        job.download_expires_at = datetime.utcnow() + timedelta(days=7)
        await session.commit()

        return download_url


# Singleton
export_service = ExportService()


def get_export_service() -> ExportService:
    """Get the export service instance."""
    return export_service
```

---

### Task 10.3: Excel Exporter

Create `backend/app/services/exporters/excel_exporter.py`:

```python
"""Excel export implementation using openpyxl."""

import uuid
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, NamedStyle
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.chart import BarChart, Reference
import structlog

from app.services.export_service import BaseExporter, ExportService

logger = structlog.get_logger()


# Define styles
HEADER_STYLE = NamedStyle(name="header_style")
HEADER_STYLE.font = Font(bold=True, color="FFFFFF", size=11)
HEADER_STYLE.fill = PatternFill(start_color="2B579A", end_color="2B579A", fill_type="solid")
HEADER_STYLE.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
HEADER_STYLE.border = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)

TOTAL_STYLE = NamedStyle(name="total_style")
TOTAL_STYLE.font = Font(bold=True, size=11)
TOTAL_STYLE.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
TOTAL_STYLE.border = Border(
    top=Side(style="double"),
    bottom=Side(style="thin"),
)

NUMBER_FORMAT = "#,##0.00"
INTEGER_FORMAT = "#,##0"


class ExcelExporter(BaseExporter):
    """Generates Excel takeoff exports."""

    async def generate(self) -> Path:
        """Generate Excel export file."""
        self.logger.info("generating_excel_export")

        # Get data
        data = await self.get_export_data()

        # Create workbook
        wb = Workbook()

        # Add named styles
        if "header_style" not in wb.named_styles:
            wb.add_named_style(HEADER_STYLE)
        if "total_style" not in wb.named_styles:
            wb.add_named_style(TOTAL_STYLE)

        # Remove default sheet
        wb.remove(wb.active)

        # Create sheets
        if self.job.include_summary:
            self._create_summary_sheet(wb, data)

        if self.job.include_details:
            self._create_details_sheet(wb, data)
            self._create_by_page_sheet(wb, data)

        # Create condition breakdown sheets
        if self.job.group_by == "csi_code":
            self._create_csi_breakdown_sheet(wb, data)

        # Save to temp file
        temp_file = NamedTemporaryFile(
            suffix=".xlsx",
            delete=False,
            prefix=f"{self.job.export_name}_",
        )
        wb.save(temp_file.name)

        self.logger.info("excel_export_generated", path=temp_file.name)

        return Path(temp_file.name)

    def _create_summary_sheet(self, wb: Workbook, data: dict[str, Any]):
        """Create the summary sheet."""
        ws = wb.create_sheet("Summary")

        project = data["project"]
        summary = data["summary"]

        # Project header
        ws["A1"] = "TAKEOFF SUMMARY"
        ws["A1"].font = Font(bold=True, size=16)
        ws.merge_cells("A1:E1")

        # Project info
        ws["A3"] = "Project:"
        ws["B3"] = project.name
        ws["A4"] = "Client:"
        ws["B4"] = project.client_name or "N/A"
        ws["A5"] = "Address:"
        ws["B5"] = project.address or "N/A"
        ws["A6"] = "Export Date:"
        ws["B6"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        ws["A7"] = "Total Conditions:"
        ws["B7"] = summary["total_conditions"]
        ws["A8"] = "Total Measurements:"
        ws["B8"] = summary["total_measurements"]

        for row in range(3, 9):
            ws[f"A{row}"].font = Font(bold=True)

        # Totals by unit
        row = 10
        ws[f"A{row}"] = "TOTALS BY UNIT"
        ws[f"A{row}"].font = Font(bold=True, size=12)
        ws.merge_cells(f"A{row}:C{row}")
        row += 1

        # Headers
        ws[f"A{row}"] = "Unit"
        ws[f"B{row}"] = "Count"
        ws[f"C{row}"] = "Total Quantity"
        for col in ["A", "B", "C"]:
            ws[f"{col}{row}"].style = "header_style"
        row += 1

        for unit, values in summary["by_unit"].items():
            ws[f"A{row}"] = unit
            ws[f"B{row}"] = values["count"]
            ws[f"C{row}"] = values["total_quantity"]
            ws[f"C{row}"].number_format = NUMBER_FORMAT
            row += 1

        # Totals by CSI code
        row += 2
        ws[f"A{row}"] = "TOTALS BY CSI CODE"
        ws[f"A{row}"].font = Font(bold=True, size=12)
        ws.merge_cells(f"A{row}:C{row}")
        row += 1

        ws[f"A{row}"] = "CSI Code"
        ws[f"B{row}"] = "Conditions"
        ws[f"C{row}"] = "Total Quantity"
        for col in ["A", "B", "C"]:
            ws[f"{col}{row}"].style = "header_style"
        row += 1

        for csi, values in summary["by_csi_code"].items():
            ws[f"A{row}"] = csi
            ws[f"B{row}"] = len(values["conditions"])
            ws[f"C{row}"] = values["total_quantity"]
            ws[f"C{row}"].number_format = NUMBER_FORMAT
            row += 1

        # Adjust column widths
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 20
        ws.column_dimensions["C"].width = 20

    def _create_details_sheet(self, wb: Workbook, data: dict[str, Any]):
        """Create the detailed measurements sheet."""
        ws = wb.create_sheet("Details")

        # Headers
        headers = [
            "Condition",
            "CSI Code",
            "Description",
            "Page",
            "Quantity",
            "Unit",
            "Status",
            "AI Generated",
            "Confidence",
            "Notes",
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.style = "header_style"

        # Data rows
        row = 2
        for item in data["conditions"]:
            condition = item["condition"]
            for measurement in item["measurements"]:
                ws.cell(row=row, column=1, value=condition.name)
                ws.cell(row=row, column=2, value=condition.csi_code or "")
                ws.cell(row=row, column=3, value=condition.description or "")
                ws.cell(row=row, column=4, value=measurement.page.page_number)
                
                qty_cell = ws.cell(row=row, column=5, value=measurement.quantity)
                qty_cell.number_format = NUMBER_FORMAT
                
                ws.cell(row=row, column=6, value=measurement.unit)
                ws.cell(row=row, column=7, value=measurement.review_status)
                ws.cell(row=row, column=8, value="Yes" if measurement.is_ai_generated else "No")
                
                if measurement.ai_confidence:
                    conf_cell = ws.cell(row=row, column=9, value=measurement.ai_confidence)
                    conf_cell.number_format = "0.0%"
                
                ws.cell(row=row, column=10, value=measurement.notes or "")
                row += 1

        # Update job statistics
        self.job.conditions_exported = len(data["conditions"])
        self.job.measurements_exported = row - 2

        # Adjust column widths
        widths = [30, 15, 40, 10, 15, 10, 12, 12, 12, 30]
        for col, width in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

        # Add autofilter
        ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{row-1}"

        # Freeze header row
        ws.freeze_panes = "A2"

    def _create_by_page_sheet(self, wb: Workbook, data: dict[str, Any]):
        """Create sheet organized by page."""
        ws = wb.create_sheet("By Page")

        # Group measurements by page
        by_page: dict[int, list[dict]] = {}
        for item in data["conditions"]:
            condition = item["condition"]
            for measurement in item["measurements"]:
                page_num = measurement.page.page_number
                if page_num not in by_page:
                    by_page[page_num] = []
                by_page[page_num].append({
                    "condition": condition,
                    "measurement": measurement,
                })

        # Headers
        headers = ["Page", "Condition", "Quantity", "Unit", "Status"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.style = "header_style"

        # Data rows grouped by page
        row = 2
        for page_num in sorted(by_page.keys()):
            items = by_page[page_num]
            
            # Page header row
            ws.cell(row=row, column=1, value=f"Page {page_num}")
            ws[f"A{row}"].font = Font(bold=True)
            ws.merge_cells(f"A{row}:E{row}")
            ws[f"A{row}"].fill = PatternFill(
                start_color="D9E2F3",
                end_color="D9E2F3",
                fill_type="solid",
            )
            row += 1

            # Page measurements
            for item in items:
                ws.cell(row=row, column=1, value="")
                ws.cell(row=row, column=2, value=item["condition"].name)
                
                qty_cell = ws.cell(row=row, column=3, value=item["measurement"].quantity)
                qty_cell.number_format = NUMBER_FORMAT
                
                ws.cell(row=row, column=4, value=item["measurement"].unit)
                ws.cell(row=row, column=5, value=item["measurement"].review_status)
                row += 1

            row += 1  # Blank row between pages

        self.job.pages_exported = len(by_page)

        # Adjust widths
        ws.column_dimensions["A"].width = 12
        ws.column_dimensions["B"].width = 35
        ws.column_dimensions["C"].width = 15
        ws.column_dimensions["D"].width = 12
        ws.column_dimensions["E"].width = 12

    def _create_csi_breakdown_sheet(self, wb: Workbook, data: dict[str, Any]):
        """Create sheet organized by CSI code."""
        ws = wb.create_sheet("By CSI Code")

        # Group by CSI
        by_csi = data["summary"]["by_csi_code"]

        row = 1
        for csi, values in by_csi.items():
            # CSI header
            ws.cell(row=row, column=1, value=csi)
            ws[f"A{row}"].font = Font(bold=True, size=12)
            ws.merge_cells(f"A{row}:C{row}")
            ws[f"A{row}"].fill = PatternFill(
                start_color="2B579A",
                end_color="2B579A",
                fill_type="solid",
            )
            ws[f"A{row}"].font = Font(bold=True, color="FFFFFF")
            row += 1

            # Conditions in this CSI
            for cond_name in values["conditions"]:
                ws.cell(row=row, column=1, value=cond_name)
                row += 1

            # Total
            ws.cell(row=row, column=1, value="Total:")
            ws[f"A{row}"].font = Font(bold=True)
            ws.cell(row=row, column=2, value=values["total_quantity"])
            ws[f"B{row}"].number_format = NUMBER_FORMAT
            ws[f"B{row}"].font = Font(bold=True)
            row += 2

        ws.column_dimensions["A"].width = 40

    def _create_assembly_summary_section(self, ws, data: dict[str, Any], start_row: int) -> int:
        """Add assembly cost summary to summary sheet.
        
        NEW in v2.0: Adds cost breakdown by assembly type.
        """
        row = start_row
        
        # Check if assembly data exists
        if "assemblies" not in data or not data["assemblies"]:
            return row
        
        ws[f"A{row}"] = "ASSEMBLY COST SUMMARY"
        ws[f"A{row}"].font = Font(bold=True, size=12)
        ws.merge_cells(f"A{row}:E{row}")
        row += 1
        
        # Headers
        headers = ["Assembly", "Quantity", "Unit", "Unit Cost", "Total Cost"]
        for col, header in enumerate(headers, 1):
            ws.cell(row=row, column=col, value=header)
            ws.cell(row=row, column=col).style = "header_style"
        row += 1
        
        total_cost = 0
        for assembly in data["assemblies"]:
            ws.cell(row=row, column=1, value=assembly["name"])
            ws.cell(row=row, column=2, value=assembly["quantity"])
            ws[f"B{row}"].number_format = NUMBER_FORMAT
            ws.cell(row=row, column=3, value=assembly["unit"])
            ws.cell(row=row, column=4, value=assembly["unit_cost"])
            ws[f"D{row}"].number_format = CURRENCY_FORMAT
            ws.cell(row=row, column=5, value=assembly["total_cost"])
            ws[f"E{row}"].number_format = CURRENCY_FORMAT
            total_cost += assembly["total_cost"]
            row += 1
        
        # Total row
        ws.cell(row=row, column=1, value="TOTAL")
        ws[f"A{row}"].font = Font(bold=True)
        ws.cell(row=row, column=5, value=total_cost)
        ws[f"E{row}"].number_format = CURRENCY_FORMAT
        ws[f"E{row}"].style = "total_style"
        row += 2
        
        return row

    def _create_assembly_details_sheet(self, wb: Workbook, data: dict[str, Any]):
        """Create sheet with detailed assembly component breakdown.
        
        NEW in v2.0: Shows material, labor, equipment breakdown for each assembly.
        """
        if "assemblies" not in data or not data["assemblies"]:
            return
            
        ws = wb.create_sheet("Assembly Details")
        
        # Headers
        headers = [
            "Assembly",
            "Condition",
            "Component",
            "Type",
            "Formula",
            "Quantity",
            "Unit",
            "Unit Cost",
            "Total Cost",
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.style = "header_style"
        
        row = 2
        for assembly in data["assemblies"]:
            # Assembly header row
            ws.cell(row=row, column=1, value=assembly["name"])
            ws[f"A{row}"].font = Font(bold=True)
            
            condition_name = assembly.get("condition_name", "")
            ws.cell(row=row, column=2, value=condition_name)
            row += 1
            
            # Component rows
            for component in assembly.get("components", []):
                ws.cell(row=row, column=1, value="")  # Assembly name col empty
                ws.cell(row=row, column=2, value="")  # Condition col empty
                ws.cell(row=row, column=3, value=component["name"])
                ws.cell(row=row, column=4, value=component["type"])  # material, labor, equipment
                ws.cell(row=row, column=5, value=component.get("formula", ""))
                
                qty_cell = ws.cell(row=row, column=6, value=component["quantity"])
                qty_cell.number_format = NUMBER_FORMAT
                
                ws.cell(row=row, column=7, value=component["unit"])
                
                unit_cost_cell = ws.cell(row=row, column=8, value=component["unit_cost"])
                unit_cost_cell.number_format = CURRENCY_FORMAT
                
                total_cell = ws.cell(row=row, column=9, value=component["total_cost"])
                total_cell.number_format = CURRENCY_FORMAT
                row += 1
            
            # Assembly subtotal
            ws.cell(row=row, column=1, value="")
            ws.cell(row=row, column=8, value="Subtotal:")
            ws[f"H{row}"].font = Font(bold=True)
            subtotal_cell = ws.cell(row=row, column=9, value=assembly["total_cost"])
            subtotal_cell.number_format = CURRENCY_FORMAT
            subtotal_cell.font = Font(bold=True)
            row += 2  # Blank row between assemblies
        
        # Adjust column widths
        widths = [25, 25, 30, 12, 30, 12, 10, 15, 15]
        for col, width in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width
        
        # Add autofilter
        ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{row-1}"
        
        # Freeze header row
        ws.freeze_panes = "A2"

        ws.column_dimensions["B"].width = 20


# Register exporter
ExportService.register_exporter("xlsx", ExcelExporter)
```

---

### Task 10.4: On Screen Takeoff XML Exporter

Create `backend/app/services/exporters/ost_exporter.py`:

```python
"""On Screen Takeoff (OST) XML export implementation."""

import uuid
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from xml.etree.ElementTree import Element, SubElement, ElementTree
from xml.dom import minidom
import structlog

from app.services.export_service import BaseExporter, ExportService

logger = structlog.get_logger()


class OSTExporter(BaseExporter):
    """Generates On Screen Takeoff compatible XML exports.
    
    OST XML format reference based on common export structures.
    This produces an XML file that can be imported into On Screen Takeoff.
    """

    async def generate(self) -> Path:
        """Generate OST XML export file."""
        self.logger.info("generating_ost_xml_export")

        # Get data
        data = await self.get_export_data()

        # Create root element
        root = Element("OnScreenTakeoff")
        root.set("version", "1.0")
        root.set("exportDate", datetime.utcnow().isoformat())

        # Add project info
        self._add_project_element(root, data)

        # Add conditions (called "items" in OST)
        self._add_conditions_element(root, data)

        # Add measurements (called "quantities" in OST)
        self._add_measurements_element(root, data)

        # Pretty print XML
        xml_string = minidom.parseString(
            ElementTree.tostring(root, encoding="unicode")
        ).toprettyxml(indent="  ")

        # Save to temp file
        temp_file = NamedTemporaryFile(
            suffix=".xml",
            delete=False,
            prefix=f"{self.job.export_name}_ost_",
            mode="w",
            encoding="utf-8",
        )
        temp_file.write(xml_string)
        temp_file.close()

        self.logger.info("ost_xml_export_generated", path=temp_file.name)

        return Path(temp_file.name)

    def _add_project_element(self, root: Element, data: dict[str, Any]):
        """Add project information to XML."""
        project = data["project"]

        proj_elem = SubElement(root, "Project")
        
        SubElement(proj_elem, "Name").text = project.name
        SubElement(proj_elem, "Description").text = project.description or ""
        SubElement(proj_elem, "Client").text = project.client_name or ""
        SubElement(proj_elem, "Address").text = project.address or ""
        SubElement(proj_elem, "CreatedDate").text = project.created_at.isoformat()

    def _add_conditions_element(self, root: Element, data: dict[str, Any]):
        """Add conditions (items) to XML."""
        items_elem = SubElement(root, "Items")

        for idx, item in enumerate(data["conditions"]):
            condition = item["condition"]
            
            item_elem = SubElement(items_elem, "Item")
            item_elem.set("id", str(condition.id))
            item_elem.set("index", str(idx + 1))

            SubElement(item_elem, "Name").text = condition.name
            SubElement(item_elem, "Description").text = condition.description or ""
            SubElement(item_elem, "CSICode").text = condition.csi_code or ""
            
            # Unit type mapping for OST
            unit_type = self._map_unit_type(condition.unit)
            SubElement(item_elem, "UnitType").text = unit_type
            SubElement(item_elem, "Unit").text = condition.unit

            # Color (for visual identification in OST)
            SubElement(item_elem, "Color").text = condition.color or "#0000FF"

            # Calculate totals
            total_qty = sum(m.quantity for m in item["measurements"])
            SubElement(item_elem, "TotalQuantity").text = str(round(total_qty, 2))

        self.job.conditions_exported = len(data["conditions"])

    def _add_measurements_element(self, root: Element, data: dict[str, Any]):
        """Add measurements (quantities) to XML."""
        quantities_elem = SubElement(root, "Quantities")

        measurement_count = 0
        page_ids = set()

        for item in data["conditions"]:
            condition = item["condition"]

            for measurement in item["measurements"]:
                qty_elem = SubElement(quantities_elem, "Quantity")
                qty_elem.set("id", str(measurement.id))
                qty_elem.set("itemId", str(condition.id))

                # Page reference
                SubElement(qty_elem, "PageNumber").text = str(measurement.page.page_number)
                SubElement(qty_elem, "PageId").text = str(measurement.page_id)
                page_ids.add(str(measurement.page_id))

                # Geometry type mapping
                geom_type = self._map_geometry_type(measurement.geometry_type)
                SubElement(qty_elem, "GeometryType").text = geom_type

                # Quantity value
                SubElement(qty_elem, "Value").text = str(round(measurement.quantity, 4))
                SubElement(qty_elem, "Unit").text = measurement.unit

                # Geometry data (for reconstruction in OST)
                geom_elem = SubElement(qty_elem, "Geometry")
                self._add_geometry_data(geom_elem, measurement)

                # Status
                SubElement(qty_elem, "Status").text = measurement.review_status
                SubElement(qty_elem, "AIGenerated").text = str(measurement.is_ai_generated).lower()

                if measurement.ai_confidence:
                    SubElement(qty_elem, "AIConfidence").text = str(
                        round(measurement.ai_confidence, 3)
                    )

                if measurement.notes:
                    SubElement(qty_elem, "Notes").text = measurement.notes

                measurement_count += 1

        self.job.measurements_exported = measurement_count
        self.job.pages_exported = len(page_ids)

    def _add_geometry_data(self, parent: Element, measurement):
        """Add geometry data to XML element."""
        geom = measurement.geometry_data

        if measurement.geometry_type == "polygon":
            points_elem = SubElement(parent, "Points")
            for point in geom.get("points", []):
                pt_elem = SubElement(points_elem, "Point")
                pt_elem.set("x", str(round(point["x"], 2)))
                pt_elem.set("y", str(round(point["y"], 2)))

        elif measurement.geometry_type == "polyline":
            points_elem = SubElement(parent, "Points")
            for point in geom.get("points", []):
                pt_elem = SubElement(points_elem, "Point")
                pt_elem.set("x", str(round(point["x"], 2)))
                pt_elem.set("y", str(round(point["y"], 2)))

        elif measurement.geometry_type == "line":
            start = geom.get("start", {})
            end = geom.get("end", {})
            start_elem = SubElement(parent, "Start")
            start_elem.set("x", str(round(start.get("x", 0), 2)))
            start_elem.set("y", str(round(start.get("y", 0), 2)))
            end_elem = SubElement(parent, "End")
            end_elem.set("x", str(round(end.get("x", 0), 2)))
            end_elem.set("y", str(round(end.get("y", 0), 2)))

        elif measurement.geometry_type == "rectangle":
            SubElement(parent, "X").text = str(round(geom.get("x", 0), 2))
            SubElement(parent, "Y").text = str(round(geom.get("y", 0), 2))
            SubElement(parent, "Width").text = str(round(geom.get("width", 0), 2))
            SubElement(parent, "Height").text = str(round(geom.get("height", 0), 2))

        elif measurement.geometry_type == "circle":
            center = geom.get("center", {})
            SubElement(parent, "CenterX").text = str(round(center.get("x", 0), 2))
            SubElement(parent, "CenterY").text = str(round(center.get("y", 0), 2))
            SubElement(parent, "Radius").text = str(round(geom.get("radius", 0), 2))

        elif measurement.geometry_type == "point":
            SubElement(parent, "X").text = str(round(geom.get("x", 0), 2))
            SubElement(parent, "Y").text = str(round(geom.get("y", 0), 2))

    def _map_unit_type(self, unit: str) -> str:
        """Map unit to OST unit type."""
        unit_lower = unit.lower()
        
        linear_units = ["lf", "ft", "in", "m", "cm", "mm", "linear feet"]
        area_units = ["sf", "sq ft", "sq in", "sq m", "sq cm", "square feet"]
        volume_units = ["cf", "cu ft", "cu yd", "cy", "cubic yards", "cu m"]
        count_units = ["ea", "each", "count"]

        if any(u in unit_lower for u in linear_units):
            return "Linear"
        elif any(u in unit_lower for u in area_units):
            return "Area"
        elif any(u in unit_lower for u in volume_units):
            return "Volume"
        elif any(u in unit_lower for u in count_units):
            return "Count"
        else:
            return "Other"

    def _map_geometry_type(self, geom_type: str) -> str:
        """Map internal geometry type to OST type."""
        mapping = {
            "polygon": "Area",
            "polyline": "Linear",
            "line": "Linear",
            "rectangle": "Area",
            "circle": "Area",
            "point": "Count",
        }
        return mapping.get(geom_type, "Other")


# Register exporter
ExportService.register_exporter("ost_xml", OSTExporter)
```

---

### Task 10.5: CSV Exporter

Create `backend/app/services/exporters/csv_exporter.py`:

```python
"""CSV export implementation."""

import csv
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
import structlog

from app.services.export_service import BaseExporter, ExportService

logger = structlog.get_logger()


class CSVExporter(BaseExporter):
    """Generates CSV takeoff exports."""

    async def generate(self) -> Path:
        """Generate CSV export file."""
        self.logger.info("generating_csv_export")

        # Get data
        data = await self.get_export_data()

        # Determine columns based on options
        columns = self._get_columns()

        # Save to temp file
        temp_file = NamedTemporaryFile(
            suffix=".csv",
            delete=False,
            prefix=f"{self.job.export_name}_",
            mode="w",
            newline="",
            encoding="utf-8-sig",  # BOM for Excel compatibility
        )

        writer = csv.writer(temp_file)

        # Write header
        writer.writerow(columns)

        # Write data rows
        measurement_count = 0
        page_ids = set()

        for item in data["conditions"]:
            condition = item["condition"]

            for measurement in item["measurements"]:
                row = self._build_row(columns, condition, measurement)
                writer.writerow(row)
                measurement_count += 1
                page_ids.add(str(measurement.page_id))

        temp_file.close()

        # Update statistics
        self.job.conditions_exported = len(data["conditions"])
        self.job.measurements_exported = measurement_count
        self.job.pages_exported = len(page_ids)

        self.logger.info("csv_export_generated", path=temp_file.name)

        return Path(temp_file.name)

    def _get_columns(self) -> list[str]:
        """Get column headers based on export options."""
        columns = [
            "Condition Name",
            "CSI Code",
            "Description",
            "Page Number",
            "Quantity",
            "Unit",
            "Review Status",
        ]

        options = self.job.export_options or {}

        if options.get("include_ai_info", True):
            columns.extend(["AI Generated", "AI Confidence"])

        if options.get("include_geometry", False):
            columns.extend(["Geometry Type", "Geometry Data"])

        if options.get("include_review_info", True):
            columns.extend(["Reviewed By", "Reviewed At", "Notes"])

        if options.get("include_ids", False):
            columns.insert(0, "Measurement ID")
            columns.insert(1, "Condition ID")

        return columns

    def _build_row(self, columns: list[str], condition, measurement) -> list[Any]:
        """Build a CSV row for a measurement."""
        column_map = {
            "Measurement ID": str(measurement.id),
            "Condition ID": str(condition.id),
            "Condition Name": condition.name,
            "CSI Code": condition.csi_code or "",
            "Description": condition.description or "",
            "Page Number": measurement.page.page_number,
            "Quantity": round(measurement.quantity, 4),
            "Unit": measurement.unit,
            "Review Status": measurement.review_status,
            "AI Generated": "Yes" if measurement.is_ai_generated else "No",
            "AI Confidence": (
                f"{measurement.ai_confidence:.1%}"
                if measurement.ai_confidence
                else ""
            ),
            "Geometry Type": measurement.geometry_type,
            "Geometry Data": str(measurement.geometry_data),
            "Reviewed By": measurement.reviewed_by or "",
            "Reviewed At": (
                measurement.reviewed_at.isoformat()
                if measurement.reviewed_at
                else ""
            ),
            "Notes": measurement.notes or "",
        }

        return [column_map.get(col, "") for col in columns]


# Register exporter
ExportService.register_exporter("csv", CSVExporter)
```

---

### Task 10.6: PDF Report Exporter

Create `backend/app/services/exporters/pdf_exporter.py`:

```python
"""PDF report export implementation using ReportLab."""

from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import structlog

from app.services.export_service import BaseExporter, ExportService
from app.utils.storage import storage_client

logger = structlog.get_logger()


class PDFExporter(BaseExporter):
    """Generates PDF takeoff reports."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name="Title",
            parent=self.styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name="SectionHeader",
            parent=self.styles["Heading2"],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#2B579A"),
        ))
        self.styles.add(ParagraphStyle(
            name="TableHeader",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=colors.white,
        ))

    async def generate(self) -> Path:
        """Generate PDF report."""
        self.logger.info("generating_pdf_export")

        # Get data
        data = await self.get_export_data()

        # Create PDF
        temp_file = NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
            prefix=f"{self.job.export_name}_report_",
        )

        doc = SimpleDocTemplate(
            temp_file.name,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build content
        story = []

        # Title page
        story.extend(self._build_title_page(data))
        story.append(PageBreak())

        # Summary section
        if self.job.include_summary:
            story.extend(self._build_summary_section(data))
            story.append(PageBreak())

        # Details section
        if self.job.include_details:
            story.extend(self._build_details_section(data))

        # Build PDF
        doc.build(story)

        # Update statistics
        self.job.conditions_exported = len(data["conditions"])
        self.job.measurements_exported = data["summary"]["total_measurements"]

        self.logger.info("pdf_export_generated", path=temp_file.name)

        return Path(temp_file.name)

    def _build_title_page(self, data: dict[str, Any]) -> list:
        """Build the title page content."""
        project = data["project"]
        elements = []

        # Title
        elements.append(Spacer(1, 2 * inch))
        elements.append(Paragraph(
            "TAKEOFF REPORT",
            self.styles["Title"],
        ))
        elements.append(Spacer(1, 0.5 * inch))

        # Project name
        elements.append(Paragraph(
            project.name,
            ParagraphStyle(
                name="ProjectName",
                parent=self.styles["Normal"],
                fontSize=18,
                alignment=TA_CENTER,
            ),
        ))
        elements.append(Spacer(1, inch))

        # Project info table
        info_data = [
            ["Client:", project.client_name or "N/A"],
            ["Address:", project.address or "N/A"],
            ["Generated:", datetime.now().strftime("%B %d, %Y")],
            ["Total Conditions:", str(data["summary"]["total_conditions"])],
            ["Total Measurements:", str(data["summary"]["total_measurements"])],
        ]

        info_table = Table(info_data, colWidths=[1.5 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ]))

        elements.append(info_table)

        return elements

    def _build_summary_section(self, data: dict[str, Any]) -> list:
        """Build the summary section."""
        elements = []
        summary = data["summary"]

        elements.append(Paragraph("SUMMARY", self.styles["SectionHeader"]))
        elements.append(Spacer(1, 0.2 * inch))

        # Totals by unit
        elements.append(Paragraph("Totals by Unit", self.styles["Heading3"]))

        unit_data = [["Unit", "Count", "Total Quantity"]]
        for unit, values in summary["by_unit"].items():
            unit_data.append([
                unit,
                str(values["count"]),
                f"{values['total_quantity']:,.2f}",
            ])

        unit_table = Table(unit_data, colWidths=[2 * inch, 1.5 * inch, 2 * inch])
        unit_table.setStyle(self._get_table_style())
        elements.append(unit_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Totals by CSI code
        elements.append(Paragraph("Totals by CSI Code", self.styles["Heading3"]))

        csi_data = [["CSI Code", "Conditions", "Total Quantity"]]
        for csi, values in summary["by_csi_code"].items():
            csi_data.append([
                csi,
                str(len(values["conditions"])),
                f"{values['total_quantity']:,.2f}",
            ])

        csi_table = Table(csi_data, colWidths=[2 * inch, 1.5 * inch, 2 * inch])
        csi_table.setStyle(self._get_table_style())
        elements.append(csi_table)

        return elements

    def _build_details_section(self, data: dict[str, Any]) -> list:
        """Build the details section with condition breakdowns."""
        elements = []

        elements.append(Paragraph("CONDITION DETAILS", self.styles["SectionHeader"]))
        elements.append(Spacer(1, 0.2 * inch))

        for item in data["conditions"]:
            condition = item["condition"]
            measurements = item["measurements"]

            # Condition header
            elements.append(Paragraph(
                f"{condition.name}",
                ParagraphStyle(
                    name="ConditionName",
                    parent=self.styles["Heading3"],
                    textColor=colors.HexColor(condition.color or "#2B579A"),
                ),
            ))

            # Condition info
            if condition.description:
                elements.append(Paragraph(
                    condition.description,
                    self.styles["Normal"],
                ))

            info_text = f"CSI: {condition.csi_code or 'N/A'} | Unit: {condition.unit}"
            elements.append(Paragraph(
                info_text,
                ParagraphStyle(
                    name="ConditionInfo",
                    parent=self.styles["Normal"],
                    fontSize=9,
                    textColor=colors.gray,
                ),
            ))
            elements.append(Spacer(1, 0.1 * inch))

            # Measurements table
            detail_data = [["Page", "Quantity", "Status", "Notes"]]
            total_qty = 0

            for m in measurements:
                detail_data.append([
                    str(m.page.page_number),
                    f"{m.quantity:,.2f}",
                    m.review_status,
                    (m.notes or "")[:50],  # Truncate long notes
                ])
                total_qty += m.quantity

            # Add total row
            detail_data.append([
                "TOTAL",
                f"{total_qty:,.2f}",
                "",
                "",
            ])

            detail_table = Table(
                detail_data,
                colWidths=[0.8 * inch, 1.5 * inch, 1 * inch, 3 * inch],
            )
            detail_table.setStyle(self._get_table_style(has_total_row=True))
            elements.append(detail_table)
            elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _get_table_style(self, has_total_row: bool = False) -> TableStyle:
        """Get standard table style."""
        style = [
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B579A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            
            # Data rows
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),  # Numbers right-aligned
            
            # Borders
            ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
            
            # Alternating row colors
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
            
            # Padding
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]

        if has_total_row:
            style.extend([
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E7E6E6")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
            ])

        return TableStyle(style)


# Register exporter
ExportService.register_exporter("pdf", PDFExporter)
```

---

### Task 10.7: JSON Exporter

Create `backend/app/services/exporters/json_exporter.py`:

```python
"""JSON export implementation."""

import json
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import UUID
import structlog

from app.services.export_service import BaseExporter, ExportService

logger = structlog.get_logger()


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime and UUID."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class JSONExporter(BaseExporter):
    """Generates JSON takeoff exports."""

    async def generate(self) -> Path:
        """Generate JSON export file."""
        self.logger.info("generating_json_export")

        # Get data
        data = await self.get_export_data()

        # Build export structure
        export_data = self._build_export_structure(data)

        # Save to temp file
        temp_file = NamedTemporaryFile(
            suffix=".json",
            delete=False,
            prefix=f"{self.job.export_name}_",
            mode="w",
            encoding="utf-8",
        )

        json.dump(
            export_data,
            temp_file,
            cls=CustomJSONEncoder,
            indent=2,
            ensure_ascii=False,
        )
        temp_file.close()

        self.logger.info("json_export_generated", path=temp_file.name)

        return Path(temp_file.name)

    def _build_export_structure(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build the JSON export structure."""
        project = data["project"]

        export = {
            "exportInfo": {
                "format": "takeoff-platform-v1",
                "generatedAt": datetime.utcnow().isoformat(),
                "exportJobId": str(self.job.id),
            },
            "project": {
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "clientName": project.client_name,
                "address": project.address,
                "createdAt": project.created_at,
            },
            "summary": {
                "totalConditions": data["summary"]["total_conditions"],
                "totalMeasurements": data["summary"]["total_measurements"],
                "byUnit": data["summary"]["by_unit"],
                "byCSICode": data["summary"]["by_csi_code"],
            },
            "conditions": [],
        }

        # Add conditions and measurements
        page_ids = set()
        measurement_count = 0

        for item in data["conditions"]:
            condition = item["condition"]
            measurements_data = []

            for m in item["measurements"]:
                measurements_data.append({
                    "id": str(m.id),
                    "pageId": str(m.page_id),
                    "pageNumber": m.page.page_number,
                    "geometryType": m.geometry_type,
                    "geometryData": m.geometry_data,
                    "quantity": m.quantity,
                    "unit": m.unit,
                    "reviewStatus": m.review_status,
                    "isAIGenerated": m.is_ai_generated,
                    "aiConfidence": m.ai_confidence,
                    "reviewedBy": m.reviewed_by,
                    "reviewedAt": m.reviewed_at,
                    "notes": m.notes,
                })
                page_ids.add(str(m.page_id))
                measurement_count += 1

            export["conditions"].append({
                "id": str(condition.id),
                "name": condition.name,
                "description": condition.description,
                "csiCode": condition.csi_code,
                "unit": condition.unit,
                "color": condition.color,
                "totalQuantity": sum(m["quantity"] for m in measurements_data),
                "measurementCount": len(measurements_data),
                "measurements": measurements_data,
            })

        # Update statistics
        self.job.conditions_exported = len(export["conditions"])
        self.job.measurements_exported = measurement_count
        self.job.pages_exported = len(page_ids)

        return export


# Register exporter
ExportService.register_exporter("json", JSONExporter)
```

---

## API Routes

### Task 10.8: Export API Routes

Create `backend/app/api/routes/exports.py`:

```python
"""Export API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.export import (
    ExportJobCreate,
    ExportJobResponse,
    ExportJobListResponse,
    ExportTemplateCreate,
    ExportTemplateResponse,
)
from app.services.export_service import get_export_service, ExportServiceError
from app.workers.export_tasks import process_export_task

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/projects/{project_id}/export", response_model=ExportJobResponse)
async def create_export(
    project_id: uuid.UUID,
    data: ExportJobCreate,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Create a new export job."""
    export_service = get_export_service()

    try:
        job = await export_service.create_export_job(
            session,
            project_id,
            data.export_format,
            export_name=data.export_name,
            condition_ids=data.condition_ids,
            page_ids=data.page_ids,
            include_images=data.include_images,
            include_summary=data.include_summary,
            include_details=data.include_details,
            include_unverified=data.include_unverified,
            group_by=data.group_by,
            requested_by=data.requested_by,
            options=data.options,
        )

        # Queue background processing
        background_tasks.add_task(
            process_export_task,
            str(job.id),
        )

        return ExportJobResponse.model_validate(job)

    except ExportServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/exports", response_model=ExportJobListResponse)
async def list_exports(
    project_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List export jobs for a project."""
    export_service = get_export_service()

    jobs, total = await export_service.list_export_jobs(
        session,
        project_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return ExportJobListResponse(
        exports=[ExportJobResponse.model_validate(j) for j in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=ExportJobResponse)
async def get_export(
    job_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Get export job details."""
    export_service = get_export_service()
    job = await export_service.get_export_job(session, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    return ExportJobResponse.model_validate(job)


@router.post("/{job_id}/refresh-url")
async def refresh_download_url(
    job_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Refresh the download URL for an export."""
    export_service = get_export_service()

    try:
        url = await export_service.refresh_download_url(session, job_id)
        return {"download_url": url}
    except ExportServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{job_id}")
async def delete_export(
    job_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Delete an export job."""
    export_service = get_export_service()
    job = await export_service.get_export_job(session, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    # Delete file from storage if exists
    if job.file_path:
        from app.utils.storage import storage_client
        await storage_client.delete_file(job.file_path)

    await session.delete(job)
    await session.commit()

    return {"message": "Export deleted"}
```

---

### Task 10.9: Export Schemas

Create `backend/app/schemas/export.py`:

```python
"""Export schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExportJobCreate(BaseModel):
    """Schema for creating an export job."""

    export_format: str = Field(..., pattern="^(xlsx|ost_xml|csv|pdf|json)$")
    export_name: str | None = None
    
    # Scope
    condition_ids: list[str] | None = None
    page_ids: list[str] | None = None
    
    # Options
    include_images: bool = False
    include_summary: bool = True
    include_details: bool = True
    include_unverified: bool = False
    group_by: str = Field("condition", pattern="^(condition|page|csi_code)$")
    
    # Metadata
    requested_by: str | None = None
    options: dict[str, Any] | None = None


class ExportJobResponse(BaseModel):
    """Schema for export job response."""

    id: uuid.UUID
    project_id: uuid.UUID
    export_format: str
    export_name: str
    
    status: str
    progress: int
    
    started_at: datetime | None
    completed_at: datetime | None
    
    file_path: str | None
    file_size: int | None
    download_url: str | None
    download_expires_at: datetime | None
    
    error_message: str | None
    
    conditions_exported: int
    measurements_exported: int
    pages_exported: int
    
    requested_by: str | None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExportJobListResponse(BaseModel):
    """Schema for export job list response."""

    exports: list[ExportJobResponse]
    total: int
    limit: int
    offset: int


class ExportTemplateCreate(BaseModel):
    """Schema for creating an export template."""

    name: str
    description: str | None = None
    export_format: str
    column_config: dict[str, Any] | None = None
    style_config: dict[str, Any] | None = None
    options: dict[str, Any] | None = None


class ExportTemplateResponse(BaseModel):
    """Schema for export template response."""

    id: uuid.UUID
    project_id: uuid.UUID | None
    name: str
    description: str | None
    is_default: bool
    export_format: str
    column_config: dict[str, Any] | None
    style_config: dict[str, Any] | None
    options: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

---

### Task 10.10: Export Worker Tasks

Create `backend/app/workers/export_tasks.py`:

```python
"""Celery tasks for export processing."""

import uuid
import asyncio

from celery import shared_task
import structlog

from app.database import async_session_maker
from app.services.export_service import get_export_service

# Import exporters to register them
from app.services.exporters import (
    excel_exporter,
    ost_exporter,
    csv_exporter,
    pdf_exporter,
    json_exporter,
)

logger = structlog.get_logger()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def process_export_task(self, job_id: str):
    """Process an export job."""
    log = logger.bind(job_id=job_id, task_id=self.request.id)
    log.info("processing_export_task")

    asyncio.run(_process_export(job_id))


async def _process_export(job_id: str):
    """Async wrapper for export processing."""
    export_service = get_export_service()

    async with async_session_maker() as session:
        try:
            await export_service.process_export(session, uuid.UUID(job_id))
        except Exception as e:
            logger.error("export_task_failed", job_id=job_id, error=str(e))
            raise


@shared_task
def cleanup_expired_exports():
    """Cleanup exports older than retention period."""
    asyncio.run(_cleanup_expired_exports())


async def _cleanup_expired_exports():
    """Async cleanup of expired exports."""
    from datetime import datetime, timedelta
    from sqlalchemy import select, delete
    from app.models.export import ExportJob
    from app.utils.storage import storage_client

    async with async_session_maker() as session:
        # Find exports older than 30 days
        cutoff = datetime.utcnow() - timedelta(days=30)

        result = await session.execute(
            select(ExportJob).where(ExportJob.created_at < cutoff)
        )
        old_exports = result.scalars().all()

        for export in old_exports:
            # Delete file from storage
            if export.file_path:
                await storage_client.delete_file(export.file_path)

            await session.delete(export)

        await session.commit()

        logger.info("cleaned_up_expired_exports", count=len(old_exports))
```

Add to Celery beat schedule in `backend/app/workers/celery_app.py`:

```python
# Add to beat_schedule
app.conf.beat_schedule["cleanup-expired-exports"] = {
    "task": "app.workers.export_tasks.cleanup_expired_exports",
    "schedule": crontab(hour=2, minute=0),  # Run daily at 2 AM
}
```

---

## Frontend Components

### Task 10.11: Export Modal Component

Create `frontend/src/components/export/ExportModal.tsx`:

```tsx
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { apiClient } from '@/api/client';
import { FileSpreadsheet, FileText, FileCode, FileDown } from 'lucide-react';

interface ExportModalProps {
  projectId: string;
  projectName: string;
  conditions: Array<{ id: string; name: string }>;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ExportConfig {
  export_format: string;
  export_name: string;
  condition_ids: string[] | null;
  include_summary: boolean;
  include_details: boolean;
  include_unverified: boolean;
  group_by: string;
}

const FORMAT_INFO = {
  xlsx: {
    name: 'Excel',
    description: 'Detailed spreadsheet with formulas and formatting',
    icon: FileSpreadsheet,
  },
  ost_xml: {
    name: 'On Screen Takeoff',
    description: 'Import into On Screen Takeoff software',
    icon: FileCode,
  },
  csv: {
    name: 'CSV',
    description: 'Simple comma-separated values for data import',
    icon: FileText,
  },
  pdf: {
    name: 'PDF Report',
    description: 'Formatted report for clients and stakeholders',
    icon: FileDown,
  },
  json: {
    name: 'JSON',
    description: 'Structured data for API integrations',
    icon: FileCode,
  },
};

export function ExportModal({
  projectId,
  projectName,
  conditions,
  open,
  onOpenChange,
}: ExportModalProps) {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<ExportConfig>({
    export_format: 'xlsx',
    export_name: '',
    condition_ids: null,
    include_summary: true,
    include_details: true,
    include_unverified: false,
    group_by: 'condition',
  });
  const [selectedConditions, setSelectedConditions] = useState<Set<string>>(new Set());

  const createExportMutation = useMutation({
    mutationFn: async (data: ExportConfig) => {
      const response = await apiClient.post(
        `/projects/${projectId}/export`,
        {
          ...data,
          condition_ids: selectedConditions.size > 0 
            ? Array.from(selectedConditions)
            : null,
        }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports', projectId] });
      onOpenChange(false);
    },
  });

  const handleExport = () => {
    createExportMutation.mutate({
      ...config,
      export_name: config.export_name || `${projectName}_takeoff`,
    });
  };

  const toggleCondition = (id: string) => {
    const newSelected = new Set(selectedConditions);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedConditions(newSelected);
  };

  const selectAllConditions = () => {
    if (selectedConditions.size === conditions.length) {
      setSelectedConditions(new Set());
    } else {
      setSelectedConditions(new Set(conditions.map(c => c.id)));
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Export Takeoff</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="format" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="format">Format</TabsTrigger>
            <TabsTrigger value="scope">Scope</TabsTrigger>
            <TabsTrigger value="options">Options</TabsTrigger>
          </TabsList>

          <TabsContent value="format" className="space-y-4 pt-4">
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(FORMAT_INFO).map(([key, info]) => {
                const Icon = info.icon;
                return (
                  <button
                    key={key}
                    onClick={() => setConfig({ ...config, export_format: key })}
                    className={`flex items-start gap-3 p-4 rounded-lg border-2 transition-colors text-left ${
                      config.export_format === key
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <Icon className="h-5 w-5 mt-0.5 text-muted-foreground" />
                    <div>
                      <div className="font-medium">{info.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {info.description}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="space-y-2">
              <Label htmlFor="export-name">Export Name</Label>
              <Input
                id="export-name"
                placeholder={`${projectName}_takeoff`}
                value={config.export_name}
                onChange={(e) =>
                  setConfig({ ...config, export_name: e.target.value })
                }
              />
            </div>
          </TabsContent>

          <TabsContent value="scope" className="space-y-4 pt-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Conditions to Export</Label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={selectAllConditions}
                >
                  {selectedConditions.size === conditions.length
                    ? 'Deselect All'
                    : 'Select All'}
                </Button>
              </div>

              <div className="border rounded-lg max-h-60 overflow-y-auto">
                {conditions.length === 0 ? (
                  <div className="p-4 text-center text-muted-foreground">
                    No conditions available
                  </div>
                ) : (
                  conditions.map((condition) => (
                    <div
                      key={condition.id}
                      className="flex items-center gap-3 p-3 border-b last:border-0 hover:bg-muted/50"
                    >
                      <Checkbox
                        id={`condition-${condition.id}`}
                        checked={
                          selectedConditions.size === 0 ||
                          selectedConditions.has(condition.id)
                        }
                        onCheckedChange={() => toggleCondition(condition.id)}
                      />
                      <label
                        htmlFor={`condition-${condition.id}`}
                        className="flex-1 cursor-pointer"
                      >
                        {condition.name}
                      </label>
                    </div>
                  ))
                )}
              </div>

              <p className="text-sm text-muted-foreground">
                {selectedConditions.size === 0
                  ? 'All conditions will be exported'
                  : `${selectedConditions.size} condition(s) selected`}
              </p>
            </div>
          </TabsContent>

          <TabsContent value="options" className="space-y-4 pt-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Include Summary</Label>
                  <p className="text-sm text-muted-foreground">
                    Add summary sheet with totals
                  </p>
                </div>
                <Checkbox
                  checked={config.include_summary}
                  onCheckedChange={(checked) =>
                    setConfig({ ...config, include_summary: !!checked })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Include Details</Label>
                  <p className="text-sm text-muted-foreground">
                    Add detailed measurement breakdown
                  </p>
                </div>
                <Checkbox
                  checked={config.include_details}
                  onCheckedChange={(checked) =>
                    setConfig({ ...config, include_details: !!checked })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Include Unverified</Label>
                  <p className="text-sm text-muted-foreground">
                    Export measurements not yet reviewed
                  </p>
                </div>
                <Checkbox
                  checked={config.include_unverified}
                  onCheckedChange={(checked) =>
                    setConfig({ ...config, include_unverified: !!checked })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>Group By</Label>
                <Select
                  value={config.group_by}
                  onValueChange={(v) => setConfig({ ...config, group_by: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="condition">Condition</SelectItem>
                    <SelectItem value="page">Page</SelectItem>
                    <SelectItem value="csi_code">CSI Code</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleExport}
            disabled={createExportMutation.isPending}
          >
            {createExportMutation.isPending ? 'Creating...' : 'Export'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

---

### Task 10.12: Export History Component

Create `frontend/src/components/export/ExportHistory.tsx`:

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { apiClient } from '@/api/client';
import {
  Download,
  MoreHorizontal,
  RefreshCw,
  Trash2,
  FileSpreadsheet,
  FileText,
  FileCode,
} from 'lucide-react';

interface ExportHistoryProps {
  projectId: string;
}

interface ExportJob {
  id: string;
  export_format: string;
  export_name: string;
  status: string;
  progress: number;
  file_size: number | null;
  download_url: string | null;
  download_expires_at: string | null;
  conditions_exported: number;
  measurements_exported: number;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

const STATUS_BADGES = {
  pending: { variant: 'secondary' as const, label: 'Pending' },
  processing: { variant: 'default' as const, label: 'Processing' },
  completed: { variant: 'success' as const, label: 'Completed' },
  failed: { variant: 'destructive' as const, label: 'Failed' },
};

const FORMAT_ICONS = {
  xlsx: FileSpreadsheet,
  ost_xml: FileCode,
  csv: FileText,
  pdf: FileText,
  json: FileCode,
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function ExportHistory({ projectId }: ExportHistoryProps) {
  const queryClient = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['exports', projectId],
    queryFn: async () => {
      const response = await apiClient.get(`/projects/${projectId}/exports`);
      return response.data;
    },
    refetchInterval: (query) => {
      // Poll if any exports are processing
      const data = query.state.data as { exports: ExportJob[] } | undefined;
      const hasProcessing = data?.exports?.some(
        (e) => e.status === 'pending' || e.status === 'processing'
      );
      return hasProcessing ? 3000 : false;
    },
  });

  const refreshUrlMutation = useMutation({
    mutationFn: async (jobId: string) => {
      const response = await apiClient.post(`/exports/${jobId}/refresh-url`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports', projectId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (jobId: string) => {
      await apiClient.delete(`/exports/${jobId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports', projectId] });
    },
  });

  const handleDownload = (job: ExportJob) => {
    if (job.download_url) {
      window.open(job.download_url, '_blank');
    }
  };

  const isUrlExpired = (expiresAt: string | null): boolean => {
    if (!expiresAt) return true;
    return new Date(expiresAt) < new Date();
  };

  if (isLoading) {
    return <div className="p-4 text-center text-muted-foreground">Loading...</div>;
  }

  const exports: ExportJob[] = data?.exports || [];

  if (exports.length === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        <FileSpreadsheet className="h-12 w-12 mx-auto mb-3 opacity-50" />
        <p>No exports yet</p>
        <p className="text-sm">Create an export to see it here</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Export History</h3>
        <Button variant="ghost" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-1" />
          Refresh
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Export</TableHead>
            <TableHead>Format</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Size</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {exports.map((job) => {
            const FormatIcon = FORMAT_ICONS[job.export_format as keyof typeof FORMAT_ICONS] || FileText;
            const statusInfo = STATUS_BADGES[job.status as keyof typeof STATUS_BADGES];

            return (
              <TableRow key={job.id}>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <FormatIcon className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{job.export_name}</span>
                  </div>
                  {job.status === 'completed' && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {job.conditions_exported} conditions, {job.measurements_exported} measurements
                    </div>
                  )}
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="uppercase">
                    {job.export_format}
                  </Badge>
                </TableCell>
                <TableCell>
                  {job.status === 'processing' ? (
                    <div className="space-y-1">
                      <Badge variant={statusInfo?.variant}>{statusInfo?.label}</Badge>
                      <Progress value={job.progress} className="h-1 w-20" />
                    </div>
                  ) : (
                    <Badge variant={statusInfo?.variant}>{statusInfo?.label}</Badge>
                  )}
                  {job.error_message && (
                    <p className="text-xs text-destructive mt-1">{job.error_message}</p>
                  )}
                </TableCell>
                <TableCell>
                  {job.file_size ? formatFileSize(job.file_size) : '-'}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {job.status === 'completed' && (
                        <>
                          {isUrlExpired(job.download_expires_at) ? (
                            <DropdownMenuItem
                              onClick={() => refreshUrlMutation.mutate(job.id)}
                            >
                              <RefreshCw className="h-4 w-4 mr-2" />
                              Refresh Download Link
                            </DropdownMenuItem>
                          ) : (
                            <DropdownMenuItem onClick={() => handleDownload(job)}>
                              <Download className="h-4 w-4 mr-2" />
                              Download
                            </DropdownMenuItem>
                          )}
                        </>
                      )}
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => deleteMutation.mutate(job.id)}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
```

---

### Task 10.13: Export API Client

Create `frontend/src/api/exports.ts`:

```typescript
import { apiClient } from './client';

export interface ExportJobCreate {
  export_format: 'xlsx' | 'ost_xml' | 'csv' | 'pdf' | 'json';
  export_name?: string;
  condition_ids?: string[];
  page_ids?: string[];
  include_images?: boolean;
  include_summary?: boolean;
  include_details?: boolean;
  include_unverified?: boolean;
  group_by?: 'condition' | 'page' | 'csi_code';
  requested_by?: string;
  options?: Record<string, unknown>;
}

export interface ExportJob {
  id: string;
  project_id: string;
  export_format: string;
  export_name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  started_at: string | null;
  completed_at: string | null;
  file_path: string | null;
  file_size: number | null;
  download_url: string | null;
  download_expires_at: string | null;
  error_message: string | null;
  conditions_exported: number;
  measurements_exported: number;
  pages_exported: number;
  requested_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExportJobList {
  exports: ExportJob[];
  total: number;
  limit: number;
  offset: number;
}

export const exportsApi = {
  create: async (projectId: string, data: ExportJobCreate): Promise<ExportJob> => {
    const response = await apiClient.post(`/projects/${projectId}/export`, data);
    return response.data;
  },

  list: async (
    projectId: string,
    params?: { status?: string; limit?: number; offset?: number }
  ): Promise<ExportJobList> => {
    const response = await apiClient.get(`/projects/${projectId}/exports`, { params });
    return response.data;
  },

  get: async (jobId: string): Promise<ExportJob> => {
    const response = await apiClient.get(`/exports/${jobId}`);
    return response.data;
  },

  refreshUrl: async (jobId: string): Promise<{ download_url: string }> => {
    const response = await apiClient.post(`/exports/${jobId}/refresh-url`);
    return response.data;
  },

  delete: async (jobId: string): Promise<void> => {
    await apiClient.delete(`/exports/${jobId}`);
  },
};
```

---

### Task 10.14: Export Hook

Create `frontend/src/hooks/useExports.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { exportsApi, ExportJobCreate, ExportJob, ExportJobList } from '@/api/exports';

export function useExports(projectId: string, options?: { status?: string }) {
  return useQuery<ExportJobList>({
    queryKey: ['exports', projectId, options],
    queryFn: () => exportsApi.list(projectId, options),
    refetchInterval: (query) => {
      const data = query.state.data;
      const hasProcessing = data?.exports?.some(
        (e) => e.status === 'pending' || e.status === 'processing'
      );
      return hasProcessing ? 3000 : false;
    },
  });
}

export function useExport(jobId: string) {
  return useQuery<ExportJob>({
    queryKey: ['export', jobId],
    queryFn: () => exportsApi.get(jobId),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.status === 'pending' || data?.status === 'processing' ? 2000 : false;
    },
  });
}

export function useCreateExport(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ExportJobCreate) => exportsApi.create(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports', projectId] });
    },
  });
}

export function useRefreshExportUrl() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: exportsApi.refreshUrl,
    onSuccess: (_, jobId) => {
      queryClient.invalidateQueries({ queryKey: ['export', jobId] });
    },
  });
}

export function useDeleteExport(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: exportsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports', projectId] });
    },
  });
}
```

---

## Requirements Updates

### Task 10.15: Update Requirements

Add to `backend/requirements.txt`:

```txt
# Export libraries
openpyxl>=3.1.2
reportlab>=4.0.4
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] Excel export generates valid .xlsx file with summary and details sheets
- [ ] Excel export includes Assembly Cost Summary section (if assemblies exist)
- [ ] Excel export includes Assembly Details sheet with component breakdown (NEW v2.0)
- [ ] OST XML export generates valid XML importable into On Screen Takeoff
- [ ] CSV export generates valid CSV with correct encoding
- [ ] PDF export generates formatted report with tables
- [ ] JSON export generates valid JSON structure
- [ ] Export jobs track progress correctly
- [ ] Download URLs work and can be refreshed
- [ ] Expired exports are cleaned up by scheduled task
- [ ] Export modal allows format selection and configuration
- [ ] Export history shows all exports with status
- [ ] Filtering by conditions works correctly
- [ ] Group by options work for all formats

### Test Cases

1. Create Excel export → Download and verify in Excel
2. Create OST XML export → Verify XML structure
3. Create export with specific conditions → Only those conditions exported
4. Create export excluding unverified → Only approved/verified measurements
5. Export large project → Progress updates in real-time
6. Cancel and retry failed export → Handles gracefully
7. Download expired export → Refresh URL works
8. Wait 30+ days → Old exports cleaned up
9. Export project with assemblies → Assembly Cost Summary appears in summary sheet (NEW v2.0)
10. Export project with assemblies → Assembly Details sheet shows component breakdown (NEW v2.0)
11. Verify assembly unit costs and totals calculate correctly (NEW v2.0)
12. Export project without assemblies → Assembly sheets/sections gracefully omitted (NEW v2.0)

---

## Next Phase

Once verified, proceed to **`11-TESTING-QA.md`** for implementing comprehensive testing and quality assurance.
