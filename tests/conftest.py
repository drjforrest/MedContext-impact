"""Shared test fixtures and configuration."""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Provide sample image bytes for testing."""
    # Simple 1x1 red PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


@pytest.fixture
def sample_image_bytes_alt() -> bytes:
    """Provide alternative sample image bytes for testing (different content)."""
    # Simple 1x1 blue PNG (different pixel data from sample_image_bytes)
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\x00\x00\xff\x00\x00\x00\x03\x00\x01"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
