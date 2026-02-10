"""
AgentARC Wallets Module.

This module provides a universal wallet abstraction layer
that supports any wallet type.

Components:
    - WalletAdapter: Abstract base class for wallets
    - WalletFactory: Create wallets from various sources
    - PolicyWallet: Wallet with policy enforcement
    - Adapters: PrivateKey, Mnemonic, CDP, EIP-1193

Example:
    >>> from agentarc.wallets import WalletFactory, PolicyWallet
    >>>
    >>> # Create wallet from private key
    >>> wallet = WalletFactory.from_private_key("0x...", rpc_url="https://...")
    >>>
    >>> # Wrap with policy enforcement
    >>> policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")
    >>> result = policy_wallet.send_transaction({"to": "0x...", "value": 100})
"""

from .base import WalletAdapter

# Optional modules (phase 2 - may not be available yet)
try:
    from .factory import WalletFactory
except ImportError:
    WalletFactory = None  # type: ignore

try:
    from .policy_wallet import PolicyWallet
except ImportError:
    PolicyWallet = None  # type: ignore

# Wallet adapters (optional)
from .adapters import (
    PrivateKeyWallet,
    MnemonicWallet,
    CdpWalletAdapter,
)

__all__ = [
    "WalletAdapter",
    "WalletFactory",
    "PolicyWallet",
    # Adapters
    "PrivateKeyWallet",
    "MnemonicWallet",
    "CdpWalletAdapter",
]
