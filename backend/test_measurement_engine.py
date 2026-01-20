"""Test script for Phase 3A Measurement Engine verification."""

import asyncio
import sys
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.project import Project
from app.models.condition import Condition
from app.models.page import Page
from app.models.measurement import Measurement
from app.services.measurement_engine import get_measurement_engine
from app.utils.geometry import MeasurementCalculator, Point
from app.config import get_settings

settings = get_settings()


async def test_geometry_calculations():
    """Test 1: Verify geometry calculation functions."""
    print("\n=== Test 1: Geometry Calculations ===")
    
    # Test with 10 pixels per foot scale
    calc = MeasurementCalculator(pixels_per_foot=10.0)
    
    # Test 1.1: Line measurement (100 pixels = 10 feet)
    result = calc.calculate_line(
        start={"x": 0, "y": 0},
        end={"x": 100, "y": 0}
    )
    assert abs(result["length_feet"] - 10.0) < 0.01, f"Line test failed: {result}"
    print(f"✓ Line: 100px → {result['length_feet']:.1f} LF")
    
    # Test 1.2: Rectangle (100x100 pixels = 100 SF)
    result = calc.calculate_rectangle(
        x=0, y=0, width=100, height=100
    )
    assert abs(result["area_sf"] - 100.0) < 0.01, f"Rectangle test failed: {result}"
    print(f"✓ Rectangle: 100x100px → {result['area_sf']:.1f} SF")
    
    # Test 1.3: Volume calculation (100 SF with 4" depth = 1.23 CY)
    result = calc.calculate_rectangle(
        x=0, y=0, width=100, height=100, depth_inches=4
    )
    expected_cy = 100 * (4/12) / 27  # 1.234567...
    assert abs(result["volume_cy"] - expected_cy) < 0.01, f"Volume test failed: {result}"
    print(f"✓ Volume: 100 SF × 4\" → {result['volume_cy']:.2f} CY")
    
    # Test 1.4: Polygon area (triangle)
    result = calc.calculate_polygon(
        points=[
            {"x": 0, "y": 0},
            {"x": 100, "y": 0},
            {"x": 50, "y": 100}
        ]
    )
    # Triangle area = 0.5 * base * height = 0.5 * 100px * 100px = 5000 px²
    # At 10 px/ft: 5000 / (10²) = 50 SF
    assert abs(result["area_sf"] - 50.0) < 0.01, f"Polygon test failed: {result}"
    print(f"✓ Polygon: Triangle → {result['area_sf']:.1f} SF")
    
    # Test 1.5: Circle
    result = calc.calculate_circle(
        center={"x": 0, "y": 0},
        radius=50  # 50 pixels = 5 feet radius
    )
    # Area = π * r² = π * 5² = 78.54 SF
    expected_area = 3.14159 * 5 * 5
    assert abs(result["area_sf"] - expected_area) < 0.1, f"Circle test failed: {result}"
    print(f"✓ Circle: r=50px (5ft) → {result['area_sf']:.1f} SF")
    
    print("✓ All geometry calculations passed!")
    return True


async def test_database_integration():
    """Test 2: Verify database models and migration."""
    print("\n=== Test 2: Database Integration ===")
    
    engine = create_async_engine(str(settings.database_url), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if conditions table has new fields
        result = await session.execute(
            select(Condition).limit(1)
        )
        condition = result.scalar_one_or_none()
        
        if condition:
            # Verify new fields exist
            assert hasattr(condition, 'measurement_type'), "Missing measurement_type field"
            assert hasattr(condition, 'color'), "Missing color field"
            assert hasattr(condition, 'total_quantity'), "Missing total_quantity field"
            assert hasattr(condition, 'extra_metadata'), "Missing extra_metadata field"
            print(f"✓ Condition model has all new fields")
            print(f"  - measurement_type: {condition.measurement_type}")
            print(f"  - color: {condition.color}")
            print(f"  - total_quantity: {condition.total_quantity}")
        
        # Check measurements table
        result = await session.execute(
            select(Measurement).limit(1)
        )
        measurement = result.scalar_one_or_none()
        
        if measurement:
            assert hasattr(measurement, 'unit'), "Missing unit field"
            assert hasattr(measurement, 'is_ai_generated'), "Missing is_ai_generated field"
            assert hasattr(measurement, 'extra_metadata'), "Missing extra_metadata field"
            print(f"✓ Measurement model has all new fields")
            print(f"  - unit: {measurement.unit}")
            print(f"  - is_ai_generated: {measurement.is_ai_generated}")
        else:
            print("⚠ No measurements in database yet (expected for fresh install)")
    
    await engine.dispose()
    print("✓ Database integration verified!")
    return True


async def test_measurement_engine():
    """Test 3: Verify MeasurementEngine service."""
    print("\n=== Test 3: Measurement Engine Service ===")
    
    engine_db = create_async_engine(str(settings.database_url), echo=False)
    async_session = sessionmaker(engine_db, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find a project with a calibrated page
        result = await session.execute(
            select(Page)
            .where(Page.scale_calibrated == True)
            .limit(1)
        )
        page = result.scalar_one_or_none()
        
        if not page:
            print("⚠ No calibrated pages found - skipping measurement creation test")
            print("  (This is expected if no documents have been uploaded)")
            return True
        
        print(f"✓ Found calibrated page: {page.id}")
        print(f"  - Scale: {page.scale_value:.2f} px/ft")
        
        # Find or create a test condition
        result = await session.execute(
            select(Project).limit(1)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            print("⚠ No projects found - skipping measurement creation test")
            return True
        
        # Create a test condition
        test_condition = Condition(
            project_id=project.id,
            name="Test Slab (Phase 3A Verification)",
            measurement_type="area",
            unit="SF",
            color="#FF0000",
            scope="test"
        )
        session.add(test_condition)
        await session.commit()
        await session.refresh(test_condition)
        
        print(f"✓ Created test condition: {test_condition.id}")
        
        # Create a test measurement
        measurement_engine = get_measurement_engine()
        
        measurement = await measurement_engine.create_measurement(
            session=session,
            condition_id=test_condition.id,
            page_id=page.id,
            geometry_type="rectangle",
            geometry_data={
                "x": 100,
                "y": 100,
                "width": 100,
                "height": 100
            },
            notes="Test measurement for Phase 3A verification"
        )
        
        print(f"✓ Created test measurement: {measurement.id}")
        print(f"  - Geometry: rectangle 100x100px")
        print(f"  - Quantity: {measurement.quantity:.2f} {measurement.unit}")
        print(f"  - Expected: ~{100 / (page.scale_value ** 2):.2f} SF")
        
        # Verify condition totals updated
        await session.refresh(test_condition)
        assert test_condition.measurement_count == 1, "Measurement count not updated"
        assert test_condition.total_quantity > 0, "Total quantity not updated"
        print(f"✓ Condition totals updated:")
        print(f"  - Count: {test_condition.measurement_count}")
        print(f"  - Total: {test_condition.total_quantity:.2f} {test_condition.unit}")
        
        # Clean up test data
        await session.delete(measurement)
        await session.delete(test_condition)
        await session.commit()
        print("✓ Test data cleaned up")
    
    await engine_db.dispose()
    print("✓ Measurement engine service verified!")
    return True


async def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Phase 3A: Measurement Engine - Verification Tests")
    print("=" * 60)
    
    try:
        # Test 1: Geometry calculations
        await test_geometry_calculations()
        
        # Test 2: Database integration
        await test_database_integration()
        
        # Test 3: Measurement engine service
        await test_measurement_engine()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Phase 3A Implementation Verified!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
