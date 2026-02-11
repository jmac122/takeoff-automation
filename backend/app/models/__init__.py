"""Database models package."""

# Import all models to ensure they're registered with SQLAlchemy
from app.models.base import Base, UUIDMixin, TimestampMixin
from app.models.project import Project
from app.models.condition import Condition
from app.models.document import Document
from app.models.page import Page
from app.models.measurement import Measurement
from app.models.measurement_history import MeasurementHistory
from app.models.classification_history import ClassificationHistory
from app.models.task import TaskRecord
from app.models.export_job import ExportJob
from app.models.assembly import Assembly, AssemblyComponent, AssemblyTemplate, CostItem

__all__ = [
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "Project",
    "Condition",
    "Document",
    "Page",
    "Measurement",
    "MeasurementHistory",
    "ClassificationHistory",
    "TaskRecord",
    "ExportJob",
    "Assembly",
    "AssemblyComponent",
    "AssemblyTemplate",
    "CostItem",
]
