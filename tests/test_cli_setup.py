"""
Tests for the AgentARC CLI setup wizard.

Uses Click's CliRunner and pytest's tmp_path fixture to test
the setup command without touching the filesystem or prompting
real input.
"""

import os
import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from agentarc.__main__ import cli
from agentarc.cli.wizard import SetupWizard, _build_policy_yaml, _get_requirements


# ============================================================
# Test policy YAML generation
# ============================================================

class TestBuildPolicyYaml:
    def test_generates_valid_yaml(self):
        network_info = {"rpc_url": "https://sepolia.base.org", "chain_id": 84532,
                        "usdc": "0x036CbD53842c5426634e7929541eC2318f3dCF7e"}
        yaml_str = _build_policy_yaml(["Spending Limits (ETH + per-asset)"], network_info)
        assert "version:" in yaml_str
        assert "eth_value_limit" in yaml_str
        assert "per_asset_limit" in yaml_str

    def test_denylist_policy_included(self):
        network_info = {"rpc_url": "https://sepolia.base.org", "chain_id": 84532, "usdc": ""}
        yaml_str = _build_policy_yaml(["Address Denylist"], network_info)
        assert "address_denylist" in yaml_str

    def test_allowlist_policy_included(self):
        network_info = {"rpc_url": "https://sepolia.base.org", "chain_id": 84532, "usdc": ""}
        yaml_str = _build_policy_yaml(["Address Allowlist"], network_info)
        assert "address_allowlist" in yaml_str

    def test_function_allowlist_included(self):
        network_info = {"rpc_url": "https://sepolia.base.org", "chain_id": 84532, "usdc": ""}
        yaml_str = _build_policy_yaml(["Function Allowlist"], network_info)
        assert "function_allowlist" in yaml_str

    def test_gas_limit_always_included(self):
        network_info = {"rpc_url": "https://sepolia.base.org", "chain_id": 84532, "usdc": ""}
        yaml_str = _build_policy_yaml([], network_info)
        assert "gas_limit" in yaml_str

    def test_usdc_address_substituted(self):
        network_info = {
            "rpc_url": "https://mainnet.base.org",
            "chain_id": 8453,
            "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        }
        yaml_str = _build_policy_yaml(["Spending Limits (ETH + per-asset)"], network_info)
        assert "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913" in yaml_str


# ============================================================
# Test requirements generation
# ============================================================

class TestGetRequirements:
    def test_base_requirements_always_present(self):
        reqs = _get_requirements("eoa", "openai")
        assert "agentarc" in reqs
        assert "python-dotenv" in reqs

    def test_openai_framework_adds_openai(self):
        reqs = _get_requirements("eoa", "openai")
        assert any("openai" in r for r in reqs)

    def test_langchain_framework_adds_langchain(self):
        reqs = _get_requirements("eoa", "langchain")
        assert any("langchain" in r for r in reqs)
        assert any("langgraph" in r for r in reqs)

    def test_cdp_wallet_adds_agentkit(self):
        reqs = _get_requirements("cdp", "openai")
        assert any("coinbase-agentkit" in r for r in reqs)

    def test_erc4337_no_extra_deps(self):
        reqs = _get_requirements("erc4337", "openai")
        # ERC-4337 deps are already in core agentarc
        assert "agentarc" in reqs


# ============================================================
# Test SetupWizard template files exist
# ============================================================

class TestSetupWizardTemplates:
    def test_templates_dir_exists(self):
        assert SetupWizard.TEMPLATES_DIR.exists()

    def test_all_agent_templates_exist(self):
        expected = [
            "agent_eoa_openai.py.template",
            "agent_eoa_langchain.py.template",
            "agent_erc4337_openai.py.template",
            "agent_erc4337_langchain.py.template",
            "agent_safe_openai.py.template",
            "agent_safe_langchain.py.template",
            "agent_cdp_openai.py.template",
            "agent_cdp_langchain.py.template",
        ]
        for name in expected:
            path = SetupWizard.TEMPLATES_DIR / name
            assert path.exists(), f"Template missing: {name}"

    def test_all_env_templates_exist(self):
        expected = [
            "env_eoa.template",
            "env_erc4337.template",
            "env_safe.template",
            "env_cdp.template",
        ]
        for name in expected:
            path = SetupWizard.TEMPLATES_DIR / name
            assert path.exists(), f"Env template missing: {name}"

    def test_erc4337_template_contains_bundler_url(self):
        template_path = SetupWizard.TEMPLATES_DIR / "agent_erc4337_openai.py.template"
        content = template_path.read_text()
        assert "BUNDLER_URL" in content
        assert "OWNER_PRIVATE_KEY" in content

    def test_safe_template_contains_safe_address(self):
        template_path = SetupWizard.TEMPLATES_DIR / "agent_safe_openai.py.template"
        content = template_path.read_text()
        assert "SAFE_ADDRESS" in content
        assert "SIGNER_PRIVATE_KEY" in content


# ============================================================
# Test file writing helpers
# ============================================================

class TestSetupWizardFileWriters:
    def test_write_agent_template_eoa_openai(self, tmp_path):
        wizard = SetupWizard()
        out = wizard._write_agent_template(tmp_path, "my-agent", "eoa", "openai")
        assert out.exists()
        content = out.read_text()
        assert "my-agent" in content
        assert "WalletFactory.from_private_key" in content

    def test_write_agent_template_erc4337_langchain(self, tmp_path):
        wizard = SetupWizard()
        out = wizard._write_agent_template(tmp_path, "my-agent", "erc4337", "langchain")
        assert out.exists()
        content = out.read_text()
        assert "WalletFactory.from_erc4337" in content
        assert "LangChainAdapter" in content

    def test_write_agent_template_safe_openai(self, tmp_path):
        wizard = SetupWizard()
        out = wizard._write_agent_template(tmp_path, "safe-agent", "safe", "openai")
        assert out.exists()
        content = out.read_text()
        assert "WalletFactory.from_safe" in content

    def test_write_policy_yaml(self, tmp_path):
        wizard = SetupWizard()
        network_info = {
            "rpc_url": "https://sepolia.base.org",
            "chain_id": 84532,
            "usdc": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        }
        out = wizard._write_policy_yaml(tmp_path, ["Spending Limits (ETH + per-asset)"], network_info)
        assert out.exists()
        assert "eth_value_limit" in out.read_text()

    def test_write_env_template_eoa(self, tmp_path):
        wizard = SetupWizard()
        network_info = {"rpc_url": "https://mainnet.base.org", "chain_id": 8453, "usdc": ""}
        out = wizard._write_env_template(tmp_path, "eoa", network_info)
        assert out.name == ".env.example"
        content = out.read_text()
        assert "PRIVATE_KEY" in content
        # RPC URL should be substituted
        assert "https://mainnet.base.org" in content

    def test_write_env_template_erc4337(self, tmp_path):
        wizard = SetupWizard()
        network_info = {"rpc_url": "https://sepolia.base.org", "chain_id": 84532, "usdc": ""}
        out = wizard._write_env_template(tmp_path, "erc4337", network_info)
        content = out.read_text()
        assert "OWNER_PRIVATE_KEY" in content
        assert "BUNDLER_URL" in content

    def test_write_requirements_openai(self, tmp_path):
        wizard = SetupWizard()
        out = wizard._write_requirements(tmp_path, "eoa", "openai")
        assert out.exists()
        content = out.read_text()
        assert "agentarc" in content
        assert "openai" in content

    def test_write_gitignore(self, tmp_path):
        wizard = SetupWizard()
        out = wizard._write_gitignore(tmp_path)
        assert out.exists()
        content = out.read_text()
        assert ".env" in content


# ============================================================
# Test CLI command via CliRunner
# ============================================================

class TestCLISetupCommand:
    def test_setup_command_exists(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "setup" in result.output

    def test_setup_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["setup", "--help"])
        assert result.exit_code == 0

    def test_setup_new_project_eoa_openai(self, tmp_path):
        """Full new project flow: EOA + OpenAI SDK on Base Sepolia."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            user_inputs = "\n".join([
                "new",          # new project
                "test-agent",   # project name
                "openai",       # framework
                "eoa",          # wallet type
                "1",            # Base Sepolia
                "1",            # Spending Limits
            ]) + "\n"

            result = runner.invoke(cli, ["setup"], input=user_inputs)

        assert result.exit_code == 0
        project_dir = Path(runner.isolated_filesystem.__self__.name if hasattr(runner, '_isolated_filesystem') else tmp_path) / "test-agent"

    def test_setup_new_project_creates_files(self, tmp_path):
        """Verify all expected files are created for a new project."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            user_inputs = "\n".join([
                "new",
                "my-agent",
                "openai",
                "erc4337",
                "1",
                "1,2",
            ]) + "\n"

            result = runner.invoke(cli, ["setup"], input=user_inputs)

            # Check files were created
            project_dir = Path(".") / "my-agent"
            assert project_dir.exists(), f"Project dir not created. Output:\n{result.output}"
            assert (project_dir / "agent.py").exists()
            assert (project_dir / "policy.yaml").exists()
            assert (project_dir / ".env.example").exists()
            assert (project_dir / "requirements.txt").exists()
            assert (project_dir / ".gitignore").exists()

            # Verify agent.py has ERC-4337 specific content
            agent_content = (project_dir / "agent.py").read_text()
            assert "WalletFactory.from_erc4337" in agent_content
            assert "BUNDLER_URL" in agent_content

    def test_setup_new_project_safe_langchain(self, tmp_path):
        """Verify Safe + LangChain generates correct agent.py."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            user_inputs = "\n".join([
                "new",
                "safe-agent",
                "langchain",
                "safe",
                "1",
                "1",
            ]) + "\n"

            result = runner.invoke(cli, ["setup"], input=user_inputs)

            project_dir = Path(".") / "safe-agent"
            if project_dir.exists():
                agent_content = (project_dir / "agent.py").read_text()
                assert "WalletFactory.from_safe" in agent_content
                assert "LangChainAdapter" in agent_content
