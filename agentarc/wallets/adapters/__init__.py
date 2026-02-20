"""
Wallet adapters for different wallet types.

Each adapter implements the WalletAdapter interface for a specific
wallet type (private key, mnemonic, CDP, etc.).
"""

# Optional adapters (phase 2 - may not be available yet)
try:
    from .private_key import PrivateKeyWallet
except ImportError:
    PrivateKeyWallet = None  # type: ignore

try:
    from .mnemonic import MnemonicWallet
except ImportError:
    MnemonicWallet = None  # type: ignore

try:
    from .cdp import CdpWalletAdapter
except ImportError:
    CdpWalletAdapter = None  # type: ignore

__all__ = [
    "PrivateKeyWallet",
    "MnemonicWallet",
    "CdpWalletAdapter",
]
