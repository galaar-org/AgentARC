#!/usr/bin/env python3
"""
Test script for LLM Judge with various attack patterns

Usage:
    export OPENAI_API_KEY="your-api-key-here"
    python tests/test_llm_patterns.py

Or set the API key directly in the script.
"""

import os
import sys
from dataclasses import dataclass
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentarc.llm_judge import LLMJudge, SecurityIndicators


@dataclass
class MockTrace:
    """Mock call trace for testing"""
    type: str
    from_address: str
    to_address: str
    value: int
    gas_used: int
    calls: List['MockTrace']

    def __post_init__(self):
        if self.calls is None:
            self.calls = []


@dataclass
class MockAssetChange:
    """Mock asset change for testing"""
    address: str
    delta: int
    profited: bool
    type: str = "ERC20"

    def to_dict(self):
        return {
            "address": self.address,
            "delta": str(self.delta),
            "profited": self.profited,
            "type": self.type
        }


@dataclass
class MockLog:
    """Mock event log for testing"""
    name: str
    address: str


@dataclass
class MockSimulationResult:
    """Mock simulation result"""
    call_trace: List[MockTrace]
    asset_changes: List[MockAssetChange]
    logs: List[MockLog]
    success: bool = True

    def has_data(self):
        return True


@dataclass
class MockParsedTx:
    """Mock parsed transaction"""
    to: str
    value: int
    function_name: str
    function_selector: str
    recipient_address: str = None
    token_amount: int = None
    token_address: str = None
    decoded_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.decoded_params is None:
            self.decoded_params = {}


