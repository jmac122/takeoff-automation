"""AI predict-next-point service for AutoTab feature.

Provides low-latency (<800ms target) prediction of the next likely
measurement point after a user completes a measurement.  Uses a
synchronous LLM call (NOT Celery) with aggressive image downscaling
for speed.  Errors are silently swallowed — the AutoTab feature must
never block the user's drawing flow.
"""

from typing import Any

import structlog

from app.services.llm_client import get_llm_client
from app.utils.pdf_utils import resize_image_for_llm

logger = structlog.get_logger()

# Aggressive downscale for speed — 768px keeps latency low
PREDICT_MAX_DIMENSION = 768

PREDICT_SYSTEM_PROMPT = (
    "You are an expert construction estimator assistant. "
    "Your job is to predict the NEXT measurement location on a construction plan drawing. "
    "Respond with valid JSON only."
)

PREDICT_NEXT_PROMPT = """Analyze this construction plan image ({width}x{height} pixels).

The user just completed a {geometry_type} measurement at these coordinates (in pixels, 0,0 = top-left):
{last_coords}

Predict where the NEXT similar measurement is most likely located on this drawing.
Look for repeating patterns, adjacent elements, continuation of the same element type,
or the next logical measurement a construction estimator would take.

Return exactly ONE prediction in this JSON format:
{{
    "geometry_type": "{geometry_type}",
    "geometry_data": {geometry_template},
    "confidence": 0.75,
    "description": "Brief description of predicted element"
}}

If you cannot confidently predict a next measurement, return:
{{"geometry_type": null, "geometry_data": null, "confidence": 0, "description": "No prediction"}}

Points must be pixel coordinates on this image."""


def _format_last_coords(geometry_type: str, geometry_data: dict[str, Any]) -> str:
    """Format last measurement coordinates for the prompt."""
    if geometry_type == "point":
        x = geometry_data.get("x", 0)
        y = geometry_data.get("y", 0)
        return f'{{"x": {x}, "y": {y}}}'
    elif geometry_type == "rectangle":
        x = geometry_data.get("x", 0)
        y = geometry_data.get("y", 0)
        w = geometry_data.get("width", 0)
        h = geometry_data.get("height", 0)
        return f'{{"x": {x}, "y": {y}, "width": {w}, "height": {h}}}'
    elif geometry_type == "circle":
        center = geometry_data.get("center", {})
        cx = center.get("x", 0) if isinstance(center, dict) else 0
        cy = center.get("y", 0) if isinstance(center, dict) else 0
        r = geometry_data.get("radius", 0)
        return f'{{"center": {{"x": {cx}, "y": {cy}}}, "radius": {r}}}'
    else:
        points = geometry_data.get("points", [])
        if not points:
            return "[]"
        formatted = ", ".join(
            f'{{"x": {p.get("x", 0)}, "y": {p.get("y", 0)}}}' for p in points
        )
        return f"[{formatted}]"


def _geometry_template(geometry_type: str) -> str:
    """Return the expected geometry_data JSON template for the prompt."""
    if geometry_type == "point":
        return '{"x": <number>, "y": <number>}'
    elif geometry_type == "rectangle":
        return '{"x": <number>, "y": <number>, "width": <number>, "height": <number>}'
    elif geometry_type == "circle":
        return '{"center": {"x": <number>, "y": <number>}, "radius": <number>}'
    else:
        return '{"points": [{"x": <number>, "y": <number>}, ...]}'


