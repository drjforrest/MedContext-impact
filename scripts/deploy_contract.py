"""
Deploy MedicalImageProvenance smart contract to Polygon network.

Usage:
    POLYGON_RPC_URL=https://rpc-mumbai.maticvigil.com \
    ETHEREUM_PRIVATE_KEY=0x... \
    python scripts/deploy_contract.py

Outputs:
    - Prints contract address and transaction hash
    - Writes ABI to src/app/provenance/contract_abi.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from eth_account import Account
from solcx import compile_source, install_solc
from web3 import Web3

# Paths
REPO_ROOT = Path(__file__).parent.parent
CONTRACT_PATH = REPO_ROOT / "contracts" / "MedicalProvenance.sol"
ABI_OUTPUT_PATH = REPO_ROOT / "src" / "app" / "provenance" / "contract_abi.json"


def main() -> None:
    rpc_url = os.environ.get("POLYGON_RPC_URL", "")
    private_key = os.environ.get("ETHEREUM_PRIVATE_KEY", "")
    network = os.environ.get("POLYGON_NETWORK", "mumbai")

    if not rpc_url or not private_key:
        print(
            "Error: POLYGON_RPC_URL and ETHEREUM_PRIVATE_KEY environment variables required.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Install Solidity compiler
    print("Installing Solidity compiler...")
    install_solc("0.8.20")

    # Read contract source
    contract_source = CONTRACT_PATH.read_text()

    # Compile
    print("Compiling contract...")
    compiled = compile_source(contract_source, output_values=["abi", "bin"])
    contract_interface = compiled["<stdin>:MedicalImageProvenance"]

    # Connect to Polygon
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"Error: Cannot connect to {rpc_url}", file=sys.stderr)
        sys.exit(1)

    account = Account.from_key(private_key)
    print(f"Deploying from address: {account.address}")
    print(f"Network: {network}")

    balance = w3.eth.get_balance(account.address)
    print(f"Balance: {w3.from_wei(balance, 'ether')} MATIC")
    if balance == 0:
        print(
            "Warning: wallet has zero balance. Fund from https://faucet.polygon.technology/",
            file=sys.stderr,
        )

    # Deploy
    print("Deploying contract...")
    Contract = w3.eth.contract(
        abi=contract_interface["abi"],
        bytecode=contract_interface["bin"],
    )

    tx = Contract.constructor().build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 2000000,
            "gasPrice": w3.eth.gas_price,
        }
    )

    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(f"Transaction sent: {tx_hash.hex()}")
    print("Waiting for confirmation...")

    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if tx_receipt["status"] != 1:
        print("Error: Contract deployment transaction failed.", file=sys.stderr)
        sys.exit(1)

    contract_address = tx_receipt["contractAddress"]

    if network == "mumbai":
        explorer_url = f"https://mumbai.polygonscan.com/address/{contract_address}"
    else:
        explorer_url = f"https://polygonscan.com/address/{contract_address}"

    print(f"\n✓ Contract deployed successfully!")
    print(f"  Address: {contract_address}")
    print(f"  Tx hash: {tx_hash.hex()}")
    print(f"  Explorer: {explorer_url}")

    # Write ABI to app location for runtime use
    ABI_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ABI_OUTPUT_PATH.write_text(json.dumps(contract_interface["abi"], indent=2))
    print(f"\n✓ ABI written to {ABI_OUTPUT_PATH}")

    print(f"\nAdd to .env:")
    print(f"  CONTRACT_ADDRESS={contract_address}")
    print(f"  ENABLE_BLOCKCHAIN_ANCHORING=true")


if __name__ == "__main__":
    main()
