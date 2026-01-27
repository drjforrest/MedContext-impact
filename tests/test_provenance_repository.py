from uuid import uuid4

from unittest.mock import MagicMock

from app.provenance.service import build_provenance, store_provenance_manifest


def _mock_query(db: MagicMock, return_value=None) -> None:
    query = MagicMock()
    query.filter.return_value = query
    query.one_or_none.return_value = return_value
    db.query.return_value = query


def test_store_provenance_manifest_sets_label() -> None:
    db = MagicMock()
    _mock_query(db)

    record = store_provenance_manifest(
        db,
        image_hash="a" * 64,
        manifest_json={"active_manifest": "manifest-1"},
    )

    assert record.image_hash == "a" * 64
    assert record.manifest_label == "manifest-1"
    db.add.assert_called_once()


def test_build_provenance_without_manifest() -> None:
    db = MagicMock()
    _mock_query(db)

    result = build_provenance(
        image_id=uuid4(),
        image_hash="b" * 64,
        db=db,
    )

    assert result.status == "not_found"
    assert len(result.blocks) == 1
    assert result.blocks[0].observation_type == "image_submission"