class PredictNextPointService:
    """Service for predicting the next measurement point.

    Designed for low-latency synchronous use — NOT Celery.
    """

    def predict_next(
        self,
        image_bytes: bytes,
        image_width: int,
        image_height: int,
        last_geometry_type: str,
        last_geometry_data: dict[str, Any],
        provider: str | None = None,
    ) -> dict[str, Any] | None:
        """Predict the next likely measurement point.

        Args:
            image_bytes: Full page image bytes.
            image_width: Original image width in pixels.
            image_height: Original image height in pixels.
            last_geometry_type: Geometry type of last completed measurement
                ("point", "line", "polyline", "polygon", "rectangle", "circle").
            last_geometry_data: Geometry data dict of the last measurement.
            provider: Optional LLM provider override.

        Returns:
            Dict with ``geometry_type``, ``geometry_data``, ``confidence``
            if a prediction was made, or ``None`` on any failure.
        """
        try:
            # Downscale aggressively for speed
            resized_bytes, llm_width, llm_height = resize_image_for_llm(
                image_bytes,
                max_dimension=PREDICT_MAX_DIMENSION,
                fmt="PNG",
            )

            # Scale last geometry coords into LLM image space so the prompt
            # references coordinates the model can actually see.
            scale_to_llm_x = llm_width / image_width if image_width else 1
            scale_to_llm_y = llm_height / image_height if image_height else 1
            scaled_last = _scale_geometry(
                last_geometry_type,
                last_geometry_data,
                scale_to_llm_x,
                scale_to_llm_y,
            )

            prompt = PREDICT_NEXT_PROMPT.format(
                width=llm_width,
                height=llm_height,
                geometry_type=last_geometry_type,
                last_coords=_format_last_coords(last_geometry_type, scaled_last),
                geometry_template=_geometry_template(last_geometry_type),
            )

            llm = get_llm_client(provider=provider, task="element_detection")

            data, response = llm.analyze_image_json(
                image_bytes=resized_bytes,
                prompt=prompt,
                system_prompt=PREDICT_SYSTEM_PROMPT,
                max_tokens=256,
            )

            # Check for null / low-confidence prediction
            if not data.get("geometry_type") or not data.get("geometry_data"):
                logger.debug("AI returned no prediction")
                return None

            confidence = float(data.get("confidence", 0))
            if confidence < 0.3:
                logger.debug(
                    "AI prediction below confidence threshold", confidence=confidence
                )
                return None

            geometry_type = data["geometry_type"]
            geometry_data = data["geometry_data"]

            # Normalise point format coming from the LLM
            if geometry_type == "point" and isinstance(geometry_data, dict):
                if "x" not in geometry_data:
                    # Try alternative coordinate formats from LLM
                    if "point" in geometry_data and isinstance(
                        geometry_data["point"], dict
                    ):
                        geometry_data = {
                            "x": geometry_data["point"].get("x", 0),
                            "y": geometry_data["point"].get("y", 0),
                        }
                    elif isinstance(geometry_data, list) and len(geometry_data) >= 2:
                        geometry_data = {"x": geometry_data[0], "y": geometry_data[1]}
                    else:
                        logger.warning(
                            "Unrecognized point format from LLM", data=geometry_data
                        )
                        return None
            elif (
                geometry_type == "point"
                and isinstance(geometry_data, list)
                and len(geometry_data) >= 2
            ):
                # Handle list format: [x, y]
                geometry_data = {"x": geometry_data[0], "y": geometry_data[1]}
            elif geometry_type in ("line", "polyline", "polygon"):
                if "points" not in geometry_data and isinstance(geometry_data, list):
                    geometry_data = {"points": geometry_data}

            # Scale coordinates back to original image space
            scale_back_x = image_width / llm_width if llm_width else 1
            scale_back_y = image_height / llm_height if llm_height else 1
            geometry_data = _scale_geometry(
                geometry_type,
                geometry_data,
                scale_back_x,
                scale_back_y,
            )

            logger.info(
                "Predict-next-point succeeded",
                geometry_type=geometry_type,
                confidence=confidence,
                latency_ms=round(response.latency_ms, 1),
            )

            return {
                "geometry_type": geometry_type,
                "geometry_data": geometry_data,
                "confidence": confidence,
            }

        except Exception:
            logger.warning("Predict-next-point failed silently", exc_info=True)
            return None


def _scale_geometry(
    geometry_type: str,
    geometry_data: dict[str, Any],
    sx: float,
    sy: float,
) -> dict[str, Any]:
    """Scale geometry coordinates by (sx, sy)."""
    if geometry_type == "point":
        return {
            "x": (geometry_data.get("x") or 0) * sx,
            "y": (geometry_data.get("y") or 0) * sy,
        }
    elif geometry_type == "rectangle":
        return {
            "x": (geometry_data.get("x") or 0) * sx,
            "y": (geometry_data.get("y") or 0) * sy,
            "width": (geometry_data.get("width") or 0) * sx,
            "height": (geometry_data.get("height") or 0) * sy,
        }
    elif geometry_type == "circle":
        center = geometry_data.get("center", {})
        if not isinstance(center, dict):
            center = {}
        return {
            "center": {
                "x": (center.get("x") or 0) * sx,
                "y": (center.get("y") or 0) * sy,
            },
            "radius": (geometry_data.get("radius") or 0) * (sx + sy) / 2,
        }
    else:
        points = geometry_data.get("points", [])
        return {
            "points": [
                {"x": (p.get("x") or 0) * sx, "y": (p.get("y") or 0) * sy}
                for p in points
            ],
        }


# Singleton
_service: PredictNextPointService | None = None


def get_predict_point_service() -> PredictNextPointService:
    """Get (or create) the singleton predict-next-point service."""
    global _service
    if _service is None:
        _service = PredictNextPointService()
    return _service
