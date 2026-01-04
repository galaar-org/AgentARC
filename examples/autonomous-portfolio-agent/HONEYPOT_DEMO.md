# Honeypot Detection Demo

This demo shows how PolicyLayer's **Stage 3.5 Honeypot Detection** automatically blocks malicious token swaps without any manual blacklist.

## 🎯 The Honeypot Token: LEGIT

**Address:** `0xFe836592564C37D6cE99657c379a387CC5CE0868`

### Malicious Features:
1. **Fake balanceOf()** - Shows 100x inflated balances
2. **Transfer Restrictions** - Only owner and whitelisted addresses can sell
3. **Auto-Blacklisting** - Automatically blacklists anyone who tries to sell
4. **Fake Transfer Events** - Emits Transfer events even when transfers fail
5. **Time Lock** - Requires waiting `type(uint256).max` seconds (never unlocks!)

## 🚀 Setup Instructions

### Step 1: Create Uniswap Pool

First, create a Uniswap V3 pool for the honeypot token so it appears tradeable:

```bash
python setup_honeypot_pool.py
```

This will:
- ✅ Create WETH/LEGIT pool on Uniswap V3
- ✅ Initialize price (1 WETH = 10,000 LEGIT)
- ✅ Add initial liquidity (0.1 WETH + 1000 LEGIT)

### Step 2: Run the Autonomous Agent

The autonomous agent is already configured to allocate 10% to LEGIT:

```bash
python autonomous_agent.py
```

## 🛡️ What Happens

### Without PolicyLayer:
```
❌ Agent tries to buy LEGIT tokens
❌ Swap succeeds
❌ Agent receives tokens
❌ Agent tries to sell later (rebalance)
❌ Transfer FAILS - tokens are locked!
❌ User loses funds
```

### With PolicyLayer (Stage 3.5):
```
✅ Agent tries to buy LEGIT tokens
✅ PolicyLayer simulates the BUY
✅ PolicyLayer detects Transfer events (tokens received)
✅ PolicyLayer simulates a SELL (try to transfer tokens back)
❌ SELL simulation FAILS - transfer reverts!
🛡️ PolicyLayer BLOCKS the original BUY transaction
✅ Agent is protected - no funds lost!
```

## 📊 Expected Output

```
======================================================================
CYCLE 1 - 2026-01-02 13:30:00
======================================================================

📋 Starting portfolio analysis...
   💱 Executing swap: 0.1 ETH → LEGIT

============================================================
🔍 POLICYLAYER: Transaction Validation Pipeline
============================================================

Stage 1: Intent Judge - Parsing Transaction
----------------------------------------
✅ Function: exactInputSingle

Stage 2: Policy Validation
----------------------------------------
✅ All policies passed

Stage 3: Transaction Simulation
----------------------------------------
✅ Simulation successful (gas: 166300)

Stage 3.5: Honeypot Detection
----------------------------------------
   🔍 Token BUY detected. Checking if tokens can be sold back...
   🧪 Testing sell for token 0xFe8365...
   ❌ Sell simulation FAILED/REVERTED
🛡️  ❌ BLOCKED: HONEYPOT DETECTED
   Token 0xFe8365... can be bought but cannot be sold
```

## 🎓 Key Takeaways

1. **No Manual Blacklist Needed**
   - PolicyLayer automatically detects honeypots
   - Works for ANY honeypot token, even unknown ones

2. **Proactive Protection**
   - Simulates both BUY and SELL before executing
   - If sell fails → honeypot detected → blocks buy

3. **Zero False Positives**
   - Only blocks if sell actually fails
   - Legitimate tokens pass through fine

4. **Fully Automated**
   - Agent doesn't need any honeypot knowledge
   - PolicyLayer handles all security validation

## 🔬 Technical Details

### How Honeypot Detection Works

```python
# Stage 3.5 in PolicyLayer
1. Simulate original transaction (BUY)
2. Parse Transfer events to detect tokens received
3. For each token received:
   a. Build a test SELL transaction (transfer to burn address)
   b. Simulate the SELL
   c. If SELL fails → HONEYPOT → Block original BUY
4. If all tokens can be sold → Not a honeypot → Allow transaction
```

### Honeypot Token Contract

See: `/tests/contracts/src/HoneypotToken.sol`

The contract implements multiple honeypot techniques:
- Hidden blacklist via external call to BlacklistManager
- balanceOf() manipulation (fake inflated balances)
- Transfer restrictions (silently fails for non-whitelisted)
- Fake Transfer events (emitted even on failure)
- Time-locked transfers that never unlock

## 📚 Resources

- [Olympix: ERC-20 Honeypot Scams](https://olympixai.medium.com/erc-20-honeypot-scams-a-beginners-guide-and-advanced-detection-techniques-4019ed2300e8)
- [Crytic: Not So Smart Contracts - Honeypots](https://github.com/crytic/not-so-smart-contracts/blob/master/honeypots/README.md)
- [Solidity by Example: Honeypot](https://solidity-by-example.org/hacks/honeypot/)

## 🎬 Video Demo

Record your terminal when running `python autonomous_agent.py` to show:
1. Agent analyzes portfolio
2. Detects need to buy LEGIT tokens
3. PolicyLayer validates transaction
4. Stage 3.5 detects honeypot
5. Transaction blocked automatically
6. Agent continues safely with other rebalancing
