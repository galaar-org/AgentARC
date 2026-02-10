"""
Wallet factory for creating wallet adapters.

This factory provides a unified interface for creating wallets
from various sources (private key, mnemonic, CDP, etc.).

Example:
    >>> wallet = WalletFactory.from_private_key("0x...", rpc_url="https://...")
    >>> wallet = WalletFactory.from_mnemonic("word1 word2 ...", rpc_url="https://...")
    >>> wallet = WalletFactory.from_cdp(cdp_provider)
"""

from typing import Any, Optional

from .base import WalletAdapter


class WalletFactory:
    """
    Factory for creating wallet adapters from various sources.

    Supported wallet types:
        - Private key: Raw Ethereum private key
        - Mnemonic: BIP-39 mnemonic phrase
        - CDP: Coinbase Developer Platform wallet provider
        - EIP-1193: Browser wallet provider (MetaMask, etc.)

    Example:
        >>> # From private key
        >>> wallet = WalletFactory.from_private_key(
        ...     private_key="0x...",
        ...     rpc_url="https://mainnet.base.org"
        ... )
        >>>
        >>> # From mnemonic
        >>> wallet = WalletFactory.from_mnemonic(
        ...     mnemonic="word1 word2 ... word12",
        ...     rpc_url="https://mainnet.base.org"
        ... )
        >>>
        >>> # From CDP provider
        >>> wallet = WalletFactory.from_cdp(cdp_provider)
    """

    @staticmethod
    def from_private_key(
        private_key: str,
        rpc_url: str,
        chain_id: Optional[int] = None,
    ) -> WalletAdapter:
        """
        Create wallet from a private key.

        Args:
            private_key: Ethereum private key (with or without 0x prefix)
            rpc_url: RPC endpoint URL
            chain_id: Optional chain ID (auto-detected if not provided)

        Returns:
            WalletAdapter instance

        Example:
            >>> wallet = WalletFactory.from_private_key(
            ...     private_key="0x1234...",
            ...     rpc_url="https://mainnet.base.org",
            ...     chain_id=8453
            ... )
        """
        from .adapters.private_key import PrivateKeyWallet

        return PrivateKeyWallet(
            private_key=private_key,
            rpc_url=rpc_url,
            chain_id=chain_id,
        )

    @staticmethod
    def from_mnemonic(
        mnemonic: str,
        rpc_url: str,
        derivation_path: str = "m/44'/60'/0'/0/0",
        chain_id: Optional[int] = None,
    ) -> WalletAdapter:
        """
        Create wallet from a mnemonic phrase.

        Args:
            mnemonic: BIP-39 mnemonic phrase (12 or 24 words)
            rpc_url: RPC endpoint URL
            derivation_path: HD derivation path (default: standard Ethereum)
            chain_id: Optional chain ID (auto-detected if not provided)

        Returns:
            WalletAdapter instance

        Example:
            >>> wallet = WalletFactory.from_mnemonic(
            ...     mnemonic="word1 word2 ... word12",
            ...     rpc_url="https://mainnet.base.org"
            ... )
        """
        from .adapters.mnemonic import MnemonicWallet

        return MnemonicWallet(
            mnemonic=mnemonic,
            rpc_url=rpc_url,
            derivation_path=derivation_path,
            chain_id=chain_id,
        )

    @staticmethod
    def from_cdp(cdp_provider: Any) -> WalletAdapter:
        """
        Create wallet from a Coinbase Developer Platform provider.

        Args:
            cdp_provider: CDP wallet provider instance

        Returns:
            WalletAdapter instance

        Example:
            >>> from coinbase_agentkit import CdpEvmWalletProvider
            >>> cdp_provider = CdpEvmWalletProvider(config)
            >>> wallet = WalletFactory.from_cdp(cdp_provider)
        """
        from .adapters.cdp import CdpWalletAdapter

        return CdpWalletAdapter(cdp_provider)

    @staticmethod
    def from_eip1193(
        provider: Any,
        chain_id: Optional[int] = None,
    ) -> WalletAdapter:
        """
        Create wallet from an EIP-1193 provider (browser wallets).

        Args:
            provider: EIP-1193 compliant provider
            chain_id: Optional chain ID

        Returns:
            WalletAdapter instance

        Example:
            >>> # For use with web3.py's window.ethereum
            >>> wallet = WalletFactory.from_eip1193(provider)
        """
        from .adapters.eip1193 import EIP1193WalletAdapter

        return EIP1193WalletAdapter(provider, chain_id=chain_id)

    @staticmethod
    def from_web3(
        web3_instance: Any,
        account_address: Optional[str] = None,
    ) -> WalletAdapter:
        """
        Create wallet from a Web3 instance with unlocked account.

        Args:
            web3_instance: Web3 instance
            account_address: Address of the account (uses first account if not specified)

        Returns:
            WalletAdapter instance

        Example:
            >>> from web3 import Web3
            >>> w3 = Web3(Web3.HTTPProvider(rpc_url))
            >>> wallet = WalletFactory.from_web3(w3, "0x...")
        """
        from .adapters.web3_adapter import Web3WalletAdapter

        return Web3WalletAdapter(web3_instance, account_address)
