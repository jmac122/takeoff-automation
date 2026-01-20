"""Test script for scale detection functionality."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.scale_detector import ScaleParser, ScaleDetector


def test_scale_parser():
    """Test the scale parser with various formats."""
    parser = ScaleParser()

    test_cases = [
        # Architectural scales
        ('1/4" = 1\'-0"', 48, "architectural"),
        ('1/8" = 1\'-0"', 96, "architectural"),
        ('3/16" = 1\'-0"', 64, "architectural"),
        ('1/2" = 1\'-0"', 24, "architectural"),
        ('1" = 1\'-0"', 12, "architectural"),
        ('3" = 1\'-0"', 4, "architectural"),
        # Engineering scales
        ("1\" = 20'", 240, "engineering"),
        ("1\" = 50'", 600, "engineering"),
        ("1\" = 100'", 1200, "engineering"),
        # Ratio scales
        ("1:48", 48, "ratio"),
        ("1:100", 100, "ratio"),
        ("SCALE 1:50", 50, "ratio"),
        # Not to scale
        ("N.T.S.", 0, "not_to_scale"),
        ("NOT TO SCALE", 0, "not_to_scale"),
    ]

    print("Testing Scale Parser")
    print("=" * 60)

    passed = 0
    failed = 0

    for text, expected_ratio, scale_type in test_cases:
        result = parser.parse_scale_text(text)

        if result is None:
            print(f"❌ FAILED: '{text}' - Could not parse")
            failed += 1
            continue

        if abs(result.scale_ratio - expected_ratio) < 0.01:
            print(f"✅ PASSED: '{text}' → {result.scale_ratio:.1f} ({scale_type})")
            passed += 1
        else:
            print(
                f"❌ FAILED: '{text}' - Expected {expected_ratio}, got {result.scale_ratio}"
            )
            failed += 1

    print(f"\n{passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 60)

    return failed == 0


def test_scale_calibration():
    """Test manual scale calibration calculations."""
    detector = ScaleDetector()

    print("\nTesting Scale Calibration")
    print("=" * 60)

    # Test case: 100 pixel line = 10 feet
    # Should give 10 pixels per foot
    result = detector.calculate_scale_from_calibration(
        pixel_distance=100,
        real_distance=10,
        real_unit="foot",
    )

    expected_ppf = 10.0
    if abs(result["pixels_per_foot"] - expected_ppf) < 0.01:
        print(f"✅ PASSED: 100px = 10ft → {result['pixels_per_foot']:.1f} px/ft")
    else:
        print(f"❌ FAILED: Expected {expected_ppf}, got {result['pixels_per_foot']}")
        return False

    # Test case: 240 pixel line = 20 feet
    # Should give 12 pixels per foot
    result = detector.calculate_scale_from_calibration(
        pixel_distance=240,
        real_distance=20,
        real_unit="foot",
    )

    expected_ppf = 12.0
    if abs(result["pixels_per_foot"] - expected_ppf) < 0.01:
        print(f"✅ PASSED: 240px = 20ft → {result['pixels_per_foot']:.1f} px/ft")
    else:
        print(f"❌ FAILED: Expected {expected_ppf}, got {result['pixels_per_foot']}")
        return False

    # Test case: 120 pixel line = 10 inches
    # Should give 144 pixels per foot (120/10 * 12)
    result = detector.calculate_scale_from_calibration(
        pixel_distance=120,
        real_distance=10,
        real_unit="inch",
    )

    expected_ppf = 144.0
    if abs(result["pixels_per_foot"] - expected_ppf) < 0.01:
        print(f"✅ PASSED: 120px = 10in → {result['pixels_per_foot']:.1f} px/ft")
    else:
        print(f"❌ FAILED: Expected {expected_ppf}, got {result['pixels_per_foot']}")
        return False

    print("=" * 60)
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SCALE DETECTION VERIFICATION TESTS")
    print("=" * 60 + "\n")

    parser_ok = test_scale_parser()
    calibration_ok = test_scale_calibration()

    print("\n" + "=" * 60)
    if parser_ok and calibration_ok:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60 + "\n")

    return 0 if (parser_ok and calibration_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
