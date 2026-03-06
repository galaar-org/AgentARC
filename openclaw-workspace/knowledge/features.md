# AgentARC Features

## 4-Stage Security Pipeline

Every transaction passes through these stages before signing:

### Stage 1: Intent Analysis
- Parses transaction calldata using ABI decoding
- Identifies function being called
- Extracts parameters (addresses, amounts, tokens)
- Determines transaction type (transfer, swap, approve, etc.)

**What it catches**: Misidentified transactions, unexpected function calls

### Stage 2: Policy Validation
Configurable rule-based checks via `policy.yaml`:

| Policy | Description | Example |
|--------|-------------|---------|
| `eth_value_limit` | Max ETH per transaction | `1.0` (blocks >1 ETH transfers) |
| `address_denylist` | Blocked addresses | Sanctioned wallets, known scams |
| `address_allowlist` | Whitelist mode | Only approved contracts |
| `per_asset_limit` | Token-specific limits | Max 1000 USDC per tx |
| `token_amount_limit` | Global ERC-20 limit | Any token transfer cap |
| `gas_limit` | Max gas allowed | Prevents expensive txs |
| `function_allowlist` | Allowed functions only | `["transfer", "swap"]` |

**What it catches**: Over-limit transactions, blacklisted addresses, unauthorized functions

### Stage 3: Transaction Simulation
- Uses Tenderly sandbox environment
- Executes transaction without spending gas
- Analyzes state changes
- Detects reverts before they cost money

**What it catches**: Transactions that would fail, unexpected state changes

### Stage 3.5: Honeypot Detection
- Triggers automatically when BUY transaction detected
- Simulates corresponding SELL transaction
- If sell fails → blocks the buy
- Zero manual blacklist maintenance

**What it catches**: Honeypot tokens (buy succeeds, sell fails)

### Stage 4: LLM Security Analysis (Optional)
AI-powered threat detection using Claude or GPT-4:

- Hidden token approvals
- Reentrancy patterns
- Flash loan exploit signatures
- Phishing contract patterns
- Hidden fees and fund draining
- Unusual parameter combinations

**Cost**: ~$0.003 per transaction with gpt-4o-mini

**What it catches**: Sophisticated attacks that rule-based checks miss

---

## Wallet Support

Universal compatibility with single API:

### EOA (Externally Owned Account)
- Standard private key wallets
- Direct transaction signing
- Simplest setup

### ERC-4337 (Account Abstraction)
- Smart contract wallets
- Gas sponsorship via Paymasters
- Bundler integration (Pimlico, Alchemy)
- Session keys support

### Safe (Gnosis Safe)
- Multi-signature wallets
- Team/DAO treasury management
- Threshold signing
- Transaction queue

### CDP (Coinbase Developer Platform)
- Coinbase-managed wallets
- Institutional custody
- API-based signing

**Key benefit**: Change wallet type with one line of code, same agent logic.

---

## Framework Adapters

### OpenAI SDK
```python
from agentarc.frameworks.openai import OpenAIAdapter

adapter = OpenAIAdapter(arc)
tools = adapter.get_tools()
# Use with OpenAI function calling
```

### LangChain / LangGraph
```python
from agentarc.frameworks.langchain import LangChainAdapter

adapter = LangChainAdapter(arc)
tools = adapter.get_langchain_tools()
# Use with LangChain agents
```

### Coinbase AgentKit
```python
from agentarc.frameworks.agentkit import AgentKitAdapter

adapter = AgentKitAdapter(arc)
# Wraps AgentKit with security layer
```

---

## CLI Scaffolding Tool

Interactive project generator:

```bash
agentarc setup
```

**Features**:
- Choose wallet type (EOA, ERC-4337, Safe, CDP)
- Choose framework (OpenAI, LangChain, AgentKit)
- Generates complete project:
  - `agent.py` - Working agent code
  - `policy.yaml` - Security policies
  - `.env.example` - Required environment variables
  - `requirements.txt` - Dependencies
  - `.gitignore` - Proper ignores

**12 template combinations** for all wallet × framework permutations.

---

## Configuration

### policy.yaml Example

```yaml
version: "1.0"

validation:
  intent_analysis: true
  policy_check: true
  simulation: true
  honeypot_detection: true
  llm_analysis: false  # Enable for $0.003/tx

policies:
  eth_value_limit: 1.0
  gas_limit: 500000

  address_denylist:
    - "0x123..."  # Known scam

  function_allowlist:
    - "transfer"
    - "approve"
    - "swap"

logging:
  level: info  # minimal, info, debug

simulation:
  provider: tenderly
  # TENDERLY_API_KEY in env
```

---

## Supported Blockchains

| Network | Chain ID | Status |
|---------|----------|--------|
| Ethereum Mainnet | 1 | Supported |
| Ethereum Sepolia | 11155111 | Supported |
| Base Mainnet | 8453 | Supported |
| Base Sepolia | 84532 | Supported |
| Arbitrum One | 42161 | Supported |
| Arbitrum Sepolia | 421614 | Supported |
| Optimism Mainnet | 10 | Supported |
| Optimism Sepolia | 11155420 | Supported |

---

## Event Streaming

Real-time validation events for frontend integration:

```python
arc = AgentARC.from_policy("policy.yaml", streaming=True)

for event in arc.validate_stream(transaction):
    print(f"Stage: {event.stage}, Status: {event.status}")
    # Update UI in real-time
```

Events include: stage entry, stage result, warnings, final verdict.
