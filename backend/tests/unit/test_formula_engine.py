"""Unit tests for the formula engine."""

import pytest

from app.services.formula_engine import (
    FORMULA_PRESETS,
    FormulaContext,
    FormulaEngine,
    get_formula_engine,
)


@pytest.fixture
def engine():
    return FormulaEngine()


@pytest.fixture
def default_context():
    return FormulaContext(qty=1000.0, depth=4.0, thickness=6.0)


# ---------------------------------------------------------------------------
# Basic formulas
# ---------------------------------------------------------------------------


class TestSimpleFormulas:
    def test_direct_quantity(self, engine, default_context):
        result = engine.evaluate("{qty}", default_context)
        assert result == 1000.0

    def test_empty_formula_returns_qty(self, engine, default_context):
        result = engine.evaluate("", default_context)
        assert result == 1000.0

    def test_whitespace_formula_returns_qty(self, engine, default_context):
        result = engine.evaluate("   ", default_context)
        assert result == 1000.0

    def test_waste_factor(self, engine, default_context):
        result = engine.evaluate("{qty} * 1.05", default_context)
        assert abs(result - 1050.0) < 0.001

    def test_sf_to_cy_conversion(self, engine, default_context):
        result = engine.evaluate("{qty} * {depth} / 12 / 27", default_context)
        expected = 1000.0 * 4.0 / 12 / 27
        assert abs(result - expected) < 0.001

    def test_multiplication(self, engine, default_context):
        result = engine.evaluate("{qty} * 0.89", default_context)
        assert abs(result - 890.0) < 0.001

    def test_constant_expression(self, engine, default_context):
        result = engine.evaluate("42", default_context)
        assert result == 42.0


# ---------------------------------------------------------------------------
# Computed variables
# ---------------------------------------------------------------------------


class TestComputedVariables:
    def test_depth_ft(self, engine):
        ctx = FormulaContext(qty=100.0, depth=6.0)
        result = engine.evaluate("{depth_ft}", ctx)
        assert result == 0.5

    def test_thickness_ft(self, engine):
        ctx = FormulaContext(qty=100.0, thickness=12.0)
        result = engine.evaluate("{thickness_ft}", ctx)
        assert result == 1.0

    def test_volume_cf(self, engine):
        ctx = FormulaContext(qty=100.0, depth=6.0)
        result = engine.evaluate("{volume_cf}", ctx)
        assert result == 50.0  # 100 * 6 / 12

    def test_volume_cy(self, engine):
        ctx = FormulaContext(qty=2700.0, depth=12.0)
        result = engine.evaluate("{volume_cy}", ctx)
        expected = 2700.0 * 12.0 / 12.0 / 27.0
        assert abs(result - expected) < 0.001


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


class TestFunctions:
    def test_ceil(self, engine, default_context):
        result = engine.evaluate("ceil({qty} / 100) * 100", default_context)
        assert result == 1000.0

    def test_ceil_rounds_up(self, engine):
        ctx = FormulaContext(qty=1050.0)
        result = engine.evaluate("ceil({qty} / 100) * 100", ctx)
        assert result == 1100.0

    def test_floor(self, engine):
        ctx = FormulaContext(qty=1050.0)
        result = engine.evaluate("floor({qty} / 100) * 100", ctx)
        assert result == 1000.0

    def test_round(self, engine):
        ctx = FormulaContext(qty=1555.5)
        result = engine.evaluate("round({qty})", ctx)
        assert result == 1556.0

    def test_min(self, engine, default_context):
        result = engine.evaluate("min({qty}, 500)", default_context)
        assert result == 500.0

    def test_max(self, engine, default_context):
        result = engine.evaluate("max({qty}, 500)", default_context)
        assert result == 1000.0

    def test_abs(self, engine):
        ctx = FormulaContext(qty=-100.0)
        result = engine.evaluate("abs({qty})", ctx)
        assert result == 100.0

    def test_sqrt(self, engine):
        ctx = FormulaContext(qty=144.0)
        result = engine.evaluate("sqrt({qty})", ctx)
        assert result == 12.0

    def test_pow(self, engine):
        ctx = FormulaContext(qty=3.0)
        result = engine.evaluate("pow({qty}, 2)", ctx)
        assert result == 9.0

    def test_pi(self, engine, default_context):
        result = engine.evaluate("pi", default_context)
        assert abs(result - 3.14159265) < 0.001


