"""AST-based safe formula evaluation engine for assembly quantity calculations."""

import ast
import math
import re
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Formula context — variables available inside formulas
# ---------------------------------------------------------------------------


@dataclass
class FormulaContext:
    """Variables available for formula evaluation, built from condition data."""

    qty: float = 0.0
    depth: float = 0.0  # inches
    thickness: float = 0.0  # inches
    perimeter: float = 0.0  # LF
    count: int = 0
    height: float = 0.0  # feet
    width: float = 0.0  # feet
    length: float = 0.0  # feet

    @property
    def depth_ft(self) -> float:
        return self.depth / 12.0 if self.depth else 0.0

    @property
    def thickness_ft(self) -> float:
        return self.thickness / 12.0 if self.thickness else 0.0

    @property
    def volume_cf(self) -> float:
        return self.qty * self.depth / 12.0 if self.depth else 0.0

    @property
    def volume_cy(self) -> float:
        return self.volume_cf / 27.0

    def to_dict(self) -> dict[str, float]:
        """Return all variables (including computed properties) as a dict."""
        return {
            "qty": self.qty,
            "depth": self.depth,
            "thickness": self.thickness,
            "perimeter": self.perimeter,
            "count": float(self.count),
            "height": self.height,
            "width": self.width,
            "length": self.length,
            "depth_ft": self.depth_ft,
            "thickness_ft": self.thickness_ft,
            "volume_cf": self.volume_cf,
            "volume_cy": self.volume_cy,
        }


# ---------------------------------------------------------------------------
# AST-based safe evaluator
# ---------------------------------------------------------------------------

# Allowed node types in the AST
_ALLOWED_NODE_TYPES = frozenset(
    {
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Call,
        ast.Constant,
        ast.Name,
        ast.Load,
        # Operators
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
        ast.Pow,
        ast.USub,
        ast.UAdd,
    }
)

# Functions and constants available in formulas
_ALLOWED_NAMES: dict[str, Any] = {
    "ceil": math.ceil,
    "floor": math.floor,
    "round": round,
    "min": min,
    "max": max,
    "abs": abs,
    "sqrt": math.sqrt,
    "pow": pow,
    "pi": math.pi,
}


class SafeEvaluator(ast.NodeVisitor):
    """Validates an AST to ensure it only contains safe, allowed constructs."""

    def generic_visit(self, node: ast.AST) -> None:
        if type(node) not in _ALLOWED_NODE_TYPES:
            raise ValueError(
                f"Disallowed expression element: {type(node).__name__}"
            )
        super().generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Only allow calls to known function names
        if isinstance(node.func, ast.Name):
            if node.func.id not in _ALLOWED_NAMES:
                raise ValueError(f"Disallowed function call: {node.func.id}")
        else:
            raise ValueError("Only simple function calls are allowed")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        # Name nodes are fine — they'll be resolved against the allowed names dict
        # at eval time. Unknown names will raise NameError, which we catch.
        self.generic_visit(node)


# ---------------------------------------------------------------------------
# Variable placeholder pattern: {variable_name}
# ---------------------------------------------------------------------------
_VAR_PATTERN = re.compile(r"\{(\w+)\}")


# ---------------------------------------------------------------------------
# FormulaEngine
# ---------------------------------------------------------------------------


