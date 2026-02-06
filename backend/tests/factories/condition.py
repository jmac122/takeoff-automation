"""Condition factory for tests."""

import uuid

import factory

from app.models.condition import Condition


class ConditionFactory(factory.Factory):
    class Meta:
        model = Condition

    id = factory.LazyFunction(uuid.uuid4)
    project_id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Condition {n}")
    description = factory.Faker("sentence")
    scope = "concrete"
    category = "slab"
    measurement_type = "area"
    color = "#3B82F6"
    line_width = 2
    fill_opacity = 0.3
    unit = "SF"
    total_quantity = 0.0
    measurement_count = 0
    sort_order = factory.Sequence(lambda n: n)
    is_ai_generated = False
