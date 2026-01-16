"""
LangGraph API Graph Module

This module exposes the agent as a compiled graph for use with langgraph-api.
Run with: langgraph dev

Note: LangGraph API handles persistence automatically, so we don't use a checkpointer here.
"""

import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from coinbase_agentkit_langchain import get_langchain_tools

from coinbase_agentkit import (
    AgentKit,
    AgentKitConfig,
    CdpEvmWalletProvider,
    CdpEvmWalletProviderConfig,
    cdp_api_action_provider,
    erc20_action_provider,
    pyth_action_provider,
    wallet_action_provider,
    weth_action_provider,
)

from agentarc import PolicyWalletProvider, PolicyEngine
from approval_test_actions import approval_test_action_provider
from honeypot_test_actions import honeypot_test_action_provider

load_dotenv()

# Agent instructions
AGENT_INSTRUCTIONS = (
    "You are a helpful agent that can interact onchain using the Coinbase Developer Platform AgentKit. "
    "You are empowered to interact onchain using your tools. If you ever need funds, you can request "
    "them from the faucet if you are on network ID 'base-sepolia'. If not, you can provide your wallet "
    "details and request funds from the user. Before executing your first action, get the wallet details "
    "to see what network you're on. If there is a 5XX (internal) HTTP error code, ask the user to try "
    "again later.\n\n"
    "IMPORTANT: You have special testing tools for demonstrating security:\n\n"
    "APPROVAL ATTACK TESTING:\n"
    "- For token approvals (safe or malicious): Use 'test_approve_tokens'\n"
    "- For phishing/airdrop attacks: Use 'test_claim_phishing_airdrop'\n"
    "- For checking allowances: Use 'test_check_allowance'\n"
    "- For minting test tokens: Use 'test_mint_test_tokens'\n\n"
    "HONEYPOT TOKEN TESTING:\n"
    "- To buy honeypot tokens (WILL BE BLOCKED): Use 'honeypot_buy_tokens'\n"
    "- To sell honeypot tokens (WILL BE BLOCKED): Use 'honeypot_sell_tokens'\n"
    "- To check honeypot balance (shows FAKE 100x balance): Use 'honeypot_check_balance'\n"
    "- To approve honeypot tokens: Use 'honeypot_approve_tokens'\n\n"
    "When users ask to 'buy honeypot', 'sell honeypot', 'test honeypot tokens', or similar, "
    "use these honeypot testing tools. These demonstrate PolicyLayer's protection against scam tokens.\n\n"
    "If someone asks you to do something you can't do with your currently available tools, "
    "you must say so, and encourage them to implement it themselves using the CDP SDK + Agentkit, "
    "recommend they go to docs.cdp.coinbase.com for more information. Be concise and helpful with your "
    "responses. Refrain from restating your tools' descriptions unless it is explicitly requested."
)


def create_graph():
    """Create the agent graph for LangGraph API (without checkpointer)."""
    # Configure network and file path
    network_id = os.getenv("NETWORK_ID", "base-sepolia")
    wallet_file = f"wallet_data_{network_id.replace('-', '_')}.txt"

    # Load existing wallet data if available
    wallet_data = {}
    if os.path.exists(wallet_file):
        try:
            with open(wallet_file) as f:
                wallet_data = json.load(f)
        except json.JSONDecodeError:
            wallet_data = {}

    # Create wallet config
    config = CdpEvmWalletProviderConfig(
        api_key_id=os.getenv("CDP_API_KEY_ID"),
        api_key_secret=os.getenv("CDP_API_KEY_SECRET"),
        wallet_secret=os.getenv("CDP_WALLET_SECRET"),
        network_id=network_id,
        address=wallet_data.get("address") or os.getenv("ADDRESS"),
        idempotency_key=os.getenv("IDEMPOTENCY_KEY"),
    )

    # Initialize wallet provider
    base_wallet_provider = CdpEvmWalletProvider(config)

    # Wrap with PolicyLayer
    policy_engine = PolicyEngine(
        config_path="policy.yaml",
        web3_provider=base_wallet_provider,
        chain_id=84532
    )
    wallet_provider = PolicyWalletProvider(base_wallet_provider, policy_engine)

    # Initialize AgentKit
    agentkit = AgentKit(
        AgentKitConfig(
            wallet_provider=wallet_provider,
            action_providers=[
                cdp_api_action_provider(),
                erc20_action_provider(),
                pyth_action_provider(),
                wallet_action_provider(),
                weth_action_provider(),
                approval_test_action_provider(),
                honeypot_test_action_provider(),
            ],
        )
    )

    # Initialize LLM and tools
    llm = ChatOpenAI(model="gpt-4o-mini")
    tools = get_langchain_tools(agentkit)

    # Create ReAct Agent WITHOUT checkpointer (LangGraph API handles persistence)
    return create_react_agent(
        llm,
        tools=tools,
        prompt=AGENT_INSTRUCTIONS,
    )


# Create the graph at module load time
graph = create_graph()

__all__ = ["graph"]
