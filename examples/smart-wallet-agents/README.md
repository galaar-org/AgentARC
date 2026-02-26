# Smart Wallet Agents with AgentARC

Secure AI agents using **ERC-4337 smart wallets** and **Safe multisig wallets**, protected by [AgentARC](https://github.com/galaar-org/AgentARC) policy enforcement.

## What's in this directory

| File | Description |
|------|-------------|
| `erc4337_agent.py` | Chat agent using an ERC-4337 smart contract wallet |
| `safe_agent.py` | Chat agent using a Gnosis Safe multisig wallet |
| `policy.yaml` | Security policy rules (shared by both agents) |
| `.env.example` | Environment variable template |

---

## Why smart wallets?

Normal wallets (EOA) require you to hold ETH just to pay gas. Smart wallets unlock:

| Feature | EOA | ERC-4337 | Safe |
|---------|-----|----------|------|
| Holds funds | your key address | smart contract address | safe contract address |
| Gas sponsorship | no | yes (via Paymaster) | no |
| Multi-signature | no | no | yes |
| Counterfactual address | no | yes | no |
| Best for | simple agents | production agents | team/enterprise |

Regardless of wallet type, **your agent code is identical** — only the wallet setup line changes.

---

## ERC-4337 Agent

### How it works

```
Your Owner Key (signs UserOperations)
        │
        ▼
Smart Account (contract at a fixed address — holds your funds)
        │
        ▼
Bundler (e.g. Pimlico) — submits UserOperation to the chain
        │
        ▼
EntryPoint contract → Smart Account executes the transaction
```

The smart account address is **counterfactual** — it is derived from your owner key before the contract is deployed. You can fund it before the first transaction. On the first transaction, the contract deploys automatically.

### Prerequisites

1. **A bundler URL** — sign up free at [pimlico.io](https://pimlico.io) or [alchemy.com](https://alchemy.com)
2. **Base Sepolia ETH** — get some from the [Base faucet](https://docs.base.org/docs/tools/network-faucets/)
3. **An owner private key** — any Ethereum private key

### Setup

```bash
# 1. Install dependencies
pip install openai agentarc web3 python-dotenv requests

# 2. Configure environment
cp .env.example .env
```

Edit `.env`:
```bash
OPENAI_API_KEY=sk-...
OWNER_PRIVATE_KEY=0x...     # any Ethereum private key
BUNDLER_URL=https://api.pimlico.io/v2/84532/rpc?apikey=YOUR_KEY
RPC_URL=https://sepolia.base.org
```

```bash
# 3. Run the agent
python erc4337_agent.py
```

### What you'll see on startup

```
============================================================
ERC-4337 Smart Wallet Agent with AgentARC
============================================================

[1/3] Creating ERC-4337 smart wallet...
  Smart Account : 0xAbC...  ← this is YOUR wallet address (fund this)
  Owner EOA     : 0xDeF...  ← your private key's address (do not fund this)
  Chain ID      : 84532
  Deployed      : False     ← will deploy automatically on first transaction

  Note: Smart account not yet deployed.
  It will be deployed automatically on your first transaction.
  Fund this address first: 0xAbC...

[2/3] Applying policy enforcement...
  Policies active: 4
    - eth_value_limit
    - address_denylist
    - per_asset_limit
    - gas_limit

[3/3] Creating OpenAI tools...
  Tools available: ['send_transaction', 'get_wallet_balance', 'get_wallet_info', 'validate_transaction']

Agent ready!
```

### Try it out

```
You: What is my smart account address?
You: What is my balance?
You: Validate a transaction of 0.001 ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f5a5b0
You: Send 2 ETH to 0x...     ← will be blocked (exceeds 1 ETH policy limit)
```

---

## Safe Multisig Agent

### How it works

```
Your Signer Key (one of the Safe owners)
        │
        ▼
Safe Contract (holds funds, enforces threshold)
        │
  threshold=1 → executes immediately
  threshold=2+ → proposes transaction, waits for co-signers
        │
        ▼
Transaction executes on-chain
```

### Prerequisites

1. **A deployed Safe** — create one free at [app.safe.global](https://app.safe.global)
   - Choose Base Sepolia network
   - You can start with a 1-of-1 Safe for testing
2. **Base Sepolia ETH** — fund the Safe address (not your key)
3. **A signer private key** — must be one of the Safe owners

### Setup

```bash
# 1. Install dependencies
pip install openai agentarc web3 python-dotenv

# 2. Configure environment
cp .env.example .env
```

Edit `.env`:
```bash
OPENAI_API_KEY=sk-...
SAFE_ADDRESS=0x...          # your deployed Safe contract address
SIGNER_PRIVATE_KEY=0x...    # private key of one of the Safe owners
RPC_URL=https://sepolia.base.org
```

```bash
# 3. Run the agent
python safe_agent.py
```

### What you'll see on startup

```
============================================================
Safe Multisig Wallet Agent with AgentARC
============================================================

[1/4] Connecting to Safe contract...
  Safe Address  : 0xAbC...  ← this is YOUR wallet address (fund this)
  Signer EOA    : 0xDeF...  ← your private key's address
  Chain ID      : 84532
  Deployed      : True

[2/4] Reading Safe configuration...
  Threshold     : 1 of 1 owners
  Owners        :
    0xDeF... <-- you

[3/4] Applying policy enforcement...
  Policies active: 4
    - eth_value_limit
    - address_denylist
    - per_asset_limit
    - gas_limit

[4/4] Creating OpenAI tools...
  Tools available: ['send_transaction', 'get_wallet_balance', 'get_wallet_info', 'validate_transaction']

Agent ready!
```

### Try it out

```
You: What is the Safe address and how many owners does it have?
You: What is the Safe balance?
You: Validate a transaction of 0.001 ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f5a5b0
You: Send 5 ETH to 0x...     ← will be blocked (exceeds 1 ETH policy limit)
```

---

## Configuring policies (`policy.yaml`)

The same `policy.yaml` works for both agents. Edit it to change your security rules:

```yaml
policies:
  - type: eth_value_limit
    max_value_wei: '500000000000000000'  # change to 0.5 ETH

  - type: address_denylist
    denied_addresses:
      - '0xKnownScamAddress...'          # add addresses to block
```

See `policy.yaml` for the full list of available policies with comments explaining each one.

### Enable AI-powered threat detection

For sophisticated attack detection (honeypots, hidden approvals, reentrancy):

```yaml
# in policy.yaml
llm_validation:
  enabled: true     # change false → true
  model: gpt-4o-mini
  block_threshold: 0.70
```

Cost: ~$0.003 per transaction.

---

## How agent code compares across wallet types

The agent loop is **identical** across all wallet types. Only line 1 changes:

```python
# EOA wallet
wallet = WalletFactory.from_private_key(private_key, rpc_url)

# ERC-4337 smart wallet
wallet = WalletFactory.from_erc4337(owner_key, bundler_url, rpc_url)

# Safe multisig
wallet = WalletFactory.from_safe(safe_address, signer_key, rpc_url)

# Everything below is identical for all three ↓
policy_wallet = PolicyWallet(wallet, config_path="policy.yaml")
adapter = OpenAIAdapter()
tools = adapter.create_all_tools(policy_wallet)
```

---

## Troubleshooting

**`Error: OWNER_PRIVATE_KEY not set`**
→ Copy `.env.example` to `.env` and fill in your values.

**`Smart Account Balance: 0 ETH` / `Tip: Fund your smart account at 0x...`**
→ Send Base Sepolia ETH to the smart account address shown on startup (not your owner key address).

**`Bundler RPC error`**
→ Check your `BUNDLER_URL` includes a valid API key. The URL format for Pimlico is:
`https://api.pimlico.io/v2/84532/rpc?apikey=YOUR_KEY`

**`PolicyViolationError: eth_value_limit exceeded`**
→ Your transaction exceeds the spending limit in `policy.yaml`. Either reduce the transaction amount or raise `max_value_wei`.

**`Safe not found` / connection errors**
→ Check `SAFE_ADDRESS` is correct and `RPC_URL` points to the right network.
