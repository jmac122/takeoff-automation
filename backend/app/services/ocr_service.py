"""OCR service using Google Cloud Vision."""

import re
from dataclasses import dataclass
from typing import Any

from google.cloud import vision
import structlog

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class TextBlock:
    """Represents a detected text block with position."""

    text: str
    confidence: float
    bounding_box: dict[str, int]  # x, y, width, height

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bounding_box": self.bounding_box,
        }


@dataclass
class OCRResult:
    """Complete OCR result for a page."""

    full_text: str
    blocks: list[TextBlock]
    detected_scale_texts: list[str]
    detected_sheet_numbers: list[str]
    detected_titles: list[str]


class OCRService:
    """Service for extracting text from images using Google Cloud Vision."""

    # Patterns for construction plan elements
    SCALE_PATTERNS = [
        # Standard architectural scales
        r'(?:SCALE[:\s]*)?(\d+(?:/\d+)?["\']?\s*=\s*\d+[\'"]\s*-?\s*\d*[\'""]?)',
        r'(\d+/\d+"\s*=\s*1\'-0")',  # 1/4" = 1'-0"
        r'(\d+"\s*=\s*\d+\')',  # 1" = 10'
        r"SCALE[:\s]*1[:\s]*(\d+)",  # SCALE: 1:100
        r"(\d+:\d+)\s*SCALE",
        r"NTS|NOT\s*TO\s*SCALE",  # Not to scale
    ]

    SHEET_NUMBER_PATTERNS = [
        r"\b([A-Z]{1,2}[-.]?\d{1,3}(?:\.\d{1,2})?)\b",  # A1.01, S-101, M101
        r"SHEET\s*(?:NO\.?|NUMBER|#)?\s*:?\s*([A-Z0-9.-]+)",
        r"DWG\.?\s*(?:NO\.?)?:?\s*([A-Z0-9.-]+)",
    ]

    TITLE_PATTERNS = [
        r"^([A-Z][A-Z\s]{3,40}(?:PLAN|ELEVATION|SECTION|DETAIL|SCHEDULE))$",
        r"TITLE[:\s]*([A-Z][A-Z\s]+)",
    ]

    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def extract_text(self, image_bytes: bytes) -> OCRResult:
        """Extract text from an image.

        Args:
            image_bytes: Image file contents

        Returns:
            OCRResult with full text and structured blocks
        """
        image = vision.Image(content=image_bytes)

        # Use document text detection for better layout understanding
        response = self.client.document_text_detection(image=image)

        if response.error.message:
            raise RuntimeError(f"Vision API error: {response.error.message}")

        # Extract full text
        full_text = ""
        if response.full_text_annotation:
            full_text = response.full_text_annotation.text

        # Extract individual blocks with positions
        blocks: list[TextBlock] = []

        if response.full_text_annotation:
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    block_text = ""
                    confidence = block.confidence

                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            word_text = "".join(symbol.text for symbol in word.symbols)
                            block_text += word_text + " "

                    block_text = block_text.strip()

                    if block_text:
                        # Get bounding box
                        vertices = block.bounding_box.vertices
                        bbox = {
                            "x": min(v.x for v in vertices),
                            "y": min(v.y for v in vertices),
                            "width": max(v.x for v in vertices)
                            - min(v.x for v in vertices),
                            "height": max(v.y for v in vertices)
                            - min(v.y for v in vertices),
                        }

                        blocks.append(
                            TextBlock(
                                text=block_text,
                                confidence=confidence,
                                bounding_box=bbox,
                            )
                        )

        # Extract specific elements
        detected_scales = self._extract_scales(full_text)
        detected_sheet_numbers = self._extract_sheet_numbers(full_text, blocks)
        detected_titles = self._extract_titles(full_text, blocks)

        return OCRResult(
            full_text=full_text,
            blocks=blocks,
            detected_scale_texts=detected_scales,
            detected_sheet_numbers=detected_sheet_numbers,
            detected_titles=detected_titles,
        )

    def _extract_scales(self, text: str) -> list[str]:
        """Extract scale notations from text."""
        scales = []

        for pattern in self.SCALE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            scales.extend(matches)

        # Clean and deduplicate
        cleaned = []
        for scale in scales:
            if isinstance(scale, tuple):
                scale = scale[0] if scale else ""
            scale = scale.strip()
            if scale and scale not in cleaned:
                cleaned.append(scale)

        return cleaned

    def _extract_sheet_numbers(
        self,
        text: str,
        blocks: list[TextBlock],
    ) -> list[str]:
        """Extract sheet numbers from text."""
        sheet_numbers = []

        for pattern in self.SHEET_NUMBER_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            sheet_numbers.extend(matches)

        # Also check title block area (typically bottom-right corner)
        # Look for blocks in bottom 20% of page
        if blocks:
            max_y = max(b.bounding_box["y"] + b.bounding_box["height"] for b in blocks)
            title_block_threshold = max_y * 0.8

            for block in blocks:
                if block.bounding_box["y"] > title_block_threshold:
                    for pattern in self.SHEET_NUMBER_PATTERNS:
                        matches = re.findall(pattern, block.text, re.IGNORECASE)
                        sheet_numbers.extend(matches)

        # Clean and deduplicate
        cleaned = list(set(s.strip().upper() for s in sheet_numbers if s.strip()))
        return cleaned

    def _extract_titles(
        self,
        text: str,
        blocks: list[TextBlock],
    ) -> list[str]:
        """Extract sheet titles from text."""
        titles = []

        # Look for common title patterns
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            for pattern in self.TITLE_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    title = match.group(1) if match.lastindex else match.group(0)
                    titles.append(title.strip())

        # Look for large text blocks (likely titles)
        if blocks:
            avg_height = sum(b.bounding_box["height"] for b in blocks) / len(blocks)

            for block in blocks:
                # Titles are usually larger text
                if block.bounding_box["height"] > avg_height * 1.5:
                    text_upper = block.text.upper()
                    # Check if it looks like a title
                    if any(
                        keyword in text_upper
                        for keyword in [
                            "PLAN",
                            "ELEVATION",
                            "SECTION",
                            "DETAIL",
                            "SCHEDULE",
                            "FOUNDATION",
                        ]
                    ):
                        titles.append(block.text.strip())

        # Clean and deduplicate
        cleaned = list(set(t for t in titles if len(t) > 3))
        return cleaned


