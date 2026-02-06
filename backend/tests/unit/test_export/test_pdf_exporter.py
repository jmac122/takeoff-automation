"""Tests for PDF report generation."""

import uuid

import fitz  # PyMuPDF
import pytest
from io import BytesIO

from app.services.export.base import ExportData, ConditionData, MeasurementData
from app.services.export.pdf_exporter import PDFExporter


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


class TestPDFExporter:

    @pytest.fixture
    def exporter(self):
        return PDFExporter()

    def test_content_type(self, exporter):
        """Content type is PDF."""
        assert exporter.content_type == "application/pdf"

    def test_file_extension(self, exporter):
        """File extension is .pdf."""
        assert exporter.file_extension == ".pdf"

    def test_generates_valid_pdf(self, exporter, sample_project_data):
        """Output starts with %PDF magic bytes."""
        result = exporter.generate(sample_project_data)
        assert isinstance(result, bytes)
        assert result[:5] == b'%PDF-'

    def test_contains_project_name(self, exporter, sample_project_data):
        """PDF contains the project name in text content."""
        result = exporter.generate(sample_project_data)
        text = _extract_pdf_text(result)
        assert "Test Construction Project" in text

    def test_condition_tables_present(self, exporter, sample_project_data):
        """PDF contains a table for each condition with totals."""
        result = exporter.generate(sample_project_data)
        text = _extract_pdf_text(result)
        assert "Floor Slab" in text
        assert "Footing" in text

    def test_empty_project_valid_pdf(self, exporter, empty_project_data):
        """Empty project produces valid PDF."""
        result = exporter.generate(empty_project_data)
        assert result[:5] == b'%PDF-'

    def test_client_name_included(self, exporter, sample_project_data):
        """PDF includes client name."""
        result = exporter.generate(sample_project_data)
        text = _extract_pdf_text(result)
        assert "Acme Construction" in text

    def test_pdf_has_nonzero_size(self, exporter, sample_project_data):
        """Generated PDF has substantial size (not just a header)."""
        result = exporter.generate(sample_project_data)
        assert len(result) > 1000  # A real PDF with tables should be > 1KB

    def test_summary_section_present(self, exporter, sample_project_data):
        """PDF contains project summary heading."""
        result = exporter.generate(sample_project_data)
        text = _extract_pdf_text(result)
        assert "Project Summary" in text

    def test_measurement_type_in_detail(self, exporter, sample_project_data):
        """PDF detail sections include measurement type info."""
        result = exporter.generate(sample_project_data)
        text = _extract_pdf_text(result)
        assert "area" in text.lower() or "SF" in text
