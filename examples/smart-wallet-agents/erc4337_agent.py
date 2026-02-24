"""
ERC-4337 Smart Wallet Agent with AgentARC Policy Enforcement

A chat agent that uses an ERC-4337 smart contract wallet instead of a
normal private key wallet. Transactions are submitted as UserOperations
through a bundler service, with full AgentARC policy validation before
anything hits the chain.

What makes this different from a normal EOA agent:
  - Your wallet is a SMART CONTRACT (not just a private key)
  - Transactions go through a BUNDLER (e.g. Pimlico) instead of a plain RPC
  - The smart account is COUNTERFACTUALLY deployed — it has a fixed address
    before the contract is even deployed on-chain
  - On your first transaction the contract is deployed automatically

Requirements:
    pip install openai agentarc web3 requests

Environment Variables:
    OPENAI_API_KEY     - Your OpenAI API key
    OWNER_PRIVATE_KEY  - Private key of the EOA that controls the smart account
    BUNDLER_URL        - ERC-4337 bundler RPC URL (get one free at pimlico.io)
    RPC_URL            - Standard JSON-RPC URL (e.g. https://sepolia.base.org)

Usage:
    cp .env.example .env
    # Fill in your keys in .env
    python erc4337_agent.py

Get a free bundler at:
    https://pimlico.io  (supports Base Sepolia)
    https://alchemy.com (supports many networks)
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3

from openai import OpenAI

from agentarc import WalletFactory, PolicyWallet, PolicyConfig
from agentarc.frameworks import OpenAIAdapter

# Load environment variables from .env file
load_dotenv()

# ============================================================
# System prompt — tells the agent it has a smart wallet
# ============================================================
SYSTEM_PROMPT = """You are a helpful blockchain assistant using an ERC-4337 smart wallet.

Your wallet setup:
- Smart Account: the contract address that holds funds (use get_wallet_info to see it)
- Owner EOA: the private key that signs transactions (different from smart account)
- Transactions go through a bundler as UserOperations before hitting the chain

You have access to the following tools:
- send_transaction: Send ETH or call contracts (goes through bundler after policy check)
- get_wallet_balance: Check the smart account balance
- get_wallet_info: Get smart account address, network, and policy status
- validate_transaction: Dry-run policy check without sending

IMPORTANT:
- Always check your balance before sending transactions
- The smart account address (not your owner EOA) is what receives funds
- All transactions are validated by AgentARC before being submitted to the bundler
- If a transaction is blocked by policy, explain why clearly

