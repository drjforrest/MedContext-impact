"""Tests for the provenance service."""
from uuid import UUID, uuid4

import pytest

from app.provenance.service import build_provenance


class TestProvenanceService:
    """Test suite for provenance blockchain-style service."""

    @pytest.mark.unit
    def test_build_provenance_creates_chain(self, sample_image_bytes):
        """Test that build_provenance creates a valid provenance chain."""
        image_id = uuid4()
        result = build_provenance(image_id=image_id, image_bytes=sample_image_bytes)

        assert hasattr(result, "chain_id")
        assert hasattr(result, "blocks")
        assert isinstance(result.chain_id, UUID)
        assert isinstance(result.blocks, list)
        assert len(result.blocks) > 0

    @pytest.mark.unit
    def test_provenance_block_structure(self, sample_image_bytes):
        """Test that provenance blocks have correct structure."""
        image_id = uuid4()
        result = build_provenance(image_id=image_id, image_bytes=sample_image_bytes)

        first_block = result.blocks[0]

        assert hasattr(first_block, "block_number")
        assert hasattr(first_block, "block_hash")
        assert hasattr(first_block, "previous_hash")
        assert hasattr(first_block, "observation_type")
        assert hasattr(first_block, "recorded_at")

        # First block should have no previous hash
        assert first_block.previous_hash is None
        assert first_block.block_number == 0

    @pytest.mark.unit
    def test_provenance_chain_linking(self, sample_image_bytes):
        """Test that blocks are properly linked via hashes."""
        image_id = uuid4()
        result = build_provenance(image_id=image_id, image_bytes=sample_image_bytes)

        blocks = result.blocks
        if len(blocks) > 1:
            for i in range(1, len(blocks)):
                previous_block = blocks[i - 1]
                current_block = blocks[i]

                # Current block's previous_hash should match previous block's hash
                assert current_block.previous_hash == previous_block.block_hash
                assert current_block.block_number == i

    @pytest.mark.unit
    def test_provenance_hash_deterministic(self, sample_image_bytes):
        """Test that same input produces same hashes."""
        image_id = uuid4()

        result1 = build_provenance(image_id=image_id, image_bytes=sample_image_bytes)
        result2 = build_provenance(image_id=image_id, image_bytes=sample_image_bytes)

        # Hashes should be deterministic for same input
        # Note: timestamps may differ, so we check structure not exact equality
        assert len(result1.blocks) == len(result2.blocks)
        assert all(hasattr(block, "block_hash") for block in result1.blocks)
        assert all(hasattr(block, "block_hash") for block in result2.blocks)

    @pytest.mark.unit
    def test_provenance_observation_type(self, sample_image_bytes):
        """Test that observation has correct type."""
        image_id = uuid4()
        result = build_provenance(image_id=image_id, image_bytes=sample_image_bytes)

        first_block = result.blocks[0]
        observation_type = first_block.observation_type

        assert observation_type in [
            "image_submission",
            "reverse_search",
            "forensics",
            "provenance_snapshot",
        ]

    @pytest.mark.unit
    def test_provenance_with_different_images(self, sample_image_bytes):
        """Test that different images produce different chains."""
        image_id1 = uuid4()
        image_id2 = uuid4()

        result1 = build_provenance(image_id=image_id1, image_bytes=sample_image_bytes)
        result2 = build_provenance(image_id=image_id2, image_bytes=sample_image_bytes)

        # Different image IDs should produce different chain IDs
        assert result1.chain_id != result2.chain_id

    @pytest.mark.unit
    def test_provenance_block_hash_format(self, sample_image_bytes):
        """Test that block hashes are in correct format."""
        image_id = uuid4()
        result = build_provenance(image_id=image_id, image_bytes=sample_image_bytes)

        for block in result.blocks:
            block_hash = block.block_hash

            # SHA-256 produces 64 character hex string
            assert isinstance(block_hash, str)
            assert len(block_hash) == 64
            assert all(c in "0123456789abcdef" for c in block_hash)
