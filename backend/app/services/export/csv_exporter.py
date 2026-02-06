"""CSV exporter — one row per measurement."""

import csv
import json
from io import StringIO

from app.services.export.base import BaseExporter, ExportData, format_unit, sanitize_field


class CSVExporter(BaseExporter):
    """Export project data to CSV format."""

    HEADERS = [
        "Condition",
        "Page",
        "Sheet Number",
        "Geometry Type",
        "Quantity",
        "Unit",
        "Coordinates",
        "Verified",
        "AI Generated",
        "Notes",
    ]

    @property
    def content_type(self) -> str:
        return "text/csv"

    @property
    def file_extension(self) -> str:
        return ".csv"

    def generate(self, data: ExportData, options: dict | None = None) -> bytes:
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(self.HEADERS)

        for m in data.all_measurements:
            coords = json.dumps(m.geometry_data, ensure_ascii=False)
            writer.writerow([
                sanitize_field(m.condition_name),
                m.page_number,
                m.sheet_number or "",
                m.geometry_type,
                f"{m.quantity:.4f}",
                format_unit(m.unit),
                sanitize_field(coords),
                "Yes" if m.is_verified else "No",
                "Yes" if m.is_ai_generated else "No",
                sanitize_field(m.notes or ""),
            ])

        return buf.getvalue().encode("utf-8")