# ---------------------------------------------------------------------------
# Safety / rejection
# ---------------------------------------------------------------------------


class TestSafety:
    def test_rejects_import(self, engine, default_context):
        with pytest.raises(ValueError):
            engine.evaluate("__import__('os')", default_context)

    def test_rejects_exec(self, engine, default_context):
        with pytest.raises(ValueError):
            engine.evaluate("exec('print(1)')", default_context)

    def test_rejects_open(self, engine, default_context):
        with pytest.raises(ValueError):
            engine.evaluate("open('/etc/passwd')", default_context)

    def test_rejects_eval(self, engine, default_context):
        with pytest.raises(ValueError):
            engine.evaluate("eval('1+1')", default_context)

    def test_rejects_unknown_variable(self, engine, default_context):
        with pytest.raises(ValueError, match="Unknown variable"):
            engine.evaluate("{unknown_var}", default_context)

    def test_rejects_attribute_access(self, engine, default_context):
        with pytest.raises(ValueError):
            engine.evaluate("{qty}.__class__", default_context)

    def test_rejects_dunder(self, engine, default_context):
        with pytest.raises(ValueError):
            engine.evaluate("__builtins__", default_context)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_division_by_zero(self, engine, default_context):
        with pytest.raises(ValueError, match="Division by zero"):
            engine.evaluate("{qty} / 0", default_context)

    def test_negative_quantity(self, engine):
        ctx = FormulaContext(qty=-100.0)
        result = engine.evaluate("{qty} * 1.05", ctx)
        assert abs(result - (-105.0)) < 0.001

    def test_zero_quantity(self, engine):
        ctx = FormulaContext(qty=0.0)
        result = engine.evaluate("{qty} * 1.05", ctx)
        assert result == 0.0

    def test_large_number(self, engine):
        ctx = FormulaContext(qty=1_000_000.0)
        result = engine.evaluate("{qty} * 2", ctx)
        assert result == 2_000_000.0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_valid_formula(self, engine):
        is_valid, error = engine.validate_formula("{qty} * 1.05")
        assert is_valid is True
        assert error is None

    def test_empty_formula_is_valid(self, engine):
        is_valid, error = engine.validate_formula("")
        assert is_valid is True
        assert error is None

    def test_invalid_variable(self, engine):
        is_valid, error = engine.validate_formula("{bogus}")
        assert is_valid is False
        assert "Unknown variable" in error

    def test_syntax_error(self, engine):
        is_valid, error = engine.validate_formula("{qty} * * 2")
        assert is_valid is False

    def test_all_variables_recognized(self, engine):
        for var in FormulaEngine.VALID_VARIABLES:
            is_valid, error = engine.validate_formula(f"{{{var}}}")
            assert is_valid is True, f"Variable {var} failed validation: {error}"


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------


class TestPresets:
    def test_presets_not_empty(self):
        assert len(FORMULA_PRESETS) > 0

    def test_presets_all_valid(self, engine):
        for key, preset in FORMULA_PRESETS.items():
            is_valid, error = engine.validate_formula(preset["formula"])
            assert is_valid, f"Preset {key} failed validation: {error}"

    def test_direct_quantity_preset(self, engine, default_context):
        formula = FORMULA_PRESETS["direct_quantity"]["formula"]
        result = engine.evaluate(formula, default_context)
        assert result == 1000.0


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_get_formula_engine_returns_same_instance(self):
        e1 = get_formula_engine()
        e2 = get_formula_engine()
        assert e1 is e2


# ---------------------------------------------------------------------------
# Formula help
# ---------------------------------------------------------------------------


class TestFormulaHelp:
    def test_formula_help_has_sections(self, engine):
        help_data = engine.get_formula_help()
        assert "variables" in help_data
        assert "functions" in help_data
        assert "examples" in help_data

    def test_formula_help_variables_complete(self, engine):
        help_data = engine.get_formula_help()
        for var in FormulaEngine.VALID_VARIABLES:
            assert f"{{{var}}}" in help_data["variables"]
