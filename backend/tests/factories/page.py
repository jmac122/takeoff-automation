"""Page factory for tests."""

import uuid

import factory

from app.models.page import Page


class PageFactory(factory.Factory):
    class Meta:
        model = Page

    id = factory.LazyFunction(uuid.uuid4)
    document_id = factory.LazyFunction(uuid.uuid4)
    page_number = factory.Sequence(lambda n: n + 1)
    width = 2550
    height = 3300
    dpi = 150
    image_key = factory.LazyAttribute(lambda o: f"pages/{o.document_id}/{o.id}.png")
    status = "ready"
    sheet_number = factory.Sequence(lambda n: f"S-{n + 1:03d}")
    sheet_title = factory.Sequence(lambda n: f"Sheet {n + 1}")
    scale_value = 12.0
    scale_unit = "foot"
