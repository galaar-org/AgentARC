# 🍯 Honeypot Token Testing Guide

## Deployed Contracts (Base Sepolia)

- **HoneypotToken**: `0xb76955877C2a167F297BcC83954485e1AC65Ac17`
- **BlacklistManager**: `0xbf4f142574818a8Dd0e4ab6640493069D18f4643`

## Overview

The honeypot token contract implements 7 real-world scam techniques to test AgentGuard's protection capabilities. The agent now has special actions to interact with this honeypot and demonstrate PolicyLayer's honeypot detection.

## Available Agent Actions

### 1. **honeypot_buy_tokens**
Attempts to buy honeypot tokens (simulates purchasing)

### 2. **honeypot_sell_tokens**
Attempts to sell/transfer honeypot tokens

### 3. **honeypot_check_balance**
Checks token balance (shows FAKE 100x inflated balance!)

### 4. **honeypot_approve_tokens**
Approves honeypot tokens to a spender

---

## Testing Scenarios

### Test 1: Buy Honeypot Tokens (Should Be BLOCKED!)

**Prompt:**
```
Buy 0.01 ETH worth of  tokens at 0xb76955877C2a167F297BcC83954485e1AC65Ac17
```

**Expected Behavior:**
```
Stage 1: Intent Judge ✓
Stage 2: Policy Validation ✓
Stage 3: Tenderly Simulation ✓ (Buy succeeds, user receives tokens)

Stage 3.5: Honeypot Detection
  → Token BUY detected. Checking if tokens can be sold back...
  → Testing sell for token 0xb7695587...
  → Simulating transfer() call...
  → ⚠️ No Transfer events in sell simulation!
  → 🚫 HONEYPOT DETECTED

❌ BLOCKED: HONEYPOT DETECTED: Token 0xb7695587... transfer() succeeds but emits no Transfer events
```

**What This Tests:**
- ✅ Pre-purchase honeypot detection
- ✅ Simulates buy, then simulates sell
- ✅ Detects missing Transfer events
- ✅ Blocks the BUY to protect user funds

---

### Test 2: Check Honeypot Balance (Shows FAKE Balance)

**Prompt:**
```
Check my honeypot token balance at 0xb76955877C2a167F297BcC83954485e1AC65Ac17
```

**Expected Behavior:**
```
Honeypot Token Balance Check:

Token: LegitToken (LEGIT)
Address: 0x[YOUR_ADDR]...
Balance: 100,000 LEGIT

⚠️ WARNING: This balance is likely FAKE!

The honeypot token shows 100x the actual balance for non-whitelisted users.
If you see a large balance, the actual balance is 100x SMALLER.

This is a honeypot technique to make the token look valuable and attractive to buy.
```

**What This Tests:**
- ✅ Fake balanceOf() function
- ✅ Shows 100x inflated balance to non-whitelisted users
- ✅ Demonstrates deceptive UI technique

---

### Test 3: Sell Honeypot Tokens (Should Be BLOCKED!)

**Prompt:**
```
Sell 100 honeypot tokens at 0xb76955877C2a167F297BcC83954485e1AC65Ac17 to 0x0000000000000000000000000000000000000001
```

**Expected Behavior:**
```
Stage 1: Intent Judge ✓
Stage 2: Policy Validation ✓
Stage 3: Tenderly Simulation ✓

Stage 3.5: Honeypot Detection
  (Not triggered - this is a direct transfer, not a token purchase)

Stage 4: LLM Validation
  → Analyzing transaction for malicious patterns...
  → ⚠️ No Transfer events detected!
  → HONEYPOT INDICATOR: Transfer called but no actual token movement

❌ BLOCKED by LLM: Honeypot token detected - transfer() called but no Transfer events emitted
```

**What This Tests:**
- ✅ Transfer restrictions (owner-only selling)
- ✅ Auto-blacklisting on sell attempts
- ✅ Fake Transfer events detection
- ✅ LLM-based honeypot indicator extraction

---

### Test 4: Approve Honeypot Tokens

**Prompt:**
```
Approve unlimited honeypot tokens at 0xb76955877C2a167F297BcC83954485e1AC65Ac17 to 0x0000000000000000000000000000000000000001
```

**Expected Behavior:**
```
⚠️ HONEYPOT TRAP:
- The approval will likely SUCCEED
- But when the spender tries to use transferFrom(), it will FAIL
- Only owner and whitelisted addresses can actually move tokens
- This gives false confidence that the token works normally

Don't be fooled by successful approvals on honeypot tokens!
```

**What This Tests:**
- ✅ Approval trap technique
- ✅ Demonstrates that approvals succeed but transfers fail
- ✅ Shows deceptive "legitimate" behavior

---

## How Honeypot Detection Works

### Stage 3.5: Honeypot Detection Flow

```
1. User tries to BUY honeypot tokens
   ↓
2. PolicyLayer simulates the BUY transaction
   ↓
3. BUY simulation succeeds, user receives tokens ✓
   ↓
4. PolicyLayer detects token purchase (positive ERC20 balance change)
   ↓
5. PolicyLayer simulates a SELL transaction (transfer to test address)
   ↓
6. SELL simulation is analyzed for honeypot indicators:
   - ❌ Simulation reverts → HONEYPOT
   - ❌ No Transfer events emitted → HONEYPOT
   - ❌ User balance doesn't decrease → HONEYPOT
   ↓
7. If honeypot detected → BLOCK the original BUY transaction
   ↓
8. User is protected! 🛡️
```

