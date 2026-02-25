"""Tests for AI takeoff prompt dimension accuracy fix.

Verifies that analyze_page and analyze_page_autonomous use the actual
resized image dimensions in the LLM prompt, not the original page
dimensions. This prevents coordinate space mismatch where the AI
returns coordinates in the wrong scale.

Requires: pip install anthropic openai google-generativeai (or run in Docker)
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# Stub out heavy optional dependencies so tests can import without Docker
# ============================================================================

_STUB_MODULES = {}
for mod_name in ("anthropic", "openai", "google.generativeai", "google", "tenacity"):
    if mod_name not in sys.modules:
        _STUB_MODULES[mod_name] = sys.modules[mod_name] = MagicMock()

# tenacity decorators need to be callables that return the original function
_tenacity_mock = _STUB_MODULES.get("tenacity")
if _tenacity_mock:
    _tenacity_mock.retry = lambda **kw: lambda fn: fn
    _tenacity_mock.stop_after_attempt = lambda n: None
    _tenacity_mock.wait_exponential = lambda **kw: None
    _tenacity_mock.retry_if_exception_type = lambda t: None


from app.services.ai_takeoff import AITakeoffService, scale_coordinates  # noqa: E402


# Minimal valid 1x1 PNG image bytes
FAKE_IMAGE = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
    b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _make_mock_llm(response_width: int, response_height: int, elements=None):
    """Build a mock LLM client + response pair."""
    mock_response = MagicMock()
    mock_response.image_width = response_width
    mock_response.image_height = response_height
    mock_response.provider = "anthropic"
    mock_response.model = "claude-sonnet-4-20250514"
    mock_response.latency_ms = 1000
    mock_response.input_tokens = 500
    mock_response.output_tokens = 200

    mock_llm = MagicMock()
    mock_llm.provider = MagicMock(value="anthropic")
    mock_llm.analyze_image_json.return_value = (
        {
            "page_description": "Test",
            "elements": elements or [],
            "analysis_notes": "",
        },
        mock_response,
    )
    return mock_llm


# ============================================================================
# scale_coordinates — pure function, no mocking needed
# ============================================================================


class TestScaleCoordinates:
    """Verify scale_coordinates handles all geometry types correctly."""

    def test_identity_when_same_dimensions(self):
        data = {"points": [{"x": 100, "y": 200}]}
        result = scale_coordinates(data, "polygon", 1568, 1015, 1568, 1015)
        assert result == data

    def test_scale_polygon_2x(self):
        data = {"points": [{"x": 100, "y": 200}, {"x": 300, "y": 400}]}
        result = scale_coordinates(data, "polygon", 500, 500, 1000, 1000)
        assert result["points"][0]["x"] == pytest.approx(200.0)
        assert result["points"][0]["y"] == pytest.approx(400.0)
        assert result["points"][1]["x"] == pytest.approx(600.0)
        assert result["points"][1]["y"] == pytest.approx(800.0)

    def test_scale_point(self):
        data = {"x": 384, "y": 256}
        result = scale_coordinates(data, "point", 768, 512, 1536, 1024)
        assert result["x"] == pytest.approx(768.0)
        assert result["y"] == pytest.approx(512.0)

    def test_scale_polyline(self):
        data = {"points": [{"x": 100, "y": 100}, {"x": 200, "y": 200}]}
        result = scale_coordinates(data, "polyline", 500, 500, 2500, 2500)
        assert result["points"][0]["x"] == pytest.approx(500.0)
        assert result["points"][0]["y"] == pytest.approx(500.0)
        assert result["points"][1]["x"] == pytest.approx(1000.0)
        assert result["points"][1]["y"] == pytest.approx(1000.0)

    def test_scale_with_null_values(self):
        """Null coordinates should become 0 after scaling (or 0 stays)."""
        data = {"x": None, "y": None}
        result = scale_coordinates(data, "point", 768, 512, 1536, 1024)
        assert result["x"] == 0
        assert result["y"] == 0

    def test_scale_with_missing_keys(self):
        data = {}
        result = scale_coordinates(data, "point", 768, 512, 1536, 1024)
        assert result["x"] == 0
        assert result["y"] == 0

    def test_scale_empty_polygon(self):
        data = {"points": []}
        result = scale_coordinates(data, "polygon", 500, 500, 1000, 1000)
        assert result == {"points": []}

    def test_asymmetric_scale(self):
        """Different x and y scale factors (non-square resize)."""
        data = {"x": 100, "y": 100}
        result = scale_coordinates(data, "point", 800, 400, 1600, 1200)
        assert result["x"] == pytest.approx(200.0)
        assert result["y"] == pytest.approx(300.0)


# ============================================================================
# analyze_page — verifies prompt uses resized dimensions
# ============================================================================


class TestAnalyzePagePromptDimensions:
    """The prompt must tell the AI the actual image dimensions it will see,
    not the original page dimensions. Otherwise the AI returns coordinates
    in the wrong space and they get double-scaled."""

    @patch("app.services.ai_takeoff.resize_image_for_llm")
    @patch("app.services.ai_takeoff.get_llm_client")
    def test_prompt_contains_resized_dimensions(self, mock_get_llm, mock_resize):
        """analyze_page should format the prompt with LLM image width/height."""
        mock_resize.return_value = (FAKE_IMAGE, 1568, 1015)
        mock_get_llm.return_value = _make_mock_llm(1568, 1015)

        service = AITakeoffService()
        service.analyze_page(
            image_bytes=FAKE_IMAGE,
            width=5100,
            height=3300,
            element_type="slab_on_grade",
            measurement_type="area",
        )

        call_args = mock_get_llm.return_value.analyze_image_json.call_args
        prompt = call_args.kwargs.get("prompt", "")

        assert "1568" in prompt, "Prompt should contain resized width 1568"
        assert "1015" in prompt, "Prompt should contain resized height 1015"
        assert "5100" not in prompt, "Prompt must NOT contain original width 5100"
        assert "3300" not in prompt, "Prompt must NOT contain original height 3300"

    @patch("app.services.ai_takeoff.resize_image_for_llm")
    @patch("app.services.ai_takeoff.get_llm_client")
    def test_sends_pre_resized_image_bytes(self, mock_get_llm, mock_resize):
        """analyze_page should send the pre-resized image, not the original."""
        resized_bytes = b"RESIZED_IMAGE_DATA"
        mock_resize.return_value = (resized_bytes, 1568, 1015)
        mock_get_llm.return_value = _make_mock_llm(1568, 1015)

        service = AITakeoffService()
        service.analyze_page(
            image_bytes=FAKE_IMAGE,
            width=5100,
            height=3300,
            element_type="slab",
            measurement_type="area",
        )

        call_args = mock_get_llm.return_value.analyze_image_json.call_args
        sent_image = call_args.kwargs.get("image_bytes", b"")
        assert sent_image == resized_bytes, "Must send pre-resized image, not original"

    @patch("app.services.ai_takeoff.resize_image_for_llm")
    @patch("app.services.ai_takeoff.get_llm_client")
    def test_scales_coordinates_back_to_original_space(self, mock_get_llm, mock_resize):
        """AI coordinates in LLM space must be scaled back to original page space."""
        mock_resize.return_value = (FAKE_IMAGE, 1568, 1015)
        mock_get_llm.return_value = _make_mock_llm(
            1568,
            1015,
            elements=[
                {
                    "element_type": "slab",
                    "geometry_type": "polygon",
                    "points": [
                        {"x": 100, "y": 100},
                        {"x": 500, "y": 100},
                        {"x": 500, "y": 400},
                        {"x": 100, "y": 400},
                    ],
                    "confidence": 0.9,
                    "description": "Test slab",
                }
            ],
        )

        service = AITakeoffService()
        result = service.analyze_page(
            image_bytes=FAKE_IMAGE,
            width=5100,
            height=3300,
            element_type="slab",
            measurement_type="area",
        )

        assert len(result.elements) > 0
        points = result.elements[0].geometry_data["points"]
        scale_x = 5100 / 1568
        scale_y = 3300 / 1015
        assert points[0]["x"] == pytest.approx(100 * scale_x, rel=0.01)
        assert points[0]["y"] == pytest.approx(100 * scale_y, rel=0.01)
        assert points[2]["x"] == pytest.approx(500 * scale_x, rel=0.01)
        assert points[2]["y"] == pytest.approx(400 * scale_y, rel=0.01)


# ============================================================================
# analyze_page_autonomous — same dimension fix
# ============================================================================


class TestAnalyzePageAutonomousPromptDimensions:
    """Same fix as analyze_page, but for the autonomous detection path."""

    @patch("app.services.ai_takeoff.resize_image_for_llm")
    @patch("app.services.ai_takeoff.get_llm_client")
    def test_autonomous_prompt_contains_resized_dimensions(
        self, mock_get_llm, mock_resize
    ):
        mock_resize.return_value = (FAKE_IMAGE, 1568, 1015)
        mock_get_llm.return_value = _make_mock_llm(1568, 1015)

        service = AITakeoffService()
        service.analyze_page_autonomous(
            image_bytes=FAKE_IMAGE,
            width=5100,
            height=3300,
        )

        call_args = mock_get_llm.return_value.analyze_image_json.call_args
        prompt = call_args.kwargs.get("prompt", "")

        assert "1568" in prompt
        assert "1015" in prompt
        assert "5100" not in prompt
        assert "3300" not in prompt

    @patch("app.services.ai_takeoff.resize_image_for_llm")
    @patch("app.services.ai_takeoff.get_llm_client")
    def test_autonomous_sends_pre_resized_image(self, mock_get_llm, mock_resize):
        resized_bytes = b"RESIZED_AUTONOMOUS"
        mock_resize.return_value = (resized_bytes, 1568, 1015)
        mock_get_llm.return_value = _make_mock_llm(1568, 1015)

        service = AITakeoffService()
        service.analyze_page_autonomous(
            image_bytes=FAKE_IMAGE,
            width=5100,
            height=3300,
        )

        call_args = mock_get_llm.return_value.analyze_image_json.call_args
        sent_image = call_args.kwargs.get("image_bytes", b"")
        assert sent_image == resized_bytes

    @patch("app.services.ai_takeoff.resize_image_for_llm")
    @patch("app.services.ai_takeoff.get_llm_client")
    def test_autonomous_coordinates_scaled_back(self, mock_get_llm, mock_resize):
        mock_resize.return_value = (FAKE_IMAGE, 1568, 1015)
        mock_get_llm.return_value = _make_mock_llm(
            1568,
            1015,
            elements=[
                {
                    "element_type": "slab_on_grade",
                    "geometry_type": "polygon",
                    "points": [
                        {"x": 100, "y": 100},
                        {"x": 500, "y": 100},
                        {"x": 500, "y": 400},
                        {"x": 100, "y": 400},
                    ],
                    "confidence": 0.9,
                    "description": "Test slab",
                }
            ],
        )

        service = AITakeoffService()
        result = service.analyze_page_autonomous(
            image_bytes=FAKE_IMAGE,
            width=5100,
            height=3300,
        )

        assert len(result.elements) > 0
        points = result.elements[0].geometry_data["points"]
        scale_x = 5100 / 1568
        scale_y = 3300 / 1015
        assert points[0]["x"] == pytest.approx(100 * scale_x, rel=0.01)
        assert points[0]["y"] == pytest.approx(100 * scale_y, rel=0.01)

    @patch("app.services.ai_takeoff.resize_image_for_llm")
    @patch("app.services.ai_takeoff.get_llm_client")
    def test_no_resize_when_image_already_small(self, mock_get_llm, mock_resize):
        """When image is already smaller than provider max, dimensions pass through."""
        mock_resize.return_value = (FAKE_IMAGE, 800, 600)
        mock_get_llm.return_value = _make_mock_llm(800, 600)

        service = AITakeoffService()
        service.analyze_page_autonomous(
            image_bytes=FAKE_IMAGE,
            width=800,
            height=600,
        )

        call_args = mock_get_llm.return_value.analyze_image_json.call_args
        prompt = call_args.kwargs.get("prompt", "")
        assert "800" in prompt
        assert "600" in prompt


# ============================================================================
# Domino-effect / regression tests
# ============================================================================


class TestNoDominoEffects:
    """Verify the resolution fix doesn't break existing behavior."""

    @patch("app.services.ai_takeoff.resize_image_for_llm")
    @patch("app.services.ai_takeoff.get_llm_client")
    def test_elements_still_filtered_by_original_bounds(
        self, mock_get_llm, mock_resize
    ):
        """_filter_valid_geometries uses original page dimensions, not LLM dimensions."""
        mock_resize.return_value = (FAKE_IMAGE, 1568, 1015)
        mock_get_llm.return_value = _make_mock_llm(
            1568,
            1015,
            elements=[
                {
                    "element_type": "slab",
                    "geometry_type": "polygon",
                    "points": [
                        {"x": 1500, "y": 900},
                        {"x": 1560, "y": 900},
                        {"x": 1560, "y": 1010},
                        {"x": 1500, "y": 1010},
                    ],
                    "confidence": 0.9,
                    "description": "Near-edge slab",
                }
            ],
        )

        service = AITakeoffService()
        result = service.analyze_page(
            image_bytes=FAKE_IMAGE,
            width=5100,
            height=3300,
            element_type="slab",
            measurement_type="area",
        )

        # After scaling: x=1500*(5100/1568)≈4886, y=900*(3300/1015)≈2926
        # These should be within 5100x3300 bounds
        assert len(result.elements) == 1

    @patch("app.services.ai_takeoff.resize_image_for_llm")
    @patch("app.services.ai_takeoff.get_llm_client")
    def test_result_metadata_preserved(self, mock_get_llm, mock_resize):
        """LLM metadata (provider, model, latency) still flows through."""
        mock_resize.return_value = (FAKE_IMAGE, 1568, 1015)
        mock_get_llm.return_value = _make_mock_llm(1568, 1015)

        service = AITakeoffService()
        result = service.analyze_page(
            image_bytes=FAKE_IMAGE,
            width=5100,
            height=3300,
            element_type="slab",
            measurement_type="area",
        )

        assert result.llm_provider == "anthropic"
        assert result.llm_model == "claude-sonnet-4-20250514"
        assert result.llm_latency_ms == 1000

    def test_scale_coordinates_preserves_polygon_point_count(self):
        """Scaling must not add or drop polygon vertices."""
        data = {
            "points": [
                {"x": 10, "y": 10},
                {"x": 20, "y": 10},
                {"x": 20, "y": 20},
                {"x": 10, "y": 20},
                {"x": 15, "y": 25},
            ]
        }
        result = scale_coordinates(data, "polygon", 500, 500, 1000, 1000)
        assert len(result["points"]) == 5

    def test_scale_coordinates_no_negative_values(self):
        """Positive LLM coordinates should never become negative after scaling."""
        data = {"points": [{"x": 1, "y": 1}, {"x": 500, "y": 500}]}
        result = scale_coordinates(data, "polygon", 1568, 1015, 5100, 3300)
        for pt in result["points"]:
            assert pt["x"] >= 0
            assert pt["y"] >= 0

    @patch("app.services.ai_takeoff.resize_image_for_llm")
    @patch("app.services.ai_takeoff.get_llm_client")
    def test_line_normalized_to_polyline(self, mock_get_llm, mock_resize):
        """Lines from AI should be normalized to polyline type (existing behavior)."""
        mock_resize.return_value = (FAKE_IMAGE, 1568, 1015)
        mock_get_llm.return_value = _make_mock_llm(
            1568,
            1015,
            elements=[
                {
                    "element_type": "footing",
                    "geometry_type": "line",
                    "points": [{"x": 100, "y": 100}, {"x": 500, "y": 500}],
                    "confidence": 0.8,
                    "description": "Footing line",
                }
            ],
        )

        service = AITakeoffService()
        result = service.analyze_page(
            image_bytes=FAKE_IMAGE,
            width=5100,
            height=3300,
            element_type="footing",
            measurement_type="linear",
        )

        assert len(result.elements) == 1
        assert result.elements[0].geometry_type == "polyline"
