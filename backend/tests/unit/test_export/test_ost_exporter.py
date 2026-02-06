"""Tests for OST XML export generation."""

import uuid

import pytest
from xml.etree import ElementTree

from app.services.export.base import ExportData, ConditionData, MeasurementData
from app.services.export.ost_exporter import OSTExporter


class TestOSTExporter:

    @pytest.fixture
    def exporter(self):
        return OSTExporter()

    def test_content_type(self, exporter):
        """Content type is XML."""
        assert exporter.content_type == "application/xml"

    def test_file_extension(self, exporter):
        """File extension is .xml."""
        assert exporter.file_extension == ".xml"

    def test_generates_valid_xml(self, exporter, sample_project_data):
        """Output is well-formed XML."""
        result = exporter.generate(sample_project_data)
        assert isinstance(result, bytes)
        tree = ElementTree.fromstring(result)  # Should not raise
        assert tree.tag == "OSTProject"

    def test_conditions_mapped_to_ost_format(self, exporter, sample_project_data):
        """ForgeX conditions correctly map to OST condition elements."""
        result = exporter.generate(sample_project_data)
        tree = ElementTree.fromstring(result)
        conditions = tree.find("Conditions")
        assert conditions is not None
        condition_elements = conditions.findall("Condition")
        assert len(condition_elements) == 3  # Floor Slab, Footing, Column Pads

        # Verify first condition
        first_cond = condition_elements[0]
        assert first_cond.find("Name").text == "Floor Slab"
        assert first_cond.find("Type").text == "area"
        assert first_cond.find("Unit").text == "SF"
        assert first_cond.find("Color").text == "#3B82F6"

    def test_measurements_have_coordinates(self, exporter, sample_project_data):
        """Each measurement includes its geometry coordinates in OST format."""
        result = exporter.generate(sample_project_data)
        tree = ElementTree.fromstring(result)

        conditions = tree.find("Conditions")
        first_cond = conditions.findall("Condition")[0]
        items = first_cond.find("TakeoffItems")
        first_item = items.findall("TakeoffItem")[0]

        geom = first_item.find("Geometry")
        assert geom is not None
        # Polygon type — should have Points
        points = geom.find("Points")
        assert points is not None
        point_list = points.findall("Point")
        assert len(point_list) == 4

    def test_scale_factors_included(self, exporter, sample_project_data):
        """Page numbers are included for coordinate context."""
        result = exporter.generate(sample_project_data)
        tree = ElementTree.fromstring(result)

        conditions = tree.find("Conditions")
        first_cond = conditions.findall("Condition")[0]
        items = first_cond.find("TakeoffItems")
        first_item = items.findall("TakeoffItem")[0]

        page_num = first_item.find("PageNumber")
        assert page_num is not None
        assert page_num.text == "1"

    def test_empty_project_valid_xml(self, exporter, empty_project_data):
        """Empty project produces valid minimal OST XML."""
        result = exporter.generate(empty_project_data)
        tree = ElementTree.fromstring(result)
        assert tree.tag == "OSTProject"
        conditions = tree.find("Conditions")
        assert conditions is not None
        assert len(conditions.findall("Condition")) == 0

    def test_project_info_section(self, exporter, sample_project_data):
        """Project info section contains name, description, and client."""
        result = exporter.generate(sample_project_data)
        tree = ElementTree.fromstring(result)
        info = tree.find("ProjectInfo")
        assert info is not None
        assert info.find("Name").text == "Test Construction Project"
        assert info.find("Description").text == "A test project for export validation"
        assert info.find("Client").text == "Acme Construction Co."

    def test_line_geometry_format(self, exporter, sample_project_data):
        """Line geometry has Start and End elements."""
        result = exporter.generate(sample_project_data)
        tree = ElementTree.fromstring(result)

        # Footing has a line measurement
        conditions = tree.find("Conditions")
        footing = conditions.findall("Condition")[1]
        items = footing.find("TakeoffItems")
        line_item = items.findall("TakeoffItem")[1]

        geom = line_item.find("Geometry")
        start = geom.find("Start")
        end = geom.find("End")
        assert start is not None
        assert end is not None
        assert start.find("X").text == "400"
        assert start.find("Y").text == "500"
        assert end.find("X").text == "600"
        assert end.find("Y").text == "500"

    def test_total_quantity_included(self, exporter, sample_project_data):
        """Each condition includes its total quantity."""
        result = exporter.generate(sample_project_data)
        tree = ElementTree.fromstring(result)
        conditions = tree.find("Conditions")
        first_cond = conditions.findall("Condition")[0]
        total = first_cond.find("TotalQuantity")
        assert total is not None
        assert float(total.text) == 1500.0
