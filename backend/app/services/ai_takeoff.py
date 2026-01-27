"""AI-powered takeoff generation service with multi-provider support."""

from dataclasses import dataclass
from typing import Any

import structlog

from app.services.llm_client import get_llm_client, LLMProvider, LLMResponse
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


def scale_coordinates(
    geometry_data: dict[str, Any],
    geometry_type: str,
    llm_width: int,
    llm_height: int,
    original_width: int,
    original_height: int,
) -> dict[str, Any]:
    """Scale coordinates from LLM image space to original image space.
    
    The LLM receives a resized image but returns coordinates in that resized space.
    We need to scale them back to the original image dimensions so they align
    with the page's scale_value (pixels_per_foot) which is calibrated for the
    original image.
    
    Args:
        geometry_data: The geometry data with coordinates
        geometry_type: "polygon", "polyline", "line", or "point"
        llm_width: Width of image sent to LLM
        llm_height: Height of image sent to LLM
        original_width: Original page image width
        original_height: Original page image height
        
    Returns:
        Geometry data with scaled coordinates
    """
    # No scaling needed if dimensions match
    if llm_width == original_width and llm_height == original_height:
        return geometry_data
    
    scale_x = original_width / llm_width
    scale_y = original_height / llm_height
    
    if geometry_type == "point":
        # Use `or 0` to handle both missing keys AND explicit null values
        x = geometry_data.get("x") or 0
        y = geometry_data.get("y") or 0
        return {
            "x": x * scale_x,
            "y": y * scale_y,
        }
    else:
        # polygon, polyline, line - all have "points" array
        scaled_points = []
        for point in geometry_data.get("points", []):
            # Use `or 0` to handle both missing keys AND explicit null values
            x = point.get("x") or 0
            y = point.get("y") or 0
            scaled_points.append({
                "x": x * scale_x,
                "y": y * scale_y,
            })
        return {"points": scaled_points}


@dataclass
class DetectedElement:
    """An element detected by AI."""

    element_type: str  # slab, footing, wall, column, etc.
    geometry_type: str  # polygon, polyline, line, point
    geometry_data: dict[str, Any]
    confidence: float
    description: str
    depth_inches: float | None = None  # For CY calculation

    def to_dict(self) -> dict[str, Any]:
        result = {
            "element_type": self.element_type,
            "geometry_type": self.geometry_type,
            "geometry_data": self.geometry_data,
            "confidence": self.confidence,
            "description": self.description,
        }
        if self.depth_inches is not None:
            result["depth_inches"] = self.depth_inches
        return result


@dataclass
class AITakeoffResult:
    """Result of AI takeoff analysis."""

    elements: list[DetectedElement]
    page_description: str
    analysis_notes: str
    # LLM metadata for tracking and benchmarking
    llm_provider: str = ""
    llm_model: str = ""
    llm_latency_ms: float = 0.0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "elements": [e.to_dict() for e in self.elements],
            "page_description": self.page_description,
            "analysis_notes": self.analysis_notes,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_latency_ms": self.llm_latency_ms,
            "llm_input_tokens": self.llm_input_tokens,
            "llm_output_tokens": self.llm_output_tokens,
        }


TAKEOFF_SYSTEM_PROMPT = """You are an expert construction estimator analyzing construction plan drawings to identify and measure concrete elements.

Your task is to identify specific concrete elements on the drawing and provide their locations as geometric shapes that can be used for quantity takeoff.

CRITICAL: You must provide coordinates as pixel positions on the image. The image dimensions will be provided.

When identifying elements:
1. Look for hatching patterns that indicate concrete (diagonal lines, dots)
2. Look for labels like "CONC.", "CONCRETE", "SOG" (slab on grade)
3. Identify foundation walls, footings, slabs, columns, and piers
4. Note any dimensions shown on the drawing
5. Exclude openings, equipment pads, and non-concrete areas

Respond with valid JSON only."""


