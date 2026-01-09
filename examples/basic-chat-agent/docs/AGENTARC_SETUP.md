# AgentARC Setup Guide

## Integration Steps

### 1. Install AgentARC

```bash
# Using pip
pip install agentarc

# Using poetry
poetry add agentarc
```

### 2. Configure Policies

Edit `policy.yaml` to configure your security policies:

- **ETH Value Limits**: Maximum ETH per transaction
- **Address Denylist**: Block sanctioned/malicious addresses
- **Address Allowlist**: Only allow approved recipients
- **Per-Asset Limits**: Different spending limits per token (USDC, DAI, etc.)
- **Gas Limits**: Prevent expensive transactions
- **Function Allowlist**: Only allow specific function calls

### 3. Integrate with Your Agent

Add these 3 lines to your agent initialization code:

```python
from agentarc import PolicyWalletProvider, PolicyEngine

# After creating your base wallet provider
policy_engine = PolicyEngine(
    config_path="policy.yaml",
    web3_provider=base_wallet_provider  # For transaction simulation
)
policy_wallet = PolicyWalletProvider(base_wallet_provider, policy_engine)

# Use policy_wallet instead of base_wallet_provider
agentkit = AgentKit(wallet_provider=policy_wallet, action_providers=[...])
```

### 4. Example Integration

**Before (without AgentARC):**
```python
from coinbase_agentkit import AgentKit, CdpEvmWalletProvider

wallet = CdpEvmWalletProvider(config)
agentkit = AgentKit(wallet_provider=wallet, action_providers=[...])
```

**After (with AgentARC):**
```python
from coinbase_agentkit import AgentKit, CdpEvmWalletProvider
from agentarc import PolicyWalletProvider, PolicyEngine

# Create base wallet
wallet = CdpEvmWalletProvider(config)

# Wrap with policy layer (3 lines!)
policy_engine = PolicyEngine(config_path="policy.yaml", web3_provider=wallet)
policy_wallet = PolicyWalletProvider(wallet, policy_engine)

# Use policy-protected wallet
agentkit = AgentKit(wallet_provider=policy_wallet, action_providers=[...])
```

### 5. Test Your Setup

Run your agent and verify policy enforcement:

1. Try a transaction within limits - should succeed
2. Try a transaction exceeding limits - should be blocked with clear error message
3. Check logs to see 3-stage validation pipeline in action

### 6. Customize Policies

Common configurations:

**Conservative (High Security):**
```yaml
policies:
  - type: eth_value_limit
    max_value_wei: "100000000000000000"  # 0.1 ETH
    enabled: true

  - type: address_allowlist
    allowed_addresses:
      - "0xYourTrustedAddress1..."
      - "0xYourTrustedAddress2..."
    enabled: true

  - type: gas_limit
    max_gas: 300000
    enabled: true
```

**Moderate (Balanced):**
```yaml
policies:
  - type: eth_value_limit
    max_value_wei: "1000000000000000000"  # 1 ETH
    enabled: true

  - type: address_denylist
    denied_addresses:
      - "0xSanctionedAddress..."
    enabled: true

  - type: per_asset_limit
    asset_limits:
      - name: USDC
        address: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        max_amount: "10000000"  # 10 USDC
        decimals: 6
    enabled: true
```

### 7. Logging Levels

Control verbosity in `policy.yaml`:

```yaml
logging:
  level: info  # Options: minimal, info, debug
```

- **minimal**: Only critical policy decisions
- **info**: Full validation pipeline (recommended)
- **debug**: Detailed debugging information

### 8. Transaction Simulation

Enable pre-broadcast validation:

```yaml
simulation:
  enabled: true
  fail_on_revert: true  # Block transactions that would revert
  estimate_gas: true
```

## Support

- Documentation: https://github.com/yourusername/agentarc
- Issues: https://github.com/yourusername/agentarc/issues
- Examples: See `examples/` directory

## Security

AgentARC provides multiple layers of protection:
1. **Intent Analysis**: Parse transaction intent and calldata
2. **Policy Validation**: Enforce user-defined rules
3. **Simulation**: Test execution before sending
4. **Calldata Verification**: Validate data integrity

Always test policies in a development environment before production use.
