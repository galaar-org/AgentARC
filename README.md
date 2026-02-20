# AgentARC - Security Layer for AI Blockchain Agents

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/galaar-org/AgentARC)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/github-galaar-org)](https://github.com/galaar-org)
[![PyPI version](https://img.shields.io/pypi/v/agentarc.svg)](https://pypi.org/project/agentarc/)


**Advanced security and policy enforcement layer for AI blockchain agents with multi-stage validation, transaction simulation, and threat detection across DeFi + smart-contract attack surfaces, with LLM-based risk analysis.**

## 🎯 Overview

AgentARC provides a comprehensive security framework for AI agents interacting with blockchain networks. It validates all transactions through multiple security stages before execution, reducing exposure to the broader DeFi threat surface and common smart-contract attack planes, including:

- 💰 Unauthorized fund transfers and unexpected value movement
- 🔓 Hidden or unlimited token approvals and allowance abuse
- 🧨 Malicious smart contracts and hostile call chains (e.g., delegatecall to untrusted code)
- 🎣 Token traps (honeypots, sell-blocks, malicious fee mechanics)
- 🌊 Liquidity and price-manipulation patterns (context-dependent)
- 🔄 Reentrancy-style execution hazards and unexpected re-calls
- 🧾 Suspicious fund-flow anomalies and downstream interactions that don’t match intent

These are representative examples, not an exhaustive list. AgentARC is designed to expand with more DeFi and smart-contract threat cases over time.


### Key Features


- ✅ **Multi-Stage Validation Pipeline**: Intent → Policies → Simulation → Threat Detection
- ✅ **Comprehensive Policy Engine**: 7 policy types for granular control
- ✅ **Transaction Simulation**: Tenderly integration for detailed execution traces
- ✅ **Threat Detection (Includes Honeypots)**: Automated checks for token traps and other suspicious patterns
- ✅ **Optional LLM-based Security**: AI-powered malicious activity detection and risk scoring
- ✅ **Zero Agent Modifications**: Pure wrapper pattern for seamless integration
- ✅ **Asset Change Tracking**: Monitor balance changes before execution
- ✅ **Multi-Framework Support**: LangChain, OpenAI SDK and AgentKit
- ✅ **Universal Wallet Support**: Private key, mnemonic and CDP
- ✅ **Event Streaming**: Real-time validation events for frontend integration
- ✅ **Plugin Architecture**: Extensible validators, simulators, and parsers

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

### Integration

#### New API (v0.2.0+) - Universal Wallet

```python
from agentarc import WalletFactory, PolicyWallet

# Create wallet from private key, mnemonic, or CDP
wallet = WalletFactory.from_private_key(
    private_key="0x...",
    rpc_url="https://sepolia.base.org"
)

# Wrap with policy enforcement
policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")

# All transactions now go through multi-stage validation
result = policy_wallet.send_transaction({"to": "0x...", "value": 1000})
```

#### AgentKit Integration (Legacy API)

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

All transactions now go through multi-stage security validation.

---

## 📚 Examples

### 1. Basic Chat Agent (`examples/basic-chat-agent/`)

Production-ready Coinbase AgentKit chatbot with AgentARC and a Next.js frontend.

```bash
cd examples/basic-chat-agent
cp .env.example .env
# Edit .env with your API keys

poetry install
python chatbot.py
```

**Features:**
- ✅ Real CDP wallet integration
- ✅ Interactive chatbot interface
- ✅ Complete policy configuration
- ✅ Next.js frontend with real-time validation events
- ✅ LangGraph server integration

**See:** [Basic Chat Agent Docs](examples/basic-chat-agent/docs/)

### 2. Autonomous Portfolio Agent (`examples/autonomous-portfolio-agent/`)

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
├── agentarc/                    # Main package
│   ├── __init__.py              # Public API exports
│   ├── __main__.py              # CLI entry point
│   ├── core/                    # Core abstractions
│   │   ├── config.py            # PolicyConfig for YAML loading
│   │   ├── types.py             # TypedDict definitions
│   │   ├── errors.py            # Custom exceptions
│   │   ├── interfaces.py        # Protocol definitions
│   │   └── events.py            # Event types
│   ├── engine/                  # Validation pipeline
│   │   ├── policy_engine.py     # Main orchestrator
│   │   ├── pipeline.py          # ValidationPipeline
│   │   ├── context.py           # ValidationContext
│   │   ├── factory.py           # ComponentFactory (DI)
│   │   └── stages/              # Pipeline stages
│   │       ├── intent.py        # Intent parsing
│   │       ├── policy.py        # Policy validation
│   │       ├── simulation.py    # Transaction simulation
│   │       ├── honeypot.py      # Honeypot detection
│   │       └── llm.py           # LLM analysis
│   ├── validators/              # Plugin-based validators
│   │   ├── base.py              # PolicyValidator ABC
│   │   ├── registry.py          # ValidatorRegistry
│   │   └── builtin/             # 7 built-in validators
│   │       ├── address.py       # Allowlist/Denylist
│   │       ├── limits.py        # Value/Token limits
│   │       ├── gas.py           # Gas limit
│   │       └── functions.py     # Function allowlist
│   ├── wallets/                 # Universal wallet support
│   │   ├── base.py              # WalletAdapter ABC
│   │   ├── factory.py           # WalletFactory
│   │   ├── policy_wallet.py     # PolicyWallet wrapper
│   │   └── adapters/            # Wallet implementations
│   │       ├── private_key.py   # PrivateKeyWallet
│   │       ├── mnemonic.py      # MnemonicWallet
│   │       └── cdp.py           # CdpWalletAdapter
│   ├── frameworks/              # Multi-framework adapters
│   │   ├── base.py              # FrameworkAdapter ABC
│   │   ├── agentkit.py          # Coinbase AgentKit
│   │   ├── langchain.py         # LangChain adapter
│   │   └── openai_sdk.py        # OpenAI SDK adapter
│   ├── simulators/              # Transaction simulation
│   │   ├── basic.py             # Basic eth_call simulator
│   │   └── tenderly.py          # Tenderly integration
│   ├── analysis/                # Security analysis
│   │   └── llm_judge.py         # LLM-based threat detection
│   ├── parsers/                 # Calldata parsing
│   │   └── calldata.py          # ABI decoding
│   ├── compat/                  # Legacy compatibility
│   │   └── wallet_wrapper.py    # PolicyWalletProvider
│   ├── log/                     # Logging system
│   │   └── logger.py            # PolicyLogger
│   └── events/                  # Event streaming
│       └── events.py            # EventEmitter
├── examples/                    # Usage examples
│   ├── basic-chat-agent/        # Production chatbot with frontend
│   └── autonomous-portfolio-agent/  # AI portfolio manager
├── tests/                     
├── README.md
├── CHANGELOG.md
└── pyproject.toml
```

---

## 🤝 Compatibility

### Framework Support

AgentARC integrates with popular AI agent frameworks:

- ✅ **Coinbase AgentKit** - Primary integration with full support
- ✅ **LangChain** - LangChainAdapter for LangChain agents
- ✅ **OpenAI SDK** - OpenAIAdapter for function-calling agents

### Wallet Support

Universal wallet support for any blockchain interaction:

- ✅ **Private Key Wallets** - Direct private key management
- ✅ **Mnemonic Wallets** - HD wallet derivation (BIP-39/44)
- ✅ **CDP Wallets** - Coinbase Developer Platform integration

### AgentKit Wallet Providers

For Coinbase AgentKit users:

- ✅ **CDP EVM Wallet Provider**
- ✅ **CDP Smart Wallet Provider**
- ✅ **Ethereum Account Wallet Provider**

---

## 📖 Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and updates
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contributing guidelines
- **[Examples](examples/)** - Sample implementations and demos

---

## 🔒 Security Best Practices

- **Start with restrictive policies** — Use low limits and gradually increase  
- **Enable simulation** — Catch failures before sending transactions  
- **Use Tenderly** — Get detailed execution traces and asset changes  
- **Enable optional LLM validation** — Add AI-powered risk analysis where useful  
- **Test on testnet** — Validate policies on Base Sepolia before mainnet  
- **Monitor logs** — Review transaction validations regularly  
- **Keep denylists updated** — Add known malicious addresses  
- **Enable threat checks** — Automatically catch token traps (honeypots and related patterns) and expand coverage over time  

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
