# LLM Judge Test Suite

This directory contains test scripts for the enhanced LLM Judge with advanced attack pattern detection.

## Setup

1. **Install dependencies** (if not already installed):
```bash
pip install openai anthropic
```

2. **Set your OpenAI API key**:
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Or set it in your `.env` file:
```bash
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

## Quick Test (Recommended for first-time testing)

Run a single honeypot detection test to verify everything works:

```bash
# From the project root directory
python tests/quick_test_llm.py
```

**Expected output:**
```
🛡️  ✅ SUCCESS: Transaction correctly BLOCKED!
✨ The LLM successfully detected the honeypot token!
```

## Full Test Suite

Run all 7 attack pattern tests:

```bash
python tests/test_llm_patterns.py
```

### Test Coverage

The full test suite covers these attack patterns:

1. **✅ Legitimate Transfer** - Should ALLOW
   - Normal USDC transfer to whitelisted address
   - Proper Transfer events emitted
   - No suspicious indicators

2. **🚨 Honeypot Token** - Should BLOCK (CRITICAL)
   - `transfer()` called but NO Transfer events emitted
   - Indicates token cannot be sold/transferred
   - Confidence: 0.9-1.0

3. **🚨 Unlimited Approval** - Should BLOCK (CRITICAL)
   - Approval amount = max uint256
   - Spender address not whitelisted
   - Hidden approval attack
   - Confidence: 0.9-1.0

4. **🚨 Delegatecall Attack** - Should BLOCK (CRITICAL)
   - DELEGATECALL to untrusted contract
   - Storage manipulation possible
   - Confidence: 0.9-1.0

5. **⚠️  Callback Hook Attack** - Should BLOCK/WARN (HIGH)
   - Contract calls back to sender's address 2+ times
   - Potential reentrancy or state manipulation
   - Confidence: 0.7-0.9

6. **⚠️  Hidden Fees** - Should BLOCK/WARN (HIGH)
   - User loses 100 tokens, recipient gets 85, fee collector gets 15
   - 15% hidden fee (undisclosed)
   - Unexpected recipients
   - Confidence: 0.7-0.9

7. **⚠️  Reentrancy Attack** - Should BLOCK (HIGH)
   - Same contract called multiple times in call stack
   - Classic reentrancy pattern
   - Confidence: 0.7-0.9

## Understanding the Output

Each test shows:

### 🔍 Security Indicators (Deterministic)
Pre-computed flags extracted from simulation data:
- Approval details (unlimited, to_unknown)
- Delegatecalls count
- Callbacks to sender count
- Transfer events status
- Hidden fees detection
- Reentrancy patterns

### 🤖 LLM Analysis
AI-powered analysis based on indicators:
- **Malicious**: Boolean flag
- **Confidence**: 0.0-1.0 (higher = more certain)
- **Risk Level**: LOW, MEDIUM, HIGH, CRITICAL
- **Action**: ALLOW, WARN, BLOCK
- **Reason**: Detailed explanation
- **Indicators**: List of detected attack patterns

## Cost Estimate

Using `gpt-4o-mini`:
- ~$0.003 per transaction analysis
- Full test suite (7 tests): ~$0.02
- Very affordable for testing and production use

## Troubleshooting

### "OPENAI_API_KEY not set"
```bash
export OPENAI_API_KEY="sk-your-key-here"
# Or add to ~/.bashrc or ~/.zshrc for persistence
```

### "openai package not installed"
```bash
pip install openai
```

### Test fails to block obvious attack
- Check that you're using `gpt-4o-mini` or better (not `gpt-3.5-turbo`)
- Review the system prompt in `llm_judge.py`
- Check if security indicators were extracted correctly

### Low confidence scores
- This is normal for ambiguous cases
- The system is designed to be conservative
- Adjust `block_threshold` and `warn_threshold` in judge initialization

## Integration Example

```python
from agentguard.llm_judge import LLMJudge

# Initialize
judge = LLMJudge(
    provider="openai",
    model="gpt-4o-mini",
    api_key="sk-your-key-here",
    block_threshold=0.70,  # Block if confidence >= 70%
    warn_threshold=0.40    # Warn if confidence >= 40%
)

# Analyze transaction
analysis = judge.analyze(
    transaction=tx,
    parsed_tx=parsed_tx,
    simulation_result=simulation,
    policy_context=policy_context
)

# Make decision
if analysis and analysis.should_block():
    print(f"🛡️  BLOCKED: {analysis.reason}")
    raise Exception("Transaction blocked by security policy")
elif analysis and analysis.should_warn():
    print(f"⚠️  WARNING: {analysis.reason}")
    # Maybe ask user for confirmation
else:
    print("✅ Transaction approved")
    # Proceed with execution
```

## Attack Pattern Detection Details

### Honeypot Detection Algorithm
```python
# Pseudocode
if function_name in ['transfer', 'transferFrom']:
    transfer_events = count_events(['Transfer', 'TransferSingle', 'TransferBatch'])
    if transfer_events == 0:
        # CRITICAL: Honeypot detected!
        return BLOCK, confidence=0.95
```

### Delegatecall Detection
```python
# Pseudocode
for trace in call_trace:
    if trace.type == "DELEGATECALL":
        # CRITICAL: Storage manipulation possible
        return BLOCK, confidence=0.95
```

### Hidden Fee Detection
```python
# Pseudocode
user_outflow = sum(user's negative balance changes)
total_inflow = sum(all positive balance changes)
fee_pct = (total_inflow - user_outflow) / user_outflow * 100

if fee_pct > 10:
    return BLOCK, confidence=0.85
elif fee_pct > 5:
    return WARN, confidence=0.65
```

## Next Steps

After running tests successfully:

1. **Update your policy.yaml** with correct token addresses
2. **Integrate LLM judge** into your transaction pipeline
3. **Monitor false positives** and adjust thresholds
4. **Add custom patterns** to `check_patterns` list
5. **Consider using GPT-4** for even better accuracy (higher cost)

## Support

For issues or questions:
- Check the main PolicyLayer documentation
- Review the `llm_judge.py` implementation
- Open an issue on GitHub