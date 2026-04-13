"""Inspect the Master203token (203T) deployed on the Sepolia testnet.

Usage:
    export INFURA_PROJECT_ID=your_key
    python scripts/track_token.py [wallet_address]

If no address is provided, the deployer's balance is shown.
"""

import json
import logging
import os
import sys

from web3 import Web3

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CONTRACT_ADDRESS  = "0xA0f0a2D53b3476c50F2Cf24307F8a1Cd3c758254"
DEPLOYER_ADDRESS  = "0x0390cF896B4a7D984017e6C9D3d17b5A6287a874"

CONTRACT_ABI = json.loads("""
[
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]
""")


def main() -> None:
    infura_id = os.environ.get("INFURA_PROJECT_ID")
    if not infura_id:
        logger.error("INFURA_PROJECT_ID is not set. Copy .env.example to .env.")
        sys.exit(1)

    web3 = Web3(Web3.HTTPProvider(f"https://sepolia.infura.io/v3/{infura_id}"))
    if not web3.is_connected():
        logger.error("Could not connect to the Sepolia testnet.")
        sys.exit(1)

    logger.info("Connected — current block: %d", web3.eth.block_number)

    contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
    address  = sys.argv[1] if len(sys.argv) > 1 else DEPLOYER_ADDRESS

    name         = contract.functions.name().call()
    symbol       = contract.functions.symbol().call()
    total_supply = web3.from_wei(contract.functions.totalSupply().call(), "ether")
    balance      = web3.from_wei(contract.functions.balanceOf(address).call(), "ether")

    logger.info("Contract:     %s", CONTRACT_ADDRESS)
    logger.info("Token:        %s (%s)", name, symbol)
    logger.info("Total supply: %s %s", total_supply, symbol)
    logger.info("Balance of %s: %s %s", address, balance, symbol)


if __name__ == "__main__":
    main()
