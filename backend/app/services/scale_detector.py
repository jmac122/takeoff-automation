"""Scale detection and parsing service."""

import json
import re
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
import structlog

from app.services.llm_client import get_llm_client

logger = structlog.get_logger()


@dataclass
class ParsedScale:
    """Parsed scale information."""

    original_text: str
    scale_ratio: float  # e.g., 48 for 1/4" = 1'-0" (1:48)
    drawing_unit: str  # "inch" or "foot"
    real_unit: str  # "foot" or "inch"
    is_metric: bool
    confidence: float

    @property
    def pixels_per_foot(self) -> float | None:
        """Calculate pixels per foot given standard DPI assumptions.

        This is a rough estimate. Actual calibration should use
        known dimensions or manual calibration.
        """
        # Assuming 150 DPI rendering (common for plan images)
        # and the drawing was originally on paper at the stated scale
        if self.is_metric:
            return None  # Metric needs different handling

        # For architectural scale like 1/4" = 1'-0":
        # 1 foot on the real building = 1/4" on the drawing
        # At 150 DPI: 1/4" = 150/4 = 37.5 pixels
        # So 1 real foot = 37.5 pixels

        dpi = 150
        if self.drawing_unit == "inch":
            # drawing_inches = real_feet / scale_ratio
            # pixels = drawing_inches * dpi
            # pixels_per_foot = dpi / scale_ratio
            return dpi / self.scale_ratio

        return None


