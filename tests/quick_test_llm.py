#!/usr/bin/env python3
"""
Quick test for LLM Judge - Single honeypot test

Usage:
    export OPENAI_API_KEY="sk-your-key-here"
    python tests/quick_test_llm.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentguard.llm_judge import LLMJudge


def create_honeypot_scenario():
    """Create a simple honeypot token scenario"""
    from dataclasses import dataclass
    from typing import List

    @dataclass
    class MockTrace:
        type: str
        from_address: str
        to_address: str
        value: int
        gas_used: int
        calls: List = None

        def __post_init__(self):
            if self.calls is None:
                self.calls = []

    @dataclass
    class MockSimulation:
        call_trace: List
        asset_changes: List
        logs: List

        def has_data(self):
            return True

    @dataclass
    class MockParsedTx:
        to: str
        value: int
        function_name: str
        function_selector: str
        recipient_address: str = None
        token_amount: int = None
        token_address: str = None
        decoded_params: dict = None

    # Transaction details
    user_addr = "0xuser123456789abcdef"
    honeypot_token = "0xhoneypot123456789abcdef"
    recipient_addr = "0xrecipient123456789abcdef"

    tx = {
        "from": user_addr,
        "to": honeypot_token,
        "value": 0,
        "data": "0xa9059cbb..."
    }

    parsed_tx = MockParsedTx(
        to=honeypot_token,
        value=0,
        function_name="transfer",
        function_selector="0xa9059cbb",
        recipient_address=recipient_addr,
        token_amount=1000000000000000000,
        token_address=honeypot_token
    )

    # CRITICAL: No Transfer events emitted = HONEYPOT!
    simulation = MockSimulation(
        call_trace=[
            MockTrace(
                type="CALL",
                from_address=user_addr,
                to_address=honeypot_token,
                value=0,
                gas_used=50000
            )
        ],
        asset_changes=[],
        logs=[]  # NO TRANSFER EVENT = HONEYPOT
    )

    policy_context = {}

    return tx, parsed_tx, simulation, policy_context


def main():
    print("\n" + "="*80)
    print("🧪 QUICK LLM JUDGE TEST - Honeypot Detection")
    print("="*80)

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: OPENAI_API_KEY not set!")
        print("\nSet it with:")
        print("  export OPENAI_API_KEY='sk-your-key-here'")
        print("\nOr in Python:")
        print("  os.environ['OPENAI_API_KEY'] = 'sk-your-key-here'")
        return 1

    print(f"\n✅ API Key found: {api_key[:20]}...")

    # Initialize LLM judge
    print("\n📝 Initializing LLM Judge...")
    judge = LLMJudge(
        provider="openai",
        model="gpt-4o-mini",
        api_key=api_key,
        block_threshold=0.70,
        warn_threshold=0.40
    )

    if not judge.is_available():
        print("❌ LLM Judge initialization failed!")
        return 1

    print("✅ LLM Judge initialized successfully")

    # Create test scenario
    print("\n🎭 Creating honeypot token scenario...")
    print("   - transfer() function called")
    print("   - NO Transfer events emitted")
    print("   - Expected: BLOCK with CRITICAL risk")

    tx, parsed_tx, simulation, policy_context = create_honeypot_scenario()

    # Analyze
    print("\n🔍 Analyzing transaction...")
    analysis = judge.analyze(tx, parsed_tx, simulation, policy_context)

    if not analysis:
        print("❌ Analysis failed!")
        return 1

    # Print results
    print("\n" + "="*80)
    print("📊 RESULTS")
    print("="*80)

    print(f"\n🤖 LLM Analysis:")
    print(f"   Malicious: {analysis.is_malicious}")
    print(f"   Confidence: {analysis.confidence:.2%}")
    print(f"   Risk Level: {analysis.risk_level}")
    print(f"   Action: {analysis.recommended_action}")
    print(f"\n   Reason: {analysis.reason}")
    print(f"\n   Indicators: {', '.join(analysis.indicators)}")

    # Verdict
    print("\n" + "="*80)
    if analysis.should_block():
        print("🛡️  ✅ SUCCESS: Transaction correctly BLOCKED!")
        print("="*80)
        print("\n✨ The LLM successfully detected the honeypot token!")
        return 0
    else:
        print("❌ FAILURE: Transaction was not blocked!")
        print("="*80)
        print(f"\n⚠️  Expected BLOCK but got {analysis.recommended_action}")
        return 1


if __name__ == "__main__":
    sys.exit(main())