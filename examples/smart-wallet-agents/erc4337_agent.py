"""
ERC-4337 Smart Wallet Agent Example

Demonstrates using AgentARC with an ERC-4337 Account Abstraction smart wallet.

The agent uses a smart account (counterfactually derived from the owner EOA)
and submits transactions as UserOperations through a bundler.

Key differences vs EOA:
  - wallet.get_address()       → smart account address
  - wallet.get_owner_address() → owner EOA address
  - wallet.is_deployed()       → whether smart account is deployed
  - Transactions go through bundler → EntryPoint → SmartAccount

Usage:
    cp .env.example .env
    # Fill in OWNER_PRIVATE_KEY, BUNDLER_URL, RPC_URL, OPENAI_API_KEY
    python erc4337_agent.py

Environment variables:
    OWNER_PRIVATE_KEY  - Private key of the EOA that controls the smart account
    BUNDLER_URL        - ERC-4337 bundler URL (e.g. Pimlico, Alchemy)
    RPC_URL            - Standard JSON-RPC URL (e.g. Base Sepolia)
    OPENAI_API_KEY     - OpenAI API key for the agent
"""

import os
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
from agentarc import WalletFactory, PolicyWallet, OpenAIAdapter

# ============================================================
# 1. Create ERC-4337 smart wallet
# ============================================================
wallet = WalletFactory.from_erc4337(
    owner_key=os.environ["OWNER_PRIVATE_KEY"],
    bundler_url=os.environ["BUNDLER_URL"],
    rpc_url=os.environ["RPC_URL"],
    # chain_id=84532,  # Optional: Base Sepolia (auto-detected if omitted)
    # account_address="0x...",  # Optional: skip counterfactual derivation
)

# ============================================================
# 2. Wrap with off-chain policy enforcement
# ============================================================
policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")

# ============================================================
# 3. Create OpenAI tools (identical to EOA — no changes needed)
# ============================================================
adapter = OpenAIAdapter()
tools = adapter.create_all_tools(policy_wallet)

print("=" * 50)
print("ERC-4337 Smart Wallet Agent")
print("=" * 50)
print(f"Smart Account: {policy_wallet.get_address()}")
print(f"Owner EOA:     {wallet.get_owner_address()}")
print(f"Deployed:      {wallet.is_deployed()}")
print(f"Policies:      {len(policy_wallet.get_config().get_enabled_policies())} active")
print("=" * 50)
print("Type 'quit' to exit\n")

# ============================================================
# 4. Chat loop
# ============================================================
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
messages = [
    {
        "role": "system",
        "content": (
            "You are a blockchain agent using an ERC-4337 smart wallet. "
            "Your transactions go through a bundler as UserOperations. "
            "Always check the balance before sending. "
            "Be explicit about the smart account address vs the owner EOA address."
        ),
    }
]

while True:
    user_input = input("You: ").strip()
    if not user_input:
        continue
    if user_input.lower() in ("quit", "exit"):
        print("Goodbye!")
        break

    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, tools=tools
    )

    assistant_message = response.choices[0].message
    while assistant_message.tool_calls:
        messages.append(assistant_message)
        tool_results = adapter.process_tool_calls(response, policy_wallet)
        messages.extend(tool_results)
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=tools
        )
        assistant_message = response.choices[0].message

    messages.append(assistant_message)
    print(f"\nAgent: {assistant_message.content}\n")