Be helpful, concise, and always confirm transaction details before sending."""


def check_env():
    """Check that all required environment variables are set."""
    required = {
        "OPENAI_API_KEY": "Your OpenAI API key",
        "OWNER_PRIVATE_KEY": "Private key of the EOA that controls the smart account",
        "BUNDLER_URL": "ERC-4337 bundler URL (get one at pimlico.io)",
        "RPC_URL": "Standard JSON-RPC URL (e.g. https://sepolia.base.org)",
    }
    missing = []
    for var, description in required.items():
        if not os.getenv(var):
            missing.append(f"  {var} — {description}")

    if missing:
        print("Error: Missing required environment variables:\n")
        print("\n".join(missing))
        print("\nCopy .env.example to .env and fill in your values.")
        sys.exit(1)


def initialize_agent():
    """
    Initialize the ERC-4337 smart wallet and OpenAI tools.

    Steps:
      1. Create ERC4337Adapter from owner key + bundler URL
      2. Wrap with PolicyWallet for transaction validation
      3. Create OpenAI tools from the policy wallet
    """
    print("=" * 60)
    print("ERC-4337 Smart Wallet Agent with AgentARC")
    print("=" * 60)

    # ----------------------------------------------------------
    # Step 1: Create the ERC-4337 smart wallet
    # ----------------------------------------------------------
    # The ERC4337Adapter does three things:
    #   a) Derives your smart account address from the factory
    #      (counterfactually — even before the contract is deployed)
    #   b) Builds UserOperations from normal tx dicts
    #   c) Submits them to the bundler
    print("\n[1/3] Creating ERC-4337 smart wallet...")

    wallet = WalletFactory.from_erc4337(
        owner_key=os.environ["OWNER_PRIVATE_KEY"],
        bundler_url=os.environ["BUNDLER_URL"],
        rpc_url=os.environ["RPC_URL"],
    )

    # Two addresses to be aware of:
    print(f"  Smart Account : {wallet.get_address()}")       # contract that holds funds
    print(f"  Owner EOA     : {wallet.get_owner_address()}") # key that signs UserOps
    print(f"  Chain ID      : {wallet.get_chain_id()}")
    print(f"  Deployed      : {wallet.is_deployed()}")

    if not wallet.is_deployed():
        print("\n  Note: Smart account not yet deployed.")
        print("  It will be deployed automatically on your first transaction.")
        print(f"  Fund this address first: {wallet.get_address()}")

    # ----------------------------------------------------------
    # Step 2: Wrap with AgentARC policy enforcement
    # ----------------------------------------------------------
    # PolicyWallet sits in front of the ERC4337Adapter.
    # Every send_transaction() call goes through the 4-stage pipeline:
    #   1. Intent Analysis  — parse the calldata
    #   2. Policy Check     — spending limits, denylist, gas limits
    #   3. Simulation       — test execution via Tenderly (if configured)
    #   4. LLM Analysis     — AI threat detection (if enabled)
    # Only if all stages pass does the UserOperation reach the bundler.
    print("\n[2/3] Applying policy enforcement...")

    policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")
    active = policy_wallet.get_config().get_enabled_policies()
    print(f"  Policies active: {len(active)}")
    for p in active:
        print(f"    - {p.get('type', 'unknown')}")

    # ----------------------------------------------------------
    # Step 3: Create OpenAI tools
    # ----------------------------------------------------------
    # OpenAIAdapter wraps the policy wallet into OpenAI function-calling
    # tool schemas. The agent can call:
    #   send_transaction, get_wallet_balance, get_wallet_info, validate_transaction
    print("\n[3/3] Creating OpenAI tools...")

    adapter = OpenAIAdapter()
    tools = adapter.create_all_tools(policy_wallet)
    print(f"  Tools available: {[t['function']['name'] for t in tools]}")

    print("\nAgent ready!")
    print("=" * 60)

    return policy_wallet, adapter, tools


def chat_loop(client, policy_wallet, adapter, tools):
    """Run the interactive chat loop."""
    print("\nChat with the agent (type 'quit' to exit):")
    print("Try: 'What is my smart account address?'")
    print("Try: 'What is my balance?'")
    print("Try: 'Validate a transaction of 0.001 ETH to 0x...'")
    print()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            messages.append({"role": "user", "content": user_input})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
            )

            assistant_message = response.choices[0].message

            # Handle tool calls — loop until agent gives a plain text response
            while assistant_message.tool_calls:
                messages.append(assistant_message)

                for tool_call in assistant_message.tool_calls:
                    print(f"  [Tool: {tool_call.function.name}]")

                tool_results = adapter.process_tool_calls(response, policy_wallet)
                messages.extend(tool_results)

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=tools,
                )
                assistant_message = response.choices[0].message

            messages.append(assistant_message)
            print(f"Agent: {assistant_message.content}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    """Main entry point."""
    check_env()

    policy_wallet, adapter, tools = initialize_agent()

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # Show initial balance
    try:
        balance_wei = policy_wallet.get_balance()
        balance_eth = Web3.from_wei(balance_wei, "ether")
        print(f"\nSmart Account Balance: {balance_eth} ETH")
        if balance_eth == 0:
            print(f"  Tip: Fund your smart account at {policy_wallet.get_address()}")
            print("  You need ETH there to pay for transactions.")
    except Exception as e:
        print(f"\nCould not fetch balance: {e}")

    chat_loop(client, policy_wallet, adapter, tools)


if __name__ == "__main__":
    main()