class TestScenarios:
    """Test scenarios for different attack patterns"""

    @staticmethod
    def test_1_legitimate_transfer():
        """Test 1: Legitimate token transfer (should ALLOW)"""
        print("\n" + "="*80)
        print("TEST 1: Legitimate Token Transfer")
        print("="*80)

        user_addr = "0xuser123456789"
        recipient_addr = "0x501ab28fc3c7d29c2d12b243723eb5c5418b9de6"
        token_addr = "0x036cbd53842c5426634e7929541ec2318f3dcf7e"

        tx = {
            "from": user_addr,
            "to": token_addr,
            "value": 0,
            "data": "0xa9059cbb..."
        }

        parsed_tx = MockParsedTx(
            to=token_addr,
            value=0,
            function_name="transfer",
            function_selector="0xa9059cbb",
            recipient_address=recipient_addr,
            token_amount=2000000,  # 2 USDC
            token_address=token_addr
        )

        simulation = MockSimulationResult(
            call_trace=[
                MockTrace(
                    type="CALL",
                    from_address=user_addr,
                    to_address=token_addr,
                    value=0,
                    gas_used=25000,
                    calls=[]
                )
            ],
            asset_changes=[
                MockAssetChange(user_addr, -2000000, False),
                MockAssetChange(recipient_addr, 2000000, True)
            ],
            logs=[
                MockLog("Transfer", token_addr)
            ]
        )

        policy_context = {
            "whitelisted_addresses": [recipient_addr.lower()]
        }

        return tx, parsed_tx, simulation, policy_context

    @staticmethod
    def test_2_honeypot_token():
        """Test 2: Honeypot token (NO Transfer events emitted) - should BLOCK"""
        print("\n" + "="*80)
        print("TEST 2: Honeypot Token Detection")
        print("="*80)

        user_addr = "0xuser123456789"
        honeypot_token = "0xhoneypot123456789"
        recipient_addr = "0xrecipient123456789"

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

        # CRITICAL: No Transfer events emitted!
        simulation = MockSimulationResult(
            call_trace=[
                MockTrace(
                    type="CALL",
                    from_address=user_addr,
                    to_address=honeypot_token,
                    value=0,
                    gas_used=50000,
                    calls=[]
                )
            ],
            asset_changes=[],
            logs=[]  # NO TRANSFER EVENT = HONEYPOT
        )

        policy_context = {}

        return tx, parsed_tx, simulation, policy_context

    @staticmethod
    def test_3_unlimited_approval_to_unknown():
        """Test 3: Unlimited approval to unknown address - should BLOCK"""
        print("\n" + "="*80)
        print("TEST 3: Unlimited Approval to Unknown Address")
        print("="*80)

        user_addr = "0xuser123456789"
        token_addr = "0x036cbd53842c5426634e7929541ec2318f3dcf7e"
        unknown_spender = "0xmalicious123456789"

        max_uint256 = 2**256 - 1

        tx = {
            "from": user_addr,
            "to": token_addr,
            "value": 0,
            "data": "0x095ea7b3..."
        }

        parsed_tx = MockParsedTx(
            to=token_addr,
            value=0,
            function_name="approve",
            function_selector="0x095ea7b3",
            recipient_address=unknown_spender,
            token_amount=max_uint256,
            token_address=token_addr,
            decoded_params={"spender": unknown_spender, "amount": max_uint256}
        )

        simulation = MockSimulationResult(
            call_trace=[
                MockTrace(
                    type="CALL",
                    from_address=user_addr,
                    to_address=token_addr,
                    value=0,
                    gas_used=45000,
                    calls=[]
                )
            ],
            asset_changes=[],
            logs=[
                MockLog("Approval", token_addr)
            ]
        )

        policy_context = {
            "whitelisted_addresses": []  # Unknown spender not whitelisted
        }

        return tx, parsed_tx, simulation, policy_context

    @staticmethod
    def test_4_delegatecall_attack():
        """Test 4: Delegatecall to untrusted contract - should BLOCK"""
        print("\n" + "="*80)
        print("TEST 4: Delegatecall to Untrusted Contract")
        print("="*80)

        user_addr = "0xuser123456789"
        contract_addr = "0xcontract123456789"
        malicious_impl = "0xmalicious123456789"

        tx = {
            "from": user_addr,
            "to": contract_addr,
            "value": 0,
            "data": "0x12345678..."
        }

        parsed_tx = MockParsedTx(
            to=contract_addr,
            value=0,
            function_name="executeAction",
            function_selector="0x12345678",
            token_address=contract_addr
        )

        # CRITICAL: Contains DELEGATECALL
        simulation = MockSimulationResult(
            call_trace=[
                MockTrace(
                    type="CALL",
                    from_address=user_addr,
                    to_address=contract_addr,
                    value=0,
                    gas_used=100000,
                    calls=[
                        MockTrace(
                            type="DELEGATECALL",  # MALICIOUS!
                            from_address=contract_addr,
                            to_address=malicious_impl,
                            value=0,
                            gas_used=80000,
                            calls=[]
                        )
                    ]
                )
            ],
            asset_changes=[],
            logs=[]
        )

        policy_context = {}

        return tx, parsed_tx, simulation, policy_context

    @staticmethod
    def test_5_callback_hook_attack():
        """Test 5: Callback to sender (hook attack) - should WARN/BLOCK"""
        print("\n" + "="*80)
        print("TEST 5: Callback to Sender (Hook Attack)")
        print("="*80)

        user_addr = "0xuser123456789"
        malicious_contract = "0xmalicious123456789"

        tx = {
            "from": user_addr,
            "to": malicious_contract,
            "value": 0,
            "data": "0xabcdef..."
        }

        parsed_tx = MockParsedTx(
            to=malicious_contract,
            value=0,
            function_name="claimReward",
            function_selector="0xabcdef",
            token_address=malicious_contract
        )

        # Contract calls back to user's address multiple times
        simulation = MockSimulationResult(
            call_trace=[
                MockTrace(
                    type="CALL",
                    from_address=user_addr,
                    to_address=malicious_contract,
                    value=0,
                    gas_used=150000,
                    calls=[
                        MockTrace(
                            type="CALL",
                            from_address=malicious_contract,
                            to_address=user_addr,  # Callback 1
                            value=0,
                            gas_used=50000,
                            calls=[]
                        ),
                        MockTrace(
                            type="CALL",
                            from_address=malicious_contract,
                            to_address=user_addr,  # Callback 2
                            value=0,
                            gas_used=50000,
                            calls=[]
                        )
                    ]
                )
            ],
            asset_changes=[],
            logs=[]
        )

        policy_context = {}

        return tx, parsed_tx, simulation, policy_context

    @staticmethod
    def test_6_hidden_fees():
        """Test 6: Hidden fees (user loses more than expected) - should WARN/BLOCK"""
        print("\n" + "="*80)
        print("TEST 6: Hidden Fees Detection")
        print("="*80)

        user_addr = "0xuser123456789"
        token_addr = "0xtoken123456789"
        recipient_addr = "0xrecipient123456789"
        fee_collector = "0xfeecollector123456789"

        tx = {
            "from": user_addr,
            "to": token_addr,
            "value": 0,
            "data": "0xa9059cbb..."
        }

        parsed_tx = MockParsedTx(
            to=token_addr,
            value=0,
            function_name="transfer",
            function_selector="0xa9059cbb",
            recipient_address=recipient_addr,
            token_amount=100000000,  # 100 tokens
            token_address=token_addr
        )

        # User loses 100, recipient gets 85, fee collector gets 15 (15% fee!)
        simulation = MockSimulationResult(
            call_trace=[
                MockTrace(
                    type="CALL",
                    from_address=user_addr,
                    to_address=token_addr,
                    value=0,
                    gas_used=60000,
                    calls=[]
                )
            ],
            asset_changes=[
                MockAssetChange(user_addr, -100000000, False),
                MockAssetChange(recipient_addr, 85000000, True),
                MockAssetChange(fee_collector, 15000000, True)  # Hidden 15% fee
            ],
            logs=[
                MockLog("Transfer", token_addr),
                MockLog("Transfer", token_addr)
            ]
        )

        policy_context = {
            "whitelisted_addresses": [recipient_addr.lower()]
        }

        return tx, parsed_tx, simulation, policy_context

    @staticmethod
    def test_7_reentrancy_attack():
        """Test 7: Reentrancy attack - should BLOCK"""
        print("\n" + "="*80)
        print("TEST 7: Reentrancy Attack Detection")
        print("="*80)

        user_addr = "0xuser123456789"
        vulnerable_contract = "0xvulnerable123456789"

        tx = {
            "from": user_addr,
            "to": vulnerable_contract,
            "value": 0,
            "data": "0xwithdraw..."
        }

        parsed_tx = MockParsedTx(
            to=vulnerable_contract,
            value=0,
            function_name="withdraw",
            function_selector="0x3ccfd60b",
            token_address=vulnerable_contract
        )

        # Same contract called multiple times in call stack = reentrancy
        simulation = MockSimulationResult(
            call_trace=[
                MockTrace(
                    type="CALL",
                    from_address=user_addr,
                    to_address=vulnerable_contract,
                    value=0,
                    gas_used=200000,
                    calls=[
                        MockTrace(
                            type="CALL",
                            from_address=vulnerable_contract,
                            to_address=user_addr,
                            value=1000000000000000000,
                            gas_used=100000,
                            calls=[
                                MockTrace(
                                    type="CALL",
                                    from_address=user_addr,
                                    to_address=vulnerable_contract,  # REENTRANT CALL!
                                    value=0,
                                    gas_used=50000,
                                    calls=[]
                                )
                            ]
                        )
                    ]
                )
            ],
            asset_changes=[],
            logs=[]
        )

        policy_context = {}

        return tx, parsed_tx, simulation, policy_context


