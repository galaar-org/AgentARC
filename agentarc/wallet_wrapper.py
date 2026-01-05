"""
Policy Wallet Provider - Wraps AgentKit wallet providers with policy enforcement
"""

from typing import Any, Dict, Optional
from decimal import Decimal
from web3 import Web3

from .logger import PolicyLogger, LogLevel

# Try to import WalletProvider from AgentKit
# If not available, create a minimal base class for compatibility
try:
    from coinbase_agentkit.wallet_providers import WalletProvider
    HAS_AGENTKIT = True
except ImportError:
    # Fallback for when AgentKit is not installed
    from abc import ABC
    class WalletProvider(ABC):
        """Minimal WalletProvider stub for compatibility"""
        pass
    HAS_AGENTKIT = False


class PolicyViolationError(Exception):
    """Raised when a transaction violates a policy"""
    pass


class PolicyWalletProvider(WalletProvider):
    """
    Wraps any AgentKit EvmWalletProvider to enforce policies.

    This wrapper intercepts send_transaction() calls and validates them
    against configured policies before execution.
    """

    def __init__(self, base_provider: Any, policy_engine: Any, logger: Optional[PolicyLogger] = None):
        """
        Initialize the policy wallet provider

        Args:
            base_provider: The underlying AgentKit wallet provider
            policy_engine: PolicyEngine instance for validation
            logger: Optional PolicyLogger instance (creates default if not provided)
        """
        self._base_provider = base_provider
        self._policy_engine = policy_engine
        self.logger = logger or PolicyLogger()

    def send_transaction(self, transaction: Dict[str, Any]) -> str:
        """
        Send a transaction after policy validation

        This is the main interception point for contract interactions.

        Args:
            transaction: Transaction parameters (to, value, data, gas, etc.)

        Returns:
            Transaction hash

        Raises:
            PolicyViolationError: If transaction violates any policy
        """
        # Get sender address for simulation
        from_address = self._base_provider.get_address()

        # Validate transaction against policies (with simulation)
        passed, reason = self._policy_engine.validate_transaction(transaction, from_address)

        # Print clear result
        print("\n" + "="*60)
        if not passed:
            print("🚫 TRANSACTION BLOCKED")
            print("="*60)
            print(f"Reason: {reason}")
            print("="*60 + "\n")
            raise PolicyViolationError(f"Policy violation: {reason}")
        else:
            print("✅ TRANSACTION APPROVED")
            print("="*60 + "\n")

        # Normalize transaction field types for web3.py compatibility
        # web3.py requires integer types for numeric fields, not floats
        normalized_tx = transaction.copy()
        numeric_fields = ['value', 'gas', 'gasPrice', 'maxFeePerGas', 'maxPriorityFeePerGas', 'nonce', 'chainId']

        for field in numeric_fields:
            if field in normalized_tx and normalized_tx[field] is not None:
                # Convert to int if it's a float or string
                normalized_tx[field] = int(normalized_tx[field])

        # If validation passed, execute the transaction
        return self._base_provider.send_transaction(normalized_tx)

    def track_initialization(self) -> None:
        """Override to prevent double-tracking (base provider already tracks)"""
        # Skip tracking for the wrapper - the base provider will handle it
        pass

    # Delegate all other methods to the base provider
    def get_address(self) -> str:
        """Get wallet address"""
        return self._base_provider.get_address()

    def get_network(self):
        """Get network configuration"""
        return self._base_provider.get_network()

    def get_balance(self) -> Decimal:
        """Get wallet balance"""
        return self._base_provider.get_balance()

    def sign_message(self, message: str) -> str:
        """Sign a message"""
        return self._base_provider.sign_message(message)

    def native_transfer(self, to: str, value: Decimal) -> str:
        """Transfer native currency (ETH) with policy validation"""
        # Convert value to wei for validation
        # Note: CDP provider uses Web3.to_wei(value, "ether") internally
        value_wei = Web3.to_wei(value, "ether")

        # Construct transaction dict for policy validation
        transaction = {
            'to': to,
            'value': value_wei,
            'data': '0x',  # Native transfers have no calldata
        }

        # Validate transaction against policies
        passed, reason = self._policy_engine.validate_transaction(transaction)

        if not passed:
            raise PolicyViolationError(f"Policy violation: {reason}")

        # If validation passed, execute the native transfer
        self.logger.success("Policy checks passed - Executing transaction...\n")
        return self._base_provider.native_transfer(to, value)

    def get_name(self) -> str:
        """Get wallet provider name"""
        return f"Policy({self._base_provider.get_name()})"

    def wait_for_transaction_receipt(self, tx_hash: str, timeout: int = 120) -> Dict[str, Any]:
        """Wait for transaction receipt"""
        return self._base_provider.wait_for_transaction_receipt(tx_hash, timeout)

    def read_contract(self, *args, **kwargs) -> Any:
        """Read contract data"""
        return self._base_provider.read_contract(*args, **kwargs)

    def sign_typed_data(self, typed_data: Dict[str, Any]) -> str:
        """Sign typed data"""
        return self._base_provider.sign_typed_data(typed_data)

    def sign_transaction(self, transaction: Dict[str, Any]) -> Any:
        """Sign a transaction (without sending)"""
        return self._base_provider.sign_transaction(transaction)

    @property
    def web3(self):
        """Access underlying web3 instance if available"""
        if hasattr(self._base_provider, 'web3'):
            return self._base_provider.web3
        raise AttributeError("Base provider does not have web3 instance")

    def __getattr__(self, name: str) -> Any:
        """
        Delegate all unknown attributes/methods to the base provider.
        This ensures compatibility with any wallet provider methods not explicitly overridden.
        """
        return getattr(self._base_provider, name)

    def __repr__(self) -> str:
        return f"PolicyWalletProvider(base={self._base_provider.__class__.__name__})"
