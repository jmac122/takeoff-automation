"""LLM-based similarity detection for auto-count."""

from __future__ import annotations

import json
from dataclasses import dataclass

import structlog

from app.services.auto_count.template_matcher import MatchResult

logger = structlog.get_logger()

# Prompt for LLM vision detection
FIND_SIMILAR_PROMPT = """You are analyzing a construction drawing. I have highlighted a specific element
with a RED bounding box on the image. Your task is to find ALL other instances of this same element
type on the drawing.

For each instance found, return its bounding box coordinates in pixel space.

Rules:
- Only find elements that are visually IDENTICAL or very similar to the highlighted one
- Do NOT include the highlighted element itself
- Return coordinates relative to the full image dimensions
- Include a confidence score (0.0 to 1.0) for each detection

Return your response as a JSON object:
{
  "detections": [
    {
      "x": <left pixel>,
      "y": <top pixel>,
      "w": <width pixels>,
      "h": <height pixels>,
      "confidence": <0.0 to 1.0>,
      "description": "<brief description>"
    }
  ],
  "total_found": <count>,
  "element_description": "<what the element appears to be>"
}

If no similar elements are found, return an empty detections array.
Image dimensions: {width}x{height} pixels."""


class LLMSimilarityService:
    """Use a vision LLM to find instances of a template element on a drawing."""

    def __init__(self, provider: str | None = None) -> None:
        self.provider = provider

    async def find_similar(
        self,
        page_image_bytes: bytes,
        template_bbox: dict,
        image_width: int,
        image_height: int,
    ) -> list[MatchResult]:
        """Find similar elements using LLM vision analysis.

        Args:
            page_image_bytes: Full page image with template highlighted.
            template_bbox: Original template location for reference.
            image_width: Page image width in pixels.
            image_height: Page image height in pixels.

        Returns:
            List of MatchResult from LLM detections.
        """
        from app.services.llm_client import get_llm_client

        # Draw a red rectangle overlay on the page image to highlight the template
        highlighted_bytes = self._highlight_template(
            page_image_bytes, template_bbox
        )

        prompt = FIND_SIMILAR_PROMPT.format(
            width=image_width, height=image_height
        )

        client = get_llm_client(provider=self.provider, task="auto_count")

        try:
            response_data, llm_response = client.analyze_image_json(
                image_bytes=highlighted_bytes,
                prompt=prompt,
                max_tokens=4096,
            )
        except Exception as e:
            logger.error("LLM similarity detection failed", error=str(e))
            return []

        # Parse detections from LLM response
        detections = response_data.get("detections", [])
        matches: list[MatchResult] = []

        # Scale from LLM image dimensions back to original
        llm_w = llm_response.image_width or image_width
        llm_h = llm_response.image_height or image_height
        scale_x = image_width / llm_w if llm_w > 0 else 1.0
        scale_y = image_height / llm_h if llm_h > 0 else 1.0

        for det in detections:
            try:
                x = float(det["x"]) * scale_x
                y = float(det["y"]) * scale_y
                w = float(det["w"]) * scale_x
                h = float(det["h"]) * scale_y
                confidence = float(det.get("confidence", 0.5))

                # Clamp to image bounds
                x = max(0, min(x, image_width - 1))
                y = max(0, min(y, image_height - 1))
                w = min(w, image_width - x)
                h = min(h, image_height - y)

                if w <= 0 or h <= 0:
                    continue

                matches.append(
                    MatchResult(
                        x=x,
                        y=y,
                        w=w,
                        h=h,
                        center_x=x + w / 2,
                        center_y=y + h / 2,
                        confidence=min(1.0, max(0.0, confidence)),
                    )
                )
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(
                    "Skipping invalid LLM detection", detection=det, error=str(e)
                )
                continue

        logger.info(
            "LLM similarity detection complete",
            raw_detections=len(detections),
            valid_matches=len(matches),
            llm_latency_ms=llm_response.latency_ms,
        )

        return matches

    def _highlight_template(
        self, page_image_bytes: bytes, template_bbox: dict
    ) -> bytes:
        """Draw a red bounding box on the page image to highlight the template region."""
        try:
            import cv2
            import numpy as np

            page_array = np.frombuffer(page_image_bytes, dtype=np.uint8)
            img = cv2.imdecode(page_array, cv2.IMREAD_COLOR)
            if img is None:
                return page_image_bytes

            x = int(template_bbox["x"])
            y = int(template_bbox["y"])
            w = int(template_bbox["w"])
            h = int(template_bbox["h"])

            # Draw red rectangle (BGR: 0, 0, 255)
            thickness = max(2, min(img.shape[0], img.shape[1]) // 300)
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), thickness)

            _, encoded = cv2.imencode(".png", img)
            return encoded.tobytes()
        except ImportError:
            # If cv2 not available, return original image
            return page_image_bytes
