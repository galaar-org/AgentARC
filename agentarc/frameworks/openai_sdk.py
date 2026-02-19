"""
OpenAI SDK framework adapter.

This adapter creates tools compatible with OpenAI's function calling format
for use with the OpenAI Python SDK.

Example:
    >>> from openai import OpenAI
    >>> from agentarc.frameworks import OpenAIAdapter
    >>>
    >>> adapter = OpenAIAdapter()
    >>> tools = adapter.create_all_tools(policy_wallet)
    >>> handlers = adapter.create_tool_handlers(policy_wallet)
    >>>
    >>> response = client.chat.completions.create(
    ...     model="gpt-4",
    ...     messages=[...],
    ...     tools=tools,
    ... )
"""

import json
from typing import Any, Callable, Dict, List, Optional, Union

from web3 import Web3

from .base import FrameworkAdapter
from ..wallets.policy_wallet import PolicyWallet
from ..core.errors import PolicyViolationError


class OpenAIAdapter(FrameworkAdapter):
    """
    OpenAI SDK framework adapter.

    Creates tools compatible with OpenAI's function calling format.
    Works with openai.chat.completions.create(tools=[...]).

    Example:
        >>> adapter = OpenAIAdapter()
        >>> tools = adapter.create_all_tools(policy_wallet)
        >>> handlers = adapter.create_tool_handlers(policy_wallet)
        >>>
        >>> # Use with OpenAI
        >>> response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Send 0.1 ETH to 0x..."}],
        ...     tools=tools,
        ... )
        >>>
        >>> # Handle tool calls
        >>> for tool_call in response.choices[0].message.tool_calls or []:
        ...     result = adapter.handle_tool_call(
        ...         tool_call.function.name,
        ...         json.loads(tool_call.function.arguments),
        ...         policy_wallet
        ...     )
    """

    def create_transaction_tool(self, policy_wallet: PolicyWallet) -> Dict[str, Any]:
        """
        Create an OpenAI tool schema for sending transactions.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            OpenAI tool schema dictionary
        """
        return {
            "type": "function",
            "function": {
                "name": "send_transaction",
                "description": "Send a blockchain transaction. Policy validation is applied automatically to ensure the transaction is safe.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient Ethereum address (0x...)",
                        },
                        "value": {
                            "type": "string",
                            "description": "Amount to send in ETH (e.g., '0.1' for 0.1 ETH). Defaults to '0'.",
                        },
                        "data": {
                            "type": "string",
                            "description": "Transaction calldata as hex string. Defaults to '0x'.",
                        },
                    },
                    "required": ["to"],
                },
            },
        }

    def create_balance_tool(self, policy_wallet: PolicyWallet) -> Dict[str, Any]:
        """
        Create an OpenAI tool schema for checking balance.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            OpenAI tool schema dictionary
        """
        return {
            "type": "function",
            "function": {
                "name": "get_wallet_balance",
                "description": "Get the wallet's current native token balance and address.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }

    def create_wallet_info_tool(self, policy_wallet: PolicyWallet) -> Dict[str, Any]:
        """
        Create an OpenAI tool schema for getting wallet info.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            OpenAI tool schema dictionary
        """
        return {
            "type": "function",
            "function": {
                "name": "get_wallet_info",
                "description": "Get wallet information including address, network, and policy configuration.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }

    def create_validate_tool(self, policy_wallet: PolicyWallet) -> Dict[str, Any]:
        """
        Create an OpenAI tool schema for validating transactions without sending.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            OpenAI tool schema dictionary
        """
        return {
            "type": "function",
            "function": {
                "name": "validate_transaction",
                "description": "Validate a transaction against policies without sending it. Use this to check if a transaction would be allowed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient Ethereum address (0x...)",
                        },
                        "value": {
                            "type": "string",
                            "description": "Amount in ETH (e.g., '0.1'). Defaults to '0'.",
                        },
                        "data": {
                            "type": "string",
                            "description": "Transaction calldata as hex string. Defaults to '0x'.",
                        },
                    },
                    "required": ["to"],
                },
            },
        }

    def create_all_tools(self, policy_wallet: PolicyWallet) -> List[Dict[str, Any]]:
        """
        Create all available OpenAI tools.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            List of OpenAI tool schema dictionaries
        """
        return [
            self.create_transaction_tool(policy_wallet),
            self.create_balance_tool(policy_wallet),
            self.create_wallet_info_tool(policy_wallet),
            self.create_validate_tool(policy_wallet),
        ]

    def create_tool_handlers(
        self, policy_wallet: PolicyWallet
    ) -> Dict[str, Callable[[Dict[str, Any]], str]]:
        """
        Create handler functions for all tools.

        Args:
            policy_wallet: PolicyWallet instance

        Returns:
            Dictionary mapping function names to handler callables
        """
        return {
            "send_transaction": lambda args: self._handle_send_transaction(
                policy_wallet, args
            ),
            "get_wallet_balance": lambda args: self._handle_get_balance(
                policy_wallet, args
            ),
            "get_wallet_info": lambda args: self._handle_get_wallet_info(
                policy_wallet, args
            ),
            "validate_transaction": lambda args: self._handle_validate_transaction(
                policy_wallet, args
            ),
        }

    def handle_tool_call(
        self,
        name: str,
        arguments: Dict[str, Any],
        policy_wallet: PolicyWallet,
    ) -> str:
        """
        Handle a tool call from OpenAI response.

        Args:
            name: Function name from tool call
            arguments: Parsed arguments dictionary
            policy_wallet: PolicyWallet instance

        Returns:
            Result string to return to OpenAI

        Example:
            >>> for tool_call in response.choices[0].message.tool_calls or []:
            ...     result = adapter.handle_tool_call(
            ...         tool_call.function.name,
            ...         json.loads(tool_call.function.arguments),
            ...         policy_wallet
            ...     )
        """
        handlers = self.create_tool_handlers(policy_wallet)

        if name not in handlers:
            return f"Error: Unknown function '{name}'"

        return handlers[name](arguments)

    def process_tool_calls(
        self,
        response: Any,
        policy_wallet: PolicyWallet,
    ) -> List[Dict[str, Any]]:
        """
        Process all tool calls from an OpenAI response.

        This is a convenience method for handling the complete tool call flow.

        Args:
            response: OpenAI ChatCompletion response
            policy_wallet: PolicyWallet instance

        Returns:
            List of tool call results ready for the next API call

        Example:
            >>> response = client.chat.completions.create(...)
            >>> tool_results = adapter.process_tool_calls(response, policy_wallet)
            >>> # Add results to messages for follow-up
            >>> messages.append(response.choices[0].message)
            >>> messages.extend(tool_results)
        """
        results = []
        message = response.choices[0].message

        if not message.tool_calls:
            return results

        for tool_call in message.tool_calls:
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}

            result = self.handle_tool_call(
                tool_call.function.name,
                arguments,
                policy_wallet,
            )

            results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

        return results

    # Private handler methods

    def _handle_send_transaction(
        self,
        policy_wallet: PolicyWallet,
        args: Dict[str, Any],
    ) -> str:
        """Handle send_transaction tool call."""
        try:
            to = args.get("to", "")
            value = args.get("value", "0")
            data = args.get("data", "0x")

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
        except ValueError as e:
            return f"Invalid input: {str(e)}"
        except Exception as e:
            return f"Transaction failed: {str(e)}"

    def _handle_get_balance(
        self,
        policy_wallet: PolicyWallet,
        args: Dict[str, Any],
    ) -> str:
        """Handle get_wallet_balance tool call."""
        try:
            balance_wei = policy_wallet.get_balance()
            balance_eth = Web3.from_wei(balance_wei, "ether")
            address = policy_wallet.get_address()
            network = policy_wallet.get_network()

            return f"Address: {address}\nBalance: {balance_eth} ETH\nNetwork: {network}"

        except Exception as e:
            return f"Failed to get balance: {str(e)}"

    def _handle_get_wallet_info(
        self,
        policy_wallet: PolicyWallet,
        args: Dict[str, Any],
    ) -> str:
        """Handle get_wallet_info tool call."""
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

    def _handle_validate_transaction(
        self,
        policy_wallet: PolicyWallet,
        args: Dict[str, Any],
    ) -> str:
        """Handle validate_transaction tool call."""
        try:
            to = args.get("to", "")
            value = args.get("value", "0")
            data = args.get("data", "0x")

            # Convert ETH to wei
            value_wei = Web3.to_wei(float(value), "ether")

            passed, reason = policy_wallet.validate_transaction({
                "to": to,
                "value": value_wei,
                "data": data,
            })

            if passed:
                return f"Transaction would be ALLOWED: {reason}"
            else:
                return f"Transaction would be BLOCKED: {reason}"

        except ValueError as e:
            return f"Invalid input: {str(e)}"
        except Exception as e:
            return f"Validation failed: {str(e)}"