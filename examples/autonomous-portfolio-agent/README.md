# Autonomous Portfolio Manager with Honeypot Protection

An autonomous AI agent that manages a crypto portfolio on Base Sepolia with **automatic honeypot detection** and multi-layer security protection via PolicyLayer.

## 🎯 What This Demo Shows

This project demonstrates:

1. **Autonomous Portfolio Management** - AI agent automatically rebalances portfolio to maintain target allocation
2. **Honeypot Protection** - Automatically detects and blocks malicious tokens that can be bought but not sold
3. **Multi-Layer Security** - Policy limits, simulation, and LLM-based threat detection
4. **Zero Manual Blacklisting** - Detects unknown honeypots via simulation, not pre-configured lists

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           LangChain Agent (GPT-4 Brain)                      │
│     "Analyze portfolio and rebalance if needed"              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  AgentKit Actions                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Uniswap      │  │ Portfolio    │  │ CDP Wallet       │  │
│  │ - Swap       │  │ - Analyze    │  │ - Transfer       │  │
│  │ - Quote      │  │ - Balance    │  │ - Sign           │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         PolicyWalletProvider (Security Guard)                │
│  ✅ Stage 1: Intent Judge                                    │
│  ✅ Stage 2: Policy Validation (ETH limits, token limits)    │
│  ✅ Stage 3: Tenderly Simulation                             │
│  🛡️  Stage 3.5: HONEYPOT DETECTION (buy→sell test)          │
│  ✅ Stage 4: LLM Security Analysis                           │
└────────────────────────┬────────────────────────────────────┘
                         │ (Only safe transactions)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              CdpEvmWalletProvider (CDP Wallet)               │
│  • Keys in AWS Nitro Enclaves (secure)                       │
│  • Sub-200ms signing latency                                 │
│  • 99.9% availability                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                Base Sepolia Blockchain
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Coinbase Developer Platform (CDP) API credentials
- OpenAI API key
- Tenderly API key (for simulation)

### 1. Installation

```bash
# Navigate to the autonomous-portfolio-agent directory
cd examples/autonomous-portfolio-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install PolicyLayer from project root
cd ../..
pip install -e .
cd examples/autonomous-portfolio-agent
```

### 2. Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Fill in your credentials:

```bash
# Coinbase Developer Platform
# Get from: https://portal.cdp.coinbase.com/
CDP_API_KEY_ID=organizations/xxx/apiKeys/yyy
CDP_API_KEY_SECRET=-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----
CDP_WALLET_SECRET=your_random_secret_string

# OpenAI
OPENAI_API_KEY=sk-proj-...

# Tenderly
TENDERLY_API_KEY=your_tenderly_api_key
TENDERLY_ACCOUNT_SLUG=your_account
TENDERLY_PROJECT_SLUG=your_project

# Network
NETWORK_ID=base-sepolia
```

### 3. Fund Your Wallet

```bash
# Get your wallet address
python -c "from dotenv import load_dotenv; load_dotenv(); from coinbase_agentkit import *; w = CdpEvmWalletProvider(CdpEvmWalletProviderConfig(api_key_id=__import__('os').getenv('CDP_API_KEY_ID'), api_key_secret=__import__('os').getenv('CDP_API_KEY_SECRET'), wallet_secret=__import__('os').getenv('CDP_WALLET_SECRET'), network_id='base-sepolia')); print(w.get_default_address())"

# Fund with Base Sepolia ETH from faucet:
# https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
```

### 4. Run the Agent

```bash
# Run autonomous agent (continuous loop)
python autonomous_agent.py

# Or run demo (scripted scenarios)
python demo_runner.py
```

## 📁 Project Structure

