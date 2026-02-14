"""Tests for shared export data structures and query logic."""

import uuid

import pytest

from app.services.export.base import (
    ExportData,
    ConditionData,
    MeasurementData,
    AssemblyCostData,
    format_unit,
    BaseExporter,
)


class TestExportData:

    def test_all_measurements_returns_flat_list(self, sample_project_data):
        """all_measurements returns measurements from all conditions."""
        all_m = sample_project_data.all_measurements
        assert len(all_m) == 5  # 3 + 2 + 0

    def test_all_measurements_empty_project(self, empty_project_data):
        """all_measurements on empty project returns empty list."""
        assert empty_project_data.all_measurements == []

    def test_all_measurements_includes_correct_condition_names(self, sample_project_data):
        """Each measurement retains its condition_name."""
        all_m = sample_project_data.all_measurements
        condition_names = {m.condition_name for m in all_m}
        assert condition_names == {"Floor Slab", "Footing"}


class TestFormatUnit:

    def test_known_units(self):
        """Known units return their abbreviations."""
        assert format_unit("LF") == "LF"
        assert format_unit("SF") == "SF"
        assert format_unit("CY") == "CY"
        assert format_unit("EA") == "EA"

    def test_unknown_unit_passthrough(self):
        """Unknown units are returned as-is."""
        assert format_unit("m²") == "m²"
        assert format_unit("custom") == "custom"


class TestBaseExporterInterface:

    def test_cannot_instantiate_abstract(self):
        """BaseExporter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseExporter()

    def test_subclass_must_implement_generate(self):
        """Subclass that doesn't implement generate raises TypeError."""
        with pytest.raises(TypeError):
            class IncompleteExporter(BaseExporter):
                @property
                def content_type(self):
                    return "text/plain"

                @property
                def file_extension(self):
                    return ".txt"

            IncompleteExporter()

    def test_valid_subclass_works(self):
        """A complete subclass can be instantiated."""
        class DummyExporter(BaseExporter):
            @property
            def content_type(self):
                return "text/plain"

            @property
            def file_extension(self):
                return ".txt"

            def generate(self, data, options=None):
                return b"test"

        exporter = DummyExporter()
        assert exporter.generate(None) == b"test"


class TestMeasurementData:

    def test_measurement_data_fields(self):
        """MeasurementData stores all expected fields."""
        m = MeasurementData(
            id=uuid.uuid4(),
            condition_name="Test",
            condition_id=uuid.uuid4(),
            page_id=uuid.uuid4(),
            page_number=1,
            sheet_number="S-001",
            sheet_title="Title",
            geometry_type="polygon",
            geometry_data={"points": []},
            quantity=100.0,
            unit="SF",
            pixel_length=None,
            pixel_area=50000.0,
            is_ai_generated=True,
            is_verified=False,
            notes="A note",
        )
        assert m.condition_name == "Test"
        assert m.quantity == 100.0
        assert m.is_ai_generated is True
        assert m.notes == "A note"


class TestConditionData:

    def test_condition_data_with_empty_measurements(self):
        """ConditionData can be created with no measurements."""
        c = ConditionData(
            id=uuid.uuid4(),
            name="Empty",
            description=None,
            scope="concrete",
            category=None,
            measurement_type="area",
            color="#000",
            unit="SF",
            depth=None,
            thickness=None,
            total_quantity=0.0,
            measurement_count=0,
            building=None,
            area=None,
            elevation=None,
            measurements=[],
        )
        assert len(c.measurements) == 0
        assert c.total_quantity == 0.0

    def test_condition_data_with_assembly_cost(self):
        """ConditionData can include assembly cost data."""
        ac = AssemblyCostData(
            material_cost=1000.0,
            labor_cost=500.0,
            equipment_cost=200.0,
            subcontract_cost=0.0,
            other_cost=50.0,
            total_cost=1750.0,
            unit_cost=3.50,
            total_labor_hours=20.0,
            overhead_percent=10.0,
            profit_percent=8.0,
            total_with_markup=2065.0,
        )
        c = ConditionData(
            id=uuid.uuid4(),
            name="Costed",
            description=None,
            scope="concrete",
            category=None,
            measurement_type="area",
            color="#000",
            unit="SF",
            depth=None,
            thickness=None,
            total_quantity=500.0,
            measurement_count=2,
            building=None,
            area=None,
            elevation=None,
            assembly_cost=ac,
        )
        assert c.assembly_cost is not None
        assert c.assembly_cost.material_cost == 1000.0
        assert c.assembly_cost.total_with_markup == 2065.0

    def test_condition_data_assembly_cost_defaults_none(self):
        """ConditionData assembly_cost defaults to None."""
        c = ConditionData(
            id=uuid.uuid4(),
            name="NoAssembly",
            description=None,
            scope="concrete",
            category=None,
            measurement_type="area",
            color="#000",
            unit="SF",
            depth=None,
            thickness=None,
            total_quantity=0.0,
            measurement_count=0,
            building=None,
            area=None,
            elevation=None,
        )
        assert c.assembly_cost is None


class TestExportDataCosts:

    def test_total_project_cost(self, sample_project_data):
        """total_project_cost sums total_with_markup across costed conditions."""
        total = sample_project_data.total_project_cost
        # Only Floor Slab has assembly_cost (9676.00)
        assert total == 9676.00

    def test_total_project_cost_no_assemblies(self, empty_project_data):
        """total_project_cost is 0 when no conditions exist."""
        assert empty_project_data.total_project_cost == 0.0
