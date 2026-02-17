"""
Mnemonic (seed phrase) wallet adapter.

This adapter derives a private key from a BIP-39 mnemonic phrase.

Example:
    >>> wallet = MnemonicWallet(
    ...     mnemonic="word1 word2 ... word12",
    ...     rpc_url="https://mainnet.base.org"
    ... )
    >>> print(wallet.get_address())
"""

from typing import Any, Dict, Optional, Union

from eth_account import Account

from .private_key import PrivateKeyWallet
from ...core.types import TransactionRequest, TransactionResult


# Enable mnemonic features
Account.enable_unaudited_hdwallet_features()


class MnemonicWallet(PrivateKeyWallet):
    """
    Wallet implementation using a mnemonic phrase.

    This derives a private key from a BIP-39 mnemonic phrase
    using the specified derivation path.

    Attributes:
        mnemonic: Original mnemonic phrase
        derivation_path: HD derivation path used

    Example:
        >>> wallet = MnemonicWallet(
        ...     mnemonic="abandon abandon ... about",
        ...     rpc_url="https://mainnet.base.org",
        ...     derivation_path="m/44'/60'/0'/0/0"
        ... )
    """

    def __init__(
        self,
        mnemonic: str,
        rpc_url: str,
        derivation_path: str = "m/44'/60'/0'/0/0",
        chain_id: Optional[int] = None,
    ):
        """
        Initialize wallet from mnemonic.

        Args:
            mnemonic: BIP-39 mnemonic phrase (12 or 24 words)
            rpc_url: RPC endpoint URL
            derivation_path: HD derivation path (default: standard Ethereum)
            chain_id: Optional chain ID (auto-detected if not provided)
        """
        self.mnemonic = mnemonic
        self.derivation_path = derivation_path

        # Derive account from mnemonic
        account = Account.from_mnemonic(
            mnemonic,
            account_path=derivation_path,
        )

        # Initialize parent with derived private key
        super().__init__(
            private_key=account.key.hex(),
            rpc_url=rpc_url,
            chain_id=chain_id,
        )

    def get_account_at_index(self, index: int) -> "MnemonicWallet":
        """
        Get wallet for a different account index.

        Args:
            index: Account index (0, 1, 2, ...)

        Returns:
            New MnemonicWallet at the specified index

        Example:
            >>> wallet0 = MnemonicWallet(mnemonic, rpc_url)
            >>> wallet1 = wallet0.get_account_at_index(1)
        """
        # Modify derivation path for new index
        base_path = "/".join(self.derivation_path.split("/")[:-1])
        new_path = f"{base_path}/{index}"

        return MnemonicWallet(
            mnemonic=self.mnemonic,
            rpc_url=self.w3.provider.endpoint_uri,
            derivation_path=new_path,
            chain_id=self._chain_id,
        )