```
autonomous-portfolio-agent/
├── config/
│   ├── portfolio_config.py    # Target allocation, tokens, parameters
│   └── policy.yaml             # PolicyLayer rules (NO manual blacklist!)
│
├── action_providers/
│   ├── uniswap_actions.py      # Uniswap V2 swap & quote actions
│   └── portfolio_actions.py    # Portfolio analysis actions
│
├── core/
│   ├── agent.py                # Main autonomous agent class
│   └── metrics_logger.py       # Tracks trades & blocked attacks
│
├── autonomous_agent.py         # Main entry point (autonomous mode)
├── demo_runner.py              # Demo script (scripted scenarios)
├── README.md                   # This file
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
└── pyproject.toml              # Poetry/pip configuration
```

## 🎮 How It Works

### Autonomous Loop

The agent runs in a continuous loop:

1. **Analyze Portfolio** - Check current allocation vs target
2. **Decide** - LLM decides if rebalancing is needed
3. **Execute** - Swap tokens via Uniswap (if needed)
4. **Validate** - PolicyLayer validates BEFORE execution
5. **Wait** - Sleep for `REBALANCE_INTERVAL` seconds (default: 60s)
6. **Repeat**

### Honeypot Detection (Stage 3.5)

**Key Feature:** Detects honeypots WITHOUT manual blacklisting!

For every token purchase transaction:

```
1. Tenderly simulates BUY transaction
   → Success, receives 1000 tokens

2. Parse Transfer events
   → Detected: owner → user (1000 tokens)

3. Simulate SELL transaction
   → Encode: transfer(0x0...001, 1000)
   → Simulate via Tenderly

4. Check result:
   ✅ Sell succeeds → Safe token, allow purchase
   ❌ Sell fails → HONEYPOT! Block purchase
```

**This works for ANY honeypot technique:**
- ✅ Transfer restrictions (only owner can sell)
- ✅ Hidden blacklists
- ✅ Fake balanceOf() returns
- ✅ Time locks that never unlock
- ✅ Owner-only transfer functions

### PolicyLayer Protection

Multi-stage validation pipeline:

| Stage | Description | Example Block |
|-------|-------------|---------------|
| **Stage 1** | Intent Judge | Parses transaction calldata |
| **Stage 2** | Policy Validation | "Exceeds 0.1 ETH limit" |
| **Stage 3** | Tenderly Simulation | "Transaction would revert" |
| **Stage 3.5** | **Honeypot Detection** | **"Token cannot be sold back"** |
| **Stage 4** | LLM Security Analysis | "Unlimited approval detected" |

## 📊 Configuration

### Portfolio Allocation

Edit `config/portfolio_config.py`:

```python
TARGET_ALLOCATION = {
    "ETH": 0.50,    # 50% in ETH
    "USDC": 0.30,   # 30% in USDC
    "WETH": 0.20,   # 20% in WETH
}

REBALANCE_THRESHOLD = 0.05  # 5% deviation triggers rebalance
REBALANCE_INTERVAL = 60      # Check every 60 seconds
```

### Policy Rules

Edit `config/policy.yaml`:

```yaml
policies:
  # Max ETH per transaction
  - type: eth_value_limit
    max_value_wei: '100000000000000000'  # 0.1 ETH
    enabled: true

  # Per-token limits
  - type: per_asset_limit
    enabled: true
    asset_limits:
      - name: USDC
        address: '0x036CbD53842c5426634e7929541eC2318f3dCF7e'
        max_amount: '50000000'  # 50 USDC

# Simulation (includes honeypot detection)
simulation:
  enabled: true
  provider: 'tenderly'

# LLM security analysis
llm_validation:
  enabled: true
  model: 'gpt-4o-mini'
  block_threshold: 0.70  # 70% confidence → block
```

## 🧪 Testing Honeypot Detection

### Test with Deployed Honeypot Token

A honeypot token is already deployed on Base Sepolia for testing:

```
Address: 0xFe836592564C37D6cE99657c379a387CC5CE0868
```

**To test:**

```python
# In a Python shell (with agent running):
# Send this prompt to the agent:
"Buy 0.1 ETH worth of token at 0xFe836592564C37D6cE99657c379a387CC5CE0868"

# Expected result:
# ❌ BLOCKED by Stage 3.5: Honeypot Detection
# Reason: "Token 0xFe836... can be bought but cannot be sold"
```

