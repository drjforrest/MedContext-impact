"""Tests for the reverse search service."""

import logging
from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.reverse_search.service import run_reverse_search


class TestReverseSearchService:
    """Test suite for reverse image search service."""

    @pytest.mark.unit
    def test_run_reverse_search_returns_result(self, sample_image_bytes):
        """Test that run_reverse_search returns a valid result structure."""
        from app.reverse_search.service import ReverseSearchMatch

        fake_match = ReverseSearchMatch(
            source="serpapi",
            url="https://example.com/controlled.jpg",
            title="Controlled Image Result",
            snippet="A controlled image result.",
            confidence=0.9,
            discovered_at=datetime.now(),
        )
        image_id = uuid4()
        with patch(
            "app.reverse_search.service._fetch_serpapi_matches",
            return_value=([fake_match], ["serpapi"]),
        ):
            with patch("app.reverse_search.service.settings.serp_api_key", "test_key"):
                result = run_reverse_search(
                    image_id=image_id, image_bytes=sample_image_bytes
                )

        assert hasattr(result, "image_id")
        assert hasattr(result, "status")
        assert hasattr(result, "queued_at")
        assert result.status in ["queued", "completed", "invalid_request"]

    @pytest.mark.unit
    def test_run_reverse_search_with_mock_api(self, sample_image_bytes):
        """Test reverse search with mocked SerpAPI response."""
        from app.reverse_search.service import ReverseSearchMatch

        fake_match = ReverseSearchMatch(
            source="serpapi",
            url="https://example.com/image1.jpg",
            title="Test Medical Image",
            snippet="A test medical image result.",
            confidence=0.9,
            discovered_at=datetime.now(),
        )

        image_id = uuid4()

        with patch(
            "app.reverse_search.service._fetch_serpapi_matches",
            return_value=([fake_match], ["serpapi"]),
        ):
            with patch("app.reverse_search.service.settings.serp_api_key", "test_key"):
                result = run_reverse_search(
                    image_id=image_id, image_bytes=sample_image_bytes
                )

        assert result.status == "completed"
        assert result.image_id == image_id

    @pytest.mark.unit
    def test_run_reverse_search_query_hash(self, sample_image_bytes):
        """Test that reverse search generates consistent query hashes."""
        image_id1 = uuid4()
        image_id2 = uuid4()

        # Different image IDs but same image bytes
        with patch("app.reverse_search.service.settings.serp_api_key", ""):
            result1 = run_reverse_search(
                image_id=image_id1, image_bytes=sample_image_bytes
            )
            result2 = run_reverse_search(
                image_id=image_id2, image_bytes=sample_image_bytes
            )

        # Should have same query_hash (based on image content)
        # Note: query_hash may be None only if image_bytes is empty/None at submission time
        assert hasattr(result1, "query_hash"), "result1 missing query_hash attribute"
        assert hasattr(result2, "query_hash"), "result2 missing query_hash attribute"
        assert result1.query_hash == result2.query_hash

    @pytest.mark.unit
    def test_run_reverse_search_without_api_key(self, sample_image_bytes):
        """Test reverse search fallback when API key is missing."""
        image_id = uuid4()

        with patch("app.reverse_search.service.settings.serp_api_key", ""):
            result = run_reverse_search(
                image_id=image_id, image_bytes=sample_image_bytes
            )

        # Should still return valid structure
        assert hasattr(result, "image_id")
        assert hasattr(result, "status")
        assert result.status in ["queued", "completed", "invalid_request"]

    @pytest.mark.unit
    def test_run_reverse_search_skips_for_local_bytes(self, sample_image_bytes, caplog):
        """Test reverse search skips SerpAPI for local image bytes and falls back."""
        image_id = uuid4()

        caplog.set_level(logging.INFO, logger="app.reverse_search.service")
        with patch("app.reverse_search.service.settings.serp_api_key", "test_key"):
            result = run_reverse_search(
                image_id=image_id, image_bytes=sample_image_bytes
            )

        # Should return result with fallback matches
        assert hasattr(result, "image_id")
        assert hasattr(result, "status")
        assert result.status == "completed"

        # Verify that the skip was logged
        assert len(caplog.records) > 0, "Expected log messages to be captured"
        assert any(
            "Skipping SerpAPI" in record.message for record in caplog.records
        ), "Expected info about skipping SerpAPI in logs"

    @pytest.mark.unit
    def test_reverse_search_returns_job_response(self, sample_image_bytes):
        """Test that reverse search returns job response structure."""
        image_id = uuid4()
        with patch("app.reverse_search.service.settings.serp_api_key", ""):
            result = run_reverse_search(
                image_id=image_id, image_bytes=sample_image_bytes
            )

        # Check for job response attributes
        assert hasattr(result, "job_id")
        assert hasattr(result, "image_id")
        assert hasattr(result, "status")

    @pytest.mark.unit
    def test_reverse_search_timestamp_format(self, sample_image_bytes):
        """Test that queued_at timestamp is properly formatted."""
        image_id = uuid4()
        with patch("app.reverse_search.service.settings.serp_api_key", ""):
            result = run_reverse_search(
                image_id=image_id, image_bytes=sample_image_bytes
            )

        queued_at = result.queued_at
        assert isinstance(queued_at, datetime)
        # Should have timezone info
        assert queued_at.tzinfo is not None

    @pytest.mark.unit
    def test_reverse_search_different_images(
        self, sample_image_bytes, sample_image_bytes_alt
    ):
        """Test that different image bytes produce different query hashes."""
        image_id1 = uuid4()
        image_id2 = uuid4()

        with patch("app.reverse_search.service.settings.serp_api_key", ""):
            result1 = run_reverse_search(
                image_id=image_id1, image_bytes=sample_image_bytes
            )
            result2 = run_reverse_search(
                image_id=image_id2, image_bytes=sample_image_bytes_alt
            )

        # Different image IDs should be preserved
        assert result1.image_id == image_id1
        assert result2.image_id == image_id2
        assert result1.image_id != result2.image_id

        # Different image bytes should produce different query hashes
        assert hasattr(result1, "query_hash"), "result1 missing query_hash attribute"
        assert hasattr(result2, "query_hash"), "result2 missing query_hash attribute"
        assert result1.query_hash != result2.query_hash
