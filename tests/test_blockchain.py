"""Tests for the blockchain provenance anchoring module."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4

import pytest

from app.provenance.blockchain import BlockchainAnchorService, get_blockchain_anchor_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(
    rpc_url: str = "https://rpc-mumbai.maticvigil.com",
    private_key: str = "0x" + "a" * 64,
    network: str = "mumbai",
    contract_address: str = "0x" + "b" * 40,
    contract_abi: list | None = None,
) -> BlockchainAnchorService:
    """Create a BlockchainAnchorService with mocked Web3."""
    if contract_abi is None:
        contract_abi = []

    with (
        patch("app.provenance.blockchain._ABI_PATH") as mock_abi_path,
        patch("app.provenance.blockchain.Web3") as mock_web3_cls,
        patch("app.provenance.blockchain.Account") as mock_account_cls,
    ):
        mock_abi_path.read_text.return_value = json.dumps(contract_abi)
        mock_web3 = MagicMock()
        mock_web3_cls.return_value = mock_web3
        mock_web3_cls.to_checksum_address.return_value = contract_address
        mock_account = MagicMock()
        mock_account_cls.from_key.return_value = mock_account

        service = BlockchainAnchorService(
            rpc_url=rpc_url,
            private_key=private_key,
            network=network,
            contract_address=contract_address,
        )
        # Attach mocks for assertion in tests
        service._mock_web3 = mock_web3
        service._mock_account = mock_account

    return service


# ---------------------------------------------------------------------------
# BlockchainAnchorService unit tests
# ---------------------------------------------------------------------------

class TestBlockchainAnchorService:

    @pytest.mark.unit
    def test_get_explorer_url_mumbai(self):
        """Explorer URL uses mumbai.polygonscan.com for testnet."""
        service = _make_service(network="mumbai")
        tx = "0x" + "f" * 64
        url = service.get_explorer_url(tx)
        assert "mumbai.polygonscan.com" in url
        assert tx in url

    @pytest.mark.unit
    def test_get_explorer_url_mainnet(self):
        """Explorer URL uses polygonscan.com for mainnet."""
        service = _make_service(network="polygon")
        tx = "0x" + "f" * 64
        url = service.get_explorer_url(tx)
        assert "mumbai" not in url
        assert "polygonscan.com" in url
        assert tx in url

    @pytest.mark.unit
    def test_anchor_provenance_returns_tx_hash_on_success(self):
        """anchor_provenance returns a tx hash string on successful on-chain submission."""
        expected_tx = "0x" + "c" * 64

        service = _make_service()
        with patch.object(service, "_send_transaction", return_value=expected_tx):
            manifest = MagicMock()
            db = MagicMock()
            result = service.anchor_provenance(
                image_hash="a" * 64,
                chain_summary={"chain_id": str(uuid4()), "block_count": 2},
                manifest=manifest,
                db=db,
            )

        assert result == expected_tx
        assert manifest.blockchain_tx_hash == expected_tx
        assert manifest.blockchain_network == "mumbai"
        assert manifest.blockchain_anchored_at is not None
        db.flush.assert_called_once()

    @pytest.mark.unit
    def test_anchor_provenance_returns_none_on_failure(self):
        """anchor_provenance returns None and does not raise when transaction fails."""
        service = _make_service()
        with patch.object(service, "_send_transaction", side_effect=ConnectionError("RPC down")):
            manifest = MagicMock()
            db = MagicMock()
            result = service.anchor_provenance(
                image_hash="b" * 64,
                chain_summary={"chain_id": str(uuid4()), "block_count": 1},
                manifest=manifest,
                db=db,
            )

        assert result is None
        # Manifest should not have been updated
        assert not hasattr(manifest, "blockchain_tx_hash") or manifest.blockchain_tx_hash != "anything"

    @pytest.mark.unit
    def test_verify_on_chain_returns_records(self):
        """verify_on_chain returns records from the smart contract."""
        service = _make_service()

        metadata_json = json.dumps({"chain_id": str(uuid4()), "block_count": 2})
        service._contract.functions.getProvenanceCount.return_value.call.return_value = 1
        service._contract.functions.getProvenance.return_value.call.return_value = (
            metadata_json,
            1707000000,
            "0xRecorder",
            12345,
        )

        result = service.verify_on_chain("a" * 64)

        assert result["verified"] is True
        assert result["record_count"] == 1
        assert len(result["records"]) == 1
        assert result["records"][0]["block_number"] == 12345
        assert result["verification_method"] == "polygon_blockchain"

    @pytest.mark.unit
    def test_verify_on_chain_returns_unverified_on_error(self):
        """verify_on_chain returns verified=False if contract call raises."""
        service = _make_service()
        service._contract.functions.getProvenanceCount.return_value.call.side_effect = (
            RuntimeError("contract call failed")
        )

        result = service.verify_on_chain("c" * 64)

        assert result["verified"] is False
        assert result["record_count"] == 0
        assert "error" in result


# ---------------------------------------------------------------------------
# get_blockchain_anchor_service factory tests
# ---------------------------------------------------------------------------

class TestGetBlockchainAnchorService:

    @pytest.mark.unit
    def test_returns_none_when_anchoring_disabled(self):
        """Factory returns None when enable_blockchain_anchoring=False."""
        import app.provenance.blockchain as bm
        bm._instance = None  # reset singleton

        mock_settings = MagicMock()
        mock_settings.enable_blockchain_anchoring = False

        with patch("app.provenance.blockchain.settings", mock_settings):
            result = get_blockchain_anchor_service()

        assert result is None

    @pytest.mark.unit
    def test_returns_none_when_abi_missing(self):
        """Factory returns None when contract_abi.json has not been deployed yet."""
        import app.provenance.blockchain as bm
        bm._instance = None

        mock_settings = MagicMock()
        mock_settings.enable_blockchain_anchoring = True
        mock_settings.polygon_rpc_url = "https://rpc-mumbai.maticvigil.com"
        mock_settings.ethereum_private_key = "0x" + "a" * 64
        mock_settings.contract_address = "0x" + "b" * 40

        with (
            patch("app.provenance.blockchain.settings", mock_settings),
            patch("app.provenance.blockchain._ABI_PATH") as mock_path,
        ):
            mock_path.exists.return_value = False
            result = get_blockchain_anchor_service()

        assert result is None

    @pytest.mark.unit
    def test_returns_none_when_env_vars_missing(self):
        """Factory returns None when required env vars are empty strings."""
        import app.provenance.blockchain as bm
        bm._instance = None

        mock_settings = MagicMock()
        mock_settings.enable_blockchain_anchoring = True
        mock_settings.polygon_rpc_url = ""
        mock_settings.ethereum_private_key = ""
        mock_settings.contract_address = ""

        with (
            patch("app.provenance.blockchain.settings", mock_settings),
            patch("app.provenance.blockchain._ABI_PATH") as mock_path,
        ):
            mock_path.exists.return_value = True
            result = get_blockchain_anchor_service()

        assert result is None


# ---------------------------------------------------------------------------
# Integration: build_provenance with blockchain anchor
# ---------------------------------------------------------------------------

class TestBuildProvenanceBlockchainIntegration:

    @pytest.mark.unit
    def test_build_provenance_includes_blockchain_fields_in_response(self):
        """build_provenance response includes blockchain_tx_hash and url when anchoring succeeds."""
        from unittest.mock import MagicMock
        from app.provenance.service import build_provenance

        image_id = uuid4()
        db = MagicMock()

        # Set up db.query mock to return an existing manifest so blockchain anchoring is reached
        manifest_record = MagicMock()
        manifest_record.id = 1
        manifest_record.manifest_label = "test-manifest"
        manifest_record.signature_status = "valid"
        query = MagicMock()
        query.filter.return_value = query
        query.one_or_none.return_value = manifest_record
        query.order_by.return_value = query
        query.all.return_value = []
        db.query.return_value = query

        expected_tx = "0x" + "d" * 64

        mock_anchor = MagicMock()
        mock_anchor.anchor_provenance.return_value = expected_tx
        mock_anchor.get_explorer_url.return_value = f"https://mumbai.polygonscan.com/tx/{expected_tx}"

        with patch("app.provenance.service.get_blockchain_anchor_service", return_value=mock_anchor):
            result = build_provenance(
                image_id=image_id,
                image_hash="e" * 64,
                db=db,
            )

        assert result.blockchain_tx_hash == expected_tx
        assert result.blockchain_verification_url is not None
        assert "polygonscan.com" in result.blockchain_verification_url

    @pytest.mark.unit
    def test_build_provenance_succeeds_without_blockchain(self):
        """build_provenance returns normally when blockchain anchor service is None."""
        from app.provenance.service import build_provenance

        image_id = uuid4()
        db = MagicMock()

        query = MagicMock()
        query.filter.return_value = query
        query.one_or_none.return_value = None
        query.order_by.return_value = query
        query.all.return_value = []
        db.query.return_value = query

        with patch("app.provenance.service.get_blockchain_anchor_service", return_value=None):
            result = build_provenance(
                image_id=image_id,
                image_hash="f" * 64,
                db=db,
            )

        assert result.blockchain_tx_hash is None
        assert result.blockchain_verification_url is None
        assert len(result.blocks) >= 1

    @pytest.mark.unit
    def test_build_provenance_continues_when_anchor_raises(self):
        """build_provenance completes normally even if blockchain anchor raises an exception."""
        from app.provenance.service import build_provenance

        image_id = uuid4()
        db = MagicMock()

        query = MagicMock()
        query.filter.return_value = query
        query.one_or_none.return_value = None
        query.order_by.return_value = query
        query.all.return_value = []
        db.query.return_value = query

        mock_anchor = MagicMock()
        mock_anchor.anchor_provenance.side_effect = RuntimeError("network timeout")

        with patch("app.provenance.service.get_blockchain_anchor_service", return_value=mock_anchor):
            result = build_provenance(
                image_id=image_id,
                image_hash="0" * 64,
                db=db,
            )

        # Chain was still built successfully
        assert result.chain_id is not None
        assert len(result.blocks) >= 1
        assert result.blockchain_tx_hash is None