class TitleBlockParser:
    """Parser for extracting structured data from title blocks."""

    def parse_title_block(
        self,
        blocks: list[TextBlock],
        page_width: int,
        page_height: int,
    ) -> dict[str, Any]:
        """Parse title block from OCR blocks.

        Title blocks are typically in the bottom-right corner.

        Returns:
            Dictionary with extracted title block fields
        """
        result = {
            "sheet_number": None,
            "sheet_title": None,
            "project_name": None,
            "project_number": None,
            "date": None,
            "revision": None,
            "drawn_by": None,
            "checked_by": None,
            "scale": None,
        }

        if not blocks:
            return result

        # Filter to title block region (bottom-right 30% x 30%)
        title_block_x = page_width * 0.7
        title_block_y = page_height * 0.7

        title_block_blocks = [
            b
            for b in blocks
            if (
                b.bounding_box["x"] + b.bounding_box["width"] / 2 > title_block_x
                and b.bounding_box["y"] + b.bounding_box["height"] / 2 > title_block_y
            )
        ]

        # Combine all title block text
        title_block_text = " ".join(b.text for b in title_block_blocks)

        # Extract fields using patterns
        # Note: These patterns search ONLY in the title block region (bottom-right 30%)
        patterns = {
            "sheet_number": [
                # Standard formats: S0.04, S1.01, A-101, 03200-FL-COVER-02
                r"SHEET[:\s]+([A-Z]\d+\.\d+)",  # SHEET: S0.04, SHEET S1.01
                r"SHEET\s*(?:NO\.?|NUMBER|#)?[:\s]*([A-Z0-9][-A-Z0-9.]+)",
                r"DWG\.?\s*(?:NO\.?|NUMBER)?[:\s]*([A-Z0-9][-A-Z0-9.]+)",
                r"\b(\d{5}-[A-Z]{2}-[A-Z]+-\d{2})\b",  # 03200-FL-COVER-02
                r"\b([A-Z]\d{1,2}\.\d{1,2})\b",  # S0.04, S1.01, A2.03
                r"\b([A-Z]-\d{3})\b",  # S-101, A-201
            ],
            "sheet_title": [
                r"SHEET\s*TITLE[:\s]+([A-Z][A-Z\s]+(?:AND|OR|OF|FOR)?[A-Z\s]+)",
                r"TITLE[:\s]+([A-Z][A-Z\s]+)",
            ],
            "project_number": [
                r"PROJECT\s*(?:NO\.?|NUMBER)?[:\s]*([\d-]+)",
                r"JOB\s*(?:NO\.?)?[:\s]*([\d-]+)",
            ],
            "date": [
                r"DATE[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
                r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
            ],
            "revision": [
                r"REV(?:ISION)?\.?[:\s]*([A-Z0-9]+)",
            ],
            "scale": [
                r"SCALE[:\s]*(NO\s*SCALE|NTS|NOT\s*TO\s*SCALE)",  # No scale first
                r"SCALE[:\s]*(\d+/\d+\"\s*=\s*\d+'-\d+\")",  # 1/4" = 1'-0"
                r"SCALE[:\s]*(\d+\"\s*=\s*\d+')",  # 1" = 10'
                r"SCALE[:\s]*(1:\d+)",  # 1:100
                r"SCALE[:\s]*([^,\n]+)",  # Catch-all
            ],
        }

        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, title_block_text, re.IGNORECASE)
                if match:
                    result[field] = match.group(1).strip()
                    break

        return result


# Singleton instances
_ocr_service: OCRService | None = None
_title_block_parser: TitleBlockParser | None = None


def get_ocr_service() -> OCRService:
    """Get the OCR service singleton."""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service


def get_title_block_parser() -> TitleBlockParser:
    """Get the title block parser singleton."""
    global _title_block_parser
    if _title_block_parser is None:
        _title_block_parser = TitleBlockParser()
    return _title_block_parser