class ScaleParser:
    """Parser for construction scale notations."""

    # Architectural scale patterns (= sign optional for OCR tolerance)
    ARCH_PATTERNS = [
        # 1/4" = 1'-0" or 1/4" 1'-0" (OCR may miss =)
        (r'(\d+)/(\d+)["\']?\s*=?\s*1[\'\"]\s*-?\s*0["\']?', "fractional_arch"),
        # 1/4" = 1' or 1/4" 1'
        (r'(\d+)/(\d+)["\']?\s*=?\s*1[\'"]', "fractional_arch_simple"),
        # 1" = 1'-0" or 1" 1'-0"
        (r'(\d+)["\']?\s*=?\s*1[\'\"]\s*-?\s*0["\']?', "whole_arch"),
        # 3/4" = 1'-0" or 3/4" 1'-0"
        (r'(\d+)/(\d+)["\']?\s*=?\s*1[\'"]-0["\']?', "fractional_arch"),
    ]

    # Engineering scale patterns (= sign optional for OCR tolerance)
    ENG_PATTERNS = [
        # 1" = 20' or 1" 20'
        (r'1["\']?\s*=?\s*(\d+)[\'"]', "engineering"),
        # 1" = 20'-0" or 1" 20'-0"
        (r'1["\']?\s*=?\s*(\d+)[\'\"]\s*-?\s*0["\']?', "engineering"),
    ]

    # Ratio patterns
    RATIO_PATTERNS = [
        # 1:48, 1:100
        (r"1\s*:\s*(\d+)", "ratio"),
        # SCALE 1:48
        (r"SCALE\s*1\s*:\s*(\d+)", "ratio"),
    ]

    # Common architectural scale ratios
    ARCH_SCALE_MAP = {
        (3, 1): 4,  # 3" = 1'-0" (1:4)
        (1, 1): 12,  # 1" = 1'-0" (1:12)
        (3, 4): 16,  # 3/4" = 1'-0" (1:16)
        (1, 2): 24,  # 1/2" = 1'-0" (1:24)
        (3, 8): 32,  # 3/8" = 1'-0" (1:32)
        (1, 4): 48,  # 1/4" = 1'-0" (1:48)
        (3, 16): 64,  # 3/16" = 1'-0" (1:64)
        (1, 8): 96,  # 1/8" = 1'-0" (1:96)
        (1, 16): 192,  # 1/16" = 1'-0" (1:192)
    }

    def parse_scale_text(self, text: str) -> ParsedScale | None:
        """Parse a scale notation string.

        Args:
            text: Scale text like "1/4\" = 1'-0\"" or "1\" = 20'"

        Returns:
            ParsedScale or None if cannot parse
        """
        text = text.strip().upper()

        # Check for "NOT TO SCALE"
        if re.search(r"N\.?T\.?S\.?|NOT\s*TO\s*SCALE", text):
            return ParsedScale(
                original_text=text,
                scale_ratio=0,
                drawing_unit="inch",
                real_unit="foot",
                is_metric=False,
                confidence=1.0,
            )

        # Try architectural patterns
        for pattern, scale_type in self.ARCH_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_arch_scale(match, scale_type, text)

        # Try engineering patterns
        for pattern, scale_type in self.ENG_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_eng_scale(match, text)

        # Try ratio patterns
        for pattern, scale_type in self.RATIO_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_ratio_scale(match, text)

        return None

    def _parse_arch_scale(
        self,
        match: re.Match,
        scale_type: str,
        original: str,
    ) -> ParsedScale:
        """Parse architectural scale format."""
        if scale_type in ("fractional_arch", "fractional_arch_simple"):
            numerator = int(match.group(1))
            denominator = int(match.group(2))

            # Look up in scale map
            key = (numerator, denominator)
            if key in self.ARCH_SCALE_MAP:
                ratio = self.ARCH_SCALE_MAP[key]
            else:
                # Calculate: if n/d inch = 1 foot, ratio = 12 * d / n
                ratio = 12 * denominator / numerator
        else:
            # Whole number like 1" = 1'-0" or 3" = 1'-0"
            inches = int(match.group(1))
            ratio = 12 / inches

        return ParsedScale(
            original_text=original,
            scale_ratio=ratio,
            drawing_unit="inch",
            real_unit="foot",
            is_metric=False,
            confidence=0.9,
        )

    def _parse_eng_scale(self, match: re.Match, original: str) -> ParsedScale:
        """Parse engineering scale format (1" = X')."""
        feet = int(match.group(1))
        ratio = feet * 12  # Convert to inches for consistency

        return ParsedScale(
            original_text=original,
            scale_ratio=ratio,
            drawing_unit="inch",
            real_unit="foot",
            is_metric=False,
            confidence=0.9,
        )

    def _parse_ratio_scale(self, match: re.Match, original: str) -> ParsedScale:
        """Parse ratio scale format (1:X)."""
        ratio = int(match.group(1))

        # Determine if metric or imperial based on ratio
        is_metric = ratio in (50, 100, 200, 500, 1000)

        return ParsedScale(
            original_text=original,
            scale_ratio=ratio,
            drawing_unit="unit",
            real_unit="unit",
            is_metric=is_metric,
            confidence=0.8,
        )


class ScaleBarDetector:
    """Detect graphical scale bars using computer vision."""

    def detect_scale_bar(
        self,
        image_bytes: bytes,
    ) -> list[dict[str, Any]]:
        """Detect scale bars in an image.

        Looks for horizontal lines with tick marks and numbers
        that indicate a graphical scale.

        Returns:
            List of detected scale bar candidates with positions
        """
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        if img is None:
            return []

        # Edge detection
        edges = cv2.Canny(img, 50, 150)

        # Detect horizontal lines using HoughLinesP
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=100,
            minLineLength=100,
            maxLineGap=10,
        )

        if lines is None:
            return []

        scale_bar_candidates = []

        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Check if line is roughly horizontal
            if abs(y2 - y1) < 5:
                length = abs(x2 - x1)

                # Scale bars are typically in a specific size range
                # and located near the bottom of the page
                if 100 < length < 500 and y1 > img.shape[0] * 0.6:
                    scale_bar_candidates.append(
                        {
                            "x1": int(x1),
                            "y1": int(y1),
                            "x2": int(x2),
                            "y2": int(y2),
                            "length_pixels": int(length),
                        }
                    )

        return scale_bar_candidates