def print_analysis(test_name: str, analysis, indicators: SecurityIndicators):
    """Pretty print analysis results"""
    print(f"\n📊 {test_name} Results:")
    print("-" * 80)

    # Print security indicators
    print("\n🔍 Security Indicators Detected:")
    indicators_dict = indicators.to_dict()

    if indicators_dict['hidden_approvals']['has_approval']:
        print(f"   ⚠️  Approval detected:")
        print(f"      - Unlimited: {indicators_dict['hidden_approvals']['unlimited_approval']}")
        print(f"      - To unknown: {indicators_dict['hidden_approvals']['to_unknown_address']}")

    if indicators_dict['fund_flow']['delegatecalls'] > 0:
        print(f"   🚨 Delegatecalls: {indicators_dict['fund_flow']['delegatecalls']}")

    if indicators_dict['fund_flow']['callbacks_to_sender'] > 0:
        print(f"   ⚠️  Callbacks to sender: {indicators_dict['fund_flow']['callbacks_to_sender']}")

    if indicators_dict['token_behavior']['no_transfer_events']:
        print(f"   🚨 HONEYPOT: No Transfer events emitted!")

    if indicators_dict['balance_changes']['hidden_fees']:
        print(f"   ⚠️  Hidden fees detected!")

    if indicators_dict['technical']['reentrancy_pattern']:
        print(f"   🚨 Reentrancy pattern detected!")

    if indicators_dict['technical']['flash_loan_detected']:
        print(f"   ⚠️  Flash loan detected!")

    if not analysis:
        print("\n❌ LLM analysis not available (API key not set)")
        return

    # Print LLM analysis
    print(f"\n🤖 LLM Analysis:")
    print(f"   Malicious: {analysis.is_malicious}")
    print(f"   Confidence: {analysis.confidence:.2%}")
    print(f"   Risk Level: {analysis.risk_level}")
    print(f"   Action: {analysis.recommended_action}")
    print(f"\n   Reason: {analysis.reason}")
    print(f"\n   Indicators: {', '.join(analysis.indicators)}")

    # Final verdict
    if analysis.should_block():
        print(f"\n🛡️  ❌ BLOCKED - Transaction rejected!")
    elif analysis.should_warn():
        print(f"\n⚠️  WARNING - Transaction flagged as suspicious")
    else:
        print(f"\n✅ ALLOWED - Transaction appears safe")


