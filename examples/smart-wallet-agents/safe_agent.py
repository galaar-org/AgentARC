"""
Safe Multisig Wallet Agent Example

Demonstrates using AgentARC with a Gnosis Safe multisig wallet.

The agent signs transactions with a single signer key. If the Safe's
threshold is 1, transactions execute immediately. If threshold > 1,
the result contains the Safe transaction hash for co-signing.

Key differences vs EOA:
  - wallet.get_address()        → Safe contract address
  - wallet.get_owner_address()  → signer EOA address
  - wallet.get_threshold()      → number of required signatures
  - wallet.get_owners()         → list of Safe owner addresses

Usage:
    cp .env.example .env
    # Fill in SAFE_ADDRESS, SIGNER_PRIVATE_KEY, RPC_URL, OPENAI_API_KEY
    python safe_agent.py

Environment variables:
    SAFE_ADDRESS        - Address of the deployed Safe contract
    SIGNER_PRIVATE_KEY  - Private key of a Safe owner/signer
    RPC_URL             - JSON-RPC URL (e.g. Base Sepolia)
    OPENAI_API_KEY      - OpenAI API key for the agent
"""

import os
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
from agentarc import WalletFactory, PolicyWallet, OpenAIAdapter

# ============================================================
# 1. Create Safe multisig wallet
# ============================================================
wallet = WalletFactory.from_safe(
    safe_address=os.environ["SAFE_ADDRESS"],
    signer_key=os.environ["SIGNER_PRIVATE_KEY"],
    rpc_url=os.environ["RPC_URL"],
    auto_execute=True,   # Execute immediately if threshold == 1
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
print("Safe Multisig Wallet Agent")
print("=" * 50)
print(f"Safe Address: {policy_wallet.get_address()}")
print(f"Signer EOA:   {wallet.get_owner_address()}")
print(f"Threshold:    {wallet.get_threshold()}")
print(f"Owners:       {wallet.get_owners()}")
print(f"Policies:     {len(policy_wallet.get_config().get_enabled_policies())} active")
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
            "You are a blockchain agent managing a Gnosis Safe multisig wallet. "
            "Always check the balance and threshold before proposing transactions. "
            "If the threshold is greater than 1, explain that the transaction "
            "needs additional signatures from other owners."
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
