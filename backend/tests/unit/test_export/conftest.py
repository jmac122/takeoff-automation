"""Shared fixtures for export tests."""

import uuid

import pytest

from app.services.export.base import ExportData, ConditionData, MeasurementData


@pytest.fixture
def sample_project_id():
    return uuid.uuid4()


@pytest.fixture
def sample_page_id():
    return uuid.uuid4()


@pytest.fixture
def sample_project_data(sample_project_id, sample_page_id):
    """Create realistic project data for export testing."""
    cond1_id = uuid.uuid4()
    cond2_id = uuid.uuid4()
    cond3_id = uuid.uuid4()

    return ExportData(
        project_id=sample_project_id,
        project_name="Test Construction Project",
        project_description="A test project for export validation",
        client_name="Acme Construction Co.",
        conditions=[
            ConditionData(
                id=cond1_id,
                name="Floor Slab",
                description="Ground floor concrete slab",
                scope="concrete",
                category="slab",
                measurement_type="area",
                color="#3B82F6",
                unit="SF",
                depth=6.0,
                thickness=None,
                total_quantity=1500.0,
                measurement_count=3,
                building="Main Building",
                area="Ground Floor",
                elevation="0'-0\"",
                measurements=[
                    MeasurementData(
                        id=uuid.uuid4(),
                        condition_name="Floor Slab",
                        condition_id=cond1_id,
                        page_id=sample_page_id,
                        page_number=1,
                        sheet_number="S-001",
                        sheet_title="Foundation Plan",
                        geometry_type="polygon",
                        geometry_data={"points": [
                            {"x": 100, "y": 100},
                            {"x": 500, "y": 100},
                            {"x": 500, "y": 400},
                            {"x": 100, "y": 400},
                        ]},
                        quantity=500.0,
                        unit="SF",
                        pixel_length=None,
                        pixel_area=160000.0,
                        is_ai_generated=True,
                        is_verified=True,
                        notes="Main area slab",
                    ),
                    MeasurementData(
                        id=uuid.uuid4(),
                        condition_name="Floor Slab",
                        condition_id=cond1_id,
                        page_id=sample_page_id,
                        page_number=1,
                        sheet_number="S-001",
                        sheet_title="Foundation Plan",
                        geometry_type="rectangle",
                        geometry_data={"x": 600, "y": 100, "width": 200, "height": 300},
                        quantity=600.0,
                        unit="SF",
                        pixel_length=None,
                        pixel_area=60000.0,
                        is_ai_generated=False,
                        is_verified=True,
                        notes=None,
                    ),
                    MeasurementData(
                        id=uuid.uuid4(),
                        condition_name="Floor Slab",
                        condition_id=cond1_id,
                        page_id=sample_page_id,
                        page_number=2,
                        sheet_number="S-002",
                        sheet_title="Second Floor Plan",
                        geometry_type="polygon",
                        geometry_data={"points": [
                            {"x": 50, "y": 50},
                            {"x": 300, "y": 50},
                            {"x": 300, "y": 250},
                            {"x": 50, "y": 250},
                        ]},
                        quantity=400.0,
                        unit="SF",
                        pixel_length=None,
                        pixel_area=50000.0,
                        is_ai_generated=True,
                        is_verified=False,
                        notes=None,
                    ),
                ],
            ),
            ConditionData(
                id=cond2_id,
                name="Footing",
                description="Strip footing",
                scope="concrete",
                category="footing",
                measurement_type="linear",
                color="#EF4444",
                unit="LF",
                depth=None,
                thickness=12.0,
                total_quantity=250.0,
                measurement_count=2,
                building="Main Building",
                area=None,
                elevation=None,
                measurements=[
                    MeasurementData(
                        id=uuid.uuid4(),
                        condition_name="Footing",
                        condition_id=cond2_id,
                        page_id=sample_page_id,
                        page_number=1,
                        sheet_number="S-001",
                        sheet_title="Foundation Plan",
                        geometry_type="polyline",
                        geometry_data={"points": [
                            {"x": 100, "y": 500},
                            {"x": 300, "y": 500},
                            {"x": 300, "y": 700},
                        ]},
                        quantity=150.0,
                        unit="LF",
                        pixel_length=600.0,
                        pixel_area=None,
                        is_ai_generated=False,
                        is_verified=True,
                        notes="North wall footing",
                    ),
                    MeasurementData(
                        id=uuid.uuid4(),
                        condition_name="Footing",
                        condition_id=cond2_id,
                        page_id=sample_page_id,
                        page_number=1,
                        sheet_number="S-001",
                        sheet_title="Foundation Plan",
                        geometry_type="line",
                        geometry_data={"start": {"x": 400, "y": 500}, "end": {"x": 600, "y": 500}},
                        quantity=100.0,
                        unit="LF",
                        pixel_length=200.0,
                        pixel_area=None,
                        is_ai_generated=False,
                        is_verified=False,
                        notes=None,
                    ),
                ],
            ),
            ConditionData(
                id=cond3_id,
                name="Column Pads",
                description="Isolated column footings",
                scope="concrete",
                category="footing",
                measurement_type="count",
                color="#10B981",
                unit="EA",
                depth=None,
                thickness=None,
                total_quantity=8.0,
                measurement_count=0,
                building=None,
                area=None,
                elevation=None,
                measurements=[],
            ),
        ],
    )


@pytest.fixture
def empty_project_data(sample_project_id):
    """Create project data with no conditions or measurements."""
    return ExportData(
        project_id=sample_project_id,
        project_name="Empty Project",
        project_description=None,
        client_name=None,
        conditions=[],
    )
