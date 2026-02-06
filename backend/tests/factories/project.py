"""Project factory for tests."""

import uuid

import factory

from app.models.project import Project


class ProjectFactory(factory.Factory):
    class Meta:
        model = Project

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Test Project {n}")
    description = factory.Faker("sentence")
    client_name = factory.Faker("company")
    status = "draft"
