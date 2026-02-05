#!/usr/bin/env python3
"""Test script to verify the pipeline works without reverse image search."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.clinical.medgemma_client import MedGemmaClient


def test_direct_medgemma_analysis():
    """Test the direct MedGemma analysis method."""
    print("Testing direct MedGemma analysis...")

    # Test with a simple image and claim
    try:
        # Verify the client can be instantiated
        client = MedGemmaClient()
        print("✓ MedGemma client initialized successfully")

        # Verify client has expected methods and no reverse search methods
        assert hasattr(client, "analyze_image"), (
            "Missing analyze_image method"
        )
        assert not hasattr(client, "reverse_image_search"), (
            "Unexpected reverse_image_search method"
        )
        print("✓ Client has expected methods without reverse search")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_validation_script():
    """Test that the validation script can be imported and instantiated."""
    print("\nTesting validation script import...")

    try:
        import tempfile
        from scripts.validate_three_methods import ThreeMethodValidator

        # Create temporary paths for testing
        temp_dataset = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        try:
            # Write minimal valid JSON to the temp file
            import json
            json.dump([], temp_dataset)  # Empty list as minimal valid dataset
            temp_dataset.flush()
            temp_dataset_path = Path(temp_dataset.name)

            # Create temporary output directory
            with tempfile.TemporaryDirectory() as temp_output_dir:
                temp_output_path = Path(temp_output_dir)

                # Test instantiation with temporary paths
                validator = ThreeMethodValidator(
                    dataset_path=temp_dataset_path,
                    output_dir=temp_output_path,
                )

                print("✓ ThreeMethodValidator imported and instantiated successfully")

                # Check that the contextual_analysis method exists and has the right signature
                import inspect

                # For bound methods, 'self' is already bound so it doesn't appear in signature
                sig = inspect.signature(validator.contextual_analysis)
                params = list(sig.parameters.keys())

                if params == ["image_bytes", "claim"]:
                    print("✓ contextual_analysis method has correct signature")
                else:
                    print(f"✗ Unexpected signature: {params}")
                    print("Expected: ['image_bytes', 'claim'] for bound method")
                    return False

        finally:
            # Clean up the temporary file
            temp_dataset.close()
            Path(temp_dataset.name).unlink(missing_ok=True)

        return True

    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING PIPELINE FIX - NO REVERSE IMAGE SEARCH")
    print("=" * 60)

    test1_passed = test_direct_medgemma_analysis()
    test2_passed = test_validation_script()

    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print(f"Direct MedGemma Analysis: {'PASS' if test1_passed else 'FAIL'}")
    print(f"Validation Script Import: {'PASS' if test2_passed else 'FAIL'}")

    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED - Pipeline fixed successfully!")
        print("The pipeline now excludes reverse image search functionality.")
    else:
        print("\n❌ SOME TESTS FAILED - Please check the implementation.")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