AREA_DETECTION_PROMPT = """Analyze this construction plan image ({width}x{height} pixels) and identify all {element_type} areas.

For each {element_type} area found, provide:
1. A polygon (list of points) that outlines the area
2. Your confidence level (0.0-1.0)
3. A brief description

Points should be in pixel coordinates where (0,0) is top-left.

The page scale is approximately {scale_description}.

Respond with JSON in this exact format:
{{
    "page_description": "Brief description of what this page shows",
    "elements": [
        {{
            "geometry_type": "polygon",
            "points": [{{"x": 100, "y": 200}}, {{"x": 300, "y": 200}}, {{"x": 300, "y": 400}}, {{"x": 100, "y": 400}}],
            "confidence": 0.85,
            "description": "Main slab area - approximately 50'x30'"
        }}
    ],
    "analysis_notes": "Notes about the analysis"
}}

Focus specifically on: {element_type}
Additional context: {context}"""


LINEAR_DETECTION_PROMPT = """Analyze this construction plan image ({width}x{height} pixels) and identify all {element_type} elements.

For each {element_type} found, provide:
1. A polyline (list of points) that traces the centerline
2. Your confidence level (0.0-1.0)
3. A brief description

Points should be in pixel coordinates where (0,0) is top-left.

The page scale is approximately {scale_description}.

Respond with JSON in this exact format:
{{
    "page_description": "Brief description of what this page shows",
    "elements": [
        {{
            "geometry_type": "polyline",
            "points": [{{"x": 100, "y": 200}}, {{"x": 300, "y": 200}}, {{"x": 300, "y": 400}}],
            "confidence": 0.85,
            "description": "Foundation wall - north side"
        }}
    ],
    "analysis_notes": "Notes about the analysis"
}}

Focus specifically on: {element_type}
Additional context: {context}"""


COUNT_DETECTION_PROMPT = """Analyze this construction plan image ({width}x{height} pixels) and identify all {element_type} locations.

For each {element_type} found, provide:
1. A point (x, y) marking its center location
2. Your confidence level (0.0-1.0)
3. A brief description

Points should be in pixel coordinates where (0,0) is top-left.

The page scale is approximately {scale_description}.

Respond with JSON in this exact format:
{{
    "page_description": "Brief description of what this page shows",
    "elements": [
        {{
            "geometry_type": "point",
            "x": 150,
            "y": 250,
            "confidence": 0.9,
            "description": "Column C1 - 12x12"
        }}
    ],
    "analysis_notes": "Notes about the analysis"
}}

Focus specifically on: {element_type}
Additional context: {context}"""


# Autonomous detection - AI determines what concrete elements exist
AUTONOMOUS_DETECTION_PROMPT = """Analyze this construction plan image ({width}x{height} pixels) and identify ALL concrete elements you can find.

You are an expert construction estimator performing a concrete takeoff. Your task is to autonomously identify every concrete element on this drawing for quantity estimation.

IMPORTANT: You must determine on your own what concrete elements are present. Look for:
- Hatching patterns indicating concrete (diagonal lines, dots, stippling)
- Labels like "CONC.", "CONCRETE", "SOG", "S.O.G.", "FTG", "FOOTING"
- Dimension callouts for concrete elements
- Foundation symbols and wall thicknesses
- Reinforcing notes (#4, #5 rebar, mesh, etc.)

Common concrete elements to identify:
- Slabs on grade (SOG) - typically 4" to 6" thick
- Foundation walls - typically 8" to 12" thick  
- Strip/continuous footings - typically 12" to 24" wide, 8" to 12" deep
- Spread footings - typically 2'x2' to 6'x6'
- Grade beams - typically 12" to 18" wide
- Columns/piers
- Retaining walls
- Curb and gutter
- Sidewalks - typically 4" thick
- Concrete paving - typically 4" to 8" thick

For EACH concrete element found, provide:
1. element_type (e.g., "slab_on_grade", "strip_footing", "foundation_wall")
2. geometry_type: "polygon" for areas, "polyline" for linear elements, "point" for count items
3. Coordinates defining boundary in pixels (0,0 is top-left)
4. confidence level (0.0-1.0)
5. description with dimensions you can read from the drawing
6. depth_inches if you can determine it from the drawing (typical depths provided above)

The page scale is approximately {scale_description}.

Respond with JSON:
{{
    "page_description": "Description of this drawing",
    "elements": [
        {{
            "element_type": "slab_on_grade",
            "geometry_type": "polygon",
            "points": [{{"x": 100, "y": 200}}, {{"x": 500, "y": 200}}, {{"x": 500, "y": 600}}, {{"x": 100, "y": 600}}],
            "confidence": 0.85,
            "depth_inches": 4,
            "description": "Main building slab - 40'x30' - 4\" SOG"
        }},
        {{
            "element_type": "strip_footing",
            "geometry_type": "polyline", 
            "points": [{{"x": 100, "y": 200}}, {{"x": 500, "y": 200}}],
            "confidence": 0.80,
            "depth_inches": 12,
            "description": "Continuous footing - 24\" wide x 12\" deep"
        }}
    ],
    "analysis_notes": "Summary of analysis and recommendations"
}}

IMPORTANT: Look at detail callouts and section references on this sheet. If there are detail bubbles or section markers, note them as they reference structural details on other sheets.

Additional OCR context: {context}"""


