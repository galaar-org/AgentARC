#!/usr/bin/env python3
"""
Test LLM Judge Integration

This test verifies:
1. LLM judge initialization with different providers
2. Analysis with/without API keys
3. Response parsing and decision thresholds
4. Graceful degradation
"""

import os
import sys
import json
from unittest.mock import Mock, patch
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentarc.llm_judge import LLMJudge, LLMAnalysis
from agentarc.calldata_parser import ParsedTransaction


@dataclass
class MockSentioResult:
    """Mock Sentio result for testing"""
    success: bool = True
    call_trace: list = None
    fund_flow: list = None
    balance_changes: list = None
    events: list = None
    gas_used: int = 100000

    def __post_init__(self):
        self.call_trace = self.call_trace or []
        self.fund_flow = self.fund_flow or []
        self.balance_changes = self.balance_changes or []
        self.events = self.events or []

    def has_data(self):
        return bool(self.call_trace or self.fund_flow or self.balance_changes or self.events)


def test_llm_judge_without_api_key():
    """Test graceful degradation when API key not set"""
    print("\n" + "="*70)
    print("Test 1: LLM Judge without API key")
    print("="*70)

    # Clear API keys from environment
    original_openai = os.environ.pop("OPENAI_API_KEY", None)
    original_anthropic = os.environ.pop("ANTHROPIC_API_KEY", None)

    judge = LLMJudge(provider="openai")

    assert not judge.is_available(), "Judge should not be available without API key"
    print("✅ Judge correctly reports not available")

    # Try to analyze
    tx = {
        "from": "0xSender",
        "to": "0xRecipient",
        "value": 1000000000000000000,
        "gas": 21000,
        "data": "0x"
    }

    parsed_tx = ParsedTransaction(
        to="0xRecipient",
        value=1000000000000000000,
        function_name=None,
        function_selector=None,
        decoded_params={},
        raw_calldata=b""
    )

    result = judge.analyze(tx, parsed_tx)

    assert result is None, "Analysis should return None without API key"
    print("✅ Gracefully returns None when API key missing")

    # Restore original keys
    if original_openai:
        os.environ["OPENAI_API_KEY"] = original_openai
    if original_anthropic:
        os.environ["ANTHROPIC_API_KEY"] = original_anthropic

    print("="*70 + "\n")


def test_llm_analysis_thresholds():
    """Test LLMAnalysis decision thresholds"""
    print("\n" + "="*70)
    print("Test 2: LLMAnalysis Decision Thresholds")
    print("="*70)

    # Test BLOCK threshold
    analysis = LLMAnalysis(
        is_malicious=True,
        confidence=0.80,
        risk_level="HIGH",
        reason="Hidden approval detected",
        indicators=["unlimited_approval"],
        recommended_action="BLOCK"
    )

    assert analysis.should_block(block_threshold=0.70), "Should block at 80% confidence with 70% threshold"
    print("✅ Blocks at 80% confidence (threshold: 70%)")

    # Test WARN threshold
    analysis_medium = LLMAnalysis(
        is_malicious=True,
        confidence=0.50,
        risk_level="MEDIUM",
        reason="Unusual fund flow pattern",
        indicators=["unknown_recipient"],
        recommended_action="WARN"
    )

    assert not analysis_medium.should_block(block_threshold=0.70), "Should not block at 50% with 70% threshold"
    assert analysis_medium.should_warn(warn_threshold=0.40), "Should warn at 50% with 40% threshold"
    print("✅ Warns at 50% confidence (warn threshold: 40%, block threshold: 70%)")

    # Test ALLOW threshold
    analysis_low = LLMAnalysis(
        is_malicious=False,
        confidence=0.20,
        risk_level="LOW",
        reason="No malicious patterns detected",
        indicators=[],
        recommended_action="ALLOW"
    )

    assert not analysis_low.should_block(block_threshold=0.70), "Should not block at 20%"
    assert not analysis_low.should_warn(warn_threshold=0.40), "Should not warn at 20%"
    print("✅ Allows at 20% confidence")

    # Test CRITICAL always blocks
    critical = LLMAnalysis(
        is_malicious=True,
        confidence=0.30,
        risk_level="CRITICAL",
        reason="Reentrancy attack detected",
        indicators=["reentrancy"],
        recommended_action="BLOCK"
    )

    assert critical.should_block(block_threshold=0.70), "CRITICAL should block even at low confidence"
    print("✅ CRITICAL risk blocks regardless of confidence")

    print("="*70 + "\n")


