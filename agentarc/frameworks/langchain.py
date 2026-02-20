"""
LangChain framework adapter.

This adapter creates LangChain tools for use with LangChain agents.

Example:
    >>> from langchain.agents import create_react_agent
    >>> from agentarc.frameworks import LangChainAdapter
    >>>
    >>> adapter = LangChainAdapter()
    >>> tx_tool = adapter.create_transaction_tool(policy_wallet)
    >>> agent = create_react_agent(llm, [tx_tool])
"""

from typing import Any, Optional

from web3 import Web3

from .base import FrameworkAdapter
from ..wallets.policy_wallet import PolicyWallet
from ..core.errors import PolicyViolationError


class LangChainAdapter(FrameworkAdapter):
    """
    LangChain framework adapter.

    Creates LangChain StructuredTool instances for blockchain operations.

    Example:
        >>> adapter = LangChainAdapter()
        >>> tools = adapter.create_all_tools(policy_wallet)
        >>> agent = create_react_agent(llm, tools)
    """

    def create_transaction_tool(self, policy_wallet: PolicyWallet) -> Any:
        """
        Create a LangChain tool for sending transactions.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            LangChain StructuredTool for sending transactions
        """
        try:
            from langchain_core.tools import StructuredTool
            from pydantic import BaseModel, Field
        except ImportError:
            raise ImportError(
                "LangChain not installed. Install with: pip install langchain-core"
            )

        class TransactionInput(BaseModel):
            """Input for sending a transaction."""

            to: str = Field(description="Recipient Ethereum address (0x...)")
            value: str = Field(
                default="0",
                description="Amount to send in ETH (e.g., '0.1' for 0.1 ETH)",
            )
            data: str = Field(
                default="0x",
                description="Transaction calldata (hex string, default: 0x)",
            )

        def send_transaction(to: str, value: str = "0", data: str = "0x") -> str:
            """Send a blockchain transaction with policy validation."""
            try:
                # Convert ETH to wei
                value_wei = Web3.to_wei(float(value), "ether")

                result = policy_wallet.send_transaction({
                    "to": to,
                    "value": value_wei,
                    "data": data,
                })

                return f"Transaction sent successfully! Hash: {result.tx_hash}"

            except PolicyViolationError as e:
                return f"Transaction blocked by policy: {e.reason}"
            except Exception as e:
                return f"Transaction failed: {str(e)}"

        return StructuredTool.from_function(
            func=send_transaction,
            name="send_transaction",
            description="Send a blockchain transaction. Policy validation is applied automatically.",
            args_schema=TransactionInput,
        )

    def create_balance_tool(self, policy_wallet: PolicyWallet) -> Any:
        """
        Create a LangChain tool for checking balance.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            LangChain StructuredTool for checking balance
        """
        try:
            from langchain_core.tools import StructuredTool
            from pydantic import BaseModel
        except ImportError:
            raise ImportError(
                "LangChain not installed. Install with: pip install langchain-core"
            )

        class EmptyInput(BaseModel):
            """No input required."""

            pass

        def get_balance() -> str:
            """Get the wallet's native token balance."""
            try:
                balance_wei = policy_wallet.get_balance()
                balance_eth = Web3.from_wei(balance_wei, "ether")
                address = policy_wallet.get_address()
                network = policy_wallet.get_network()

                return f"Address: {address}\nBalance: {balance_eth} ETH\nNetwork: {network}"

            except Exception as e:
                return f"Failed to get balance: {str(e)}"

        return StructuredTool.from_function(
            func=get_balance,
            name="get_wallet_balance",
            description="Get the wallet's current balance and address.",
            args_schema=EmptyInput,
        )

    def create_wallet_info_tool(self, policy_wallet: PolicyWallet) -> Any:
        """
        Create a LangChain tool for getting wallet info.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            LangChain StructuredTool for wallet info
        """
        try:
            from langchain_core.tools import StructuredTool
            from pydantic import BaseModel
        except ImportError:
            raise ImportError(
                "LangChain not installed. Install with: pip install langchain-core"
            )

        class EmptyInput(BaseModel):
            """No input required."""

            pass

        def get_wallet_info() -> str:
            """Get wallet information including address, network, and policy status."""
            try:
                info = policy_wallet.to_dict()
                return (
                    f"Address: {info['address']}\n"
                    f"Chain ID: {info['chain_id']}\n"
                    f"Network: {info['network']}\n"
                    f"Policy Enabled: {info['policy_enabled']}\n"
                    f"Policies: {info['policies_count']}"
                )
            except Exception as e:
                return f"Failed to get wallet info: {str(e)}"

        return StructuredTool.from_function(
            func=get_wallet_info,
            name="get_wallet_info",
            description="Get wallet information including address, network, and policy configuration.",
            args_schema=EmptyInput,
        )

    def create_all_tools(self, policy_wallet: PolicyWallet) -> list:
        """
        Create all available LangChain tools.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            List of LangChain StructuredTool instances
        """
        return [
            self.create_transaction_tool(policy_wallet),
            self.create_balance_tool(policy_wallet),
            self.create_wallet_info_tool(policy_wallet),
        ]
