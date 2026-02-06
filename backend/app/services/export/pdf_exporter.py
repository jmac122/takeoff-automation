"""PDF report exporter using ReportLab."""

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from app.services.export.base import BaseExporter, ExportData, format_unit


class PDFExporter(BaseExporter):
    """Export project data to PDF report."""

    @property
    def content_type(self) -> str:
        return "application/pdf"

    @property
    def file_extension(self) -> str:
        return ".pdf"

    def generate(self, data: ExportData, options: dict | None = None) -> bytes:
        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontSize=18,
            spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=16,
        )

        elements = []

        # Title
        elements.append(Paragraph(escape(data.project_name), title_style))
        if data.client_name:
            elements.append(Paragraph(f"Client: {escape(data.client_name)}", styles["Normal"]))
        if data.project_description:
            elements.append(Paragraph(escape(data.project_description), styles["Normal"]))
        elements.append(Spacer(1, 0.3 * inch))

        # Summary section
        elements.append(Paragraph("Project Summary", heading_style))
        summary_data = [["Condition", "Type", "Unit", "Quantity", "Count"]]
        for cond in data.conditions:
            summary_data.append([
                cond.name,
                cond.measurement_type,
                format_unit(cond.unit),
                f"{cond.total_quantity:.2f}",
                str(cond.measurement_count),
            ])

        if len(summary_data) > 1:
            summary_table = Table(summary_data, repeatRows=1)
            summary_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B579A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (3, 0), (4, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4F8")]),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(summary_table)
        else:
            elements.append(Paragraph("No conditions found.", styles["Normal"]))

        elements.append(Spacer(1, 0.3 * inch))

        # Condition breakdown tables
        for cond in data.conditions:
            if not cond.measurements:
                continue

            elements.append(Paragraph(f"Condition: {escape(cond.name)}", heading_style))
            detail_info = f"Type: {escape(cond.measurement_type)}  |  Unit: {escape(format_unit(cond.unit))}  |  Total: {cond.total_quantity:.2f}"
            elements.append(Paragraph(detail_info, styles["Normal"]))
            elements.append(Spacer(1, 0.1 * inch))

            detail_data = [["Page", "Sheet #", "Geometry", "Quantity", "Unit"]]
            for m in cond.measurements:
                detail_data.append([
                    str(m.page_number) if m.page_number is not None else "",
                    m.sheet_number or "",
                    m.geometry_type,
                    f"{m.quantity:.4f}",
                    format_unit(m.unit),
                ])

            detail_table = Table(detail_data, repeatRows=1)
            detail_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (3, 0), (4, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(detail_table)
            elements.append(Spacer(1, 0.15 * inch))

        doc.build(elements)
        return buf.getvalue()
