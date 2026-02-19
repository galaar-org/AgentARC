"""
OpenAI SDK Chat Agent with AgentARC Policy Enforcement

A simple chat agent that can perform blockchain transactions with
policy validation using the OpenAI SDK and a private key wallet.

Requirements:
    pip install openai agentarc web3

Environment Variables:
    OPENAI_API_KEY - Your OpenAI API key
    PRIVATE_KEY - Your Ethereum private key (with 0x prefix)
    RPC_URL - Your RPC endpoint (e.g., BuildBear, Alchemy, Infura)

Usage:
    export OPENAI_API_KEY="sk-..."
    export PRIVATE_KEY="0x..."
    export RPC_URL="https://..."
    python openai_chat_agent.py
"""

import os
import sys
import json
from dotenv import load_dotenv

from openai import OpenAI

from agentarc import WalletFactory, PolicyWallet, PolicyConfig
from agentarc.frameworks import OpenAIAdapter

# Load environment variables
load_dotenv()

# System prompt for the agent
SYSTEM_PROMPT = """You are a helpful blockchain assistant that can perform on-chain transactions.

You have access to the following tools:
- send_transaction: Send ETH or call contracts with policy validation
- get_wallet_balance: Check your wallet balance
- get_wallet_info: Get wallet address, network, and policy status
- validate_transaction: Check if a transaction would be allowed

IMPORTANT:
- Always check your wallet balance before sending transactions
- All transactions are validated against security policies
- If a transaction is blocked, explain why to the user
- Use validate_transaction to pre-check before sending

Be helpful, concise, and always confirm transaction details before sending."""


def create_policy_config():
    """Create a basic policy configuration."""
    return {
        "version": "2.0",
        "enabled": True,
        "logging": {"level": "info"},
        "policies": [
            {
                "type": "eth_value_limit",
                "enabled": True,
                "max_value_wei": "1000000000000000000",  # 1 ETH max
            },
            {
                "type": "address_denylist",
                "enabled": True,
                "denied_addresses": [],  # Add addresses to block
            },
        ],
        "simulation": {
            "enabled": True,
            "fail_on_revert": True,
        },
    }


def initialize_wallet_and_tools():
    """Initialize wallet and OpenAI tools."""
    # Get credentials from environment
    private_key = os.getenv("PRIVATE_KEY")
    rpc_url = os.getenv("RPC_URL")

    if not private_key:
        print("Error: PRIVATE_KEY environment variable not set")
        sys.exit(1)
    if not rpc_url:
        print("Error: RPC_URL environment variable not set")
        sys.exit(1)

    print("=" * 60)
    print("OpenAI SDK Chat Agent with AgentARC Policy Enforcement")
    print("=" * 60)

    # Create wallet from private key
    print("\n[1/3] Creating wallet...")
    wallet = WalletFactory.from_private_key(private_key, rpc_url)
    print(f"  Address: {wallet.get_address()}")
    print(f"  Chain ID: {wallet.get_chain_id()}")

    # Wrap with policy enforcement
    print("\n[2/3] Applying policy enforcement...")
    policy_config = PolicyConfig(create_policy_config())
    policy_wallet = PolicyWallet(wallet, config=policy_config)
    print(f"  Policies enabled: {len(policy_config.policies)}")

    # Create OpenAI tools
    print("\n[3/3] Creating OpenAI tools...")
    adapter = OpenAIAdapter()
    tools = adapter.create_all_tools(policy_wallet)
    print(f"  Tools: {[t['function']['name'] for t in tools]}")

    print("\nAgent ready!")
    print("=" * 60)

    return policy_wallet, adapter, tools


def chat_loop(client, policy_wallet, adapter, tools):
    """Run the interactive chat loop."""
    print("\nChat with the agent (type 'quit' to exit):\n")

    # Conversation history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            # Add user message
            messages.append({"role": "user", "content": user_input})

            # Get completion with tools
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
            )

            assistant_message = response.choices[0].message

            # Handle tool calls if any
            while assistant_message.tool_calls:
                # Add assistant message with tool calls
                messages.append(assistant_message)

                # Process each tool call
                tool_results = adapter.process_tool_calls(response, policy_wallet)

                # Print tool execution info
                for tool_call in assistant_message.tool_calls:
                    print(f"  [Tool: {tool_call.function.name}]")

                # Add tool results to messages
                messages.extend(tool_results)

                # Get next response
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=tools,
                )

                assistant_message = response.choices[0].message

            # Add final assistant message
            messages.append(assistant_message)

            # Print response
            print(f"Agent: {assistant_message.content}")
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    """Main entry point."""
    # Check OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    # Initialize
    policy_wallet, adapter, tools = initialize_wallet_and_tools()

    # Create OpenAI client
    client = OpenAI(api_key=openai_api_key)

    # Show initial balance
    try:
        from web3 import Web3
        balance_wei = policy_wallet.get_balance()
        balance_eth = Web3.from_wei(balance_wei, "ether")
        print(f"\nWallet Balance: {balance_eth} ETH")
    except Exception as e:
        print(f"\nCould not fetch balance: {e}")

    # Start chat
    chat_loop(client, policy_wallet, adapter, tools)


if __name__ == "__main__":
    main()
