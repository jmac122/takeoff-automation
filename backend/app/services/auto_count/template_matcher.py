"""OpenCV-based template matching for auto-count detection."""

from __future__ import annotations

import io
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class MatchResult:
    """A single template match location."""

    x: float
    y: float
    w: float
    h: float
    center_x: float
    center_y: float
    confidence: float


class TemplateMatchingService:
    """Find instances of a template region on a page image using OpenCV."""

    def __init__(
        self,
        confidence_threshold: float = 0.80,
        scale_tolerance: float = 0.20,
        rotation_tolerance: float = 15.0,
        nms_overlap_threshold: float = 0.30,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.scale_tolerance = scale_tolerance
        self.rotation_tolerance = rotation_tolerance
        self.nms_overlap_threshold = nms_overlap_threshold

    def find_matches(
        self,
        page_image_bytes: bytes,
        template_bbox: dict,
        confidence_threshold: float | None = None,
        scale_steps: int = 5,
        rotation_steps: int = 5,
    ) -> list[MatchResult]:
        """Find all template matches on the page image.

        Args:
            page_image_bytes: Full page image as bytes.
            template_bbox: {"x": float, "y": float, "w": float, "h": float}
                           in pixel coordinates on the page image.
            confidence_threshold: Override default threshold.
            scale_steps: Number of scale variants to try in each direction.
            rotation_steps: Number of rotation variants to try in each direction.

        Returns:
            List of MatchResult sorted by confidence descending.
        """
        try:
            import cv2
            import numpy as np
        except ImportError:
            logger.warning("OpenCV not installed — returning empty matches")
            return []

        threshold = confidence_threshold or self.confidence_threshold

        # Decode page image
        page_array = np.frombuffer(page_image_bytes, dtype=np.uint8)
        page_img = cv2.imdecode(page_array, cv2.IMREAD_GRAYSCALE)
        if page_img is None:
            logger.error("Failed to decode page image")
            return []

        # Crop template from the page image
        x = int(template_bbox["x"])
        y = int(template_bbox["y"])
        w = int(template_bbox["w"])
        h = int(template_bbox["h"])

        # Clamp to image bounds
        x = max(0, x)
        y = max(0, y)
        w = min(w, page_img.shape[1] - x)
        h = min(h, page_img.shape[0] - y)

        if w <= 0 or h <= 0:
            logger.error("Invalid template bbox", bbox=template_bbox)
            return []

        template = page_img[y : y + h, x : x + w]

        # Generate scale and rotation variants
        all_matches: list[MatchResult] = []

        scale_min = 1.0 - self.scale_tolerance
        scale_max = 1.0 + self.scale_tolerance
        scales = np.linspace(scale_min, scale_max, 2 * scale_steps + 1)

        rot_min = -self.rotation_tolerance
        rot_max = self.rotation_tolerance
        rotations = np.linspace(rot_min, rot_max, 2 * rotation_steps + 1)

        for scale in scales:
            for rotation in rotations:
                variant = self._transform_template(template, scale, rotation)
                if variant is None or variant.shape[0] <= 0 or variant.shape[1] <= 0:
                    continue

                # Skip if variant is larger than the page
                if (
                    variant.shape[0] > page_img.shape[0]
                    or variant.shape[1] > page_img.shape[1]
                ):
                    continue

                matches = self._match_single_variant(
                    page_img, variant, threshold
                )
                all_matches.extend(matches)

        # Non-maximum suppression to remove overlapping detections
        filtered = self._non_maximum_suppression(all_matches)

        # Remove the template region itself (the original selection)
        filtered = self._exclude_template_region(filtered, template_bbox)

        filtered.sort(key=lambda m: m.confidence, reverse=True)

        logger.info(
            "Template matching complete",
            total_raw=len(all_matches),
            after_nms=len(filtered),
            threshold=threshold,
        )

        return filtered

    def _transform_template(
        self, template, scale: float, rotation: float
    ):
        """Apply scale and rotation to a template image."""
        try:
            import cv2
            import numpy as np
        except ImportError:
            return None

        h, w = template.shape[:2]
        new_w = int(w * scale)
        new_h = int(h * scale)

        if new_w <= 0 or new_h <= 0:
            return None

        scaled = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        if abs(rotation) < 0.1:
            return scaled

        center = (new_w // 2, new_h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, rotation, 1.0)
        rotated = cv2.warpAffine(scaled, rotation_matrix, (new_w, new_h))
        return rotated

    def _match_single_variant(
        self,
        page_img,
        variant,
        threshold: float,
    ) -> list[MatchResult]:
        """Run matchTemplate for a single variant and return matches above threshold."""
        try:
            import cv2
            import numpy as np
        except ImportError:
            return []

        result = cv2.matchTemplate(page_img, variant, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)

        vh, vw = variant.shape[:2]
        matches = []

        for pt_y, pt_x in zip(locations[0], locations[1]):
            conf = float(result[pt_y, pt_x])
            matches.append(
                MatchResult(
                    x=float(pt_x),
                    y=float(pt_y),
                    w=float(vw),
                    h=float(vh),
                    center_x=float(pt_x + vw / 2),
                    center_y=float(pt_y + vh / 2),
                    confidence=conf,
                )
            )

        return matches

    def _non_maximum_suppression(
        self, matches: list[MatchResult]
    ) -> list[MatchResult]:
        """Remove overlapping detections, keeping highest confidence."""
        if not matches:
            return []

        # Sort by confidence descending
        matches.sort(key=lambda m: m.confidence, reverse=True)
        keep: list[MatchResult] = []

        for match in matches:
            is_overlapping = False
            for kept in keep:
                iou = self._compute_iou(match, kept)
                if iou > self.nms_overlap_threshold:
                    is_overlapping = True
                    break
            if not is_overlapping:
                keep.append(match)

        return keep

    def _compute_iou(self, a: MatchResult, b: MatchResult) -> float:
        """Compute intersection over union of two bounding boxes."""
        x1 = max(a.x, b.x)
        y1 = max(a.y, b.y)
        x2 = min(a.x + a.w, b.x + b.w)
        y2 = min(a.y + a.h, b.y + b.h)

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area_a = a.w * a.h
        area_b = b.w * b.h
        union = area_a + area_b - intersection

        if union <= 0:
            return 0.0
        return intersection / union

    def _exclude_template_region(
        self, matches: list[MatchResult], template_bbox: dict
    ) -> list[MatchResult]:
        """Remove the match that overlaps with the original template selection."""
        template_match = MatchResult(
            x=template_bbox["x"],
            y=template_bbox["y"],
            w=template_bbox["w"],
            h=template_bbox["h"],
            center_x=template_bbox["x"] + template_bbox["w"] / 2,
            center_y=template_bbox["y"] + template_bbox["h"] / 2,
            confidence=1.0,
        )

        return [
            m
            for m in matches
            if self._compute_iou(m, template_match) < 0.50
        ]
