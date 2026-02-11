"""Unit tests for AI predict-next-point service."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.ai_predict_point import (
    PredictNextPointService,
    _format_last_coords,
    _geometry_template,
    _scale_geometry,
    get_predict_point_service,
    PREDICT_MAX_DIMENSION,
)


# ============================================================================
# Helper function tests
# ============================================================================


class TestFormatLastCoords:
    """Tests for _format_last_coords helper."""

    def test_format_point(self):
        result = _format_last_coords("point", {"x": 100, "y": 200})
        assert '"x": 100' in result
        assert '"y": 200' in result

    def test_format_polyline(self):
        result = _format_last_coords(
            "polyline",
            {"points": [{"x": 10, "y": 20}, {"x": 30, "y": 40}]},
        )
        assert '"x": 10' in result
        assert '"y": 20' in result
        assert '"x": 30' in result

    def test_format_empty_points(self):
        result = _format_last_coords("polyline", {"points": []})
        assert result == "[]"

    def test_format_missing_points(self):
        result = _format_last_coords("polyline", {})
        assert result == "[]"


class TestGeometryTemplate:
    """Tests for _geometry_template helper."""

    def test_point_template(self):
        result = _geometry_template("point")
        assert '"x"' in result
        assert '"y"' in result

    def test_polyline_template(self):
        result = _geometry_template("polyline")
        assert '"points"' in result

    def test_polygon_template(self):
        result = _geometry_template("polygon")
        assert '"points"' in result


class TestScaleGeometry:
    """Tests for _scale_geometry helper."""

    def test_scale_point(self):
        result = _scale_geometry("point", {"x": 100, "y": 200}, 0.5, 0.5)
        assert result == {"x": 50.0, "y": 100.0}

    def test_scale_polyline(self):
        result = _scale_geometry(
            "polyline",
            {"points": [{"x": 100, "y": 200}, {"x": 300, "y": 400}]},
            2.0,
            2.0,
        )
        assert result == {
            "points": [{"x": 200.0, "y": 400.0}, {"x": 600.0, "y": 800.0}]
        }

    def test_scale_identity(self):
        data = {"x": 50, "y": 75}
        result = _scale_geometry("point", data, 1.0, 1.0)
        assert result == {"x": 50.0, "y": 75.0}

    def test_scale_with_missing_coords(self):
        result = _scale_geometry("point", {}, 2.0, 2.0)
        assert result == {"x": 0, "y": 0}

    def test_scale_empty_points(self):
        result = _scale_geometry("polyline", {}, 2.0, 2.0)
        assert result == {"points": []}


# ============================================================================
# Service tests
# ============================================================================


class TestPredictNextPointService:
    """Tests for PredictNextPointService."""

    def setup_method(self):
        self.service = PredictNextPointService()
        # Minimal 1x1 PNG image
        self.fake_image = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
            b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
            b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )

    @patch("app.services.ai_predict_point.get_llm_client")
    @patch("app.services.ai_predict_point.resize_image_for_llm")
    def test_predict_next_returns_prediction(self, mock_resize, mock_get_llm):
        """Service returns a prediction dict on success."""
        mock_resize.return_value = (self.fake_image, 768, 512)

        mock_response = MagicMock()
        mock_response.latency_ms = 450.0
        mock_response.image_width = 768
        mock_response.image_height = 512

        mock_llm = MagicMock()
        mock_llm.analyze_image_json.return_value = (
            {
                "geometry_type": "polyline",
                "geometry_data": {"points": [{"x": 100, "y": 100}, {"x": 200, "y": 100}]},
                "confidence": 0.85,
                "description": "Next wall segment",
            },
            mock_response,
        )
        mock_get_llm.return_value = mock_llm

        result = self.service.predict_next(
            image_bytes=self.fake_image,
            image_width=1536,
            image_height=1024,
            last_geometry_type="polyline",
            last_geometry_data={"points": [{"x": 50, "y": 50}, {"x": 150, "y": 50}]},
        )

        assert result is not None
        assert result["geometry_type"] == "polyline"
        assert result["confidence"] == 0.85
        assert "geometry_data" in result

    @patch("app.services.ai_predict_point.get_llm_client")
    @patch("app.services.ai_predict_point.resize_image_for_llm")
    def test_predict_next_returns_none_on_null_prediction(self, mock_resize, mock_get_llm):
        """Service returns None when AI has no prediction."""
        mock_resize.return_value = (self.fake_image, 768, 512)

        mock_response = MagicMock()
        mock_response.latency_ms = 200.0

        mock_llm = MagicMock()
        mock_llm.analyze_image_json.return_value = (
            {
                "geometry_type": None,
                "geometry_data": None,
                "confidence": 0,
                "description": "No prediction",
            },
            mock_response,
        )
        mock_get_llm.return_value = mock_llm

        result = self.service.predict_next(
            image_bytes=self.fake_image,
            image_width=1024,
            image_height=768,
            last_geometry_type="point",
            last_geometry_data={"x": 500, "y": 300},
        )

        assert result is None

    @patch("app.services.ai_predict_point.get_llm_client")
    @patch("app.services.ai_predict_point.resize_image_for_llm")
    def test_predict_next_returns_none_on_low_confidence(self, mock_resize, mock_get_llm):
        """Service filters out predictions below 0.3 confidence."""
        mock_resize.return_value = (self.fake_image, 768, 512)

        mock_response = MagicMock()
        mock_response.latency_ms = 300.0

        mock_llm = MagicMock()
        mock_llm.analyze_image_json.return_value = (
            {
                "geometry_type": "point",
                "geometry_data": {"x": 100, "y": 100},
                "confidence": 0.1,
                "description": "Very low confidence",
            },
            mock_response,
        )
        mock_get_llm.return_value = mock_llm

        result = self.service.predict_next(
            image_bytes=self.fake_image,
            image_width=1024,
            image_height=768,
            last_geometry_type="point",
            last_geometry_data={"x": 500, "y": 300},
        )

        assert result is None

    @patch("app.services.ai_predict_point.get_llm_client")
    @patch("app.services.ai_predict_point.resize_image_for_llm")
    def test_predict_next_returns_none_on_llm_error(self, mock_resize, mock_get_llm):
        """Service returns None (silent failure) on LLM error."""
        mock_resize.return_value = (self.fake_image, 768, 512)

        mock_llm = MagicMock()
        mock_llm.analyze_image_json.side_effect = RuntimeError("LLM provider down")
        mock_get_llm.return_value = mock_llm

        result = self.service.predict_next(
            image_bytes=self.fake_image,
            image_width=1024,
            image_height=768,
            last_geometry_type="polyline",
            last_geometry_data={"points": [{"x": 50, "y": 50}]},
        )

        assert result is None  # Silent failure, no exception raised

    @patch("app.services.ai_predict_point.get_llm_client")
    @patch("app.services.ai_predict_point.resize_image_for_llm")
    def test_predict_next_scales_coordinates_back(self, mock_resize, mock_get_llm):
        """Service scales LLM coordinates back to original image space."""
        # LLM sees 768x512, original is 1536x1024 (2x scale)
        mock_resize.return_value = (self.fake_image, 768, 512)

        mock_response = MagicMock()
        mock_response.latency_ms = 400.0
        mock_response.image_width = 768
        mock_response.image_height = 512

        mock_llm = MagicMock()
        mock_llm.analyze_image_json.return_value = (
            {
                "geometry_type": "point",
                "geometry_data": {"x": 384, "y": 256},
                "confidence": 0.9,
                "description": "Scaled point",
            },
            mock_response,
        )
        mock_get_llm.return_value = mock_llm

        result = self.service.predict_next(
            image_bytes=self.fake_image,
            image_width=1536,
            image_height=1024,
            last_geometry_type="point",
            last_geometry_data={"x": 100, "y": 100},
        )

        assert result is not None
        # 384 * (1536/768) = 768, 256 * (1024/512) = 512
        assert result["geometry_data"]["x"] == pytest.approx(768.0)
        assert result["geometry_data"]["y"] == pytest.approx(512.0)

    @patch("app.services.ai_predict_point.get_llm_client")
    @patch("app.services.ai_predict_point.resize_image_for_llm")
    def test_predict_next_uses_aggressive_downscale(self, mock_resize, mock_get_llm):
        """Service uses PREDICT_MAX_DIMENSION (768) for downscaling."""
        mock_resize.return_value = (self.fake_image, 768, 512)

        mock_response = MagicMock()
        mock_response.latency_ms = 100.0
        mock_response.image_width = 768
        mock_response.image_height = 512

        mock_llm = MagicMock()
        mock_llm.analyze_image_json.return_value = (
            {
                "geometry_type": None,
                "geometry_data": None,
                "confidence": 0,
                "description": "No prediction",
            },
            mock_response,
        )
        mock_get_llm.return_value = mock_llm

        self.service.predict_next(
            image_bytes=self.fake_image,
            image_width=3000,
            image_height=2000,
            last_geometry_type="point",
            last_geometry_data={"x": 100, "y": 100},
        )

        mock_resize.assert_called_once()
        call_args = mock_resize.call_args
        assert call_args.kwargs.get("max_dimension") == PREDICT_MAX_DIMENSION or \
               call_args[1].get("max_dimension") == PREDICT_MAX_DIMENSION

    @patch("app.services.ai_predict_point.get_llm_client")
    @patch("app.services.ai_predict_point.resize_image_for_llm")
    def test_predict_next_uses_max_256_tokens(self, mock_resize, mock_get_llm):
        """Service requests max_tokens=256 for speed."""
        mock_resize.return_value = (self.fake_image, 768, 512)

        mock_response = MagicMock()
        mock_response.latency_ms = 100.0

        mock_llm = MagicMock()
        mock_llm.analyze_image_json.return_value = (
            {"geometry_type": None, "geometry_data": None, "confidence": 0, "description": ""},
            mock_response,
        )
        mock_get_llm.return_value = mock_llm

        self.service.predict_next(
            image_bytes=self.fake_image,
            image_width=1024,
            image_height=768,
            last_geometry_type="point",
            last_geometry_data={"x": 100, "y": 100},
        )

        mock_llm.analyze_image_json.assert_called_once()
        call_kwargs = mock_llm.analyze_image_json.call_args
        assert call_kwargs.kwargs.get("max_tokens") == 256 or \
               (len(call_kwargs.args) > 3 and call_kwargs.args[3] == 256)

    @patch("app.services.ai_predict_point.resize_image_for_llm")
    def test_predict_next_returns_none_on_resize_error(self, mock_resize):
        """Service returns None when image resize fails."""
        mock_resize.side_effect = Exception("Corrupt image")

        result = self.service.predict_next(
            image_bytes=b"not-an-image",
            image_width=1024,
            image_height=768,
            last_geometry_type="point",
            last_geometry_data={"x": 100, "y": 100},
        )

        assert result is None

    @patch("app.services.ai_predict_point.get_llm_client")
    @patch("app.services.ai_predict_point.resize_image_for_llm")
    def test_predict_next_includes_last_geometry_in_prompt(self, mock_resize, mock_get_llm):
        """Service includes the last measurement context in the LLM prompt."""
        mock_resize.return_value = (self.fake_image, 768, 512)

        mock_response = MagicMock()
        mock_response.latency_ms = 100.0

        mock_llm = MagicMock()
        mock_llm.analyze_image_json.return_value = (
            {"geometry_type": None, "geometry_data": None, "confidence": 0, "description": ""},
            mock_response,
        )
        mock_get_llm.return_value = mock_llm

        self.service.predict_next(
            image_bytes=self.fake_image,
            image_width=1024,
            image_height=768,
            last_geometry_type="polygon",
            last_geometry_data={"points": [{"x": 10, "y": 20}]},
        )

        call_args = mock_llm.analyze_image_json.call_args
        prompt = call_args.kwargs.get("prompt") or call_args.args[1]
        assert "polygon" in prompt


# ============================================================================
# Singleton test
# ============================================================================


class TestGetPredictPointService:
    """Tests for singleton factory."""

    def test_returns_service_instance(self):
        service = get_predict_point_service()
        assert isinstance(service, PredictNextPointService)

    def test_returns_same_instance(self):
        s1 = get_predict_point_service()
        s2 = get_predict_point_service()
        assert s1 is s2
