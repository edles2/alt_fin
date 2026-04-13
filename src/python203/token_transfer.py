import json
import logging
import os

from web3 import Web3

logger = logging.getLogger(__name__)

_CONTRACT_ADDRESS = "0xA0f0a2D53b3476c50F2Cf24307F8a1Cd3c758254"

_CONTRACT_ABI = json.loads("""
[
    {
        "inputs": [{"internalType": "address", "name": "initialOwner", "type": "address"}],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to",     "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
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


class TokenTransfer:
    """Sends ERC-20 reward tokens on the Ethereum Sepolia testnet.

    Credentials are read from the environment — never hardcoded.
    Set ``INFURA_PROJECT_ID`` before instantiating this class::

        export INFURA_PROJECT_ID=your_key
        export PRIVATE_KEY=your_wallet_private_key

    Example::

        tt = TokenTransfer(
            private_key=os.environ["PRIVATE_KEY"],
            sender_address="0xYourAddress",
        )
        tx_hash = tt.transfer_tokens_from_rating("0xRecipient", score)
    """

    def __init__(self, private_key: str, sender_address: str):
        infura_id = os.environ.get("INFURA_PROJECT_ID")
        if not infura_id:
            raise EnvironmentError(
                "INFURA_PROJECT_ID is not set. "
                "Copy .env.example to .env and fill in your Infura key."
            )

        self._web3 = Web3(Web3.HTTPProvider(f"https://sepolia.infura.io/v3/{infura_id}"))
        if not self._web3.is_connected():
            raise ConnectionError("Failed to connect to the Sepolia testnet via Infura.")
        logger.info("Connected to Sepolia testnet.")

        self._private_key = private_key
        self._sender = self._web3.to_checksum_address(sender_address)
        self._contract = self._web3.eth.contract(
            address=self._web3.to_checksum_address(_CONTRACT_ADDRESS),
            abi=_CONTRACT_ABI,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_balance(self, address: str) -> float:
        """Return the token balance of *address* in human-readable units."""
        raw = self._contract.functions.balanceOf(
            self._web3.to_checksum_address(address)
        ).call()
        return float(self._web3.from_wei(raw, "ether"))

    def transfer_tokens_from_rating(self, recipient: str, rating: float) -> str:
        """Transfer *rating* tokens to *recipient* as a backtest reward.

        Args:
            recipient: Ethereum address of the reward recipient.
            rating:    Score from ``BacktestRating.rate_backtest()`` (0–10).

        Returns:
            Transaction hash as a hex string.
        """
        recipient = self._web3.to_checksum_address(recipient)
        amount = self._web3.to_wei(rating, "ether")

        logger.info("Sender balance before:    %.4f tokens", self.get_balance(self._sender))
        logger.info("Recipient balance before: %.4f tokens", self.get_balance(recipient))

        tx = self._contract.functions.transfer(recipient, amount).build_transaction({
            "from": self._sender,
            "gas": 200_000,
            "gasPrice": self._web3.to_wei("50", "gwei"),
            "nonce": self._web3.eth.get_transaction_count(self._sender),
        })
        signed = self._web3.eth.account.sign_transaction(tx, private_key=self._private_key)
        tx_hash = self._web3.eth.send_raw_transaction(signed.raw_transaction)

        logger.info("Transaction sent: %s", self._web3.to_hex(tx_hash))
        self._web3.eth.wait_for_transaction_receipt(tx_hash)

        logger.info("Sender balance after:    %.4f tokens", self.get_balance(self._sender))
        logger.info("Recipient balance after: %.4f tokens", self.get_balance(recipient))

        return self._web3.to_hex(tx_hash)
