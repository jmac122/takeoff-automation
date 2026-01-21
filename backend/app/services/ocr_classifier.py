"""OCR-based page classification (fast, no LLM needed for basic classification)."""

from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class OCRClassificationResult:
    """Result of OCR-based classification."""

    discipline: str
    discipline_confidence: float
    page_type: str
    page_type_confidence: float
    concrete_relevance: str
    concrete_elements: list[str]
    description: str
    method: str  # "ocr" or "llm_vision"


class OCRPageClassifier:
    """Fast page classifier using OCR data (no expensive LLM vision calls)."""

    # Sheet number prefixes to discipline mapping
    DISCIPLINE_PREFIXES = {
        "S": ("Structural", 0.95),
        "A": ("Architectural", 0.95),
        "C": ("Civil", 0.90),
        "M": ("Mechanical", 0.95),
        "E": ("Electrical", 0.95),
        "P": ("Plumbing", 0.95),
        "L": ("Landscape", 0.90),
        "G": ("General", 0.85),
        "T": ("Title", 0.90),
        "FP": ("Fire Protection", 0.95),
        "HVAC": ("Mechanical", 0.95),
    }

    # Page type keywords
    PAGE_TYPE_KEYWORDS = {
        "Plan": [
            "PLAN",
            "FLOOR PLAN",
            "FOUNDATION PLAN",
            "ROOF PLAN",
            "SITE PLAN",
            "FRAMING PLAN",
        ],
        "Elevation": ["ELEVATION", "ELEVATIONS"],
        "Section": ["SECTION", "SECTIONS", "BUILDING SECTION"],
        "Detail": ["DETAIL", "DETAILS", "TYPICAL DETAILS"],
        "Schedule": ["SCHEDULE", "SCHEDULES"],
        "Notes": ["NOTES", "GENERAL NOTES", "SPECIFICATIONS"],
        "Cover": ["COVER", "COVER SHEET", "INDEX"],
        "Title": ["TITLE SHEET", "TITLE BLOCK"],
    }

    # Concrete relevance keywords
    CONCRETE_HIGH_KEYWORDS = [
        "FOUNDATION",
        "FOOTING",
        "SLAB",
        "CONCRETE",
        "GRADE BEAM",
        "PIER",
        "COLUMN",
        "WALL",
        "RETAINING",
        "PAVING",
        "CURB",
        "SIDEWALK",
        "FLATWORK",
        "TOPPING",
        "REINFORCING",
        "REBAR",
    ]

    CONCRETE_MEDIUM_KEYWORDS = [
        "STRUCTURAL",
        "FRAMING",
        "FLOOR",
        "ROOF",
        "BEAM",
        "SUPPORT",
        "BEARING",
        "LOAD",
    ]

    def classify_from_ocr(
        self,
        sheet_number: str | None,
        title: str | None,
        ocr_text: str | None,
    ) -> OCRClassificationResult:
        """Classify a page using OCR data only (no LLM vision needed).

        Args:
            sheet_number: Sheet number from OCR (e.g., "S1.01", "A-201")
            title: Sheet title from OCR
            ocr_text: Full OCR text from page

        Returns:
            OCRClassificationResult with classification
        """
        # Classify discipline from sheet number prefix
        discipline, discipline_conf = self._classify_discipline(
            sheet_number, title, ocr_text
        )

        # Classify page type from title and OCR text
        page_type, page_type_conf = self._classify_page_type(title, ocr_text)

        # Determine concrete relevance
        concrete_relevance, concrete_elements = self._assess_concrete_relevance(
            discipline, page_type, title, ocr_text
        )

        # Build description
        description = self._build_description(
            sheet_number, title, page_type, discipline
        )

        return OCRClassificationResult(
            discipline=discipline,
            discipline_confidence=discipline_conf,
            page_type=page_type,
            page_type_confidence=page_type_conf,
            concrete_relevance=concrete_relevance,
            concrete_elements=concrete_elements,
            description=description,
            method="ocr",
        )

    def _classify_discipline(
        self,
        sheet_number: str | None,
        title: str | None,
        ocr_text: str | None,
    ) -> tuple[str, float]:
        """Classify discipline from sheet number and text."""
        if not sheet_number:
            return ("Unknown", 0.5)

        # Extract prefix from sheet number
        # Handle formats: S1.01, S-101, S.01, 03200-FL-COVER-02
        sheet_upper = sheet_number.upper()

        # Try standard prefixes first
        for prefix, (discipline, confidence) in self.DISCIPLINE_PREFIXES.items():
            if sheet_upper.startswith(prefix):
                return (discipline, confidence)

        # Check for discipline keywords in title/text
        combined_text = f"{title or ''} {ocr_text or ''}".upper()

        if "STRUCTURAL" in combined_text:
            return ("Structural", 0.85)
        elif "ARCHITECTURAL" in combined_text or "ARCHITECTURE" in combined_text:
            return ("Architectural", 0.85)
        elif "CIVIL" in combined_text:
            return ("Civil", 0.85)
        elif "MECHANICAL" in combined_text or "HVAC" in combined_text:
            return ("Mechanical", 0.85)
        elif "ELECTRICAL" in combined_text:
            return ("Electrical", 0.85)
        elif "PLUMBING" in combined_text:
            return ("Plumbing", 0.85)

        return ("General", 0.60)

    def _classify_page_type(
        self,
        title: str | None,
        ocr_text: str | None,
    ) -> tuple[str, float]:
        """Classify page type from title and OCR text."""
        combined_text = f"{title or ''} {ocr_text or ''}".upper()

        # Check each page type's keywords
        for page_type, keywords in self.PAGE_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    # Higher confidence if found in title
                    if title and keyword in title.upper():
                        return (page_type, 0.95)
                    else:
                        return (page_type, 0.85)

        return ("Unknown", 0.50)

    def _assess_concrete_relevance(
        self,
        discipline: str,
        page_type: str,
        title: str | None,
        ocr_text: str | None,
    ) -> tuple[str, list[str]]:
        """Assess concrete relevance and identify concrete elements."""
        combined_text = f"{title or ''} {ocr_text or ''}".upper()

        # Find concrete elements
        concrete_elements = []

        for keyword in self.CONCRETE_HIGH_KEYWORDS:
            if keyword in combined_text:
                concrete_elements.append(keyword.lower())

        # Determine relevance level
        if len(concrete_elements) >= 3:
            return ("high", concrete_elements[:10])  # Limit to 10 elements

        if len(concrete_elements) >= 1:
            return ("high", concrete_elements)

        # Check medium keywords
        for keyword in self.CONCRETE_MEDIUM_KEYWORDS:
            if keyword in combined_text:
                return ("medium", [keyword.lower()])

        # Structural discipline usually has some concrete relevance
        if discipline == "Structural":
            return ("medium", [])

        # Civil often has concrete (paving, curbs, etc.)
        if discipline == "Civil":
            return ("medium", [])

        return ("low", [])

    def _build_description(
        self,
        sheet_number: str | None,
        title: str | None,
        page_type: str,
        discipline: str,
    ) -> str:
        """Build a description of the page."""
        parts = []

        if sheet_number:
            parts.append(f"Sheet {sheet_number}")

        if title:
            parts.append(title)
        elif page_type != "Unknown":
            parts.append(page_type)

        if discipline != "Unknown":
            parts.append(f"({discipline})")

        return " - ".join(parts) if parts else "Construction plan page"


# Singleton
_ocr_classifier: OCRPageClassifier | None = None


def get_ocr_classifier() -> OCRPageClassifier:
    """Get the OCR classifier singleton."""
    global _ocr_classifier
    if _ocr_classifier is None:
        _ocr_classifier = OCRPageClassifier()
    return _ocr_classifier
