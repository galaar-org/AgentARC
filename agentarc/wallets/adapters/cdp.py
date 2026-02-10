"""
Coinbase Developer Platform (CDP) wallet adapter.

This adapter wraps the CDP wallet provider from AgentKit
to work with the WalletAdapter interface.

Example:
    >>> from coinbase_agentkit import CdpEvmWalletProvider
    >>> cdp_provider = CdpEvmWalletProvider(config)
    >>> wallet = CdpWalletAdapter(cdp_provider)
"""

from typing import Any, Dict, Optional, Union

from ..base import WalletAdapter
from ...core.types import TransactionRequest, TransactionResult


class CdpWalletAdapter(WalletAdapter):
    """
    Wallet adapter for Coinbase Developer Platform providers.

    This wraps the CDP wallet provider from AgentKit to implement
    the WalletAdapter interface for use with PolicyWallet.

    Attributes:
        provider: CDP wallet provider instance

    Example:
        >>> from coinbase_agentkit import CdpEvmWalletProvider
        >>> cdp_provider = CdpEvmWalletProvider(config)
        >>> wallet = CdpWalletAdapter(cdp_provider)
    """

    def __init__(self, provider: Any):
        """
        Initialize CDP wallet adapter.

        Args:
            provider: CDP wallet provider instance (CdpEvmWalletProvider)
        """
        self.provider = provider

    def get_address(self) -> str:
        """Get wallet address."""
        return self.provider.get_address()

    def get_chain_id(self) -> int:
        """Get chain ID."""
        # CDP provider uses network_id, map to chain_id
        network_id = self.provider.get_network().network_id
        return self._network_to_chain_id(network_id)

    def get_balance(self) -> int:
        """Get native token balance in wei."""
        # CDP provider returns balance via Web3
        if hasattr(self.provider, "web3"):
            return self.provider.web3.eth.get_balance(self.get_address())
        return 0

    def get_nonce(self) -> int:
        """Get next nonce."""
        if hasattr(self.provider, "web3"):
            return self.provider.web3.eth.get_transaction_count(self.get_address())
        return 0

    def sign_transaction(self, tx: Union[Dict[str, Any], TransactionRequest]) -> bytes:
        """Sign a transaction."""
        tx_dict = self._to_dict(tx)
        # CDP provider handles signing internally
        # Return signed transaction bytes
        if hasattr(self.provider, "sign_transaction"):
            return self.provider.sign_transaction(tx_dict)
        raise NotImplementedError("CDP provider does not support sign_transaction")

    def send_transaction(self, tx: Union[Dict[str, Any], TransactionRequest]) -> TransactionResult:
        """Send a transaction via CDP provider."""
        tx_dict = self._to_dict(tx)

        # CDP provider sends transaction and returns result
        if hasattr(self.provider, "send_transaction"):
            result = self.provider.send_transaction(tx_dict)
            return TransactionResult(
                success=True,
                tx_hash=result if isinstance(result, str) else str(result),
            )

        # Fallback: use web3 directly
        if hasattr(self.provider, "web3"):
            tx_hash = self.provider.web3.eth.send_transaction(tx_dict)
            receipt = self.provider.web3.eth.wait_for_transaction_receipt(tx_hash)
            return TransactionResult(
                success=receipt.status == 1,
                tx_hash=tx_hash.hex(),
                gas_used=receipt.gasUsed,
                block_number=receipt.blockNumber,
            )

        raise NotImplementedError("CDP provider does not support send_transaction")

    def call(self, tx: Union[Dict[str, Any], TransactionRequest]) -> bytes:
        """Make a read-only call."""
        tx_dict = self._to_dict(tx)
        tx_dict["from"] = self.get_address()

        if hasattr(self.provider, "web3"):
            result = self.provider.web3.eth.call(tx_dict)
            return bytes(result)

        raise NotImplementedError("CDP provider does not support call")

    def estimate_gas(self, tx: Union[Dict[str, Any], TransactionRequest]) -> int:
        """Estimate gas for a transaction."""
        tx_dict = self._to_dict(tx)
        tx_dict["from"] = self.get_address()

        if hasattr(self.provider, "web3"):
            return self.provider.web3.eth.estimate_gas(tx_dict)

        return 21000

    def get_network(self) -> str:
        """Get network name."""
        if hasattr(self.provider, "get_network"):
            network = self.provider.get_network()
            return network.network_id if hasattr(network, "network_id") else str(network)
        return str(self.get_chain_id())

    def _to_dict(self, tx: Union[Dict[str, Any], TransactionRequest]) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        if isinstance(tx, TransactionRequest):
            return tx.to_dict()
        return dict(tx)

    def _network_to_chain_id(self, network_id: str) -> int:
        """Map network ID to chain ID."""
        network_map = {
            "base-mainnet": 8453,
            "base-sepolia": 84532,
            "ethereum-mainnet": 1,
            "ethereum-sepolia": 11155111,
            "arbitrum-mainnet": 42161,
            "optimism-mainnet": 10,
            "polygon-mainnet": 137,
        }
        return network_map.get(network_id, 1)

    # CDP-specific methods (passthrough)

    def native_transfer(self, to: str, amount: str) -> str:
        """Transfer native tokens (CDP-specific)."""
        if hasattr(self.provider, "native_transfer"):
            return self.provider.native_transfer(to, amount)
        raise NotImplementedError("native_transfer not available")

    def read_contract(self, address: str, abi: list, method: str, args: list = None) -> Any:
        """Read from a contract (CDP-specific)."""
        if hasattr(self.provider, "read_contract"):
            return self.provider.read_contract(address, abi, method, args or [])
        raise NotImplementedError("read_contract not available")

    def sign_message(self, message: str) -> str:
        """Sign a message (CDP-specific)."""
        if hasattr(self.provider, "sign_message"):
            return self.provider.sign_message(message)
        raise NotImplementedError("sign_message not available")
