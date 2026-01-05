# Setup Guide - Autonomous Portfolio Agent

## Quick Setup

### 1. Install Dependencies

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

### 2. Configure Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your favorite editor
```

Required credentials:

```bash
# 1. CDP API Keys (from portal.cdp.coinbase.com)
CDP_API_KEY_ID=organizations/xxx/apiKeys/yyy
CDP_API_KEY_SECRET=-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----
CDP_WALLET_SECRET=any_random_string_for_local_encryption

# 2. OpenAI API Key
OPENAI_API_KEY=sk-proj-...

# 3. Tenderly API (for simulation)
TENDERLY_API_KEY=your_key
TENDERLY_ACCOUNT_SLUG=your_account
TENDERLY_PROJECT_SLUG=your_project
```

### 3. Get CDP API Credentials

1. Go to https://portal.cdp.coinbase.com/
2. Create a new project
3. Navigate to "API Keys"
4. Click "Create API Key"
5. Download the JSON file or copy:
   - `api_key_id` → CDP_API_KEY_ID
   - `api_key_secret` → CDP_API_KEY_SECRET (includes BEGIN/END markers)
6. Create a random string for `CDP_WALLET_SECRET` (used for local encryption)

### 4. Fund Wallet

```bash
# Run the agent once to get your wallet address
python autonomous_agent.py
# It will print: "✅ CDP Wallet created: 0x..."

# Fund with Base Sepolia ETH from faucet:
# https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
```

### 5. Run the Agent

```bash
# Autonomous mode (runs continuously)
python autonomous_agent.py

# Demo mode (scripted scenarios)
python demo_runner.py
```

## Project Structure

```
autonomous-portfolio-agent/
├── config/
│   ├── portfolio_config.py    # Portfolio settings
│   └── policy.yaml             # PolicyLayer rules
├── action_providers/
│   ├── uniswap_actions.py      # Uniswap integration
│   └── portfolio_actions.py    # Portfolio analysis
├── core/
│   ├── agent.py                # Main agent class
│   └── metrics_logger.py       # Metrics tracking
├── autonomous_agent.py         # Main entry point
├── demo_runner.py              # Demo script
└── .env                        # Your credentials (create from .env.example)
```

## Import Pattern

**✅ Correct way (matches onchain-agent example):**

```python
from agentarc import PolicyWalletProvider, PolicyEngine
```

**❌ Wrong way (don't use):**

```python
from agentarc.policy_engine import PolicyEngine
from agentarc.wallet_wrapper import PolicyWalletProvider
```

## Common Issues

### "ModuleNotFoundError: No module named 'agentarc'"

**Solution**: Install PolicyLayer:
```bash
# From the project root directory
pip install -e .
```

### "CDP API error: Authentication failed"

**Solution**: Check your CDP credentials in `.env`:
- Make sure `CDP_API_KEY_ID` starts with `organizations/`
- Make sure `CDP_API_KEY_SECRET` includes the `-----BEGIN EC PRIVATE KEY-----` markers
- Include `\n` for newlines in the secret (literal backslash-n, not actual newlines)

### "Tenderly simulation failed"

**Solution**:
- Verify `TENDERLY_API_KEY` is correct
- Check `TENDERLY_ACCOUNT_SLUG` and `TENDERLY_PROJECT_SLUG` match your Tenderly project
- Ensure network is set to Base Sepolia (chain_id: 84532)

### "Wallet has no funds"

**Solution**:
```bash
# Get wallet address
python -c "from dotenv import load_dotenv; load_dotenv(); import os; from coinbase_agentkit import *; w = CdpEvmWalletProvider(CdpEvmWalletProviderConfig(api_key_id=os.getenv('CDP_API_KEY_ID'), api_key_secret=os.getenv('CDP_API_KEY_SECRET'), wallet_secret=os.getenv('CDP_WALLET_SECRET'), network_id='base-sepolia')); print(w.get_default_address())"

# Fund from faucet
# https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
```

## Testing Honeypot Detection

Your deployed honeypot token:
```
Address: 0xFe836592564C37D6cE99657c379a387CC5CE0868
Network: Base Sepolia
```

To test (in future enhancement):
1. Manually prompt agent: "Buy 0.1 ETH worth of token at 0xFe836..."
2. PolicyLayer Stage 3.5 will detect honeypot
3. Transaction will be blocked with reason

## Configuration

### Portfolio Allocation

Edit `config/portfolio_config.py`:

```python
TARGET_ALLOCATION = {
    "ETH": 0.50,    # 50%
    "USDC": 0.30,   # 30%
    "WETH": 0.20,   # 20%
}

REBALANCE_INTERVAL = 60  # Seconds between checks
```

### Policy Rules

Edit `config/policy.yaml`:

```yaml
policies:
  - type: eth_value_limit
    max_value_wei: '100000000000000000'  # 0.1 ETH

  - type: per_asset_limit
    asset_limits:
      - name: USDC
        max_amount: '50000000'  # 50 USDC

simulation:
  enabled: true  # Enables honeypot detection!

llm_validation:
  enabled: true
  model: 'gpt-4o-mini'
```

## Monitoring

### Logs
- `autonomous_agent.log` - Agent decisions
- `policy_engine.log` - PolicyLayer validation
- `metrics.json` - Trades and blocked attacks

### Metrics

Check metrics anytime:
```python
from core.metrics_logger import MetricsLogger
logger = MetricsLogger()
logger.print_summary()
```

## Next Steps

1. ✅ Set up environment and credentials
2. ✅ Fund wallet
3. ✅ Run autonomous agent
4. Test honeypot detection
5. Customize portfolio allocation
6. Add more tokens
7. Deploy to production (Base Mainnet)

---

**Built with:**
- Coinbase AgentKit
- PolicyLayer
- LangChain
- Tenderly