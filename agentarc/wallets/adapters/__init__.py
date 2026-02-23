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

try:
    from .smart_wallet_base import SmartWalletAdapter
except ImportError:
    SmartWalletAdapter = None  # type: ignore

try:
    from .erc4337 import ERC4337Adapter
except ImportError:
    ERC4337Adapter = None  # type: ignore

try:
    from .safe_adapter import SafeAdapter
except ImportError:
    SafeAdapter = None  # type: ignore

__all__ = [
    "PrivateKeyWallet",
    "MnemonicWallet",
    "CdpWalletAdapter",
    "SmartWalletAdapter",
    "ERC4337Adapter",
    "SafeAdapter",
]
