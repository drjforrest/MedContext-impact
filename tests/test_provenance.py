"""Tests for the provenance service."""

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.provenance.service import build_provenance


def _mock_query(
    db: MagicMock, one_or_none_return_value=None, all_return_value=None
) -> None:
    query = MagicMock()
    query.filter.return_value = query
    query.one_or_none.return_value = one_or_none_return_value
    query.order_by.return_value = query
    query.all.return_value = [] if all_return_value is None else all_return_value
    db.query.return_value = query


class TestProvenanceService:
    """Test suite for provenance repository service."""

    @pytest.mark.unit
    def test_build_provenance_creates_chain(self):
        """Test that build_provenance creates a valid provenance chain."""
        image_id = uuid4()
        db = MagicMock()
        _mock_query(db)

        result = build_provenance(
            image_id=image_id,
            image_hash="a" * 64,
            db=db,
        )

        assert hasattr(result, "chain_id")
        assert hasattr(result, "blocks")
        assert isinstance(result.chain_id, UUID)
        assert isinstance(result.blocks, list)
        assert len(result.blocks) == 1

    @pytest.mark.unit
    def test_provenance_block_structure(self):
        """Test that provenance blocks have correct structure."""
        image_id = uuid4()
        db = MagicMock()
        _mock_query(db)

        result = build_provenance(
            image_id=image_id,
            image_hash="b" * 64,
            db=db,
        )

        first_block = result.blocks[0]

        assert hasattr(first_block, "block_number")
        assert hasattr(first_block, "block_hash")
        assert hasattr(first_block, "previous_hash")
        assert hasattr(first_block, "observation_type")
        assert hasattr(first_block, "recorded_at")

        assert first_block.previous_hash is None
        assert first_block.block_number == 0
        assert first_block.observation_type == "image_submission"

    @pytest.mark.unit
    def test_provenance_chain_linking(self):
        """Test that blocks are properly linked via hashes."""
        image_id = uuid4()
        db = MagicMock()
        manifest_record = MagicMock()
        manifest_record.id = 1
        manifest_record.manifest_label = "test-manifest"
        manifest_record.signature_status = "valid"
        _mock_query(db, one_or_none_return_value=manifest_record)

        result = build_provenance(
            image_id=image_id,
            image_hash="c" * 64,
            db=db,
        )

        blocks = result.blocks
        assert len(blocks) == 2
        assert blocks[0].previous_hash is None
        for index in range(1, len(blocks)):
            assert blocks[index].previous_hash == blocks[index - 1].block_hash

    @pytest.mark.unit
    def test_provenance_block_hash_format(self):
        """Test that block hashes are in correct format."""
        image_id = uuid4()
        db = MagicMock()
        _mock_query(db)

        result = build_provenance(
            image_id=image_id,
            image_hash="d" * 64,
            db=db,
        )

        for block in result.blocks:
            block_hash = block.block_hash
            assert isinstance(block_hash, str)
            assert len(block_hash) == 64
            assert all(c in "0123456789abcdef" for c in block_hash)
