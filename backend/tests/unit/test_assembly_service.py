"""Unit tests for the assembly service."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.assembly_service import AssemblyService
from app.services.formula_engine import FormulaContext


@pytest.fixture
def service():
    return AssemblyService()


# ---------------------------------------------------------------------------
# FormulaContext building
# ---------------------------------------------------------------------------


class TestBuildFormulaContext:
    def test_builds_context_from_condition(self, service):
        condition = MagicMock()
        condition.total_quantity = 1000.0
        condition.depth = 4.0
        condition.thickness = 6.0

        ctx = service._build_formula_context(condition)

        assert isinstance(ctx, FormulaContext)
        assert ctx.qty == 1000.0
        assert ctx.depth == 4.0
        assert ctx.thickness == 6.0
        assert ctx.perimeter == 0.0
        assert ctx.count == 0

    def test_handles_none_values(self, service):
        condition = MagicMock()
        condition.total_quantity = None
        condition.depth = None
        condition.thickness = None

        ctx = service._build_formula_context(condition)

        assert ctx.qty == 0.0
        assert ctx.depth == 0.0
        assert ctx.thickness == 0.0


# ---------------------------------------------------------------------------
# Lock enforcement
# ---------------------------------------------------------------------------


class TestLockEnforcement:
    @pytest.mark.asyncio
    async def test_update_assembly_locked_raises(self, service):
        mock_assembly = MagicMock()
        mock_assembly.is_locked = True

        mock_session = AsyncMock()
        with patch.object(service, "get_assembly", return_value=mock_assembly):
            with pytest.raises(ValueError, match="locked"):
                await service.update_assembly(
                    session=mock_session,
                    assembly_id=uuid.uuid4(),
                    name="new name",
                )

    @pytest.mark.asyncio
    async def test_delete_assembly_locked_raises(self, service):
        mock_assembly = MagicMock()
        mock_assembly.is_locked = True

        mock_session = AsyncMock()
        with patch.object(service, "get_assembly", return_value=mock_assembly):
            with pytest.raises(ValueError, match="locked"):
                await service.delete_assembly(
                    session=mock_session,
                    assembly_id=uuid.uuid4(),
                )

    @pytest.mark.asyncio
    async def test_add_component_locked_raises(self, service):
        mock_assembly = MagicMock()
        mock_assembly.is_locked = True
        mock_assembly.components = []

        mock_session = AsyncMock()
        with patch.object(service, "get_assembly", return_value=mock_assembly):
            with pytest.raises(ValueError, match="locked"):
                await service.add_component(
                    session=mock_session,
                    assembly_id=uuid.uuid4(),
                    name="Test",
                    unit="SF",
                )