class AITakeoffService:
    """Service for AI-powered takeoff generation with multi-provider support."""

    ELEMENT_PROMPTS = {
        "area": AREA_DETECTION_PROMPT,
        "linear": LINEAR_DETECTION_PROMPT,
        "count": COUNT_DETECTION_PROMPT,
    }

    def __init__(self, provider: str | None = None):
        """Initialize the service.

        Args:
            provider: Override LLM provider (default: use task-based config)
        """
        self.provider_override = provider

    def analyze_page(
        self,
        image_bytes: bytes,
        width: int,
        height: int,
        element_type: str,
        measurement_type: str,
        scale_text: str | None = None,
        ocr_text: str | None = None,
        provider: str | None = None,
    ) -> AITakeoffResult:
        """Analyze a page and detect elements for takeoff.

        Args:
            image_bytes: Page image
            width: Image width in pixels
            height: Image height in pixels
            element_type: Type of element to detect (e.g., "concrete slab", "foundation wall")
            measurement_type: "area", "linear", or "count"
            scale_text: Page scale (e.g., "1/4\" = 1'-0\"")
            ocr_text: OCR text from page (for context)
            provider: Override LLM provider for this call

        Returns:
            AITakeoffResult with detected elements
        """
        # Determine task-based provider
        task_map = {
            "area": "element_detection",
            "linear": "element_detection",
            "count": "element_detection",
        }
        task = task_map.get(measurement_type, "element_detection")

        # Get LLM client with appropriate provider
        llm = get_llm_client(
            provider=provider or self.provider_override,
            task=task,
        )

        # Select appropriate prompt template
        prompt_template = self.ELEMENT_PROMPTS.get(measurement_type, AREA_DETECTION_PROMPT)

        # Build context
        scale_description = scale_text or "unknown - use visual cues for relative sizing"
        context = ""
        if ocr_text:
            context = f"Text found on page (truncated): {ocr_text[:500]}"

        # Build prompt
        prompt = prompt_template.format(
            width=width,
            height=height,
            element_type=element_type,
            scale_description=scale_description,
            context=context,
        )

        # Call LLM
        try:
            data, response = llm.analyze_image_json(
                image_bytes=image_bytes,
                prompt=prompt,
                system_prompt=TAKEOFF_SYSTEM_PROMPT,
                max_tokens=2048,
            )

            # Get LLM image dimensions for coordinate scaling
            llm_width = response.image_width or width
            llm_height = response.image_height or height
            
            # Log if scaling is needed
            if llm_width != width or llm_height != height:
                logger.info(
                    "Scaling AI coordinates from LLM image space to original",
                    llm_size=f"{llm_width}x{llm_height}",
                    original_size=f"{width}x{height}",
                )

            # Parse detected elements
            elements = []
            for elem in data.get("elements", []):
                geometry_type = elem.get("geometry_type", "polygon")

                if geometry_type == "point":
                    # Use `or 0` to handle both missing keys AND explicit null values
                    geometry_data = {"x": elem.get("x") or 0, "y": elem.get("y") or 0}
                else:
                    # Normalize "line" to "polyline" for consistent handling
                    # measurement_engine expects "line" to have {start, end} format,
                    # but AI returns {points} format. Polyline handles both correctly.
                    if geometry_type == "line":
                        geometry_type = "polyline"
                    geometry_data = {"points": elem.get("points", [])}

                # Scale coordinates from LLM image space to original image space
                geometry_data = scale_coordinates(
                    geometry_data, geometry_type,
                    llm_width, llm_height,
                    width, height,
                )

                elements.append(
                    DetectedElement(
                        element_type=element_type,
                        geometry_type=geometry_type,
                        geometry_data=geometry_data,
                        confidence=float(elem.get("confidence", 0.5)),
                        description=elem.get("description", ""),
                    )
                )

            # Validate geometries are within bounds
            elements = self._filter_valid_geometries(elements, width, height)

            logger.info(
                "AI takeoff analysis complete",
                element_type=element_type,
                measurement_type=measurement_type,
                elements_detected=len(elements),
                provider=response.provider,
                model=response.model,
                latency_ms=response.latency_ms,
            )

            return AITakeoffResult(
                elements=elements,
                page_description=data.get("page_description", ""),
                analysis_notes=data.get("analysis_notes", ""),
                llm_provider=response.provider,
                llm_model=response.model,
                llm_latency_ms=response.latency_ms,
                llm_input_tokens=response.input_tokens,
                llm_output_tokens=response.output_tokens,
            )

        except Exception as e:
            logger.error(
                "AI takeoff analysis failed",
                element_type=element_type,
                error=str(e),
            )
            raise

    def analyze_page_autonomous(
        self,
        image_bytes: bytes,
        width: int,
        height: int,
        scale_text: str | None = None,
        ocr_text: str | None = None,
        provider: str | None = None,
    ) -> AITakeoffResult:
        """Autonomously analyze a page and detect ALL concrete elements.

        This method does NOT require a pre-defined condition. The AI will
        independently identify all concrete elements it can find on the page.

        Args:
            image_bytes: Page image
            width: Image width in pixels
            height: Image height in pixels
            scale_text: Page scale (e.g., "1/4\" = 1'-0\"")
            ocr_text: OCR text from page (for context)
            provider: Override LLM provider for this call

        Returns:
            AITakeoffResult with all detected concrete elements
        """
        # Get LLM client
        llm = get_llm_client(
            provider=provider or self.provider_override,
            task="element_detection",
        )

        # Build context
        scale_description = scale_text or "unknown - use visual cues for relative sizing"
        context = ""
        if ocr_text:
            context = f"Text found on page (truncated): {ocr_text[:1000]}"

        # Build prompt for autonomous detection
        prompt = AUTONOMOUS_DETECTION_PROMPT.format(
            width=width,
            height=height,
            scale_description=scale_description,
            context=context,
        )

        # Call LLM
        try:
            data, response = llm.analyze_image_json(
                image_bytes=image_bytes,
                prompt=prompt,
                system_prompt=TAKEOFF_SYSTEM_PROMPT,
                max_tokens=4096,  # More tokens for autonomous detection
            )

            # Get LLM image dimensions for coordinate scaling
            llm_width = response.image_width or width
            llm_height = response.image_height or height
            
            # Log if scaling is needed
            if llm_width != width or llm_height != height:
                logger.info(
                    "Scaling AI coordinates from LLM image space to original",
                    llm_size=f"{llm_width}x{llm_height}",
                    original_size=f"{width}x{height}",
                )

            # Parse detected elements - AI determines element_type
            elements = []
            for elem in data.get("elements", []):
                geometry_type = elem.get("geometry_type", "polygon")
                # Use `or "unknown"` to handle both missing keys AND explicit null values
                element_type = elem.get("element_type") or "unknown"
                # Convert depth_inches to float - LLM may return string or number
                raw_depth = elem.get("depth_inches")
                depth_inches = float(raw_depth) if raw_depth is not None else None

                if geometry_type == "point":
                    # Use `or 0` to handle both missing keys AND explicit null values
                    geometry_data = {"x": elem.get("x") or 0, "y": elem.get("y") or 0}
                else:
                    # Normalize "line" to "polyline" for consistent handling
                    # measurement_engine expects "line" to have {start, end} format,
                    # but AI returns {points} format. Polyline handles both correctly.
                    if geometry_type == "line":
                        geometry_type = "polyline"
                    geometry_data = {"points": elem.get("points", [])}

                # Scale coordinates from LLM image space to original image space
                geometry_data = scale_coordinates(
                    geometry_data, geometry_type,
                    llm_width, llm_height,
                    width, height,
                )

                # Apply default depths if AI didn't specify
                if depth_inches is None:
                    depth_inches = self._get_default_depth(element_type)

                elements.append(
                    DetectedElement(
                        element_type=element_type,  # AI-determined type
                        geometry_type=geometry_type,
                        geometry_data=geometry_data,
                        confidence=float(elem.get("confidence", 0.5)),
                        description=elem.get("description", ""),
                        depth_inches=depth_inches,
                    )
                )

            # Validate geometries are within bounds
            elements = self._filter_valid_geometries(elements, width, height)

            # Group by element type for logging
            type_counts = {}
            for elem in elements:
                type_counts[elem.element_type] = type_counts.get(elem.element_type, 0) + 1

            logger.info(
                "Autonomous AI takeoff complete",
                elements_detected=len(elements),
                element_types=type_counts,
                provider=response.provider,
                model=response.model,
                latency_ms=response.latency_ms,
            )

            return AITakeoffResult(
                elements=elements,
                page_description=data.get("page_description", ""),
                analysis_notes=data.get("analysis_notes", ""),
                llm_provider=response.provider,
                llm_model=response.model,
                llm_latency_ms=response.latency_ms,
                llm_input_tokens=response.input_tokens,
                llm_output_tokens=response.output_tokens,
            )

        except Exception as e:
            logger.error(
                "Autonomous AI takeoff failed",
                error=str(e),
            )
            raise

    # Default depths for common concrete elements (in inches)
    DEFAULT_DEPTHS = {
        "slab_on_grade": 4,
        "slab": 4,
        "concrete_slab": 4,
        "sidewalk": 4,
        "concrete_paving": 6,
        "strip_footing": 12,
        "continuous_footing": 12,
        "spread_footing": 12,
        "column_footing": 12,
        "foundation_wall": 8,
        "grade_beam": 12,
        "retaining_wall": 8,
        "concrete_wall": 8,
        "curb": 6,
        "curb_and_gutter": 6,
    }

    def _get_default_depth(self, element_type: str) -> float | None:
        """Get default depth for an element type."""
        normalized = element_type.lower().replace(" ", "_").replace("-", "_")
        return self.DEFAULT_DEPTHS.get(normalized)

    def _filter_valid_geometries(
        self,
        elements: list[DetectedElement],
        width: int,
        height: int,
    ) -> list[DetectedElement]:
        """Filter out elements with invalid geometries."""
        valid = []

        for elem in elements:
            if elem.geometry_type == "point":
                x = elem.geometry_data.get("x", 0)
                y = elem.geometry_data.get("y", 0)
                if 0 <= x <= width and 0 <= y <= height:
                    valid.append(elem)
            else:
                points = elem.geometry_data.get("points", [])
                if points and all(
                    0 <= p.get("x", -1) <= width and 0 <= p.get("y", -1) <= height
                    for p in points
                ):
                    valid.append(elem)

        return valid

    def analyze_page_multi_provider(
        self,
        image_bytes: bytes,
        width: int,
        height: int,
        element_type: str,
        measurement_type: str,
        scale_text: str | None = None,
        ocr_text: str | None = None,
        providers: list[str] | None = None,
    ) -> dict[str, AITakeoffResult]:
        """Analyze a page with multiple providers for comparison.

        Useful for benchmarking and A/B testing.

        Args:
            providers: List of providers to use (default: all available)
            ... other args same as analyze_page

        Returns:
            Dict mapping provider name to results
        """
        if providers is None:
            providers = settings.available_providers

        results = {}
        for provider in providers:
            try:
                result = self.analyze_page(
                    image_bytes=image_bytes,
                    width=width,
                    height=height,
                    element_type=element_type,
                    measurement_type=measurement_type,
                    scale_text=scale_text,
                    ocr_text=ocr_text,
                    provider=provider,
                )
                results[provider] = result
            except Exception as e:
                logger.warning(
                    "Provider failed in multi-provider analysis",
                    provider=provider,
                    error=str(e),
                )

        return results


# Convenience function
def get_ai_takeoff_service(provider: str | None = None) -> AITakeoffService:
    """Get an AI takeoff service instance.

    Args:
        provider: Override LLM provider

    Returns:
        Configured AITakeoffService
    """
    return AITakeoffService(provider=provider)
