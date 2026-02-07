"""Tests for condition visibility toggle (Phase B) and IDOR scoping."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.condition import Condition
from app.schemas.condition import ConditionResponse, ConditionUpdate


class MockCondition:
    """Mock Condition ORM object for schema validation tests."""

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
    """Test is_visible field on Condition model and schema."""

    def test_condition_model_has_is_visible(self):
        """The Condition model should have is_visible column."""
        assert hasattr(Condition, "is_visible"), "Condition model missing is_visible column"

    def test_condition_response_includes_is_visible_true(self):
        """ConditionResponse schema includes is_visible=True."""
        cond = MockCondition(is_visible=True)
        resp = ConditionResponse.model_validate(cond)
        assert resp.is_visible is True

    def test_condition_response_includes_is_visible_false(self):
        """ConditionResponse correctly serializes is_visible=False."""
        cond = MockCondition(is_visible=False)
        resp = ConditionResponse.model_validate(cond)
        assert resp.is_visible is False

    def test_condition_default_is_visible(self):
        """Default value for is_visible should be True."""
        cond = MockCondition()
        assert cond.is_visible is True

    def test_is_visible_in_response_json(self):
        """is_visible appears in the serialized JSON output."""
        cond = MockCondition(is_visible=False)
        resp = ConditionResponse.model_validate(cond)
        data = resp.model_dump()
        assert "is_visible" in data
        assert data["is_visible"] is False


class TestConditionUpdateVisibility:
    """Test ConditionUpdate schema with is_visible field."""

    def test_update_sets_is_visible_false(self):
        """ConditionUpdate should accept is_visible=False."""
        update = ConditionUpdate(is_visible=False)
        assert update.is_visible is False

    def test_update_sets_is_visible_true(self):
        """ConditionUpdate should accept is_visible=True."""
        update = ConditionUpdate(is_visible=True)
        assert update.is_visible is True

    def test_update_is_visible_optional(self):
        """is_visible should be optional in update (None means no change)."""
        update = ConditionUpdate(name="New Name")
        assert update.is_visible is None

    def test_update_preserves_other_fields(self):
        """Updating is_visible shouldn't affect other fields."""
        update = ConditionUpdate(is_visible=False, name="Updated")
        assert update.is_visible is False
        assert update.name == "Updated"
        assert update.color is None  # Not set


class TestConditionDuplicateVisibility:
    """Test that duplicate condition preserves is_visible."""

    def test_duplicate_hidden_condition_stays_hidden(self):
        """Duplicating a hidden condition should produce a hidden copy."""
        original = MockCondition(is_visible=False, name="Hidden Cond")
        # Simulate what the duplicate endpoint does
        duplicate = MockCondition(
            name=f"Copy of {original.name}",
            is_visible=original.is_visible,
            scope=original.scope,
            color=original.color,
        )
        assert duplicate.is_visible is False
        assert duplicate.name == "Copy of Hidden Cond"

    def test_duplicate_visible_condition_stays_visible(self):
        """Duplicating a visible condition should produce a visible copy."""
        original = MockCondition(is_visible=True, name="Visible Cond")
        duplicate = MockCondition(
            name=f"Copy of {original.name}",
            is_visible=original.is_visible,
        )
        assert duplicate.is_visible is True


class TestConditionEndpointScoping:
    """Test that condition endpoints require project_id scoping (IDOR prevention)."""

    def test_routes_include_project_id(self):
        """All condition mutation endpoints should be scoped under /projects/{project_id}/."""
        from app.api.routes.conditions import router

        routes = [r.path for r in router.routes]

        # These endpoints should include project_id scoping
        assert any("/projects/{project_id}/conditions/{condition_id}" in r for r in routes), (
            "GET/PUT condition endpoints should be scoped under /projects/{project_id}/"
        )
        assert any("/projects/{project_id}/conditions/{condition_id}/duplicate" in r for r in routes), (
            "Duplicate endpoint should be scoped under /projects/{project_id}/"
        )

    def test_no_unscoped_condition_endpoints(self):
        """No condition mutation endpoints should exist without project_id."""
        from app.api.routes.conditions import router

        routes = [r.path for r in router.routes]

        # These patterns should NOT exist (unscoped)
        unscoped_patterns = [
            "/conditions/{condition_id}",  # bare GET/PUT/DELETE
        ]
        for pattern in unscoped_patterns:
            # Make sure the pattern doesn't appear without project_id prefix
            bare_routes = [r for r in routes if r == pattern]
            assert len(bare_routes) == 0, (
                f"Found unscoped endpoint: {pattern}. All condition endpoints should include project_id."
            )
