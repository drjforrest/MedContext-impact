"""Tests for forensics deepfake detection."""
import pytest

from app.forensics.deepfake import (
    DeepfakeLayerResult,
    run_deepfake_detection,
    run_layer_1,
    run_layer_3,
)


class TestForensicsDetection:
    """Test suite for deepfake detection forensics."""

    @pytest.mark.unit
    def test_run_layer_1_ela(self, sample_image_bytes):
        """Test Layer 1 (ELA) returns valid result."""
        result = run_layer_1(sample_image_bytes)

        assert isinstance(result, DeepfakeLayerResult)
        assert result.verdict in ["AUTHENTIC", "MANIPULATED", "UNCERTAIN"]
        assert 0.0 <= result.confidence <= 1.0
        assert "method" in result.details
        assert result.details["method"] == "error_level_analysis"

    @pytest.mark.unit
    def test_run_layer_1_details(self, sample_image_bytes):
        """Test Layer 1 includes ELA statistics."""
        result = run_layer_1(sample_image_bytes)

        # Should have ELA statistics (unless error occurred)
        if "error" not in result.details:
            assert "ela_mean" in result.details
            assert "ela_std" in result.details
            assert "ela_max" in result.details
            assert "image_size" in result.details

    @pytest.mark.unit
    def test_run_layer_3_exif(self, sample_image_bytes):
        """Test Layer 3 (EXIF) returns valid result."""
        result = run_layer_3(sample_image_bytes)

        assert isinstance(result, DeepfakeLayerResult)
        assert result.verdict in ["AUTHENTIC", "MANIPULATED", "UNCERTAIN"]
        assert 0.0 <= result.confidence <= 1.0
        assert "method" in result.details
        assert result.details["method"] == "exif_analysis"

    @pytest.mark.unit
    def test_run_layer_3_exif_details(self, sample_image_bytes):
        """Test Layer 3 includes EXIF metadata."""
        result = run_layer_3(sample_image_bytes)

        # Should indicate whether EXIF data was found
        if "error" not in result.details:
            assert "has_exif" in result.details

    @pytest.mark.unit
    def test_run_deepfake_detection_ensemble(self, sample_image_bytes):
        """Test full ensemble detection pipeline."""
        result = run_deepfake_detection(sample_image_bytes)

        # Check ensemble structure
        assert hasattr(result, "final_verdict")
        assert hasattr(result, "confidence")
        assert hasattr(result, "layer_1")
        assert hasattr(result, "layer_2")
        assert hasattr(result, "layer_3")

        # Check final verdict is valid
        assert result.final_verdict in ["AUTHENTIC", "MANIPULATED", "UNCERTAIN"]
        assert 0.0 <= result.confidence <= 1.0

        # Check all layers ran
        assert isinstance(result.layer_1, DeepfakeLayerResult)
        assert isinstance(result.layer_2, DeepfakeLayerResult)
        assert isinstance(result.layer_3, DeepfakeLayerResult)

    @pytest.mark.unit
    def test_ensemble_voting_logic(self, sample_image_bytes):
        """Test ensemble combines layer verdicts correctly."""
        result = run_deepfake_detection(sample_image_bytes)

        # Count layer verdicts
        verdicts = [
            result.layer_1.verdict,
            result.layer_2.verdict,
            result.layer_3.verdict,
        ]

        # If all uncertain, final should be uncertain
        if all(v == "UNCERTAIN" for v in verdicts):
            assert result.final_verdict == "UNCERTAIN"

        # If majority agrees, final should match
        authentic_count = verdicts.count("AUTHENTIC")
        manipulated_count = verdicts.count("MANIPULATED")

        if authentic_count >= 2:
            assert result.final_verdict == "AUTHENTIC"
        elif manipulated_count >= 2:
            assert result.final_verdict == "MANIPULATED"

    @pytest.mark.unit
    def test_layer_1_confidence_range(self, sample_image_bytes):
        """Test Layer 1 confidence is bounded properly."""
        result = run_layer_1(sample_image_bytes)

        # Confidence must be between 0 and 1
        assert 0.0 <= result.confidence <= 1.0

        # Non-uncertain verdicts should have higher confidence
        if result.verdict != "UNCERTAIN":
            assert result.confidence > 0.5

    @pytest.mark.unit
    def test_layer_3_software_detection(self, sample_image_bytes):
        """Test Layer 3 can detect software signatures."""
        result = run_layer_3(sample_image_bytes)

        # Should have software_tags field
        if "error" not in result.details and result.details.get("has_exif"):
            assert "software_tags" in result.details
            assert "suspicious_patterns" in result.details
            assert isinstance(result.details["software_tags"], list)
            assert isinstance(result.details["suspicious_patterns"], list)
