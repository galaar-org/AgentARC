"""
Safe Multisig Wallet Agent with AgentARC Policy Enforcement

A chat agent that uses a Gnosis Safe multisig wallet instead of a
normal private key wallet. The agent signs transactions with one key,
and AgentARC validates them before execution. If the Safe threshold
is 1, transactions execute immediately. If threshold > 1, the signed
transaction hash is returned for co-signing by other owners.

What makes this different from a normal EOA agent:
  - Your wallet is a DEPLOYED SAFE CONTRACT (not just a private key)
  - Transactions require N-of-M signatures (threshold)
  - With threshold=1: executes immediately like a normal wallet
  - With threshold=2+: you propose a transaction, co-signers approve it
  - The Safe has its own address that holds funds (separate from your key)

Requirements:
    pip install openai agentarc web3

Environment Variables:
    OPENAI_API_KEY     - Your OpenAI API key
    SAFE_ADDRESS       - Address of your deployed Safe contract
    SIGNER_PRIVATE_KEY - Private key of one of the Safe owners
    RPC_URL            - Standard JSON-RPC URL (e.g. https://sepolia.base.org)

Usage:
    cp .env.example .env
    # Fill in your keys in .env
    python safe_agent.py

Deploy a Safe at:
    https://app.safe.global  (free, supports Base Sepolia and many networks)
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
# System prompt — tells the agent it manages a Safe multisig
# ============================================================
SYSTEM_PROMPT = """You are a helpful blockchain assistant managing a Gnosis Safe multisig wallet.

Your wallet setup:
- Safe Address: the multisig contract that holds funds (use get_wallet_info to see it)
- Signer EOA: your private key, one of the Safe owners
- Threshold: number of owner signatures required to execute a transaction

You have access to the following tools:
- send_transaction: Propose/execute a Safe transaction (after policy check)
- get_wallet_balance: Check the Safe contract balance
- get_wallet_info: Get Safe address, network, and policy status
- validate_transaction: Dry-run policy check without sending

IMPORTANT:
- Always check the Safe balance before proposing transactions
- The Safe address (not your signer key) is what holds and receives funds
- If threshold > 1, a sent transaction needs co-signatures from other owners
- All transactions are validated by AgentARC before being submitted
- If a transaction is blocked by policy, explain why clearly

Be helpful, concise, and always confirm transaction details before sending."""


def check_env():
    """Check that all required environment variables are set."""
    required = {
        "OPENAI_API_KEY": "Your OpenAI API key",
        "SAFE_ADDRESS": "Address of your deployed Safe contract",
        "SIGNER_PRIVATE_KEY": "Private key of one of the Safe owners",
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
        print("Deploy a Safe at https://app.safe.global if you don't have one.")
        sys.exit(1)


def initialize_agent():
    """
    Initialize the Safe multisig wallet and OpenAI tools.

    Steps:
      1. Create SafeAdapter from Safe address + signer key
      2. Read threshold and owners from the Safe contract
      3. Wrap with PolicyWallet for transaction validation
      4. Create OpenAI tools from the policy wallet
    """
    print("=" * 60)
    print("Safe Multisig Wallet Agent with AgentARC")
    print("=" * 60)

    # ----------------------------------------------------------
    # Step 1: Create the Safe wallet adapter
    # ----------------------------------------------------------
    # SafeAdapter connects to your existing Safe contract and:
    #   a) Reads threshold and owners from the contract
    #   b) Builds Safe transactions from normal tx dicts
    #   c) Signs with your signer key
    #   d) Executes immediately (threshold=1) or returns hash for co-signing
    print("\n[1/4] Connecting to Safe contract...")

    wallet = WalletFactory.from_safe(
        safe_address=os.environ["SAFE_ADDRESS"],
        signer_key=os.environ["SIGNER_PRIVATE_KEY"],
        rpc_url=os.environ["RPC_URL"],
        auto_execute=True,  # Execute immediately if threshold == 1
    )

    print(f"  Safe Address  : {wallet.get_address()}")       # contract that holds funds
    print(f"  Signer EOA    : {wallet.get_owner_address()}") # key that signs txs
    print(f"  Chain ID      : {wallet.get_chain_id()}")
    print(f"  Deployed      : {wallet.is_deployed()}")

    # ----------------------------------------------------------
    # Step 2: Read Safe contract state
    # ----------------------------------------------------------
    # Threshold tells us how many signatures are needed.
    # If threshold > 1, transactions won't execute immediately —
    # they'll need co-signatures from other owners.
    print("\n[2/4] Reading Safe configuration...")

    threshold = wallet.get_threshold()
    owners = wallet.get_owners()

    print(f"  Threshold     : {threshold} of {len(owners)} owners")
    print(f"  Owners        :")
    for owner in owners:
        is_signer = owner.lower() == wallet.get_owner_address().lower()
        marker = " <-- you" if is_signer else ""
        print(f"    {owner}{marker}")

    if threshold > 1:
        print(f"\n  Note: This Safe requires {threshold} signatures.")
        print("  Transactions will be proposed but won't execute until")
        print(f"  {threshold - 1} more owner(s) co-sign.")

    # ----------------------------------------------------------
    # Step 3: Wrap with AgentARC policy enforcement
    # ----------------------------------------------------------
    # PolicyWallet sits in front of the SafeAdapter.
    # Every send_transaction() call goes through the 4-stage pipeline:
    #   1. Intent Analysis  — parse the calldata
    #   2. Policy Check     — spending limits, denylist, gas limits
    #   3. Simulation       — test execution via Tenderly (if configured)
    #   4. LLM Analysis     — AI threat detection (if enabled)
    # Only if all stages pass does the Safe transaction get signed.
    print("\n[3/4] Applying policy enforcement...")

    policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")
    active = policy_wallet.get_config().get_enabled_policies()
    print(f"  Policies active: {len(active)}")
    for p in active:
        print(f"    - {p.get('type', 'unknown')}")

    # ----------------------------------------------------------
    # Step 4: Create OpenAI tools
    # ----------------------------------------------------------
    # OpenAIAdapter wraps the policy wallet into OpenAI function-calling
    # tool schemas. Identical API to EOA and ERC-4337 — no framework changes.
    print("\n[4/4] Creating OpenAI tools...")

    adapter = OpenAIAdapter()
    tools = adapter.create_all_tools(policy_wallet)
    print(f"  Tools available: {[t['function']['name'] for t in tools]}")

    print("\nAgent ready!")
    print("=" * 60)

    return policy_wallet, adapter, tools


def chat_loop(client, policy_wallet, adapter, tools):
    """Run the interactive chat loop."""
    print("\nChat with the agent (type 'quit' to exit):")
    print("Try: 'What is the Safe address and threshold?'")
    print("Try: 'What is the Safe balance?'")
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

    # Show initial Safe balance
    try:
        balance_wei = policy_wallet.get_balance()
        balance_eth = Web3.from_wei(balance_wei, "ether")
        print(f"\nSafe Balance: {balance_eth} ETH")
        if balance_eth == 0:
            print(f"  Tip: Fund your Safe at {policy_wallet.get_address()}")
    except Exception as e:
        print(f"\nCould not fetch balance: {e}")

    chat_loop(client, policy_wallet, adapter, tools)


if __name__ == "__main__":
    main()