def main():
    """Run all test scenarios"""
    print("\n" + "="*80)
    print("LLM JUDGE - ATTACK PATTERN DETECTION TEST SUITE")
    print("="*80)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️  WARNING: OPENAI_API_KEY not set!")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        print("\nContinuing with indicator extraction only (no LLM analysis)...\n")

    # Initialize LLM judge
    judge = LLMJudge(
        provider="openai",
        model="gpt-4o-mini",  # Fast and cheap for testing
        api_key=api_key,
        block_threshold=0.70,
        warn_threshold=0.40
    )

    # Test scenarios
    scenarios = [
        ("Test 1: Legitimate Transfer", TestScenarios.test_1_legitimate_transfer),
        ("Test 2: Honeypot Token", TestScenarios.test_2_honeypot_token),
        ("Test 3: Unlimited Approval", TestScenarios.test_3_unlimited_approval_to_unknown),
        ("Test 4: Delegatecall Attack", TestScenarios.test_4_delegatecall_attack),
        ("Test 5: Callback Hook Attack", TestScenarios.test_5_callback_hook_attack),
        ("Test 6: Hidden Fees", TestScenarios.test_6_hidden_fees),
        ("Test 7: Reentrancy Attack", TestScenarios.test_7_reentrancy_attack),
    ]

    results = []

    for test_name, test_func in scenarios:
        tx, parsed_tx, simulation, policy_context = test_func()

        # Extract security indicators
        indicators = judge._extract_security_indicators(
            tx, parsed_tx, simulation, policy_context
        )

        # Analyze with LLM
        analysis = judge.analyze(tx, parsed_tx, simulation, policy_context)

        # Print results
        print_analysis(test_name, analysis, indicators)

        results.append({
            "test": test_name,
            "indicators": indicators,
            "analysis": analysis
        })

        print("\n")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if api_key:
        blocked = sum(1 for r in results if r['analysis'] and r['analysis'].should_block())
        warned = sum(1 for r in results if r['analysis'] and r['analysis'].should_warn() and not r['analysis'].should_block())
        allowed = sum(1 for r in results if r['analysis'] and not r['analysis'].should_warn())

        print(f"\n✅ Total tests: {len(results)}")
        print(f"🛡️  Blocked: {blocked}")
        print(f"⚠️  Warned: {warned}")
        print(f"✅ Allowed: {allowed}")

        print("\n💡 Expected results:")
        print("   - Test 1 (Legitimate): ALLOW")
        print("   - Test 2 (Honeypot): BLOCK (CRITICAL)")
        print("   - Test 3 (Unlimited Approval): BLOCK (CRITICAL)")
        print("   - Test 4 (Delegatecall): BLOCK (CRITICAL)")
        print("   - Test 5 (Callbacks): BLOCK/WARN (HIGH)")
        print("   - Test 6 (Hidden Fees): BLOCK/WARN (HIGH)")
        print("   - Test 7 (Reentrancy): BLOCK (HIGH)")
    else:
        print("\n⚠️  LLM analysis skipped (no API key)")
        print("Set OPENAI_API_KEY to run full tests")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()