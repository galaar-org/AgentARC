"""
Base class for framework adapters.

All framework adapters must implement this interface
to provide a consistent way to create tools for AI agents.
"""

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..wallets.policy_wallet import PolicyWallet


class FrameworkAdapter(ABC):
    """
    Abstract base class for AI framework adapters.

    Each adapter creates framework-specific tools that wrap
    PolicyWallet methods for use with AI agents.

    Subclasses must implement:
        - create_transaction_tool(): Create a tool for sending transactions
        - create_balance_tool(): Create a tool for checking balance

    Example:
        >>> class MyFrameworkAdapter(FrameworkAdapter):
        ...     def create_transaction_tool(self, wallet):
        ...         def send_tx(to, value):
        ...             return wallet.send_transaction({"to": to, "value": value})
        ...         return send_tx
    """

    @abstractmethod
    def create_transaction_tool(self, policy_wallet: "PolicyWallet") -> Any:
        """
        Create a transaction sending tool.

        Args:
            policy_wallet: PolicyWallet instance for sending transactions

        Returns:
            Framework-specific tool for sending transactions
        """
        raise NotImplementedError

    @abstractmethod
    def create_balance_tool(self, policy_wallet: "PolicyWallet") -> Any:
        """
        Create a balance checking tool.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            Framework-specific tool for checking balance
        """
        raise NotImplementedError

    def create_all_tools(self, policy_wallet: "PolicyWallet") -> list:
        """
        Create all available tools.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            List of all framework-specific tools
        """
        return [
            self.create_transaction_tool(policy_wallet),
            self.create_balance_tool(policy_wallet),
        ]
