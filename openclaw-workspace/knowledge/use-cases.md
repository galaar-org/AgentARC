# AgentARC Use Cases

## 1. Autonomous Portfolio Manager

**Scenario**: AI agent that automatically rebalances a crypto portfolio based on market conditions.

**Risks without AgentARC**:
- Agent buys honeypot token → funds locked forever
- Agent approves unlimited spend to malicious DEX
- Jailbreak attack makes agent transfer all funds to attacker

**With AgentARC**:
```python
# Agent decides to buy token
transaction = agent.prepare_swap(token="0x...", amount=1000)

# AgentARC intercepts
result = arc.validate(transaction)
# Stage 3.5: Simulates sell → Fails
# Result: BLOCKED (honeypot detected)

# Agent never signs, funds safe
```

**Example project**: `examples/autonomous-portfolio-agent/`

---

## 2. DeFi Trading Bot

**Scenario**: High-frequency trading bot executing swaps on Uniswap/SushiSwap.

**Risks without AgentARC**:
- Bot interacts with malicious liquidity pool
- Flash loan attack drains bot's funds
- Sandwich attack extracts value

**With AgentARC**:
- Policy: `function_allowlist: ["swap", "addLiquidity"]`
- Policy: `address_allowlist: [verified_dex_routers]`
- Simulation: Catches unexpected state changes
- LLM Analysis: Detects unusual parameter combinations

**Configuration**:
```yaml
policies:
  eth_value_limit: 10.0
  per_asset_limit:
    USDC: 50000
    WETH: 20
  function_allowlist:
    - "swapExactTokensForTokens"
    - "swapTokensForExactTokens"
  address_allowlist:
    - "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  # Uniswap V2
    - "0xE592427A0AEce92De3Edee1F18E0157C05861564"  # Uniswap V3
```

---

## 3. DAO Treasury Management

**Scenario**: AI assistant helps DAO manage treasury, execute proposals, distribute grants.

**Risks without AgentARC**:
- Compromised agent drains treasury
- Social engineering tricks agent into unauthorized transfers
- Malicious proposal execution

**With AgentARC + Safe**:
- Multi-sig requirement for large transfers
- Policy-based spending limits per recipient
- Simulation ensures proposal execution is safe

**Configuration**:
```yaml
wallet:
  type: safe
  address: "0xDAO_SAFE_ADDRESS"
  threshold: 3  # 3 of 5 signers

policies:
  eth_value_limit: 100.0  # Large treasury needs
  per_asset_limit:
    USDC: 500000
  address_allowlist:
    - "0xGrant_Recipient_1"
    - "0xGrant_Recipient_2"
```

---

## 4. Customer-Facing Wallet Assistant

**Scenario**: Chatbot that helps users manage their crypto (transfer, swap, stake).

**Risks without AgentARC**:
- User tricks chatbot via prompt injection
- Chatbot misunderstands and sends to wrong address
- Phishing attack through chat interface

**With AgentARC**:
- Every user-requested transaction validated
- Confirmation required before signing
- Address verification against known good addresses

**User experience**:
```
User: "Send 1 ETH to vitalik.eth"

Bot: "I'll send 1 ETH to vitalik.eth (0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045)

     Security check:
     ✅ Intent: ETH transfer
     ✅ Policy: Within limits
     ✅ Simulation: Will succeed
     ✅ Address: Verified ENS

     Confirm? [Yes/No]"
```

---

## 5. NFT Minting Bot

**Scenario**: Agent monitors and auto-mints promising NFT drops.

**Risks without AgentARC**:
- Fake mint contracts that steal funds
- Hidden fees in mint function
- Approval traps in NFT contracts

**With AgentARC**:
- Simulation reveals true cost before minting
- LLM Analysis catches suspicious contract patterns
- Policy limits mint spending

---

## 6. Yield Farming Optimizer

**Scenario**: Agent automatically moves funds between yield protocols for best returns.

**Risks without AgentARC**:
- Rug pull protocols
- Infinite approval exploits
- Complex DeFi attack vectors

**With AgentARC**:
```yaml
policies:
  # Limit approvals
  function_allowlist:
    - "deposit"
    - "withdraw"
    - "approve"  # Allowed but monitored

  # Cap approval amounts (no unlimited)
  approval_amount_limit: 10000  # In token units

  # Only verified protocols
  address_allowlist:
    - "0xAave_Pool"
    - "0xCompound_Pool"
    - "0xYearn_Vault"
```

---

## 7. Cross-Chain Bridge Agent

**Scenario**: Agent manages cross-chain transfers via bridges.

**Risks without AgentARC**:
- Bridge exploits (common attack vector)
- Stuck funds from failed bridges
- MEV attacks during bridging

**With AgentARC**:
- Simulation on both chains
- Policy: only verified bridges
- Amount limits per bridge transaction

---

## 8. Gas-Sponsored Agent (ERC-4337)

**Scenario**: Agent executes transactions with gas paid by sponsor (Paymaster).

**Risks without AgentARC**:
- Agent abuses gas sponsorship
- Malicious UserOps drain sponsor
- Bundler attacks

**With AgentARC + ERC-4337**:
```python
from agentarc.wallets import SmartWallet

wallet = SmartWallet(
    bundler_url="https://api.pimlico.io/v1/...",
    paymaster_url="https://api.pimlico.io/v1/..."
)

arc = AgentARC(wallet=wallet, policy="policy.yaml")
# All UserOps validated before bundler submission
```

---

## Industry Applications

| Industry | Use Case | Key AgentARC Features |
|----------|----------|----------------------|
| **DeFi** | Trading bots, yield optimizers | Honeypot detection, simulation |
| **DAOs** | Treasury management | Safe integration, policies |
| **Gaming** | In-game asset trading | Per-asset limits, allowlists |
| **Payments** | Automated disbursements | Address verification, limits |
| **Enterprise** | Compliance-required transactions | Audit trail, policy enforcement |