def test_llm_judge_with_openai_mock():
    """Test LLM judge with mocked OpenAI response"""
    print("\n" + "="*70)
    print("Test 3: LLM Judge with OpenAI (mocked)")
    print("="*70)

    # Mock OpenAI client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [
        Mock(
            message=Mock(
                content=json.dumps({
                    "is_malicious": True,
                    "confidence": 0.85,
                    "risk_level": "HIGH",
                    "reason": "Hidden unlimited approval detected in transaction",
                    "indicators": ["unlimited_approval", "suspicious_contract"],
                    "recommended_action": "BLOCK"
                })
            )
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response

    judge = LLMJudge(provider="openai", api_key="test-key")
    judge._client = mock_client

    tx = {
        "from": "0xSender",
        "to": "0xMaliciousContract",
        "value": 0,
        "gas": 100000,
        "data": "0x095ea7b3..."  # approve function
    }

    parsed_tx = ParsedTransaction(
        to="0xMaliciousContract",
        value=0,
        function_name="approve",
        function_selector="0x095ea7b3",
        decoded_params={},
        raw_calldata=bytes.fromhex("095ea7b3")
    )

    result = judge.analyze(tx, parsed_tx)

    assert result is not None, "Should return analysis"
    assert result.is_malicious, "Should detect as malicious"
    assert result.confidence == 0.85, f"Confidence should be 0.85, got {result.confidence}"
    assert result.risk_level == "HIGH", f"Risk level should be HIGH, got {result.risk_level}"
    assert result.should_block(), "Should recommend blocking"
    print(f"✅ Detected malicious activity: {result.reason}")
    print(f"✅ Confidence: {result.confidence:.0%}")
    print(f"✅ Risk level: {result.risk_level}")
    print(f"✅ Indicators: {', '.join(result.indicators)}")

    print("="*70 + "\n")


def test_llm_judge_with_sentio_data():
    """Test LLM judge with Sentio simulation data"""
    print("\n" + "="*70)
    print("Test 4: LLM Judge with Sentio Data")
    print("="*70)

    # Mock OpenAI client
    mock_client = Mock()

    # Capture the prompt that gets sent
    captured_prompt = None

    def capture_create(**kwargs):
        nonlocal captured_prompt
        captured_prompt = kwargs.get("messages", [{}])[1].get("content", "")

        return Mock(
            choices=[
                Mock(
                    message=Mock(
                        content=json.dumps({
                            "is_malicious": True,
                            "confidence": 0.75,
                            "risk_level": "HIGH",
                            "reason": "Unusual fund flow: money routed through unknown intermediary",
                            "indicators": ["unusual_fund_flow", "unknown_addresses"],
                            "recommended_action": "BLOCK"
                        })
                    )
                )
            ]
        )

    mock_client.chat.completions.create.side_effect = capture_create

    judge = LLMJudge(provider="openai", api_key="test-key")
    judge._client = mock_client

    tx = {
        "from": "0xSender",
        "to": "0xContract",
        "value": 0,
        "gas": 300000,
        "data": "0xswapdata..."
    }

    parsed_tx = ParsedTransaction(
        to="0xContract",
        value=0,
        function_name="swap",
        function_selector="0x12345678",
        decoded_params={},
        raw_calldata=bytes.fromhex("12345678")
    )

    # Mock Sentio result with suspicious fund flow
    sentio_result = MockSentioResult()
    sentio_result.fund_flow = [
        Mock(
            from_address="0xSender",
            to_address="0xUnknownMiddleman",
            asset="USDC",
            amount=1000000000,
            order=0,
            human_readable_amount=lambda: "1000.0000 USDC"
        ),
        Mock(
            from_address="0xUnknownMiddleman",
            to_address="0xFinalRecipient",
            asset="USDC",
            amount=900000000,
            order=1,
            human_readable_amount=lambda: "900.0000 USDC"
        )
    ]

    result = judge.analyze(tx, parsed_tx, sentio_result)

    assert result is not None, "Should return analysis"
    assert result.is_malicious, "Should detect malicious pattern"
    assert "fund flow" in result.reason.lower(), "Reason should mention fund flow"
    print(f"✅ Detected suspicious pattern: {result.reason}")

    # Verify Sentio data was included in prompt
    assert captured_prompt is not None, "Should have captured prompt"
    assert "FUND FLOW" in captured_prompt, "Prompt should include fund flow section"
    assert "1000.0000 USDC" in captured_prompt, "Prompt should include fund flow amounts"
    print("✅ Sentio fund flow data included in LLM prompt")
    print(f"✅ Prompt length: {len(captured_prompt)} characters")

    print("="*70 + "\n")


def test_llm_response_parsing():
    """Test parsing of various LLM response formats"""
    print("\n" + "="*70)
    print("Test 5: LLM Response Parsing")
    print("="*70)

    judge = LLMJudge(provider="openai", api_key="test-key")

    # Test 1: JSON in code block
    response_with_codeblock = """
Here's my analysis:

```json
{
  "is_malicious": true,
  "confidence": 0.65,
  "risk_level": "MEDIUM",
  "reason": "Potential phishing attempt",
  "indicators": ["phishing"],
  "recommended_action": "WARN"
}
```
"""

    analysis = judge._parse_analysis(response_with_codeblock)
    assert analysis.is_malicious, "Should parse malicious flag"
    assert analysis.confidence == 0.65, "Should parse confidence"
    print("✅ Parsed JSON from code block")

    # Test 2: Plain JSON
    plain_json = json.dumps({
        "is_malicious": False,
        "confidence": 0.10,
        "risk_level": "LOW",
        "reason": "Normal transaction",
        "indicators": [],
        "recommended_action": "ALLOW"
    })

    analysis2 = judge._parse_analysis(plain_json)
    assert not analysis2.is_malicious, "Should parse benign transaction"
    assert analysis2.confidence == 0.10, "Should parse low confidence"
    print("✅ Parsed plain JSON")

    # Test 3: Invalid JSON (fallback)
    invalid = "This is not JSON at all!"

    analysis3 = judge._parse_analysis(invalid)
    assert not analysis3.is_malicious, "Should default to non-malicious on parse error"
    assert analysis3.confidence == 0.0, "Should default to 0 confidence"
    assert "Failed to parse" in analysis3.reason, "Reason should indicate parse failure"
    print("✅ Gracefully handled invalid JSON")

    print("="*70 + "\n")


def test_prompt_building():
    """Test prompt building with different data combinations"""
    print("\n" + "="*70)
    print("Test 6: Prompt Building")
    print("="*70)

    judge = LLMJudge(
        provider="openai",
        api_key="test-key",
        check_patterns=["hidden_approvals", "reentrancy"]
    )

    tx = {
        "from": "0xSender",
        "to": "0xContract",
        "value": 1000000000000000000,
        "gas": 200000,
        "data": "0xabcdef"
    }

    parsed_tx = ParsedTransaction(
        to="0xContract",
        value=1000000000000000000,
        function_name="transfer",
        function_selector="0xa9059cbb",
        decoded_params={},
        raw_calldata=bytes.fromhex("a9059cbb"),
        recipient_address="0xRecipient",
        token_amount=100000000
    )

    prompt = judge._build_prompt(tx, parsed_tx, None)

    # Verify prompt contains key sections
    assert "TRANSACTION DETAILS:" in prompt
    assert "From: 0xSender" in prompt
    assert "To: 0xContract" in prompt
    assert "Function: transfer" in prompt
    assert "Recipient (from calldata): 0xRecipient" in prompt
    print("✅ Prompt includes transaction details")

    assert "ANALYSIS REQUIRED:" in prompt
    assert "Hidden Approvals" in prompt
    assert "Reentrancy" in prompt
    print("✅ Prompt includes analysis patterns")

    # Test with Sentio data
    sentio_result = MockSentioResult()
    sentio_result.call_trace = [
        Mock(
            type="CALL",
            from_address="0xSender",
            to_address="0xContract",
            value=0,
            gas_used=50000
        )
    ]
    sentio_result.fund_flow = [
        Mock(
            from_address="0xSender",
            to_address="0xRecipient",
            order=0,
            human_readable_amount=lambda: "1.0000 ETH"
        )
    ]
    sentio_result.balance_changes = [
        Mock(
            address="0xSender",
            delta=-1000000000000000000,
            human_readable_delta=lambda: "-1.0000 ETH"
        )
    ]
    sentio_result.events = [
        Mock(
            name="Transfer",
            address="0xContract",
            parameters={"from": "0xSender", "to": "0xRecipient", "value": "1000000000000000000"}
        )
    ]

    prompt_with_sentio = judge._build_prompt(tx, parsed_tx, sentio_result)

    assert "SIMULATION RESULTS (from Sentio):" in prompt_with_sentio
    assert "CALL TRACE:" in prompt_with_sentio
    assert "FUND FLOW" in prompt_with_sentio
    assert "BALANCE CHANGES:" in prompt_with_sentio
    assert "EVENTS EMITTED:" in prompt_with_sentio
    print("✅ Prompt includes Sentio simulation data")

    print(f"✅ Prompt length (basic): {len(prompt)} characters")
    print(f"✅ Prompt length (with Sentio): {len(prompt_with_sentio)} characters")

    print("="*70 + "\n")


def main():
    print("\n" + "="*70)
    print("LLM JUDGE TEST SUITE")
    print("="*70)

    try:
        test_llm_judge_without_api_key()
        test_llm_analysis_thresholds()
        test_llm_judge_with_openai_mock()
        test_llm_judge_with_sentio_data()
        test_llm_response_parsing()
        test_prompt_building()

        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70 + "\n")
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
