"""
LangChain Chat Agent with AgentARC Policy Enforcement

A simple chat agent that can perform blockchain transactions with
policy validation using LangChain and a private key wallet.

Requirements:
    pip install langchain-openai langgraph agentarc web3

Environment Variables:
    OPENAI_API_KEY - Your OpenAI API key
    PRIVATE_KEY - Your Ethereum private key (with 0x prefix)
    RPC_URL - Your RPC endpoint (e.g., BuildBear, Alchemy, Infura)

Usage:
    export OPENAI_API_KEY="sk-..."
    export PRIVATE_KEY="0x..."
    export RPC_URL="https://..."
    python langchain_chat_agent.py
"""

import os
import sys
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from agentarc import WalletFactory, PolicyWallet, PolicyConfig
from agentarc.frameworks import LangChainAdapter

# Load environment variables
load_dotenv()

# Agent system prompt
AGENT_PROMPT = """You are a helpful blockchain assistant that can perform on-chain transactions.

You have access to the following tools:
- send_transaction: Send ETH or call contracts with policy validation
- get_wallet_balance: Check your wallet balance
- get_wallet_info: Get wallet address, network, and policy status

IMPORTANT:
- Always check your wallet balance before sending transactions
- All transactions are validated against security policies
- If a transaction is blocked, explain why to the user

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


def initialize_agent():
    """Initialize the LangChain agent with AgentARC policy wallet."""
    # Get credentials from environment
    private_key = os.getenv("PRIVATE_KEY")
    rpc_url = os.getenv("RPC_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not private_key:
        print("Error: PRIVATE_KEY environment variable not set")
        sys.exit(1)
    if not rpc_url:
        print("Error: RPC_URL environment variable not set")
        sys.exit(1)
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    print("=" * 60)
    print("LangChain Chat Agent with AgentARC Policy Enforcement")
    print("=" * 60)

    # Create wallet from private key
    print("\n[1/4] Creating wallet...")
    wallet = WalletFactory.from_private_key(private_key, rpc_url)
    print(f"  Address: {wallet.get_address()}")
    print(f"  Chain ID: {wallet.get_chain_id()}")

    # Wrap with policy enforcement
    print("\n[2/4] Applying policy enforcement...")
    policy_config = PolicyConfig(create_policy_config())
    policy_wallet = PolicyWallet(wallet, config=policy_config)
    print(f"  Policies enabled: {len(policy_config.policies)}")

    # Create LangChain tools
    print("\n[3/4] Creating LangChain tools...")
    adapter = LangChainAdapter()
    tools = adapter.create_all_tools(policy_wallet)
    print(f"  Tools: {[t.name for t in tools]}")

    # Create agent
    print("\n[4/4] Initializing LangChain agent...")
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)
    memory = MemorySaver()

    agent = create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        prompt=AGENT_PROMPT,
    )

    print("\nAgent ready!")
    print("=" * 60)

    return agent, policy_wallet


def chat_loop(agent):
    """Run the interactive chat loop."""
    print("\nChat with the agent (type 'quit' to exit):\n")

    config = {"configurable": {"thread_id": "main"}}

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            # Stream agent response
            print("Agent: ", end="", flush=True)

            response_text = ""
            for event in agent.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config,
            ):
                if "agent" in event:
                    for message in event["agent"]["messages"]:
                        if hasattr(message, "content") and message.content:
                            response_text = message.content

            print(response_text)
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    """Main entry point."""
    agent, wallet = initialize_agent()

    # Show initial balance
    try:
        from web3 import Web3
        balance_wei = wallet.get_balance()
        balance_eth = Web3.from_wei(balance_wei, "ether")
        print(f"\nWallet Balance: {balance_eth} ETH")
    except Exception as e:
        print(f"\nCould not fetch balance: {e}")

    chat_loop(agent)


if __name__ == "__main__":
    main()
