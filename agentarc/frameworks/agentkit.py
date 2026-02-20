"""
Coinbase AgentKit framework adapter.

This adapter provides backward compatibility with the existing
PolicyWalletProvider pattern used with AgentKit.

Example:
    >>> from agentarc.frameworks import AgentKitAdapter
    >>>
    >>> adapter = AgentKitAdapter()
    >>> policy_provider = adapter.wrap_provider(cdp_provider, config_path="policy.yaml")
"""

from typing import Any, Callable, Optional

from .base import FrameworkAdapter
from ..wallets.policy_wallet import PolicyWallet
from ..core.config import PolicyConfig
from ..core.events import ValidationEvent


class AgentKitAdapter(FrameworkAdapter):
    """
    Coinbase AgentKit framework adapter.

    Provides backward compatibility with the PolicyWalletProvider pattern
    and creates tools compatible with AgentKit action providers.

    Example:
        >>> # Wrap CDP provider with policies
        >>> adapter = AgentKitAdapter()
        >>> policy_provider = adapter.wrap_provider(
        ...     cdp_provider,
        ...     config_path="policy.yaml"
        ... )
        >>>
        >>> # Use with AgentKit
        >>> agentkit = AgentKit(
        ...     AgentKitConfig(wallet_provider=policy_provider)
        ... )
    """

    def wrap_provider(
        self,
        provider: Any,
        config_path: Optional[str] = None,
        config: Optional[PolicyConfig] = None,
        event_callback: Optional[Callable[[ValidationEvent], None]] = None,
    ) -> Any:
        """
        Wrap a CDP provider with policy enforcement.

        This returns a PolicyWalletProvider that is compatible with AgentKit.

        Args:
            provider: CDP wallet provider instance
            config_path: Path to policy.yaml
            config: PolicyConfig instance
            event_callback: Callback for validation events

        Returns:
            PolicyWalletProvider instance (backward compatible)
        """
        # Import the legacy wrapper for backward compatibility
        from ..compat import PolicyWalletProvider
        from ..engine import PolicyEngine

        # Create policy engine
        engine = PolicyEngine(
            config_path=config_path,
            config=config,
            web3_provider=provider,
            event_callback=event_callback,
        )

        # Return wrapped provider
        return PolicyWalletProvider(provider, engine)

    def create_transaction_tool(self, policy_wallet: PolicyWallet) -> Any:
        """
        Create a transaction tool compatible with AgentKit.

        Note: AgentKit typically uses action providers rather than tools.
        This method is provided for compatibility with the base interface.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            Callable function for sending transactions
        """

        def send_transaction(to: str, value: int = 0, data: str = "0x") -> dict:
            """Send a transaction with policy validation."""
            result = policy_wallet.send_transaction({
                "to": to,
                "value": value,
                "data": data,
            })
            return {
                "success": result.success,
                "tx_hash": result.tx_hash,
                "gas_used": result.gas_used,
            }

        return send_transaction

    def create_balance_tool(self, policy_wallet: PolicyWallet) -> Any:
        """
        Create a balance tool compatible with AgentKit.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            Callable function for checking balance
        """

        def get_balance() -> dict:
            """Get wallet balance."""
            return {
                "address": policy_wallet.get_address(),
                "balance_wei": policy_wallet.get_balance(),
                "chain_id": policy_wallet.get_chain_id(),
            }

        return get_balance

    def create_action_provider(
        self,
        policy_wallet: PolicyWallet,
        name: str = "policy_actions",
    ) -> Any:
        """
        Create an AgentKit action provider.

        This creates a custom action provider that can be used
        with AgentKit's action_providers list.

        Args:
            policy_wallet: PolicyWallet instance
            name: Name for the action provider

        Returns:
            Action provider instance (requires AgentKit)

        Example:
            >>> provider = adapter.create_action_provider(policy_wallet)
            >>> agentkit = AgentKit(
            ...     AgentKitConfig(
            ...         wallet_provider=...,
            ...         action_providers=[provider, ...]
            ...     )
            ... )
        """
        try:
            from coinbase_agentkit import ActionProvider, action
        except ImportError:
            raise ImportError(
                "AgentKit not installed. Install with: pip install coinbase-agentkit"
            )

        class PolicyActionProvider(ActionProvider):
            """Custom action provider with policy validation."""

            def __init__(self, wallet: PolicyWallet):
                self.wallet = wallet
                super().__init__(name, [])

            @action("validate_transaction")
            def validate_transaction(self, to: str, value: int = 0, data: str = "0x") -> str:
                """Validate a transaction without sending."""
                passed, reason = self.wallet.validate_transaction({
                    "to": to,
                    "value": value,
                    "data": data,
                })
                if passed:
                    return f"Transaction would be allowed: {reason}"
                else:
                    return f"Transaction would be blocked: {reason}"

            @action("get_policy_info")
            def get_policy_info(self) -> str:
                """Get policy configuration information."""
                config = self.wallet.get_config()
                policies = [p.get("type") for p in config.policies]
                return f"Policies enabled: {config.enabled}\nActive policies: {', '.join(policies)}"

        return PolicyActionProvider(policy_wallet)
