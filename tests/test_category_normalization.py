#!/usr/bin/env python3
"""Test that category fields in distributions are single discrete values.

Ensures veracity_distribution and alignment_distribution entries have
properly normalized category fields without pipe-separated values.
"""

import pytest


def test_normalize_category_with_pipes():
    """Test that pipe-separated categories are normalized to middle option."""
    # Access the normalize_category function from the _direct_medgemma_analysis method
    # by creating a temporary validator instance
    import tempfile
    from pathlib import Path

    from scripts.validate_three_methods import ThreeMethodValidator

    # Create a minimal validator instance just to access the method logic
    with tempfile.TemporaryDirectory() as tmpdir:
        dataset_path = Path(tmpdir) / "test.json"
        dataset_path.write_text("[]")
        validator = ThreeMethodValidator(dataset_path, Path(tmpdir))

        # Test the normalization logic by calling _direct_medgemma_analysis
        # with a mocked MedGemma response
        class MockResult:
            def __init__(self, output):
                self.output = output

        # Test veracity with pipe-separated value
        test_output_uncertain_veracity = {
            "veracity": "true|partially_true|false",
            "alignment": "aligns_fully",
            "veracity_reasoning": "test",
            "alignment_reasoning": "test",
        }

        # Mock the medgemma client
        original_analyze = validator.medgemma.analyze_image
        validator.medgemma.analyze_image = lambda image_bytes, prompt: MockResult(
            test_output_uncertain_veracity
        )

        result = validator._direct_medgemma_analysis(b"fake_image", "test claim")

        # Verify normalization
        assert result["veracity_category"] == "partially_true", (
            "Pipe-separated veracity should normalize to 'partially_true'"
        )
        assert result["veracity_score"] == 0.6, (
            "Normalized 'partially_true' should map to score 0.6"
        )

        # Test alignment with pipe-separated value
        test_output_uncertain_alignment = {
            "veracity": "true",
            "alignment": "aligns_fully|partially_aligns|does_not_align",
            "veracity_reasoning": "test",
            "alignment_reasoning": "test",
        }

        validator.medgemma.analyze_image = lambda image_bytes, prompt: MockResult(
            test_output_uncertain_alignment
        )
        result = validator._direct_medgemma_analysis(b"fake_image", "test claim")

        assert result["alignment_category"] == "partially_aligns", (
            "Pipe-separated alignment should normalize to 'partially_aligns'"
        )
        assert result["alignment_score"] == 0.6, (
            "Normalized 'partially_aligns' should map to score 0.6"
        )

        # Restore
        validator.medgemma.analyze_image = original_analyze


def test_chart_data_no_pipe_separated_categories():
    """Test that generated chart_data.json has no pipe-separated categories."""
    import json
    from pathlib import Path

    # Check all existing chart_data.json files
    validation_results = Path("validation_results")
    if not validation_results.exists():
        pytest.skip("No validation_results directory")

    chart_files = list(validation_results.glob("**/chart_data.json"))
    if not chart_files:
        pytest.skip("No chart_data.json files found")

    for chart_file in chart_files:
        with open(chart_file, "r") as f:
            data = json.load(f)

        # Check veracity_distribution
        if "veracity_distribution" in data:
            for i, entry in enumerate(data["veracity_distribution"]):
                category = entry.get("category", "")
                assert "|" not in category, (
                    f"{chart_file}: veracity_distribution[{i}] has pipe-separated category: {category}"
                )

        # Check alignment_distribution
        if "alignment_distribution" in data:
            for i, entry in enumerate(data["alignment_distribution"]):
                category = entry.get("category", "")
                assert "|" not in category, (
                    f"{chart_file}: alignment_distribution[{i}] has pipe-separated category: {category}"
                )


def test_score_0_5_has_discrete_category():
    """Test that entries with score=0.5 have discrete category values."""
    import json
    from pathlib import Path

    validation_results = Path("validation_results")
    if not validation_results.exists():
        pytest.skip("No validation_results directory")

    chart_files = list(validation_results.glob("**/chart_data.json"))
    if not chart_files:
        pytest.skip("No chart_data.json files found")

    for chart_file in chart_files:
        with open(chart_file, "r") as f:
            data = json.load(f)

        # Check veracity_distribution
        if "veracity_distribution" in data:
            for i, entry in enumerate(data["veracity_distribution"]):
                if entry.get("score") == 0.5:
                    category = entry.get("category", "")
                    assert category in [
                        "true",
                        "partially_true",
                        "false",
                    ], (
                        f"{chart_file}: veracity_distribution[{i}] with score=0.5 has invalid category: {category}"
                    )
                    assert "|" not in category, (
                        f"{chart_file}: veracity_distribution[{i}] with score=0.5 has pipe-separated category"
                    )

        # Check alignment_distribution
        if "alignment_distribution" in data:
            for i, entry in enumerate(data["alignment_distribution"]):
                if entry.get("score") == 0.5:
                    category = entry.get("category", "")
                    assert category in [
                        "aligns_fully",
                        "partially_aligns",
                        "does_not_align",
                    ], (
                        f"{chart_file}: alignment_distribution[{i}] with score=0.5 has invalid category: {category}"
                    )
                    assert "|" not in category, (
                        f"{chart_file}: alignment_distribution[{i}] with score=0.5 has pipe-separated category"
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
