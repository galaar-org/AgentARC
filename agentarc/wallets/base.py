"""
Abstract base class for wallet adapters.

All wallet implementations must inherit from WalletAdapter
and implement the required methods.

Example:
    >>> class MyWalletAdapter(WalletAdapter):
    ...     def get_address(self) -> str:
    ...         return self._address
    ...
    ...     def send_transaction(self, tx):
    ...         return self._send(tx)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

from ..core.types import TransactionRequest, TransactionResult


class WalletAdapter(ABC):
    """
    Abstract base class for all wallet implementations.

    This provides a universal interface for interacting with
    different wallet types (private key, mnemonic, CDP, WalletConnect, etc.).

    Subclasses must implement:
        - get_address(): Get wallet address
        - get_chain_id(): Get current chain ID
        - get_balance(): Get native token balance
        - sign_transaction(): Sign a transaction
        - send_transaction(): Send a transaction
        - call(): Make a read-only call

    Example:
        >>> class PrivateKeyWallet(WalletAdapter):
        ...     def __init__(self, private_key, rpc_url):
        ...         self.account = Account.from_key(private_key)
        ...         self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        ...
        ...     def get_address(self) -> str:
        ...         return self.account.address
    """

    @abstractmethod
    def get_address(self) -> str:
        """
        Get the wallet's address.

        Returns:
            Ethereum address as checksummed string
        """
        raise NotImplementedError

    @abstractmethod
    def get_chain_id(self) -> int:
        """
        Get the current chain ID.

        Returns:
            Chain ID as integer (e.g., 1 for mainnet, 8453 for Base)
        """
        raise NotImplementedError

    @abstractmethod
    def get_balance(self) -> int:
        """
        Get native token balance in wei.

        Returns:
            Balance in wei as integer
        """
        raise NotImplementedError

    @abstractmethod
    def sign_transaction(self, tx: Union[Dict[str, Any], TransactionRequest]) -> bytes:
        """
        Sign a transaction without sending it.

        Args:
            tx: Transaction dictionary or TransactionRequest

        Returns:
            Signed transaction as raw bytes
        """
        raise NotImplementedError

    @abstractmethod
    def send_transaction(self, tx: Union[Dict[str, Any], TransactionRequest]) -> TransactionResult:
        """
        Sign and send a transaction.

        Args:
            tx: Transaction dictionary or TransactionRequest

        Returns:
            TransactionResult with success status and tx hash
        """
        raise NotImplementedError

    @abstractmethod
    def call(self, tx: Union[Dict[str, Any], TransactionRequest]) -> bytes:
        """
        Make a read-only call (eth_call).

        Args:
            tx: Transaction dictionary or TransactionRequest

        Returns:
            Return data as bytes
        """
        raise NotImplementedError

    def estimate_gas(self, tx: Union[Dict[str, Any], TransactionRequest]) -> int:
        """
        Estimate gas for a transaction.

        Args:
            tx: Transaction dictionary or TransactionRequest

        Returns:
            Estimated gas as integer

        Note:
            Default implementation returns 21000. Override for accurate estimates.
        """
        return 21000

    def get_nonce(self) -> int:
        """
        Get the next nonce for the wallet.

        Returns:
            Next nonce as integer

        Note:
            Default implementation returns 0. Override for accurate nonces.
        """
        return 0

    def get_network(self) -> str:
        """
        Get the network name.

        Returns:
            Network name (e.g., "mainnet", "base-sepolia")

        Note:
            Default implementation returns chain ID as string.
        """
        return str(self.get_chain_id())

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert wallet info to dictionary.

        Returns:
            Dictionary with wallet info
        """
        return {
            "address": self.get_address(),
            "chain_id": self.get_chain_id(),
            "network": self.get_network(),
        }
