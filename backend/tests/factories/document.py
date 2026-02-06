"""Document factory for tests."""

import uuid

import factory

from app.models.document import Document


class DocumentFactory(factory.Factory):
    class Meta:
        model = Document

    id = factory.LazyFunction(uuid.uuid4)
    project_id = factory.LazyFunction(uuid.uuid4)
    filename = factory.Sequence(lambda n: f"document_{n}.pdf")
    original_filename = factory.Sequence(lambda n: f"Original Document {n}.pdf")
    file_type = "pdf"
    file_size = 1024000
    mime_type = "application/pdf"
    storage_key = factory.LazyAttribute(lambda o: f"documents/{o.project_id}/{o.id}.pdf")
    status = "ready"
    page_count = 1
