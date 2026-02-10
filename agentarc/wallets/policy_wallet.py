"""
Policy-enforced wallet wrapper.

This module provides PolicyWallet which wraps any WalletAdapter
with policy enforcement, validating all transactions before sending.

Example:
    >>> wallet = WalletFactory.from_private_key("0x...", rpc_url="...")
    >>> policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")
    >>> result = policy_wallet.send_transaction({"to": "0x...", "value": 100})
"""

from typing import Any, Callable, Dict, Optional, Union

from .base import WalletAdapter
from ..core.config import PolicyConfig
from ..core.types import TransactionRequest, TransactionResult
from ..core.errors import PolicyViolationError
from ..core.events import ValidationEvent


class PolicyWallet:
    """
    Wallet wrapper with policy enforcement.

    This wraps any WalletAdapter and validates all transactions
    against configured policies before sending.

    Attributes:
        wallet: Underlying WalletAdapter
        engine: PolicyEngine for validation
        config: PolicyConfig instance

    Example:
        >>> wallet = WalletFactory.from_private_key("0x...", rpc_url="...")
        >>> policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")
        >>>
        >>> # This will be validated before sending
        >>> result = policy_wallet.send_transaction({
        ...     "to": "0x...",
        ...     "value": 1000000000000000000,  # 1 ETH
        ... })
    """

    def __init__(
        self,
        wallet: WalletAdapter,
        config_path: Optional[str] = None,
        config: Optional[PolicyConfig] = None,
        event_callback: Optional[Callable[[ValidationEvent], None]] = None,
    ):
        """
        Initialize policy wallet.

        Args:
            wallet: Underlying WalletAdapter to wrap
            config_path: Path to policy.yaml configuration
            config: PolicyConfig instance (alternative to config_path)
            event_callback: Callback for validation events

        Raises:
            ValueError: If both config_path and config are provided
        """
        if config_path and config:
            raise ValueError("Cannot specify both config_path and config")

        self.wallet = wallet

        # Import here to avoid circular imports
        from ..engine import PolicyEngine

        # Create policy engine with wallet's chain ID
        self.engine = PolicyEngine(
            config_path=config_path,
            config=config,
            chain_id=wallet.get_chain_id(),
            event_callback=event_callback,
        )

        self.config = self.engine.config

    def send_transaction(
        self,
        tx: Union[Dict[str, Any], TransactionRequest],
    ) -> TransactionResult:
        """
        Validate and send a transaction.

        Args:
            tx: Transaction dictionary or TransactionRequest

        Returns:
            TransactionResult with success status and tx hash

        Raises:
            PolicyViolationError: If transaction violates policies
        """
        # Convert to dict if needed
        if isinstance(tx, TransactionRequest):
            tx_dict = tx.to_dict()
        else:
            tx_dict = tx

        # Validate transaction
        from_address = self.wallet.get_address()
        passed, reason = self.engine.validate_transaction(tx_dict, from_address)

        if not passed:
            raise PolicyViolationError(reason)

        # Send via underlying wallet
        return self.wallet.send_transaction(tx)

    def sign_transaction(
        self,
        tx: Union[Dict[str, Any], TransactionRequest],
    ) -> bytes:
        """
        Validate and sign a transaction (without sending).

        Args:
            tx: Transaction dictionary or TransactionRequest

        Returns:
            Signed transaction as raw bytes

        Raises:
            PolicyViolationError: If transaction violates policies
        """
        # Convert to dict if needed
        if isinstance(tx, TransactionRequest):
            tx_dict = tx.to_dict()
        else:
            tx_dict = tx

        # Validate transaction
        from_address = self.wallet.get_address()
        passed, reason = self.engine.validate_transaction(tx_dict, from_address)

        if not passed:
            raise PolicyViolationError(reason)

        # Sign via underlying wallet
        return self.wallet.sign_transaction(tx)

    # Passthrough methods to underlying wallet

    def get_address(self) -> str:
        """Get wallet address."""
        return self.wallet.get_address()

    def get_chain_id(self) -> int:
        """Get chain ID."""
        return self.wallet.get_chain_id()

    def get_balance(self) -> int:
        """Get native token balance in wei."""
        return self.wallet.get_balance()

    def call(self, tx: Union[Dict[str, Any], TransactionRequest]) -> bytes:
        """Make a read-only call (no validation needed)."""
        return self.wallet.call(tx)

    def estimate_gas(self, tx: Union[Dict[str, Any], TransactionRequest]) -> int:
        """Estimate gas for a transaction."""
        return self.wallet.estimate_gas(tx)

    def get_nonce(self) -> int:
        """Get next nonce."""
        return self.wallet.get_nonce()

    def get_network(self) -> str:
        """Get network name."""
        return self.wallet.get_network()

    # Additional methods

    def validate_transaction(
        self,
        tx: Union[Dict[str, Any], TransactionRequest],
    ) -> tuple[bool, str]:
        """
        Validate a transaction without sending.

        Args:
            tx: Transaction dictionary or TransactionRequest

        Returns:
            Tuple of (passed: bool, reason: str)
        """
        if isinstance(tx, TransactionRequest):
            tx_dict = tx.to_dict()
        else:
            tx_dict = tx

        from_address = self.wallet.get_address()
        return self.engine.validate_transaction(tx_dict, from_address)

    def add_event_callback(self, callback: Callable[[ValidationEvent], None]) -> None:
        """Add an event callback."""
        self.engine.add_event_callback(callback)

    def get_config(self) -> PolicyConfig:
        """Get policy configuration."""
        return self.config

    def to_dict(self) -> Dict[str, Any]:
        """Convert wallet info to dictionary."""
        return {
            **self.wallet.to_dict(),
            "policy_enabled": self.config.enabled,
            "policies_count": len(self.config.policies),
        }
