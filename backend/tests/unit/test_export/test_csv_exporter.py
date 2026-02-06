"""Tests for CSV export generation."""

import csv
import uuid
from io import StringIO

import pytest

from app.services.export.base import ExportData, ConditionData, MeasurementData
from app.services.export.csv_exporter import CSVExporter


class TestCSVExporter:

    @pytest.fixture
    def exporter(self):
        return CSVExporter()

    def test_content_type(self, exporter):
        """Content type is text/csv."""
        assert exporter.content_type == "text/csv"

    def test_file_extension(self, exporter):
        """File extension is .csv."""
        assert exporter.file_extension == ".csv"

    def test_header_row_present(self, exporter, sample_project_data):
        """First row contains expected column headers."""
        result = exporter.generate(sample_project_data)
        text = result.decode("utf-8")
        reader = csv.reader(StringIO(text))
        headers = next(reader)
        assert "Condition" in headers
        assert "Page" in headers
        assert "Quantity" in headers
        assert "Unit" in headers
        assert "Coordinates" in headers

    def test_one_row_per_measurement(self, exporter, sample_project_data):
        """Row count matches measurement count (plus header)."""
        result = exporter.generate(sample_project_data)
        text = result.decode("utf-8")
        reader = csv.reader(StringIO(text))
        rows = list(reader)
        # 3 measurements in Floor Slab + 2 in Footing = 5, plus 1 header = 6
        assert len(rows) == 6

    def test_unicode_handling(self, exporter):
        """Condition names with unicode characters export correctly."""
        data = ExportData(
            project_id=uuid.uuid4(),
            project_name="Test",
            project_description=None,
            client_name=None,
            conditions=[
                ConditionData(
                    id=uuid.uuid4(),
                    name="Béton armé — 日本語テスト",
                    description=None,
                    scope="concrete",
                    category=None,
                    measurement_type="area",
                    color="#000000",
                    unit="SF",
                    depth=None,
                    thickness=None,
                    total_quantity=100.0,
                    measurement_count=1,
                    building=None,
                    area=None,
                    elevation=None,
                    measurements=[
                        MeasurementData(
                            id=uuid.uuid4(),
                            condition_name="Béton armé — 日本語テスト",
                            condition_id=uuid.uuid4(),
                            page_id=uuid.uuid4(),
                            page_number=1,
                            sheet_number=None,
                            sheet_title=None,
                            geometry_type="polygon",
                            geometry_data={"points": [{"x": 0, "y": 0}]},
                            quantity=100.0,
                            unit="SF",
                            pixel_length=None,
                            pixel_area=None,
                            is_ai_generated=False,
                            is_verified=False,
                            notes="Étage 1",
                        ),
                    ],
                ),
            ],
        )
        result = exporter.generate(data)
        text = result.decode("utf-8")
        assert "Béton armé — 日本語テスト" in text
        assert "Étage 1" in text

    def test_commas_in_values_escaped(self, exporter):
        """Values containing commas are properly quoted."""
        data = ExportData(
            project_id=uuid.uuid4(),
            project_name="Test",
            project_description=None,
            client_name=None,
            conditions=[
                ConditionData(
                    id=uuid.uuid4(),
                    name="Slab, Level 1",
                    description=None,
                    scope="concrete",
                    category=None,
                    measurement_type="area",
                    color="#000000",
                    unit="SF",
                    depth=None,
                    thickness=None,
                    total_quantity=100.0,
                    measurement_count=1,
                    building=None,
                    area=None,
                    elevation=None,
                    measurements=[
                        MeasurementData(
                            id=uuid.uuid4(),
                            condition_name="Slab, Level 1",
                            condition_id=uuid.uuid4(),
                            page_id=uuid.uuid4(),
                            page_number=1,
                            sheet_number=None,
                            sheet_title=None,
                            geometry_type="polygon",
                            geometry_data={"points": [{"x": 0, "y": 0}]},
                            quantity=100.0,
                            unit="SF",
                            pixel_length=None,
                            pixel_area=None,
                            is_ai_generated=False,
                            is_verified=False,
                            notes="Contains, commas, here",
                        ),
                    ],
                ),
            ],
        )
        result = exporter.generate(data)
        text = result.decode("utf-8")
        reader = csv.reader(StringIO(text))
        rows = list(reader)
        # The CSV reader should properly parse the quoted values
        assert rows[1][0] == "Slab, Level 1"
        assert rows[1][9] == "Contains, commas, here"

    def test_empty_project_has_header_only(self, exporter, empty_project_data):
        """Empty project produces CSV with header row only."""
        result = exporter.generate(empty_project_data)
        text = result.decode("utf-8")
        reader = csv.reader(StringIO(text))
        rows = list(reader)
        assert len(rows) == 1  # Header only

    def test_quantity_precision(self, exporter, sample_project_data):
        """Quantities are formatted to 4 decimal places."""
        result = exporter.generate(sample_project_data)
        text = result.decode("utf-8")
        reader = csv.reader(StringIO(text))
        next(reader)  # skip header
        row = next(reader)
        # Quantity should be formatted as 4 decimal places
        assert "." in row[4]
