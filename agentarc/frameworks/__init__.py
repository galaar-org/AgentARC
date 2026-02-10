"""
AgentARC Framework Adapters Module.

This module provides adapters for integrating AgentARC with
various AI agent frameworks.

Supported Frameworks:
    - LangChain: Create LangChain tools for transactions
    - CrewAI: Create CrewAI tools for agents
    - AutoGen: Create AutoGen functions
    - AgentKit: Backward compatible with Coinbase AgentKit

Example:
    >>> from agentarc.frameworks import LangChainAdapter
    >>> from agentarc.wallets import WalletFactory, PolicyWallet
    >>>
    >>> wallet = WalletFactory.from_private_key("0x...", rpc_url="...")
    >>> policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")
    >>>
    >>> adapter = LangChainAdapter()
    >>> tx_tool = adapter.create_transaction_tool(policy_wallet)
"""

from .base import FrameworkAdapter

# Optional adapters (may have additional dependencies)
try:
    from .langchain import LangChainAdapter
except ImportError:
    LangChainAdapter = None  # type: ignore

try:
    from .agentkit import AgentKitAdapter
except ImportError:
    AgentKitAdapter = None  # type: ignore

__all__ = [
    "FrameworkAdapter",
    "LangChainAdapter",
    "AgentKitAdapter",
]