### Expected Flow

```
Agent: "Buying 0.1 ETH of token 0xFe836..."

PolicyLayer Validation:
  ✅ Stage 1: Intent Judge - Token purchase detected
  ✅ Stage 2: Policy Check - 0.1 ETH within limit
  ⏳ Stage 3: Tenderly Simulation
      → Simulates buy() call
      → SUCCESS: Receives 1000 tokens
      → Transfer event detected

  🛡️  Stage 3.5: HONEYPOT DETECTION
      → Testing if tokens can be sold...
      → Simulates: transfer(0x0...001, 1000)
      → ❌ SELL FAILED: "Not owner"
      → 🚨 HONEYPOT DETECTED!

  🛑 TRANSACTION BLOCKED

Agent: "⚠️  Transaction blocked - honeypot detected"
```

## 📈 Monitoring

### Metrics

The agent logs all activity to `metrics.json`:

```json
{
  "start_time": "2025-12-30T14:00:00",
  "cycles": [...],
  "trades": [
    {
      "timestamp": "2025-12-30T14:05:00",
      "from_token": "ETH",
      "to_token": "USDC",
      "amount": "0.05",
      "tx_hash": "0xabc..."
    }
  ],
  "blocks": [
    {
      "timestamp": "2025-12-30T14:10:00",
      "attack_type": "honeypot",
      "reason": "Token cannot be sold back",
      "details": {...}
    }
  ]
}
```

### Logs

Check logs in:
- `autonomous_agent.log` - Agent decisions
- `policy_engine.log` - PolicyLayer validation details

## 🔧 Customization

### Add New Tokens

1. Update `config/portfolio_config.py`:

```python
TARGET_ALLOCATION = {
    "ETH": 0.40,
    "USDC": 0.30,
    "WETH": 0.20,
    "LINK": 0.10,  # Add LINK
}

TOKENS = {
    "USDC": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "WETH": "0x4200000000000000000000000000000000000006",
    "LINK": "0x...",  # Add LINK address
}
```

2. Update policy limits in `config/policy.yaml`

### Change Rebalancing Strategy

Edit `core/agent.py`:

```python
# Current: Rebalances if >5% deviation
# Change threshold in portfolio_config.py
REBALANCE_THRESHOLD = 0.10  # 10% threshold
```

## 🐛 Troubleshooting

### "CDP wallet error"
- Verify CDP API credentials in `.env`
- Check that wallet is funded with Base Sepolia ETH

### "Tenderly simulation failed"
- Verify Tenderly API key and project settings
- Check network is set to Base Sepolia (84532)

### "Agent not making trades"
- Check portfolio is unbalanced (>5% deviation)
- Verify wallet has sufficient ETH for gas
- Check logs for PolicyLayer blocks

### "Module not found"
- Run `pip install -r requirements.txt`
- Install PolicyLayer: `pip install -e ../../..`

## 📚 Learn More

- **Coinbase AgentKit**: https://docs.cdp.coinbase.com/agent-kit/welcome
- **PolicyLayer Docs**: See `../../../README.md`
- **Honeypot Research**: https://olympixai.medium.com/erc-20-honeypot-scams
- **Base Sepolia**: https://docs.base.org/docs/network-information

## 🤝 Contributing

This is a demo project. To extend:

1. Fork the repository
2. Add new action providers in `action_providers/`
3. Update portfolio strategies in `core/agent.py`
4. Submit pull request

## ⚠️ Disclaimer

**This is a demo for educational purposes.**

- Use on testnets only (Base Sepolia)
- Not financial advice
- Honeypot detection is best-effort (not 100% guaranteed)
- Always verify transactions before mainnet deployment
- The authors are not responsible for any losses

## 📝 License

MIT License - See LICENSE file

---

**Built with:**
- [Coinbase AgentKit](https://github.com/coinbase/agentkit)
- [LangChain](https://python.langchain.com/)
- [Web3.py](https://web3py.readthedocs.io/)
