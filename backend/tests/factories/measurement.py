"""Measurement factory for tests."""

import uuid

import factory

from app.models.measurement import Measurement


class MeasurementFactory(factory.Factory):
    class Meta:
        model = Measurement

    id = factory.LazyFunction(uuid.uuid4)
    condition_id = factory.LazyFunction(uuid.uuid4)
    page_id = factory.LazyFunction(uuid.uuid4)
    geometry_type = "polygon"
    geometry_data = factory.LazyFunction(
        lambda: {
            "points": [
                {"x": 100, "y": 100},
                {"x": 200, "y": 100},
                {"x": 200, "y": 200},
                {"x": 100, "y": 200},
            ]
        }
    )
    quantity = factory.Faker("pyfloat", min_value=1.0, max_value=1000.0)
    unit = "SF"
    pixel_length = None
    pixel_area = factory.Faker("pyfloat", min_value=1000.0, max_value=100000.0)
    is_ai_generated = False
    is_verified = False
    is_modified = False
    notes = None
