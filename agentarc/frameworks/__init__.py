"""
AgentARC Framework Adapters Module.

This module provides adapters for integrating AgentARC with
various AI agent frameworks.

Supported Frameworks:
    - LangChain: Create LangChain tools for transactions
    - OpenAI SDK: Create OpenAI function calling tools
    - CrewAI: Create CrewAI tools for agents
    - AutoGen: Create AutoGen functions
    - AgentKit: Backward compatible with Coinbase AgentKit

Example:
    >>> from agentarc.frameworks import LangChainAdapter, OpenAIAdapter
    >>> from agentarc.wallets import WalletFactory, PolicyWallet
    >>>
    >>> wallet = WalletFactory.from_private_key("0x...", rpc_url="...")
    >>> policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")
    >>>
    >>> # LangChain
    >>> adapter = LangChainAdapter()
    >>> tools = adapter.create_all_tools(policy_wallet)
    >>>
    >>> # OpenAI SDK
    >>> adapter = OpenAIAdapter()
    >>> tools = adapter.create_all_tools(policy_wallet)
    >>> handlers = adapter.create_tool_handlers(policy_wallet)
"""

from .base import FrameworkAdapter

# Optional adapters (may have additional dependencies)
try:
    from .langchain import LangChainAdapter
except ImportError:
    LangChainAdapter = None  # type: ignore

try:
    from .openai_sdk import OpenAIAdapter
except ImportError:
    OpenAIAdapter = None  # type: ignore

try:
    from .agentkit import AgentKitAdapter
except ImportError:
    AgentKitAdapter = None  # type: ignore

__all__ = [
    "FrameworkAdapter",
    "LangChainAdapter",
    "OpenAIAdapter",
    "AgentKitAdapter",
]
