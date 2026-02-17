"""
Private key wallet adapter.

This adapter uses a raw Ethereum private key for signing transactions.

Example:
    >>> wallet = PrivateKeyWallet(
    ...     private_key="0x1234...",
    ...     rpc_url="https://mainnet.base.org"
    ... )
    >>> print(wallet.get_address())
"""

from typing import Any, Dict, Optional, Union

from web3 import Web3
from eth_account import Account

from ..base import WalletAdapter
from ...core.types import TransactionRequest, TransactionResult


class PrivateKeyWallet(WalletAdapter):
    """
    Wallet implementation using a private key.

    This is the simplest wallet type - it uses a raw Ethereum
    private key for all signing operations.

    Attributes:
        account: eth_account Account instance
        w3: Web3 instance for RPC calls
        chain_id: Chain ID

    Example:
        >>> wallet = PrivateKeyWallet(
        ...     private_key="0x1234...",
        ...     rpc_url="https://mainnet.base.org",
        ...     chain_id=8453
        ... )
        >>> result = wallet.send_transaction({
        ...     "to": "0x...",
        ...     "value": 1000000000000000000
        ... })
    """

    def __init__(
        self,
        private_key: str,
        rpc_url: str,
        chain_id: Optional[int] = None,
    ):
        """
        Initialize wallet from private key.

        Args:
            private_key: Ethereum private key (with or without 0x prefix)
            rpc_url: RPC endpoint URL
            chain_id: Optional chain ID (auto-detected if not provided)
        """
        # Ensure 0x prefix
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key

        self.account = Account.from_key(private_key)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self._chain_id = chain_id

    def get_address(self) -> str:
        """Get wallet address."""
        return self.account.address

    def get_chain_id(self) -> int:
        """Get chain ID (auto-detect if not set)."""
        if self._chain_id is None:
            self._chain_id = self.w3.eth.chain_id
        return self._chain_id

    def get_balance(self) -> int:
        """Get native token balance in wei."""
        return self.w3.eth.get_balance(self.account.address)

    def get_nonce(self) -> int:
        """Get next nonce."""
        return self.w3.eth.get_transaction_count(self.account.address)

    def sign_transaction(self, tx: Union[Dict[str, Any], TransactionRequest]) -> bytes:
        """Sign a transaction."""
        tx_dict = self._prepare_tx(tx)
        signed = self.account.sign_transaction(tx_dict)
        return signed.rawTransaction

    def send_transaction(self, tx: Union[Dict[str, Any], TransactionRequest]) -> TransactionResult:
        """Sign and send a transaction."""
        raw_tx = self.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(raw_tx)

        # Wait for receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        return TransactionResult(
            success=receipt.status == 1,
            tx_hash=tx_hash.hex(),
            gas_used=receipt.gasUsed,
            block_number=receipt.blockNumber,
        )

    def call(self, tx: Union[Dict[str, Any], TransactionRequest]) -> bytes:
        """Make a read-only call."""
        tx_dict = self._to_dict(tx)
        tx_dict["from"] = self.account.address
        result = self.w3.eth.call(tx_dict)
        return bytes(result)

    def estimate_gas(self, tx: Union[Dict[str, Any], TransactionRequest]) -> int:
        """Estimate gas for a transaction."""
        tx_dict = self._to_dict(tx)
        tx_dict["from"] = self.account.address
        return self.w3.eth.estimate_gas(tx_dict)

    def _to_dict(self, tx: Union[Dict[str, Any], TransactionRequest]) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        if isinstance(tx, TransactionRequest):
            return tx.to_dict()
        return dict(tx)

    def _prepare_tx(self, tx: Union[Dict[str, Any], TransactionRequest]) -> Dict[str, Any]:
        """Prepare transaction for signing."""
        tx_dict = self._to_dict(tx)

        # Ensure required fields
        if "chainId" not in tx_dict:
            tx_dict["chainId"] = self.get_chain_id()

        if "nonce" not in tx_dict:
            tx_dict["nonce"] = self.get_nonce()

        if "from" not in tx_dict:
            tx_dict["from"] = self.account.address

        # Estimate gas if not provided
        if "gas" not in tx_dict:
            tx_dict["gas"] = self.estimate_gas(tx)

        # Set gas price if not using EIP-1559
        if "maxFeePerGas" not in tx_dict and "gasPrice" not in tx_dict:
            tx_dict["gasPrice"] = self.w3.eth.gas_price

        return tx_dict
