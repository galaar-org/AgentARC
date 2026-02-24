"""
Interactive setup wizard for AgentARC.

Guides the user through wallet type, framework, network, and policy
selection, then generates a complete project scaffold.
"""

from pathlib import Path
from typing import List, Optional

import click

# ============================================================
# Network constants
# ============================================================

NETWORKS = {
    "Base Sepolia (testnet)": {
        "rpc_url": "https://sepolia.base.org",
        "chain_id": 84532,
        "usdc": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    },
    "Base Mainnet": {
        "rpc_url": "https://mainnet.base.org",
        "chain_id": 8453,
        "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    },
    "Ethereum Sepolia": {
        "rpc_url": "https://rpc.sepolia.org",
        "chain_id": 11155111,
        "usdc": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
    },
    "Ethereum Mainnet": {
        "rpc_url": "https://eth.llamarpc.com",
        "chain_id": 1,
        "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    },
    "Custom RPC": None,
}

# ============================================================
# Template selection matrix
# wallet_type -> framework -> template filename (without .template)
# ============================================================

AGENT_TEMPLATES = {
    "eoa": {
        "openai": "agent_eoa_openai.py",
        "langchain": "agent_eoa_langchain.py",
    },
    "erc4337": {
        "openai": "agent_erc4337_openai.py",
        "langchain": "agent_erc4337_langchain.py",
    },
    "safe": {
        "openai": "agent_safe_openai.py",
        "langchain": "agent_safe_langchain.py",
    },
    "cdp": {
        "openai": "agent_cdp_openai.py",
        "langchain": "agent_cdp_langchain.py",
    },
}

ENV_TEMPLATES = {
    "eoa": "env_eoa.template",
    "erc4337": "env_erc4337.template",
    "safe": "env_safe.template",
    "cdp": "env_cdp.template",
}

# ============================================================
# requirements.txt per wallet + framework
# ============================================================

REQUIREMENTS: dict = {
    "base": ["agentarc", "python-dotenv"],
    "openai": ["openai>=1.0.0"],
    "langchain": ["langchain-openai>=0.1.0", "langgraph>=0.2.0"],
    "erc4337": [],       # Already in core agentarc deps
    "safe": [],          # Already in core agentarc deps
    "cdp": ["coinbase-agentkit>=0.1.0"],
}


def _get_requirements(wallet_type: str, framework: str) -> List[str]:
    reqs = list(REQUIREMENTS["base"])
    reqs += REQUIREMENTS.get(framework, [])
    reqs += REQUIREMENTS.get(wallet_type, [])
    return reqs


# ============================================================
# Policy YAML generation helpers
# ============================================================

def _build_policy_yaml(policies: List[str], network_info: dict) -> str:
    usdc_address = network_info.get("usdc", "0x036CbD53842c5426634e7929541eC2318f3dCF7e")

    policy_blocks = []

    if "Spending Limits (ETH + per-asset)" in policies:
        policy_blocks.append("""  - type: eth_value_limit
    enabled: true
    max_value_wei: "1000000000000000000"  # 1 ETH
    description: "Limit ETH transfers to 1 ETH per transaction"

  - type: per_asset_limit
    enabled: true
    asset_limits:
      - name: USDC
        address: "{usdc}"
        max_amount: "10000000"  # 10 USDC
        decimals: 6
    description: "Per-asset spending limits"
""".format(usdc=usdc_address))

    if "Address Denylist" in policies:
        policy_blocks.append("""  - type: address_denylist
    enabled: true
    denied_addresses: []  # Add addresses to block here
    description: "Block transactions to denied addresses"
""")

    if "Address Allowlist" in policies:
        policy_blocks.append("""  - type: address_allowlist
    enabled: true
    allowed_addresses: []  # Add allowed addresses here
    description: "Only allow transactions to approved addresses"
""")

    if "Function Allowlist" in policies:
        policy_blocks.append("""  - type: function_allowlist
    enabled: true
    allowed_functions:
      - "eth_transfer"
      - "transfer"
      - "approve"
    description: "Only allow specific function calls"
""")

    # Always include gas limit
    policy_blocks.append("""  - type: gas_limit
    enabled: true
    max_gas: 500000
    description: "Limit gas to 500k per transaction"
""")

    policies_yaml = "\n".join(policy_blocks)

    return """version: "2.0"
enabled: true

logging:
  level: info

policies:
{policies}
simulation:
  enabled: true
  fail_on_revert: true
  estimate_gas: true
  print_trace: false

calldata_validation:
  enabled: true
  strict_mode: false

llm_validation:
  enabled: false
  provider: "openai"
  model: "gpt-4o-mini"
  api_key: "${{OPENAI_API_KEY}}"
  block_threshold: 0.70
  warn_threshold: 0.40
""".format(policies=policies_yaml)


# ============================================================
# SetupWizard
# ============================================================

class SetupWizard:
    """
    Interactive wizard for scaffolding AgentARC-protected agents.

    Prompts the user for:
      - Project type (new vs existing)
      - Project name
      - Agent framework (OpenAI SDK, LangChain)
      - Wallet type (EOA, ERC-4337, Safe, CDP)
      - Network (Base Sepolia, Base Mainnet, Ethereum, custom)
      - Policy templates (spending limits, denylist, allowlist, function allowlist)

    Then generates a complete project directory.
    """

    TEMPLATES_DIR = Path(__file__).parent / "templates"

    def run(self, project_path: Optional[str] = None):
        """Run the interactive setup wizard."""
        self._print_banner()

        project_type = click.prompt(
            "Is this for an existing or new project?",
            type=click.Choice(["existing", "new"], case_sensitive=False),
            default="new",
        )

        if project_type.lower() == "new":
            self._run_new_project(base_path=project_path)
        else:
            self._run_existing_project(path=project_path)

    # ------------------------------------------------------------------
    # New project flow
    # ------------------------------------------------------------------

    def _run_new_project(self, base_path: Optional[str] = None):
        project_name = click.prompt("Enter your project name", default="my-secure-agent")
        base = Path(base_path) if base_path else Path.cwd()
        project_path = base / project_name

        if project_path.exists():
            click.echo(f"\nWarning: Directory {project_path} already exists")
            if not click.confirm("Continue and overwrite files?"):
                click.echo("Setup cancelled.")
                return
        else:
            project_path.mkdir(parents=True, exist_ok=True)

        framework = self._prompt_framework()
        wallet_type = self._prompt_wallet_type()
        network_name, network_info = self._prompt_network()
        selected_policies = self._prompt_policies()

        # Generate files
        click.echo("\nCreating project...")

        agent_file = self._write_agent_template(project_path, project_name, wallet_type, framework)
        policy_file = self._write_policy_yaml(project_path, selected_policies, network_info)
        env_file = self._write_env_template(project_path, wallet_type, network_info)
        req_file = self._write_requirements(project_path, wallet_type, framework)
        gitignore_file = self._write_gitignore(project_path)

        click.echo(f"\nProject created at: {project_path}")
        click.echo("\nFiles created:")
        click.echo(f"  agent.py            <- {wallet_type.upper()} + {framework.upper()} agent")
        click.echo(f"  policy.yaml         <- Off-chain policy config")
        click.echo(f"  .env.example        <- Environment variables for {wallet_type.upper()}")
        click.echo(f"  requirements.txt    <- Python dependencies")
        click.echo(f"  .gitignore")

        click.echo("\nNext steps:")
        click.echo(f"  cd {project_name}")
        click.echo(f"  cp .env.example .env")
        click.echo(f"  # Add your keys to .env")
        click.echo(f"  pip install -r requirements.txt")
        click.echo(f"  python agent.py")

    # ------------------------------------------------------------------
    # Existing project flow
    # ------------------------------------------------------------------

    def _run_existing_project(self, path: Optional[str] = None):
        from ..core.config import PolicyConfig

        project_path = Path(path) if path else Path.cwd()
        config_path = project_path / "policy.yaml"

        if config_path.exists():
            if not click.confirm(f"\n{config_path} already exists. Overwrite?"):
                click.echo("Setup cancelled.")
                return

        network_name, network_info = self._prompt_network()
        selected_policies = self._prompt_policies()

        policy_yaml = _build_policy_yaml(selected_policies, network_info)
        config_path.write_text(policy_yaml)

        click.echo(f"\nCreated policy config at: {config_path}")
        click.echo("\nNext steps:")
        click.echo(f"  1. Edit {config_path} to customize your policies")
        click.echo(f"  2. Import agentarc in your agent code:")
        click.echo(f"       from agentarc import WalletFactory, PolicyWallet")
        click.echo(f"       wallet = WalletFactory.from_private_key(private_key, rpc_url)")
        click.echo(f"       policy_wallet = PolicyWallet(wallet, config_path='policy.yaml')")

    # ------------------------------------------------------------------
    # Interactive prompts
    # ------------------------------------------------------------------

    def _prompt_framework(self) -> str:
        click.echo("")
        framework = click.prompt(
            "Choose your agent framework",
            type=click.Choice(["openai", "langchain"], case_sensitive=False),
            default="openai",
        )
        return framework.lower()

    def _prompt_wallet_type(self) -> str:
        click.echo("")
        wallet_type = click.prompt(
            "Choose wallet type",
            type=click.Choice(["eoa", "erc4337", "safe", "cdp"], case_sensitive=False),
            default="eoa",
        )
        return wallet_type.lower()

    def _prompt_network(self):
        click.echo("")
        network_choices = list(NETWORKS.keys())
        click.echo("Available networks:")
        for i, name in enumerate(network_choices, 1):
            click.echo(f"  {i}. {name}")

        choice_str = click.prompt(
            "Choose network (number or name)",
            default="1",
        )

        # Accept number or name
        try:
            idx = int(choice_str) - 1
            network_name = network_choices[idx]
        except (ValueError, IndexError):
            network_name = choice_str

        if network_name == "Custom RPC":
            rpc_url = click.prompt("Enter your RPC URL")
            chain_id = click.prompt("Enter chain ID", type=int)
            network_info = {"rpc_url": rpc_url, "chain_id": chain_id, "usdc": ""}
        else:
            network_info = NETWORKS.get(network_name, NETWORKS["Base Sepolia (testnet)"])

        return network_name, network_info

    def _prompt_policies(self) -> List[str]:
        click.echo("")
        available = [
            "Spending Limits (ETH + per-asset)",
            "Address Denylist",
            "Address Allowlist",
            "Function Allowlist",
        ]
        click.echo("Select policy templates (comma-separated numbers, e.g. 1,2):")
        for i, p in enumerate(available, 1):
            click.echo(f"  {i}. {p}")

        raw = click.prompt("Your selection", default="1,2")
        selected = []
        for part in raw.split(","):
            part = part.strip()
            try:
                idx = int(part) - 1
                if 0 <= idx < len(available):
                    selected.append(available[idx])
            except ValueError:
                if part in available:
                    selected.append(part)

        return selected if selected else [available[0]]

    # ------------------------------------------------------------------
    # File writers
    # ------------------------------------------------------------------

    def _write_agent_template(
        self, project_path: Path, project_name: str, wallet_type: str, framework: str
    ) -> Path:
        template_name = AGENT_TEMPLATES[wallet_type][framework]
        template_path = self.TEMPLATES_DIR / (template_name + ".template")

        if template_path.exists():
            content = template_path.read_text()
            content = content.replace("{project_name}", project_name)
        else:
            content = f'# {project_name} agent\n# Template not found: {template_name}.template\n'

        out_path = project_path / "agent.py"
        out_path.write_text(content)
        return out_path

    def _write_policy_yaml(
        self, project_path: Path, policies: List[str], network_info: dict
    ) -> Path:
        content = _build_policy_yaml(policies, network_info)
        out_path = project_path / "policy.yaml"
        out_path.write_text(content)
        return out_path

    def _write_env_template(
        self, project_path: Path, wallet_type: str, network_info: dict
    ) -> Path:
        template_name = ENV_TEMPLATES[wallet_type]
        template_path = self.TEMPLATES_DIR / template_name

        if template_path.exists():
            content = template_path.read_text()
            # Substitute RPC_URL with the chosen network's RPC
            if network_info and network_info.get("rpc_url"):
                content = content.replace("https://sepolia.base.org", network_info["rpc_url"])
        else:
            content = "# Add your environment variables here\n"

        out_path = project_path / ".env.example"
        out_path.write_text(content)
        return out_path

    def _write_requirements(
        self, project_path: Path, wallet_type: str, framework: str
    ) -> Path:
        reqs = _get_requirements(wallet_type, framework)
        content = "\n".join(reqs) + "\n"
        out_path = project_path / "requirements.txt"
        out_path.write_text(content)
        return out_path

    def _write_gitignore(self, project_path: Path) -> Path:
        content = """.env
__pycache__/
*.pyc
*.pyo
.pytest_cache/
*.egg-info/
dist/
build/
"""
        out_path = project_path / ".gitignore"
        out_path.write_text(content)
        return out_path

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _print_banner(self):
        click.echo("")
        click.echo("=" * 50)
        click.echo("          AgentARC Setup Wizard")
        click.echo("=" * 50)
        click.echo("")
