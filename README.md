# AgentARC - Security Layer for AI Blockchain Agents

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/galaar-org/AgentARC)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/github-galaar-org%2Fagentarc-blue.svg)](https://github.com/galaar-org/AgentARC)

**Advanced security and policy enforcement layer for AI blockchain agents with multi-stage validation, transaction simulation, honeypot detection, and LLM-based threat analysis.**

## 🎯 Overview

AgentARC provides a comprehensive security framework for AI agents interacting with blockchain networks. It validates all transactions through multiple security stages before execution, protecting against:

- 💰 Unauthorized fund transfers
- 🎣 Phishing and honeypot tokens
- 💣 Malicious smart contracts
- 🔓 Hidden token approvals
- 🌊 Flash loan attacks
- 🔄 Reentrancy exploits

### Key Features

- ✅ **Multi-Stage Validation Pipeline**: Intent → Policies → Simulation → LLM Analysis
- ✅ **Comprehensive Policy Engine**: 7 policy types for granular control
- ✅ **Transaction Simulation**: Tenderly integration for detailed execution traces
- ✅ **Honeypot Detection**: Automatic buy/sell simulation to detect scam tokens
- ✅ **LLM-based Security**: AI-powered malicious activity detection
- ✅ **Zero Agent Modifications**: Pure wrapper pattern for AgentKit
- ✅ **Asset Change Tracking**: Monitor balance changes before execution

---

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install agentarc

# Or install from source
git clone https://github.com/galaar-org/AgentARC.git
cd agentarc
pip install -e .

# Verify installation
agentarc --help
```

### Setup Policy Configuration

```bash
# Generate default policy.yaml
agentarc setup

# Edit policy.yaml to configure your security rules
vim policy.yaml
```

### Integration (3 Lines of Code)

```python
from agentarc import PolicyWalletProvider, PolicyEngine
from coinbase_agentkit import AgentKit, CdpEvmWalletProvider

# Create base wallet
base_wallet = CdpEvmWalletProvider(config)

# Wrap with AgentARC (add security layer)
policy_engine = PolicyEngine(
    config_path="policy.yaml",
    web3_provider=base_wallet,
    chain_id=84532  # Base Sepolia
)
policy_wallet = PolicyWalletProvider(base_wallet, policy_engine)

# Use with AgentKit - no other changes needed!
agentkit = AgentKit(wallet_provider=policy_wallet, action_providers=[...])
```

That's it! All transactions now go through multi-stage security validation.

---

## 📚 Examples

### 1. Basic Usage (`examples/basic_usage.py`)

Simple demonstration with mock wallet provider.

```bash
cd examples
python basic_usage.py
```

**Features:**
- Mock wallet implementation
- Policy validation examples
- Error handling demonstration

### 2. OnChain Agent (`examples/onchain-agent/`)

Production-ready Coinbase AgentKit chatbot with AgentARC.

```bash
cd examples/onchain-agent
cp .env.example .env
# Edit .env with your API keys

pip install -r requirements.txt
python chatbot.py
```

**Features:**
- ✅ Real CDP wallet integration
- ✅ Interactive chatbot interface
- ✅ Complete policy configuration

**See:** [OnChain Agent README](examples/onchain-agent/README.md)

### 3. Autonomous Portfolio Agent (`examples/autonomous-portfolio-agent/`)

AI agent that autonomously manages a crypto portfolio with honeypot protection.

```bash
cd examples/autonomous-portfolio-agent
cp .env.example .env
# Edit .env

pip install -r requirements.txt
python autonomous_agent.py
```

**Features:**
- ✅ Autonomous portfolio rebalancing
- ✅ Automatic honeypot detection
- ✅ Multi-layer security (policies + simulation + LLM)
- ✅ Zero manual blacklisting
- ✅ Demonstrates honeypot token blocking in action

**See:** [Autonomous Portfolio Agent README](examples/autonomous-portfolio-agent/README.md) and [Honeypot Demo](examples/autonomous-portfolio-agent/HONEYPOT_DEMO.md)

---

## 🛡️ Security Pipeline

AgentARC validates every transaction through 4 stages:

### Stage 1: Intent Judge
- Parse transaction calldata
- Identify function calls and parameters
- Detect token transfers and approvals

### Stage 2: Policy Validation
- ETH value limits
- Address allowlist/denylist
- Per-asset spending limits
- Gas limits
- Function allowlists

### Stage 3: Transaction Simulation
- Tenderly simulation with full execution traces
- Asset/balance change tracking
- Gas estimation
- Revert detection

### Stage 3.5: Honeypot Detection
- Simulate token BUY transaction
- Automatically test SELL transaction
- Block if tokens cannot be sold back
- **Zero manual blacklisting needed**

### Stage 4: LLM Security Analysis (Optional)
- AI-powered malicious pattern detection
- Hidden approval detection
- Unusual fund flow analysis
- Risk scoring and recommendations

---

## 📋 Policy Types

### 1. ETH Value Limit

Prevent large ETH transfers per transaction.

```yaml
policies:
  - type: eth_value_limit
    max_value_wei: "1000000000000000000"  # 1 ETH
    enabled: true
    description: "Limit ETH transfers to 1 ETH per transaction"
```

### 2. Address Denylist

Block transactions to sanctioned or malicious addresses.

```yaml
policies:
  - type: address_denylist
    denied_addresses:
      - "0xSanctionedAddress1..."
      - "0xMaliciousContract..."
    enabled: true
    description: "Block transactions to denied addresses"
```

### 3. Address Allowlist

Only allow transactions to pre-approved addresses (whitelist mode).

```yaml
policies:
  - type: address_allowlist
    allowed_addresses:
      - "0xTrustedContract1..."
      - "0xTrustedContract2..."
    enabled: false  # Disabled by default
    description: "Only allow transactions to approved addresses"
```

### 4. Per-Asset Limits

Different spending limits for each token.

```yaml
policies:
  - type: per_asset_limit
    asset_limits:
      - name: USDC
        address: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        max_amount: "10000000"  # 10 USDC
        decimals: 6
      - name: DAI
        address: "0x6B175474E89094C44Da98b954EedeAC495271d0F"
        max_amount: "100000000000000000000"  # 100 DAI
        decimals: 18
    enabled: true
    description: "Per-asset spending limits"
```

### 5. Token Amount Limit

Limit token transfers across all ERC20 tokens.

```yaml
policies:
  - type: token_amount_limit
    max_amount: "1000000000000000000000"  # 1000 tokens (18 decimals)
    enabled: false
    description: "Limit token transfers per transaction"
```

### 6. Gas Limit

Prevent expensive transactions.

```yaml
policies:
  - type: gas_limit
    max_gas: 500000
    enabled: true
    description: "Limit gas to 500k per transaction"
```

### 7. Function Allowlist

Only allow specific function calls.

```yaml
policies:
  - type: function_allowlist
    allowed_functions:
      - "eth_transfer"
      - "transfer"
      - "approve"
      - "swap"
    enabled: false
    description: "Only allow specific function calls"
```

---

## 🔬 Advanced Features

### Tenderly Simulation

Enable advanced transaction simulation with full execution traces and asset tracking:

```yaml
simulation:
  enabled: true
  fail_on_revert: true
  estimate_gas: true
  print_trace: false  # Set to true for detailed execution traces
```

**Setup Tenderly (optional but recommended):**

```bash
# Add to .env
TENDERLY_ACCESS_KEY=your_access_key
TENDERLY_ACCOUNT_SLUG=your_account
TENDERLY_PROJECT_SLUG=your_project
```

**Capabilities:**
- ✅ Full call trace analysis
- ✅ Asset/balance change tracking
- ✅ Event log decoding
- ✅ Gas prediction
- ✅ State modification tracking

**Output Example:**
```
Stage 3: Transaction Simulation
✅ Simulation successful (gas: 166300)
Asset changes:
  0x1234567... (erc20): +1000
  0xabcdef0... (erc20): -500
```

**With `print_trace: true`:**
```
Tenderly Simulation Details
----------------------------------------
Call Trace:
  [1] CALL: 0x1234567... → 0xabcdef0... (value: 0.5 ETH, gas: 50000)
    [1] DELEGATECALL: 0xabcdef0... → 0x9876543... (value: 0 ETH, gas: 30000)
    [2] CALL: 0xabcdef0... → 0x5555555... (value: 0 ETH, gas: 15000)

Asset/Balance Changes:
  0x1234567... (erc20): +1000
  0xabcdef0... (erc20): -500

Events Emitted:
  [1] Transfer
  [2] Approval
  [3] Swap
```

### LLM-based Security Validation

Enable AI-powered malicious activity detection:

```yaml
llm_validation:
  enabled: true
  provider: "openai"  # or "anthropic"
  model: "gpt-4o-mini"
  api_key: "${OPENAI_API_KEY}"  # or set in environment
  block_threshold: 0.70  # Block if confidence >= 70%
  warn_threshold: 0.40   # Warn if confidence >= 40%
```

**What LLM Analyzes:**
- Hidden token approvals
- Unusual fund flow patterns
- Reentrancy attack patterns
- Flash loan exploits
- Sandwich/MEV attacks
- Phishing attempts
- Hidden fees and draining
- Delegatecall to untrusted contracts
- Honeypot token indicators

**Example Output:**
```
Stage 4: LLM-based Security Validation
⚠️  LLM warning: Detected unlimited token approval to unknown contract
Confidence: 65% | Risk: MEDIUM
Indicators: unlimited_approval, unknown_recipient
```

### Honeypot Detection

Automatically detect scam tokens that can be bought but not sold:

**How it works:**
1. Transaction initiates a token purchase (BUY)
2. AgentARC simulates the BUY
3. Detects token receipt via Transfer events
4. Automatically simulates a SELL transaction
5. If SELL fails → **HONEYPOT DETECTED** → Block original BUY

**Configuration:**
```yaml
# Honeypot detection is automatic when Tenderly simulation is enabled
simulation:
  enabled: true
```

**Example Output:**
```
Stage 3.5: Honeypot Detection
🔍 Token BUY detected. Checking if tokens can be sold back...
🧪 Testing sell for token 0xFe8365...
❌ Sell simulation FAILED/REVERTED
🛡️  ❌ BLOCKED: HONEYPOT DETECTED
   Token 0xFe8365... can be bought but cannot be sold
```

---

## 📊 Logging Levels

Control output verbosity in `policy.yaml`:

```yaml
logging:
  level: info  # minimal, info, or debug
```

- **minimal**: Only final decisions (ALLOWED/BLOCKED)
- **info**: Full validation pipeline (recommended)
- **debug**: Detailed debugging information including trace counts

---

## 🔧 Complete Configuration Example

`policy.yaml`:

```yaml
version: "2.0"
apply_to: [all]

# Logging configuration
logging:
  level: info  # minimal, info, debug

# Policy rules
policies:
  - type: eth_value_limit
    max_value_wei: "1000000000000000000"  # 1 ETH
    enabled: true
    description: "Limit ETH transfers to 1 ETH per transaction"

  - type: address_denylist
    denied_addresses: []
    enabled: true
    description: "Block transactions to denied addresses"

  - type: address_allowlist
    allowed_addresses: []
    enabled: false
    description: "Only allow transactions to approved addresses"

  - type: per_asset_limit
    asset_limits:
      - name: USDC
        address: "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
        max_amount: "10000000"  # 10 USDC
        decimals: 6
      - name: DAI
        address: "0x6B175474E89094C44Da98b954EedeAC495271d0F"
        max_amount: "100000000000000000000"  # 100 DAI
        decimals: 18
    enabled: true
    description: "Per-asset spending limits"

  - type: token_amount_limit
    max_amount: "1000000000000000000000"  # 1000 tokens
    enabled: false
    description: "Limit token transfers per transaction"

  - type: function_allowlist
    allowed_functions:
      - "eth_transfer"
      - "transfer"
      - "approve"
    enabled: false
    description: "Only allow specific function calls"

  - type: gas_limit
    max_gas: 500000
    enabled: true
    description: "Limit gas to 500k per transaction"

# Transaction simulation
simulation:
  enabled: true
  fail_on_revert: true
  estimate_gas: true
  print_trace: false  # Enable for detailed execution traces

# Calldata validation
calldata_validation:
  enabled: true
  strict_mode: false

# LLM-based validation (optional)
llm_validation:
  enabled: false
  provider: "openai"
  model: "gpt-4o-mini"
  api_key: "${OPENAI_API_KEY}"
  block_threshold: 0.70
  warn_threshold: 0.40
```

---

## 🧪 Testing

Run the test suite:

```bash
cd tests
python test_complete_system.py
```

**Tests cover:**
- ETH value limits
- Address denylist/allowlist
- Per-asset limits
- Gas limits
- Calldata parsing
- All logging levels

---

## 🏗️ Project Structure

```
agentarc/
├── agentarc/                 # Main package
│   ├── __init__.py
│   ├── __main__.py             # CLI entry point
│   ├── policy_engine.py        # Multi-stage validation pipeline
│   ├── wallet_wrapper.py       # Wallet provider wrapper
│   ├── calldata_parser.py      # ABI decoding
│   ├── simulator.py            # Basic transaction simulation
│   ├── logger.py               # Logging system
│   ├── llm_judge.py            # LLM-based security analysis
│   ├── simulators/
│   │   └── tenderly.py         # Tenderly integration
│   └── rules/                  # Policy validators
│       ├── __init__.py
│       └── validators.py
├── examples/                   # Usage examples
│   ├── basic_usage.py
│   ├── onchain-agent/          # Production chatbot
│   └── autonomous-portfolio-agent/  # Autonomous agent
├── tests/                      # Test suite
├── README.md
├── CHANGELOG.md
└── pyproject.toml
```

---

## 🤝 Compatibility

AgentARC works with all Coinbase AgentKit wallet providers:

- ✅ **CDP EVM Wallet Provider**
- ✅ **CDP Smart Wallet Provider**
- ✅ **Ethereum Account Wallet Provider**

Same 3-line integration pattern for all wallet types!

---

## 📖 Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and updates
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contributing guidelines
- **[Examples](examples/)** - Sample implementations and demos

---

## 🔒 Security Best Practices

1. **Start with restrictive policies** - Use low limits and gradually increase
2. **Enable simulation** - Catch failures before sending transactions
3. **Use Tenderly** - Get detailed execution traces and asset changes
4. **Enable LLM validation** - Add AI-powered threat detection
5. **Test on testnet** - Validate policies on Base Sepolia before mainnet
6. **Monitor logs** - Review transaction validations regularly
7. **Keep denylists updated** - Add known malicious addresses
8. **Enable honeypot detection** - Protect against scam tokens automatically

---

## 🛠️ Environment Variables

```bash
# Coinbase CDP (required for real wallet)
CDP_API_KEY_NAME=your_cdp_key_name
CDP_API_KEY_PRIVATE_KEY=your_cdp_private_key

# LLM Provider (optional - for Stage 4)
OPENAI_API_KEY=your_openai_key
# OR
ANTHROPIC_API_KEY=your_anthropic_key

# Tenderly (optional - for advanced simulation)
TENDERLY_ACCESS_KEY=your_tenderly_key
TENDERLY_ACCOUNT_SLUG=your_account
TENDERLY_PROJECT_SLUG=your_project
```

---

## 🎯 Use Cases

- 🤖 **AI Trading Bots** - Prevent unauthorized trades and limit exposure
- 💼 **Portfolio Managers** - Enforce spending limits across assets
- 🏦 **Treasury Management** - Multi-signature with policy enforcement
- 🎮 **GameFi Agents** - Limit in-game asset transfers
- 🔐 **Security Testing** - Validate smart contract interactions
- 🛡️ **Honeypot Protection** - Automatically detect and block scam tokens

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 🆘 Support

- **Issues:** [GitHub Issues](https://github.com/galaar-org/AgentARC/issues)
- **Examples:** [examples/](examples/)
- **Documentation:** [README.md](README.md)

---

**Protect your AI agents with AgentARC - Multi-layer security for blockchain interactions** 🛡️
