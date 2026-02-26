"""
Abstract base class for smart wallet adapters.

Smart wallets (ERC-4337, Safe) extend the base WalletAdapter
with additional concepts like owner addresses and deployment status.

Example:
    >>> class ERC4337Adapter(SmartWalletAdapter):
    ...     def get_owner_address(self) -> str:
    ...         return self.owner_account.address
    ...     def is_deployed(self) -> bool:
    ...         return len(self.w3.eth.get_code(self.account_address)) > 2
"""

from abc import abstractmethod
from typing import Any, Dict

from ..base import WalletAdapter


class SmartWalletAdapter(WalletAdapter):
    """
    Abstract base class for smart wallet implementations.

    Extends WalletAdapter with smart-wallet-specific concepts
    that don't exist in EOA wallets:
    - Owner address (EOA that controls the smart wallet)
    - Deployment status (smart wallets may not be deployed yet)
    - Wallet type metadata (version, capabilities, etc.)

    Subclasses must implement all WalletAdapter methods plus:
        - get_owner_address(): Get the controlling EOA address
        - is_deployed(): Check if the smart wallet contract exists on-chain
        - get_wallet_type_info(): Get wallet type metadata
    """

    @abstractmethod
    def get_owner_address(self) -> str:
        """
        Get the address of the EOA that controls this smart wallet.

        Returns:
            Owner EOA address as checksummed string
        """
        raise NotImplementedError

    @abstractmethod
    def is_deployed(self) -> bool:
        """
        Check if the smart wallet contract is deployed on-chain.

        Returns:
            True if the contract exists at the wallet address
        """
        raise NotImplementedError

    @abstractmethod
    def get_wallet_type_info(self) -> Dict[str, Any]:
        """
        Get metadata about this smart wallet type.

        Returns:
            Dictionary with wallet type info (e.g., type, version, capabilities)
        """
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert wallet info to dictionary.

        Extends base to_dict with smart wallet specific fields.

        Returns:
            Dictionary with wallet info including owner and deployment status
        """
        base = super().to_dict()
        base["owner_address"] = self.get_owner_address()
        base["is_deployed"] = self.is_deployed()
        base["wallet_type_info"] = self.get_wallet_type_info()
        return base