class FormulaEngine:
    """Safe formula evaluation engine using AST validation.

    Formulas use {variable} placeholders that are replaced with numeric values
    from a FormulaContext before evaluation. Only whitelisted AST node types
    and function calls are permitted.
    """

    VALID_VARIABLES: set[str] = {
        "qty",
        "depth",
        "thickness",
        "perimeter",
        "count",
        "height",
        "width",
        "length",
        "depth_ft",
        "thickness_ft",
        "volume_cf",
        "volume_cy",
    }

    def evaluate(self, formula: str, context: FormulaContext) -> float:
        """Evaluate a formula string with the given context.

        Args:
            formula: Formula string with {variable} placeholders.
            context: FormulaContext with variable values.

        Returns:
            The calculated result as a float.

        Raises:
            ValueError: If the formula is invalid or contains disallowed constructs.
        """
        if not formula or not formula.strip():
            return context.qty

        # Replace {variable} placeholders with numeric values
        variables = context.to_dict()
        expression = _VAR_PATTERN.sub(
            lambda m: self._replace_var(m, variables), formula
        )

        try:
            # Parse the expression into an AST
            tree = ast.parse(expression, mode="eval")

            # Validate the AST — raises ValueError if disallowed constructs found
            SafeEvaluator().visit(tree)

            # Compile and evaluate the validated AST
            code = compile(tree, "<formula>", "eval")
            result = eval(code, {"__builtins__": {}}, _ALLOWED_NAMES)  # noqa: S307

            if not isinstance(result, (int, float)):
                raise ValueError(f"Formula did not produce a number: {type(result)}")

            if math.isnan(result) or math.isinf(result):
                raise ValueError(f"Formula produced invalid result: {result}")

            return float(result)

        except SyntaxError as e:
            raise ValueError(f"Formula syntax error: {e}") from e
        except NameError as e:
            raise ValueError(f"Unknown variable in formula: {e}") from e
        except ZeroDivisionError:
            raise ValueError("Division by zero in formula")
        except (TypeError, OverflowError) as e:
            raise ValueError(f"Formula evaluation error: {e}") from e

    def _replace_var(
        self, match: re.Match, variables: dict[str, float]
    ) -> str:
        """Replace a {variable} match with its numeric value."""
        var_name = match.group(1)
        if var_name not in self.VALID_VARIABLES:
            raise ValueError(f"Unknown variable: {{{var_name}}}")
        value = variables.get(var_name, 0.0)
        # Use repr for floats to avoid precision issues
        return repr(value)

    def validate_formula(self, formula: str) -> tuple[bool, str | None]:
        """Validate a formula without evaluating it.

        Returns:
            Tuple of (is_valid, error_message_or_none).
        """
        if not formula or not formula.strip():
            return True, None

        # Check that all {variables} are recognized
        for match in _VAR_PATTERN.finditer(formula):
            var_name = match.group(1)
            if var_name not in self.VALID_VARIABLES:
                return False, f"Unknown variable: {{{var_name}}}"

        # Replace variables with test values to check syntax
        test_expr = _VAR_PATTERN.sub("1.0", formula)

        try:
            tree = ast.parse(test_expr, mode="eval")
            SafeEvaluator().visit(tree)
            return True, None
        except (SyntaxError, ValueError) as e:
            return False, str(e)

    def get_formula_help(self) -> dict[str, Any]:
        """Return formula documentation."""
        return {
            "variables": {
                "{qty}": "Primary takeoff quantity (SF, LF, CY, EA)",
                "{depth}": "Condition depth in inches",
                "{thickness}": "Condition thickness in inches",
                "{perimeter}": "Sum of linear measurements (LF)",
                "{count}": "Number of count measurements",
                "{height}": "Height in feet",
                "{width}": "Width in feet",
                "{length}": "Total length in feet",
                "{depth_ft}": "Computed: depth / 12",
                "{thickness_ft}": "Computed: thickness / 12",
                "{volume_cf}": "Computed: qty × depth / 12",
                "{volume_cy}": "Computed: volume_cf / 27",
            },
            "functions": [
                "ceil(x)", "floor(x)", "round(x)", "round(x, n)",
                "min(a, b)", "max(a, b)", "abs(x)",
                "sqrt(x)", "pow(x, n)", "pi",
            ],
            "examples": [
                {"description": "Direct quantity", "formula": "{qty}"},
                {"description": "SF to CY conversion", "formula": "{qty} * {depth} / 12 / 27"},
                {"description": "5% waste factor", "formula": "{qty} * 1.05"},
                {"description": "Round up to nearest 100", "formula": "ceil({qty} / 100) * 100"},
                {"description": "#4 rebar at 18\" O.C.", "formula": "{qty} * 0.89"},
                {"description": "Form area (both sides)", "formula": "{perimeter} * {depth} / 12 * 2"},
            ],
        }


# ---------------------------------------------------------------------------
# Formula presets
# ---------------------------------------------------------------------------

FORMULA_PRESETS: dict[str, dict[str, str]] = {
    "direct_quantity": {
        "name": "Direct Quantity",
        "formula": "{qty}",
        "description": "Use the takeoff quantity directly",
    },
    "concrete_cy_from_sf": {
        "name": "Concrete CY from SF",
        "formula": "{qty} * {depth} / 12 / 27",
        "description": "Convert SF area × depth (inches) to cubic yards",
    },
    "rebar_lbs_4_at_18": {
        "name": "#4 Rebar @ 18\" O.C.",
        "formula": "{qty} * 0.89",
        "description": "#4 rebar weight per SF at 18\" on center spacing",
    },
    "rebar_lbs_5_at_12": {
        "name": "#5 Rebar @ 12\" O.C.",
        "formula": "{qty} * 2.09",
        "description": "#5 rebar weight per SF at 12\" on center spacing",
    },
    "with_waste_5": {
        "name": "5% Waste Factor",
        "formula": "{qty} * 1.05",
        "description": "Add 5% waste to quantity",
    },
    "with_waste_10": {
        "name": "10% Waste Factor",
        "formula": "{qty} * 1.10",
        "description": "Add 10% waste to quantity",
    },
    "vapor_barrier_with_overlap": {
        "name": "Vapor Barrier with 10% Overlap",
        "formula": "{qty} * 1.1",
        "description": "Vapor barrier SF with 10% overlap allowance",
    },
    "sfca_wall_both_sides": {
        "name": "SFCA Wall Both Sides",
        "formula": "{perimeter} * {depth} / 12 * 2",
        "description": "Square feet of contact area for forms on both sides",
    },
    "round_up_100": {
        "name": "Round Up to Nearest 100",
        "formula": "ceil({qty} / 100) * 100",
        "description": "Round quantity up to the nearest 100",
    },
    "dowels_per_footing": {
        "name": "Dowels per Footing (4 each)",
        "formula": "{count} * 4",
        "description": "4 dowels per count item (e.g., per footing)",
    },
    "concrete_pump_days": {
        "name": "Concrete Pump Days",
        "formula": "ceil({qty} * {depth} / 12 / 27 / 80)",
        "description": "Number of pump days at 80 CY per day",
    },
    "chairs_per_sf": {
        "name": "Rebar Chairs per SF",
        "formula": "{qty} / 4",
        "description": "One rebar chair per 4 SF",
    },
}


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine: FormulaEngine | None = None


def get_formula_engine() -> FormulaEngine:
    """Get the formula engine singleton."""
    global _engine
    if _engine is None:
        _engine = FormulaEngine()
    return _engine
