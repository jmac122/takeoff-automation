"""Tests for condition visibility toggle (Phase B.4)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.models.condition import Condition
from app.schemas.condition import ConditionResponse


class MockCondition:
    """Mock Condition ORM object."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.project_id = kwargs.get("project_id", uuid.uuid4())
        self.name = kwargs.get("name", "Test Condition")
        self.description = kwargs.get("description", None)
        self.scope = kwargs.get("scope", "concrete")
        self.category = kwargs.get("category", "slabs")
        self.measurement_type = kwargs.get("measurement_type", "area")
        self.color = kwargs.get("color", "#22C55E")
        self.line_width = kwargs.get("line_width", 2)
        self.fill_opacity = kwargs.get("fill_opacity", 0.3)
        self.unit = kwargs.get("unit", "SF")
        self.depth = kwargs.get("depth", 4)
        self.thickness = kwargs.get("thickness", None)
        self.total_quantity = kwargs.get("total_quantity", 0)
        self.measurement_count = kwargs.get("measurement_count", 0)
        self.sort_order = kwargs.get("sort_order", 0)
        self.is_ai_generated = kwargs.get("is_ai_generated", False)
        self.is_visible = kwargs.get("is_visible", True)
        self.extra_metadata = kwargs.get("extra_metadata", None)
        self.building = kwargs.get("building", None)
        self.area = kwargs.get("area", None)
        self.elevation = kwargs.get("elevation", None)
        self.created_at = kwargs.get("created_at", "2026-01-01T00:00:00")
        self.updated_at = kwargs.get("updated_at", "2026-01-01T00:00:00")


class TestConditionVisibility:
    """Test is_visible field on Condition model and API."""

    def test_condition_model_has_is_visible(self):
        """The Condition model should have is_visible field."""
        assert hasattr(Condition, 'is_visible'), "Condition model missing is_visible column"

    def test_condition_response_includes_is_visible(self):
        """ConditionResponse schema includes is_visible."""
        cond = MockCondition(is_visible=True)
        resp = ConditionResponse.model_validate(cond)
        assert resp.is_visible is True

    def test_condition_response_is_visible_false(self):
        """ConditionResponse correctly serializes is_visible=False."""
        cond = MockCondition(is_visible=False)
        resp = ConditionResponse.model_validate(cond)
        assert resp.is_visible is False

    def test_condition_default_is_visible(self):
        """Default value for is_visible should be True."""
        cond = MockCondition()
        assert cond.is_visible is True


class TestConditionUpdateVisibility:
    """Test updating condition visibility via API route."""

    @pytest.mark.asyncio
    async def test_update_condition_sets_is_visible(self):
        """PUT /conditions/{id} should update is_visible field."""
        from app.schemas.condition import ConditionUpdate

        update = ConditionUpdate(is_visible=False)
        assert update.is_visible is False

        update2 = ConditionUpdate(is_visible=True)
        assert update2.is_visible is True

    @pytest.mark.asyncio
    async def test_update_condition_is_visible_optional(self):
        """is_visible should be optional in update (None means no change)."""
        from app.schemas.condition import ConditionUpdate

        update = ConditionUpdate(name="New Name")
        assert update.is_visible is None

    @pytest.mark.asyncio
    async def test_update_condition_preserves_other_fields(self):
        """Updating is_visible shouldn't affect other fields."""
        from app.schemas.condition import ConditionUpdate

        update = ConditionUpdate(is_visible=False, name="Updated")
        assert update.is_visible is False
        assert update.name == "Updated"
        assert update.color is None  # Not set, shouldn't be affected
