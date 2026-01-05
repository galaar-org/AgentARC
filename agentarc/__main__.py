"""
CLI for AgentARC

Usage:
    python -m agentarc setup
    agentarc setup --path ./my-policy.yaml
"""

import click
import shutil
from pathlib import Path
from .policy_engine import PolicyConfig


@click.group()
def cli():
    """AgentARC CLI - Advanced policy enforcement for AI agents"""
    pass


def _create_setup_readme(project_path: Path):
    """Create a SETUP.md file with integration instructions"""
    readme_content = """# AgentARC Setup Guide

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
"""

    readme_path = project_path / "AGENTARC_SETUP.md"
    readme_path.write_text(readme_content)
    return readme_path


@cli.command()
@click.option("--path", default=None, help="Config file path (optional)")
def setup(path: str):
    """Create a default policy configuration file"""

    # Interactive setup
    click.echo("\n" + "="*60)
    click.echo("AgentARC Setup Wizard")
    click.echo("="*60 + "\n")

    # Ask if existing or new project
    project_type = click.prompt(
        "Is this for an existing project or new project?",
        type=click.Choice(["existing", "new"], case_sensitive=False),
        default="existing"
    )

    # Determine project path
    if project_type.lower() == "new":
        # For new projects, use current directory and copy example
        project_name = click.prompt(
            "Enter project name",
            type=str,
            default="onchain-agent"
        )
        project_path = Path.cwd() / project_name

        # Check if directory already exists
        if project_path.exists():
            click.echo(f"\n⚠️  Directory {project_path} already exists")
            if not click.confirm("Continue and overwrite files?"):
                click.echo("Setup cancelled.")
                return
        else:
            project_path.mkdir(parents=True, exist_ok=True)

        # Copy example files from agentarc package
        package_dir = Path(__file__).parent.parent
        example_dir = package_dir / "examples" / "onchain-agent"

        if example_dir.exists():
            click.echo(f"\n✓ Creating new project from template...")

            # Copy all example files
            files_to_copy = [
                "chatbot.py",
                "initialize_agent.py",
                "setup.py",
                "pyproject.toml",
                "requirements.txt",
                "README.md",
                ".env.example",
                ".gitignore"
            ]

            copied_files = []
            for file_name in files_to_copy:
                src = example_dir / file_name
                if src.exists():
                    dst = project_path / file_name
                    shutil.copy2(src, dst)
                    copied_files.append(file_name)

            click.echo(f"✓ Copied {len(copied_files)} example files to {project_path}")
        else:
            click.echo(f"\n⚠️  Example template not found at {example_dir}")
            click.echo("Creating basic setup files only...")

        config_path = project_path / "policy.yaml"
    else:
        # Existing project - use current directory or specified path
        if path:
            project_path = Path(path).parent if path != "policy.yaml" else Path.cwd()
            config_path = Path(path)
        else:
            project_path = Path.cwd()
            config_path = project_path / "policy.yaml"

    # Check if policy.yaml exists
    if config_path.exists():
        if not click.confirm(f"\n{config_path} already exists. Overwrite?"):
            click.echo("Setup cancelled.")
            return

    # Create policy configuration
    PolicyConfig.create_default(config_path)
    click.echo(f"\n✓ Created policy config at: {config_path}")

    # Create setup guide
    readme_path = _create_setup_readme(project_path)
    click.echo(f"✓ Created setup guide at: {readme_path}")

    # Show next steps
    click.echo("\n" + "="*60)
    click.echo("Setup Complete!")
    click.echo("="*60)

    if project_type.lower() == "new":
        click.echo(f"\n✨ New project created at: {project_path}")
        click.echo(f"\nFiles created:")
        click.echo(f"  • chatbot.py")
        click.echo(f"  • initialize_agent.py")
        click.echo(f"  • setup.py")
        click.echo(f"  • policy.yaml")
        click.echo(f"  • requirements.txt")
        click.echo(f"  • pyproject.toml")
        click.echo(f"  • .env.example")
        click.echo(f"  • AGENTARC_SETUP.md")
        click.echo("\nNext steps:")
        click.echo(f"  1. cd {project_path.name}")
        click.echo(f"  2. cp .env.example .env")
        click.echo(f"  3. Edit .env with your API keys")
        click.echo(f"  4. Install dependencies:")
        click.echo(f"     pip install -r requirements.txt  (or poetry install)")
        click.echo(f"  5. python chatbot.py")
    else:
        click.echo(f"\nFiles created:")
        click.echo(f"  • {config_path}")
        click.echo(f"  • {readme_path}")
        click.echo("\nNext steps:")
        click.echo(f"  1. Read {readme_path.name} for integration instructions")
        click.echo(f"  2. Edit {config_path.name} to configure your policies")
        click.echo(f"  3. Add 3 lines to your agent code (see setup guide)")
        click.echo(f"  4. Test your agent with policy enforcement")

    click.echo("\n" + "="*60)


if __name__ == "__main__":
    cli()