class ScaleDetector:
    """Main scale detection service combining OCR and CV approaches."""

    def __init__(self):
        self.parser = ScaleParser()
        self.bar_detector = ScaleBarDetector()
        self.llm = get_llm_client()

    def detect_scale(
        self,
        image_bytes: bytes,
        ocr_text: str | None = None,
        detected_scale_texts: list[str] | None = None,
    ) -> dict[str, Any]:
        """Detect scale from a page image.

        Uses multiple strategies:
        1. Use vision LLM to analyze scale notation in image (PRIMARY)
        2. Parse OCR-detected scale texts (fallback)
        3. Search OCR text for scale patterns (fallback)
        4. Detect graphical scale bars

        Args:
            image_bytes: Page image
            ocr_text: Full OCR text from page
            detected_scale_texts: Pre-detected scale text candidates

        Returns:
            Detection results with parsed scale and confidence
        """
        results = {
            "parsed_scales": [],
            "scale_bars": [],
            "best_scale": None,
            "needs_calibration": True,
        }

        # Strategy 1: Use vision LLM (PRIMARY - most accurate)
        try:
            llm_result = self._detect_scale_with_llm(image_bytes)
            if llm_result:
                scale_text = llm_result.get("scale_text")
                bbox = llm_result.get("bbox")

                if scale_text:
                    parsed = self.parser.parse_scale_text(scale_text)
                    if parsed and parsed.scale_ratio > 0:
                        scale_data = {
                            "text": scale_text,
                            "ratio": parsed.scale_ratio,
                            "pixels_per_foot": parsed.pixels_per_foot,
                            "confidence": 0.95,  # High confidence for LLM
                            "method": "vision_llm",
                        }

                        # Add bbox if provided
                        if bbox:
                            scale_data["bbox"] = bbox

                        results["parsed_scales"].append(scale_data)
                        logger.info(
                            "LLM detected scale",
                            scale_text=scale_text,
                            has_bbox=bool(bbox),
                        )
        except Exception as e:
            logger.warning("LLM scale detection failed", error=str(e))

        # Strategy 2: Parse pre-detected scale texts (fallback if LLM fails)
        if not results["parsed_scales"] and detected_scale_texts:
            for text in detected_scale_texts:
                parsed = self.parser.parse_scale_text(text)
                if parsed and parsed.scale_ratio > 0:
                    results["parsed_scales"].append(
                        {
                            "text": text,
                            "ratio": parsed.scale_ratio,
                            "pixels_per_foot": parsed.pixels_per_foot,
                            "confidence": parsed.confidence * 0.85,  # Lower than LLM
                            "method": "ocr_predetected",
                        }
                    )

        # Strategy 3: Search OCR text for scale patterns (fallback)
        if ocr_text and not results["parsed_scales"]:
            # Look for scale patterns in full text
            scale_patterns = [
                r"SCALE[:\s]*([^\n]+)",
                r'(\d+/\d+["\']?\s*=?\s*[^\n]+)',  # Made = optional
                r'(1["\']?\s*=?\s*\d+[\'"][^\n]*)',  # Made = optional
            ]

            for pattern in scale_patterns:
                matches = re.findall(pattern, ocr_text, re.IGNORECASE)
                for match in matches:
                    parsed = self.parser.parse_scale_text(match)
                    if parsed and parsed.scale_ratio > 0:
                        results["parsed_scales"].append(
                            {
                                "text": match,
                                "ratio": parsed.scale_ratio,
                                "pixels_per_foot": parsed.pixels_per_foot,
                                "confidence": parsed.confidence
                                * 0.7,  # Lowest confidence
                                "method": "ocr_pattern_match",
                            }
                        )

        # Strategy 4: Detect graphical scale bars
        results["scale_bars"] = self.bar_detector.detect_scale_bar(image_bytes)

        # Select best scale
        if results["parsed_scales"]:
            # Sort by confidence
            sorted_scales = sorted(
                results["parsed_scales"],
                key=lambda x: x["confidence"],
                reverse=True,
            )
            results["best_scale"] = sorted_scales[0]

            # High confidence means likely no calibration needed
            if sorted_scales[0]["confidence"] >= 0.85:
                results["needs_calibration"] = False

        return results

    def _detect_scale_with_llm(self, image_bytes: bytes) -> dict[str, Any] | None:
        """Use vision LLM to extract scale notation and location from image.

        Args:
            image_bytes: Page image

        Returns:
            Dict with scale_text and bbox, or None
        """
        # Get image dimensions for context
        import cv2

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            logger.error("Failed to decode image for scale detection")
            return None

        height, width = img.shape[:2]

        prompt = f"""Look at this construction drawing and find the scale notation.

Common formats:
- 1/4" = 1'-0"
- 1/8" = 1'-0"
- 1" = 20'
- SCALE: 1:100
- NTS (Not To Scale)

The scale is usually near the drawing title or in the title block.

Image dimensions: {width}x{height} pixels

Return JSON with the scale text AND its bounding box in pixel coordinates where (0,0) is top-left:
{{
    "scale_text": "1/4\\" = 1'-0\\"",
    "bbox": {{
        "x": 1200,
        "y": 50,
        "width": 150,
        "height": 30
    }}
}}

If no scale is found, return: {{"scale_text": "NONE", "bbox": null}}

Return ONLY valid JSON, no other text."""

        try:
            from app.services.llm_client import LLMProvider

            response = self.llm.analyze_image(
                image_bytes=image_bytes,
                prompt=prompt,
                provider=LLMProvider.GOOGLE,  # Gemini 2.5 Flash is fast and cheap for this
            )

            # Parse JSON response
            result = json.loads(response.content.strip())

            if result.get("scale_text") and result["scale_text"].upper() != "NONE":
                return result

        except json.JSONDecodeError as e:
            logger.warning(
                "LLM returned non-JSON response, trying to extract scale text",
                error=str(e),
                response=response.content[:200],
            )
            # Fallback: try to extract scale text from non-JSON response
            scale_text = response.content.strip()
            if (
                scale_text
                and scale_text.upper() != "NONE"
                and not scale_text.startswith("{")
            ):
                return {"scale_text": scale_text, "bbox": None}
        except Exception as e:
            logger.error("LLM scale detection error", error=str(e))

        return None

    def calculate_scale_from_calibration(
        self,
        pixel_distance: float,
        real_distance: float,
        real_unit: str = "foot",
    ) -> dict[str, Any]:
        """Calculate scale from a known distance.

        Args:
            pixel_distance: Distance in pixels
            real_distance: Real-world distance
            real_unit: Unit of real distance ("foot", "inch", "meter")

        Returns:
            Calculated scale information
        """
        if pixel_distance <= 0 or real_distance <= 0:
            raise ValueError("Distances must be positive")

        pixels_per_unit = pixel_distance / real_distance

        # Convert to pixels per foot for consistency
        if real_unit == "inch":
            pixels_per_foot = pixels_per_unit * 12
        elif real_unit == "meter":
            pixels_per_foot = pixels_per_unit / 3.28084
        else:
            pixels_per_foot = pixels_per_unit

        # Estimate scale ratio (assuming 150 DPI original)
        estimated_ratio = 150 / pixels_per_foot

        return {
            "pixels_per_foot": pixels_per_foot,
            "pixels_per_unit": pixels_per_unit,
            "unit": real_unit,
            "estimated_ratio": estimated_ratio,
            "method": "manual_calibration",
        }


# Singleton instance
_scale_detector: ScaleDetector | None = None


def get_scale_detector() -> ScaleDetector:
    """Get the scale detector singleton."""
    global _scale_detector
    if _scale_detector is None:
        _scale_detector = ScaleDetector()
    return _scale_detector
