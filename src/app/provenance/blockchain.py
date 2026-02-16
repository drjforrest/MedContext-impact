"""
Polygon blockchain anchoring for provenance chains.

Records a condensed provenance summary on-chain after the local C2PA + hash-chain
is built. The blockchain anchor provides an immutable, independently verifiable
timestamp for each provenance chain.

Requires:
    ENABLE_BLOCKCHAIN_ANCHORING=true
    POLYGON_RPC_URL, ETHEREUM_PRIVATE_KEY, POLYGON_NETWORK, CONTRACT_ADDRESS
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# Path to ABI file committed to the repo after contract deployment
_ABI_PATH = Path(__file__).parent / "contract_abi.json"


class BlockchainAnchorService:
    """
    Records provenance summaries on the Polygon blockchain.

    Each call to anchor_provenance() submits a transaction to the
    MedicalImageProvenance smart contract and stores the resulting
    tx_hash on the ProvenanceManifest database record.
    """

    def __init__(
        self, rpc_url: str, private_key: str, network: str, contract_address: str
    ) -> None:
        from eth_account import Account
        from web3 import Web3

        self._w3 = Web3(Web3.HTTPProvider(rpc_url))
        self._account = Account.from_key(private_key)
        self._network = network
        self._contract_address = contract_address

        abi = json.loads(_ABI_PATH.read_text())
        self._contract = self._w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=abi,
        )

        logger.info(
            "BlockchainAnchorService connected — network=%s contract=%s wallet=%s",
            network,
            contract_address,
            self._account.address,
        )

    def anchor_provenance(
        self,
        image_hash: str,
        chain_summary: dict[str, Any],
        manifest: Any,
        db: Session,
    ) -> str | None:
        """
        Record a provenance chain summary on-chain and persist tx_hash to the manifest.

        Args:
            image_hash: SHA256 hex digest of the image bytes.
            chain_summary: Condensed dict describing the chain (chain_id, block_count, etc.)
            manifest: ProvenanceManifest ORM instance to update with tx_hash.
            db: Active SQLAlchemy session (caller is responsible for commit).

        Returns:
            Transaction hash hex string, or None if anchoring failed.
        """
        metadata: dict[str, Any] = {
            **chain_summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            tx_hash = self._send_transaction(image_hash, json.dumps(metadata))
            manifest.blockchain_tx_hash = tx_hash
            manifest.blockchain_network = self._network
            manifest.blockchain_anchored_at = datetime.now(timezone.utc)
            db.flush()
            logger.info(
                "Blockchain anchor recorded tx=%s image_hash=%s", tx_hash, image_hash
            )
            return tx_hash
        except Exception as exc:
            logger.warning(
                "Blockchain anchor failed for image_hash=%s: %s", image_hash, exc
            )
            return None

    def verify_on_chain(self, image_hash: str) -> dict[str, Any]:
        """
        Query the smart contract for all provenance records for this image hash.

        Returns:
            dict with verified, record_count, records, and verification_method.
        """
        try:
            count: int = self._contract.functions.getProvenanceCount(image_hash).call()
            records = []
            for i in range(count):
                raw = self._contract.functions.getProvenance(image_hash, i).call()
                records.append(
                    {
                        "metadata": json.loads(raw[0]),
                        "timestamp": raw[1],
                        "recorder": raw[2],
                        "block_number": raw[3],
                    }
                )
            return {
                "image_hash": image_hash,
                "verified": True,
                "record_count": count,
                "records": records,
                "verification_method": "polygon_blockchain",
            }
        except Exception as exc:
            logger.warning(
                "On-chain verification failed for image_hash=%s: %s", image_hash, exc
            )
            return {
                "image_hash": image_hash,
                "verified": False,
                "record_count": 0,
                "records": [],
                "verification_method": "polygon_blockchain",
                "error": str(exc),
            }

    def get_explorer_url(self, tx_hash: str) -> str:
        """Return explorer URL for a transaction hash."""
        net = self._network.lower()
        if net in ("local", "hardhat", "anvil"):
            return f"local://{net}/tx/{tx_hash}"

        if net in ("mumbai", "polygon-mumbai"):
            base = "https://mumbai.polygonscan.com"
        elif net in ("amoy", "polygon-amoy"):
            base = "https://www.oklink.com/amoy"
        elif net in ("polygon", "mainnet"):
            base = "https://polygonscan.com"
        elif net == "ethereum":
            base = "https://etherscan.io"
        else:
            # Default to Polygon mainnet if unknown network
            base = "https://polygonscan.com"
        return f"{base}/tx/{tx_hash}"

    def _send_transaction(self, image_hash: str, metadata: str) -> str:
        """Submit recordProvenance to the smart contract and return the tx hash."""
        tx = self._contract.functions.recordProvenance(
            image_hash,
            metadata,
        ).build_transaction(
            {
                "from": self._account.address,
                "nonce": self._w3.eth.get_transaction_count(self._account.address),
                "gas": 200000,
                "gasPrice": self._w3.eth.gas_price,
            }
        )
        signed = self._account.sign_transaction(tx)
        tx_hash_bytes = self._w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=30)
        if receipt["status"] != 1:
            raise RuntimeError("Blockchain transaction reverted on-chain")
        return tx_hash_bytes.hex()


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_instance: BlockchainAnchorService | None = None


def get_blockchain_anchor_service() -> BlockchainAnchorService | None:
    """
    Return a singleton BlockchainAnchorService, or None if anchoring is disabled
    or configuration is incomplete.
    """
    global _instance
    if _instance is not None:
        return _instance

    if not settings.enable_blockchain_anchoring:
        return None

    if not _ABI_PATH.exists():
        logger.warning(
            "Blockchain anchoring enabled but contract ABI not found at %s. "
            "Run scripts/deploy_contract.py first.",
            _ABI_PATH,
        )
        return None

    missing = [
        name
        for name, val in [
            ("POLYGON_RPC_URL", settings.polygon_rpc_url),
            ("ETHEREUM_PRIVATE_KEY", settings.ethereum_private_key),
            ("CONTRACT_ADDRESS", settings.contract_address),
        ]
        if not val
    ]
    if missing:
        logger.warning(
            "Blockchain anchoring enabled but missing env vars: %s",
            ", ".join(missing),
        )
        return None

    try:
        _instance = BlockchainAnchorService(
            rpc_url=settings.polygon_rpc_url,
            private_key=settings.ethereum_private_key,
            network=settings.polygon_network,
            contract_address=settings.contract_address,
        )
    except Exception as exc:
        logger.error("Failed to initialize BlockchainAnchorService: %s", exc)
        return None

    return _instance
