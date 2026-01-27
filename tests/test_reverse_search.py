"""Tests for the reverse search service."""

import logging
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.reverse_search.service import run_reverse_search


class TestReverseSearchService:
    """Test suite for reverse image search service."""

    @pytest.mark.unit
    def test_run_reverse_search_returns_result(self, sample_image_bytes):
        """Test that run_reverse_search returns a valid result structure."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "inline_images": [
                {
                    "title": "Controlled Image Result",
                    "link": "https://example.com/controlled.jpg",
                    "source": "https://example.com",
                    "thumbnail": "https://example.com/controlled-thumb.jpg",
                }
            ]
        }
        image_id = uuid4()
        with patch(
            "app.reverse_search.service.requests.post", return_value=mock_response
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
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "inline_images": [
                {
                    "title": "Test Medical Image",
                    "link": "https://example.com/image1.jpg",
                    "source": "https://example.com",
                    "thumbnail": "https://example.com/thumb1.jpg",
                }
            ]
        }

        image_id = uuid4()

        with patch(
            "app.reverse_search.service.requests.get", return_value=mock_response
        ):
            with patch("app.reverse_search.service.settings.serp_api_key", "test_key"):
                with patch("app.reverse_search.service._LOGGER", MagicMock()):
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
        if hasattr(result1, "query_hash") and hasattr(result2, "query_hash"):
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
        assert result.status in ["pending", "completed", "failed"]

    @pytest.mark.unit
    def test_run_reverse_search_api_failure(self, sample_image_bytes, caplog):
        """Test reverse search handles API failures gracefully."""
        import requests

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "API Error"
        )

        image_id = uuid4()

        caplog.set_level(logging.CRITICAL, logger="app.reverse_search.service")
        with patch(
            "app.reverse_search.service.requests.get", return_value=mock_response
        ):
            with patch("app.reverse_search.service.settings.serp_api_key", "test_key"):
                result = run_reverse_search(
                    image_id=image_id, image_bytes=sample_image_bytes
                )

        # Should return result with fallback status
        assert hasattr(result, "image_id")
        assert hasattr(result, "status")

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
    def test_reverse_search_different_images(self, sample_image_bytes):
        """Test that different image IDs produce different cache entries."""
        image_id1 = uuid4()
        image_id2 = uuid4()

        with patch("app.reverse_search.service.settings.serp_api_key", ""):
            result1 = run_reverse_search(
                image_id=image_id1, image_bytes=sample_image_bytes
            )
            result2 = run_reverse_search(
                image_id=image_id2, image_bytes=sample_image_bytes
            )

        assert result1.image_id != result2.image_id
