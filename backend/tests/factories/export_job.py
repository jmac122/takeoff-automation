"""ExportJob factory for tests."""

import uuid

import factory

from app.models.export_job import ExportJob


class ExportJobFactory(factory.Factory):
    class Meta:
        model = ExportJob

    id = factory.LazyFunction(uuid.uuid4)
    project_id = factory.LazyFunction(uuid.uuid4)
    format = "excel"
    status = "pending"
    file_key = None
    file_size = None
    error_message = None
    options = None
