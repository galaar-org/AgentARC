#!/usr/bin/env python3
"""Demo Runner - Scripted demonstration of honeypot protection

This script runs a demo showing:
1. Normal portfolio rebalancing (allowed)
2. Honeypot token purchase attempt (blocked)
3. Excessive amount attempt (blocked by policy)
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../..'))

from coinbase_agentkit import CdpEvmWalletProvider, CdpEvmWalletProviderConfig

# Import PolicyLayer components
from agentguard import PolicyWalletProvider, PolicyEngine

from core.agent import AutonomousPortfolioAgent
from config.portfolio_config import TARGET_ALLOCATION, TOKENS


async def run_demo():
    """Run scripted demo scenarios"""

    load_dotenv()

    print("""
╔══════════════════════════════════════════════════════════════╗
║  AUTONOMOUS PORTFOLIO MANAGER DEMO                           ║
║  with Honeypot Protection by PolicyLayer                     ║
╚══════════════════════════════════════════════════════════════╝

This demo will show:
✅ Scenario 1: Normal portfolio rebalancing (ETH ↔ USDC swap)
⚠️  Scenario 2: Honeypot token attack (BLOCKED by PolicyLayer)
⚠️  Scenario 3: Excessive amount attack (BLOCKED by policy limits)

The agent will run autonomously and make decisions based on:
- Current portfolio allocation
- Target allocation: {TARGET_ALLOCATION}
- Protection rules in config/policy.yaml

Press Enter to start the demo...
""")

    input()

    # Initialize CDP wallet
    cdp_wallet = CdpEvmWalletProvider(CdpEvmWalletProviderConfig(
        api_key_id=os.getenv("CDP_API_KEY_ID"),
        api_key_secret=os.getenv("CDP_API_KEY_SECRET"),
        wallet_secret=os.getenv("CDP_WALLET_SECRET"),
        network_id="base-sepolia",
    ))

    # Wrap with PolicyLayer
    policy_config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "config/policy.yaml"
    )

    policy_engine = PolicyEngine(
        config_path=policy_config_path,
        web3_provider=cdp_wallet,
        chain_id=84532
    )

    protected_wallet = PolicyWalletProvider(
        base_provider=cdp_wallet,
        policy_engine=policy_engine
    )

    # Create agent
    agent = AutonomousPortfolioAgent(
        wallet_provider=protected_wallet,
        target_allocation=TARGET_ALLOCATION,
        token_addresses=TOKENS,
        rebalance_interval=60,
        policy_engine=policy_engine
    )

    print("\n" + "="*70)
    print("SCENARIO 1: Normal Rebalancing")
    print("="*70 + "\n")
    print("Agent will analyze portfolio and rebalance if needed...")
    print("This should be ALLOWED by PolicyLayer.\n")

    await agent.run_single_cycle()

    print("\n" + "="*70)
    print("SCENARIO 2: Honeypot Token Attack")
    print("="*70 + "\n")
    print("Simulating attempt to buy honeypot token at:")
    print("  0xFe836592564C37D6cE99657c379a387CC5CE0868")
    print("\nPolicyLayer should detect this is a honeypot and BLOCK it!")
    print("(Stage 3.5: Honeypot Detection)\n")

    # Note: In a real demo, you'd inject a malicious prompt here
    # For now, the agent won't try to buy honeypots on its own
    print("⚠️  Note: Agent won't attempt honeypot purchases autonomously.")
    print("   To test this, manually prompt: 'Buy 0.1 ETH worth of 0xFe836...'\n")

    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70 + "\n")

    agent.metrics.print_summary()


if __name__ == "__main__":
    asyncio.run(run_demo())
