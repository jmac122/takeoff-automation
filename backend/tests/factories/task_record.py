"""Factory for TaskRecord test instances."""

import uuid
from datetime import datetime, timezone

import factory

from app.models.task import TaskRecord


class TaskRecordFactory(factory.Factory):
    class Meta:
        model = TaskRecord

    task_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    project_id = factory.LazyFunction(uuid.uuid4)
    task_type = "document_processing"
    task_name = factory.Sequence(lambda n: f"Test Task {n}")
    status = "PENDING"
    progress_percent = 0
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
