"""
AgentARC Compatibility Module.

This module provides backward compatibility with older APIs.

Components:
    - PolicyWalletProvider: Legacy AgentKit wallet wrapper
    - PolicyViolationError: Legacy error class

Note:
    These classes are maintained for backward compatibility.
    New code should use the wallets module instead:

    >>> from agentarc.wallets import PolicyWallet, WalletFactory
"""

from .wallet_wrapper import PolicyWalletProvider, PolicyViolationError

__all__ = [
    "PolicyWalletProvider",
    "PolicyViolationError",
]
