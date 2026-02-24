# AgentARC - Security Layer for AI Blockchain Agents

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/galaar-org/AgentARC)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/github-galaar-org)](https://github.com/galaar-org)
[![PyPI version](https://img.shields.io/pypi/v/agentarc.svg)](https://pypi.org/project/agentarc/)

**Advanced security and policy enforcement layer for AI blockchain agents with multi-stage validation, transaction simulation, and threat detection across DeFi + smart-contract attack surfaces, with LLM-based risk analysis.**

---

## What is AgentARC?

AgentARC sits between your AI agent and the blockchain. Every transaction the agent wants to send passes through a 4-stage validation pipeline **before signing** — catching threats that would otherwise reach the chain.

```
Agent wants to send a transaction
          │
          ▼
┌─────────────────────────────────────┐
│         AgentARC Pipeline           │
│                                     │
│  Stage 1: Intent Analysis           │
│  → parse calldata, identify action  │
│                                     │
│  Stage 2: Policy Validation         │
│  → spending limits, allow/denylists │
│                                     │
│  Stage 3: Transaction Simulation    │
│  → Tenderly sandbox test            │
│                                     │
│  Stage 3.5: Honeypot Detection      │
│  → test buy + sell before buying    │
│                                     │
│  Stage 4: LLM Security Analysis     │
│  → AI threat detection (optional)   │
└──────────────┬──────────────────────┘
               │
      BLOCKED ─┤─ APPROVED
               │
               ▼
        Wallet executes
   (EOA / ERC-4337 / Safe / CDP)
```

Threats it catches:

- Unauthorized fund transfers and unexpected value movement
- Hidden or unlimited token approvals and allowance abuse
- Malicious smart contracts and hostile call chains
- Token traps (honeypots, sell-blocks, malicious fee mechanics)
- Liquidity and price-manipulation patterns
- Reentrancy-style execution hazards
- Suspicious fund-flow anomalies

---

## Key Features

- **Multi-Stage Validation Pipeline** — Intent → Policies → Simulation → Threat Detection
- **7 Policy Types** — ETH limits, address allow/denylists, per-asset limits, gas limits, function allowlists
- **Universal Wallet Support** — EOA, ERC-4337 smart wallets, Safe multisig, Coinbase CDP
- **Framework Adapters** — OpenAI SDK, LangChain, AgentKit — same API for all
- **Transaction Simulation** — Tenderly integration for full execution traces
- **Honeypot Detection** — Automatically test buy + sell before any token purchase
- **LLM Security Analysis** — AI-powered malicious pattern detection (optional)
- **Interactive CLI Wizard** — Scaffold a new project in under a minute

---

## Quick Start

### Installation

```bash
# Core install (EOA + CDP wallets, no framework adapters)
pip install agentarc

# With OpenAI SDK support
pip install agentarc[openai]

# With LangChain support
pip install agentarc[langchain]

# With ERC-4337 smart wallet support
pip install agentarc[smart-wallets]

# With Safe multisig support
pip install agentarc[safe]

# Everything
pip install agentarc[all]
```

### Scaffold a new project (recommended)

The interactive CLI wizard creates a complete project for your chosen wallet type and framework:

```bash
agentarc setup
```

```
==================================================
          AgentARC Setup Wizard
==================================================

Is this for an existing or new project? [existing/new]: new
Enter your project name [my-secure-agent]: my-agent
Choose your agent framework [openai/langchain]: openai
Choose wallet type [eoa/erc4337/safe/cdp]: eoa
Choose network (number or name) [1]: 1   (Base Sepolia)
Select policy templates: 1,2             (Spending Limits + Denylist)

Project created at: ./my-agent

Files created:
  agent.py            <- EOA + OPENAI agent
  policy.yaml         <- Off-chain policy config
  .env.example        <- Environment variables for EOA
  requirements.txt    <- Python dependencies
  .gitignore

Next steps:
  cd my-agent
  cp .env.example .env
  # Add your keys to .env
  pip install -r requirements.txt
  python agent.py
```

The wizard supports all combinations of wallet × framework and generates the correct `agent.py`, `policy.yaml`, `.env.example`, and `requirements.txt` for each.

---

## Wallet Support

AgentARC works with four wallet types. Your agent code changes by **one line**:

```python
from agentarc import WalletFactory, PolicyWallet, OpenAIAdapter

# EOA — normal private key wallet
wallet = WalletFactory.from_private_key(private_key, rpc_url)

# ERC-4337 — smart contract wallet, transactions go through a bundler
wallet = WalletFactory.from_erc4337(owner_key, bundler_url, rpc_url)

# Safe — Gnosis Safe multisig wallet
wallet = WalletFactory.from_safe(safe_address, signer_key, rpc_url)

# CDP — Coinbase Developer Platform wallet
wallet = WalletFactory.from_cdp(cdp_provider)

# Everything below is identical for all four wallet types
policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")
adapter = OpenAIAdapter()
tools = adapter.create_all_tools(policy_wallet)
```

### Wallet type comparison

| | EOA | ERC-4337 | Safe | CDP |
|--|--|--|--|--|
| Wallet address | key address | smart contract | safe contract | CDP managed |
| Gas sponsorship | no | yes (Paymaster) | no | no |
| Multi-signature | no | no | yes | no |
| Requires bundler | no | yes | no | no |
| Best for | testing, simple agents | production agents | teams, DAOs | AgentKit |

### ERC-4337 specifics

The smart account address is **counterfactual** — derived from your owner key before the contract is deployed. Fund the smart account address and it auto-deploys on first transaction.

```python
wallet = WalletFactory.from_erc4337(
    owner_key=os.environ["OWNER_PRIVATE_KEY"],
    bundler_url="https://api.pimlico.io/v2/84532/rpc?apikey=...",
    rpc_url="https://sepolia.base.org",
)

wallet.get_address()        # smart account address (holds funds)
wallet.get_owner_address()  # owner EOA address (signs UserOps)
wallet.is_deployed()        # False until first transaction
```

Get a free bundler URL at [pimlico.io](https://pimlico.io) or [alchemy.com](https://alchemy.com).

### Safe specifics

```python
wallet = WalletFactory.from_safe(
    safe_address=os.environ["SAFE_ADDRESS"],
    signer_key=os.environ["SIGNER_PRIVATE_KEY"],
    rpc_url="https://sepolia.base.org",
    auto_execute=True,  # execute immediately if threshold == 1
)

wallet.get_address()      # Safe contract address (holds funds)
wallet.get_owner_address() # signer EOA address
wallet.get_threshold()    # number of required signatures
wallet.get_owners()       # list of all Safe owner addresses
```

Deploy a Safe for free at [app.safe.global](https://app.safe.global).

---

## Framework Support

AgentARC has adapters for OpenAI SDK and LangChain. Both work identically with any wallet type.

### OpenAI SDK

```python
from agentarc import WalletFactory, PolicyWallet
from agentarc.frameworks import OpenAIAdapter
from openai import OpenAI

wallet = WalletFactory.from_private_key(os.environ["PRIVATE_KEY"], os.environ["RPC_URL"])
policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")

adapter = OpenAIAdapter()
tools = adapter.create_all_tools(policy_wallet)
# tools: send_transaction, get_wallet_balance, get_wallet_info, validate_transaction

client = OpenAI()
response = client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
tool_results = adapter.process_tool_calls(response, policy_wallet)
```

### LangChain + LangGraph

```python
from agentarc import WalletFactory, PolicyWallet
from agentarc.frameworks import LangChainAdapter
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

wallet = WalletFactory.from_private_key(os.environ["PRIVATE_KEY"], os.environ["RPC_URL"])
policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")

adapter = LangChainAdapter()
tools = adapter.create_all_tools(policy_wallet)  # List[StructuredTool]

llm = ChatOpenAI(model="gpt-4o-mini")
agent = create_react_agent(llm, tools=tools)
```

---

## Security Pipeline

### Stage 1: Intent Analysis
Parses transaction calldata to understand what the transaction does — identifies function calls, token transfers, approvals, and parameter values.

### Stage 2: Policy Validation
Runs all enabled policy rules against the transaction:

| Policy | What it blocks |
|--------|---------------|
| `eth_value_limit` | ETH transfers above a max per transaction |
| `address_denylist` | Transactions to specific blocked addresses |
| `address_allowlist` | Transactions to any address not on the list |
| `per_asset_limit` | ERC-20 transfers above a per-token limit |
| `token_amount_limit` | ERC-20 transfers above a global limit |
| `gas_limit` | Transactions requesting more than a gas cap |
| `function_allowlist` | Any function call not on the allowed list |

### Stage 3: Transaction Simulation
Simulates the transaction in a Tenderly sandbox before sending. Catches reverts, unexpected asset changes, and gas spikes without spending real gas.

### Stage 3.5: Honeypot Detection
When a token BUY is detected, AgentARC automatically simulates a SELL. If the sell fails, the buy is blocked — zero manual blacklisting required.

```
BUY detected → simulate SELL → SELL fails → HONEYPOT BLOCKED
```

### Stage 4: LLM Security Analysis (optional)
Uses an LLM to detect sophisticated attacks that rule-based checks miss:
- Hidden token approvals
- Reentrancy patterns
- Flash loan exploits
- Phishing contracts
- Hidden fees and fund draining

Cost: ~$0.003 per transaction with `gpt-4o-mini`.

---

## Policy Configuration

```yaml
# policy.yaml
version: "2.0"
enabled: true

logging:
  level: info  # minimal | info | debug

policies:
  - type: eth_value_limit
    enabled: true
    max_value_wei: "1000000000000000000"  # 1 ETH

  - type: address_denylist
    enabled: true
    denied_addresses:
      - "0xScamAddress..."

  - type: per_asset_limit
    enabled: true
    asset_limits:
      - name: USDC
        address: "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
        max_amount: "10000000"  # 10 USDC
        decimals: 6

  - type: gas_limit
    enabled: true
    max_gas: 500000

simulation:
  enabled: true
  fail_on_revert: true
  estimate_gas: true

llm_validation:
  enabled: false          # set true to enable AI threat detection
  provider: openai
  model: gpt-4o-mini
  block_threshold: 0.70
  warn_threshold: 0.40
```

---

## Examples

### basic-chat-agent (`examples/basic-chat-agent/`)

A simple chat agent using a normal EOA wallet. Good starting point for understanding the AgentARC integration pattern.

```bash
cd examples/basic-chat-agent
cp .env.example .env
# Add PRIVATE_KEY, RPC_URL, OPENAI_API_KEY to .env
pip install -r requirements.txt
python openai_chat_agent.py    # OpenAI SDK version
python langchain_chat_agent.py # LangChain version
```

See [examples/basic-chat-agent/README.md](examples/basic-chat-agent/README.md)

### smart-wallet-agents (`examples/smart-wallet-agents/`)

Chat agents using ERC-4337 and Safe wallets. Demonstrates that the agent code is identical to the EOA version — only the wallet setup changes.

```bash
cd examples/smart-wallet-agents
cp .env.example .env

# ERC-4337 smart wallet agent
# Add OWNER_PRIVATE_KEY, BUNDLER_URL, RPC_URL, OPENAI_API_KEY to .env
python erc4337_agent.py

# Safe multisig agent
# Add SAFE_ADDRESS, SIGNER_PRIVATE_KEY, RPC_URL, OPENAI_API_KEY to .env
python safe_agent.py
```

See [examples/smart-wallet-agents/README.md](examples/smart-wallet-agents/README.md)

### autonomous-portfolio-agent (`examples/autonomous-portfolio-agent/`)

Autonomous agent that manages a crypto portfolio with automatic honeypot protection.

```bash
cd examples/autonomous-portfolio-agent
cp .env.example .env
pip install -r requirements.txt
python autonomous_agent.py
```

See [examples/autonomous-portfolio-agent/README.md](examples/autonomous-portfolio-agent/README.md)

---

## Project Structure

```
agentarc/
├── agentarc/
│   ├── __init__.py                 # Top-level exports
│   ├── __main__.py                 # CLI entry point (agentarc setup)
│   ├── cli/
│   │   ├── wizard.py               # Interactive setup wizard
│   │   └── templates/              # Agent + env templates (8 wallet×framework combos)
│   ├── core/
│   │   ├── types.py                # TransactionRequest, TransactionResult, WalletType
│   │   └── config.py               # PolicyConfig (YAML loading)
│   ├── wallets/
│   │   ├── base.py                 # WalletAdapter abstract base class
│   │   ├── factory.py              # WalletFactory (from_private_key, from_erc4337, etc.)
│   │   ├── policy_wallet.py        # PolicyWallet (wraps any WalletAdapter)
│   │   └── adapters/
│   │       ├── private_key.py      # EOA private key wallet
│   │       ├── mnemonic.py         # HD mnemonic wallet
│   │       ├── cdp.py              # Coinbase CDP wallet
│   │       ├── smart_wallet_base.py # SmartWalletAdapter abstract base
│   │       ├── erc4337.py          # ERC-4337 UserOperation wallet
│   │       └── safe_adapter.py     # Gnosis Safe multisig wallet
│   ├── frameworks/
│   │   ├── openai_sdk.py           # OpenAIAdapter
│   │   ├── langchain.py            # LangChainAdapter
│   │   └── agentkit.py             # AgentKitAdapter
│   ├── engine/                     # Validation pipeline
│   └── validators/                 # Policy validator plugins
│
├── examples/
│   ├── basic-chat-agent/           # EOA wallet + OpenAI/LangChain
│   ├── smart-wallet-agents/        # ERC-4337 + Safe wallet agents
│   └── autonomous-portfolio-agent/ # Autonomous portfolio agent
│
└── tests/
    ├── test_smart_wallets.py       # ERC-4337 + Safe adapter tests
    └── test_cli_setup.py           # CLI wizard tests
```

---

## Testing

```bash
# Run smart wallet adapter tests
python -m pytest tests/test_smart_wallets.py -v    # 26 tests

# Run CLI wizard tests
python -m pytest tests/test_cli_setup.py -v        # 29 tests

# Run all
python -m pytest tests/test_smart_wallets.py tests/test_cli_setup.py -v
```

---

## Environment Variables

```bash
# EOA wallet
PRIVATE_KEY=0x...
RPC_URL=https://sepolia.base.org

# ERC-4337 smart wallet
OWNER_PRIVATE_KEY=0x...
BUNDLER_URL=https://api.pimlico.io/v2/84532/rpc?apikey=...
RPC_URL=https://sepolia.base.org

# Safe multisig
SAFE_ADDRESS=0x...
SIGNER_PRIVATE_KEY=0x...
RPC_URL=https://sepolia.base.org

# CDP wallet
CDP_API_KEY_NAME=your_key_name
CDP_API_KEY_PRIVATE_KEY=your_key
NETWORK_ID=base-sepolia

# OpenAI (for agent + optional LLM validation)
OPENAI_API_KEY=sk-...

# Tenderly simulation (optional — Stage 3)
TENDERLY_ACCESS_KEY=your_key
TENDERLY_ACCOUNT_SLUG=your_account
TENDERLY_PROJECT_SLUG=your_project
```

---

## Security Best Practices

- **Start restrictive** — low ETH limits, small allow lists, then loosen as needed
- **Enable simulation** — catch reverts before spending gas
- **Test on testnet first** — validate policies on Base Sepolia before mainnet
- **Keep denylists updated** — add known malicious addresses
- **Enable LLM validation** for high-value agents — worth the $0.003/tx cost
- **Monitor logs** — review `info` level output regularly

---

## Documentation

- [examples/basic-chat-agent/README.md](examples/basic-chat-agent/README.md) — EOA agent tutorial
- [examples/smart-wallet-agents/README.md](examples/smart-wallet-agents/README.md) — ERC-4337 and Safe agent tutorial
- [CHANGELOG.md](CHANGELOG.md) — Version history

---

## Support

- **Issues:** [GitHub Issues](https://github.com/galaar-org/AgentARC/issues)
- **Examples:** [examples/](examples/)

---

## License

MIT License — see [LICENSE](LICENSE) for details.