### Key Detection Points

1. **Transfer Event Check**
   - Normal token: `Transfer(from, to, amount)` event emitted
   - Honeypot: No events or fake events

2. **Balance Change Check**
   - Normal token: User balance decreases when transferring
   - Honeypot: Balance doesn't change (transfer fails silently)

3. **Simulation Success Check**
   - Normal token: Transfer simulation succeeds
   - Honeypot: Transfer simulation reverts or fails

---

## Testing Commands

### Start the Agent
```bash
# From the examples/onchain-agent directory
python chat.py
```

### Example Test Session

```
You: "Check my wallet details first"
Agent: [Shows wallet address and balance]

You: "Check my honeypot token balance"
Agent: [Shows FAKE 100x inflated balance with warning]

You: "Try to buy 0.01 ETH worth of honeypot tokens"
Agent: [Transaction BLOCKED - Honeypot detected!]

You: "What happened? Why was it blocked?"
Agent: [Explains honeypot detection - tokens cannot be sold back]
```

---

## Honeypot Techniques Demonstrated

| # | Technique | What It Does | How AgentGuard Detects |
|---|-----------|-------------|----------------------|
| 1 | Fake `balanceOf` | Shows 100x actual balance | LLM analysis of balance manipulation |
| 2 | Auto-blacklisting | Blacklists on sell attempt | Detects no Transfer events |
| 3 | Owner-only transfers | Only owner can sell | Transfer simulation fails |
| 4 | Fake Transfer events | Emits events without transfer | Checks balance didn't change |
| 5 | Hidden external call | Calls blacklist manager | Detects external CALL in trace |
| 6 | Time lock | Never unlocks (max uint256) | Code analysis (future) |
| 7 | Obfuscated functions | `__decimals` sets blacklist | Static analysis (future) |

---

## Configuration Requirements

### Required in `policy.yaml`:

```yaml
simulation:
  enabled: true
  fail_on_revert: true

llm_validation:
  enabled: true
  provider: openai
  model: gpt-4o-mini
  block_threshold: 0.70
```

### Required Environment Variables:

```bash
# Tenderly (for simulation)
TENDERLY_ACCESS_KEY=your_tenderly_key
TENDERLY_ACCOUNT_SLUG=your_account
TENDERLY_PROJECT_SLUG=your_project

# OpenAI (for LLM-based detection)
OPENAI_API_KEY=your_openai_key
```

---

## Success Criteria

### ✅ Test PASSES if:

1. **Buy transactions are BLOCKED** with reason "HONEYPOT DETECTED"
2. **Balance shows FAKE 100x value** with warning message
3. **Sell transactions are BLOCKED** by LLM detection or honeypot check
4. **Approval succeeds** but shows warning about honeypot trap

### ❌ Test FAILS if:

1. Buy transactions go through without honeypot detection
2. Balance shows real value without warning
3. Sell transactions are ALLOWED
4. No honeypot indicators are detected

---

## Troubleshooting

### Issue: Buy not blocked

**Check:**
- Tenderly simulation enabled?
- Tenderly API keys set?
- Chain ID correct (84532 for Base Sepolia)?

**Solution:**
```bash
# Verify Tenderly config
echo $TENDERLY_ACCESS_KEY
echo $TENDERLY_ACCOUNT_SLUG
echo $TENDERLY_PROJECT_SLUG

# Check policy.yaml
grep -A 5 "simulation:" policy.yaml
```

### Issue: No honeypot indicators detected

**Check:**
- LLM validation enabled in policy.yaml?
- OpenAI API key set?
- Model is gpt-4o-mini or better?

**Solution:**
```bash
# Verify OpenAI config
echo $OPENAI_API_KEY

# Check LLM config
grep -A 10 "llm_validation:" policy.yaml
```

### Issue: Balance not showing as fake

**This is expected!** The `honeypot_check_balance` action uses a direct RPC call, not going through PolicyLayer. The fake balance is shown, but it's a read-only operation that demonstrates the scam technique.

---

## What to Expect

### When Honeypot Detection Works ✅

```
You: "Buy honeypot tokens"

Agent: "I'll attempt to buy honeypot tokens..."

PolicyLayer Output:
============================================================
STAGE 3.5: HONEYPOT DETECTION
============================================================
Token BUY detected. Checking if tokens can be sold back...
  Testing sell for token 0xb7695587...
  ⚠️  No Transfer events in sell simulation!
  🚫 HONEYPOT DETECTED

❌ BLOCKED: HONEYPOT DETECTED: Token 0xb7695587... cannot be sold

Agent: "✅ Good news! PolicyLayer blocked this transaction because it
detected a honeypot token. You can buy these tokens but cannot sell
them back. Your funds are protected!"
```

### When Testing Balance Check 📊

```
You: "Check my honeypot balance"

Agent Output:
Balance: 100,000 LEGIT tokens

⚠️ WARNING: This is a FAKE balance!
The honeypot shows 100x the actual balance to trick you.
Real balance is likely 1,000 tokens.
```

---

## Next Steps

1. **Run the tests** using the prompts above
2. **Verify all protections work** as expected
3. **Check logs** for detailed honeypot detection flow
4. **Experiment** with different scenarios

Happy testing! 🛡️