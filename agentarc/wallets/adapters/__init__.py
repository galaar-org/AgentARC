"""
Wallet adapters for different wallet types.

Each adapter implements the WalletAdapter interface for a specific
wallet type (private key, mnemonic, CDP, etc.).
"""

from .private_key import PrivateKeyWallet
from .mnemonic import MnemonicWallet

# Optional adapters (may have additional dependencies)
try:
    from .cdp import CdpWalletAdapter
except ImportError:
    CdpWalletAdapter = None  # type: ignore

__all__ = [
    "PrivateKeyWallet",
    "MnemonicWallet",
    "CdpWalletAdapter",
]
