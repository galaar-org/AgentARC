"""
Advanced Policy Engine with 3-stage validation pipeline
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from .logger import PolicyLogger, LogLevel
from .calldata_parser import CalldataParser, ParsedTransaction
from .simulator import TransactionSimulator, SimulationResult
from .rules import (
    ValidationResult,
    AddressDenylistValidator,
    AddressAllowlistValidator,
    EthValueLimitValidator,
    TokenAmountLimitValidator,
    PerAssetLimitValidator,
    FunctionAllowlistValidator,
)

# Import advanced simulation (optional)
try:
    from .simulators.tenderly import TenderlySimulator
    TENDERLY_AVAILABLE = True
except ImportError:
    TENDERLY_AVAILABLE = False

# Import LLM judge (optional)
try:
    from .llm_judge import LLMJudge
    LLM_JUDGE_AVAILABLE = True
except ImportError:
    LLM_JUDGE_AVAILABLE = False


class PolicyConfig:
    """Configuration for policy enforcement"""

    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict
        self.version = config_dict.get("version", "1.0")
        # GLOBAL MASTER SWITCH: If enabled=false, ALL checks are disabled
        self.enabled = config_dict.get("enabled", True)
        self.policies = config_dict.get("policies", [])
        self.simulation = config_dict.get("simulation", {})
        self.calldata_validation = config_dict.get("calldata_validation", {})
        self.logging = config_dict.get("logging", {})
        # NEW: Advanced features
        self.llm_validation = config_dict.get("llm_validation", {})

    @classmethod
    def load(cls, path: str | Path) -> "PolicyConfig":
        """Load configuration from YAML file"""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(data)

    @classmethod
    def create_default(cls, output_path: str | Path):
        """Create a comprehensive default policy configuration file"""
        default_config = {
            "version": "2.0",

            # GLOBAL MASTER SWITCH: Set to false to disable ALL AgentArc checks
            "enabled": True,

            "apply_to": ["all"],

            # Logging configuration
            "logging": {
                "level": "info"  # minimal, info, debug
            },

            # Policies
            "policies": [
                {
                    "type": "eth_value_limit",
                    "max_value_wei": "1000000000000000000",  # 1 ETH
                    "enabled": True,
                    "description": "Limit ETH transfers to 1 ETH per transaction"
                },
                {
                    "type": "address_denylist",
                    "denied_addresses": [
                        # Add sanctioned/malicious addresses here
                        # "0x...",
                    ],
                    "enabled": True,
                    "description": "Block transactions to denied addresses"
                },
                {
                    "type": "address_allowlist",
                    "allowed_addresses": [
                        # Add approved addresses here (empty = allow all)
                        # "0x...",
                    ],
                    "enabled": False,  # Disabled by default
                    "description": "Only allow transactions to approved addresses"
                },
                {
                    "type": "token_amount_limit",
                    "max_amount": "1000000000000000000000",  # 1000 tokens (18 decimals)
                    "enabled": False,
                    "description": "Limit token transfers per transaction"
                },
                {
                    "type": "per_asset_limit",
                    "asset_limits": [
                        {
                            "name": "USDC",
                            "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC mainnet
                            "max_amount": "10000000",  # 10 USDC (6 decimals)
                            "decimals": 6
                        },
                        {
                            "name": "DAI",
                            "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI mainnet
                            "max_amount": "100000000000000000000",  # 100 DAI (18 decimals)
                            "decimals": 18
                        }
                    ],
                    "enabled": True,
                    "description": "Per-asset spending limits"
                },
                {
                    "type": "function_allowlist",
                    "allowed_functions": [
                        "eth_transfer",
                        "transfer",
                        "approve",
                        # Add more allowed functions as needed
                    ],
                    "enabled": False,
                    "description": "Only allow specific function calls"
                },
                {
                    "type": "gas_limit",
                    "max_gas": 500000,
                    "enabled": True,
                    "description": "Limit gas to 500k per transaction"
                }
            ],

            # Simulation settings
            "simulation": {
                "enabled": True,
                "fail_on_revert": True,
                "estimate_gas": True,
                "description": "Simulate transactions before execution"
            },

            # Calldata validation
            "calldata_validation": {
                "enabled": True,
                "strict_mode": False,
                "description": "Validate and parse transaction calldata"
            },

            # LLM-based Security Analysis
            "llm_validation": {
                "enabled": False,  # Disabled by default (requires API key)
                "provider": "openai",
                "model": "gpt-4o-mini",
                "description": "AI-powered pattern detection for advanced threats",
                "warn_threshold": 0.40,
                "block_threshold": 0.70,
                "patterns": [
                    "unlimited_approvals",
                    "unusual_fund_flows",
                    "hidden_fees",
                    "honeypot_indicators",
                    "fake_token_balances",
                    "transfer_restrictions",
                    "reentrancy",
                    "delegatecall_risks",
                    "time_lock_manipulation"
                ],
                "honeypot_detection": {
                    "enabled": True,
                    "description": "Automatically detect honeypot tokens via simulation"
                }
            }
        }

        with open(output_path, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)


class PolicyEngine:
    """
    Advanced policy enforcement engine with 4-stage validation

    Pipeline:
    1. Intent Judge - Parse and understand transaction intent
    2. Calldata/Tx Validation - Validate against policies
    3. Simulation - Test execution (basic or Sentio)
    4. LLM Analysis - Intelligent malicious activity detection (optional)
    5. Final Judge - Allow or block
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        web3_provider: Optional[Any] = None,
        chain_id: Optional[int] = None
    ):
        """
        Initialize policy engine

        Args:
            config_path: Path to policy.yaml configuration file
            web3_provider: Web3 instance or wallet provider for simulation
            chain_id: Chain ID for Sentio simulation (optional)
        """
        if config_path:
            self.config = PolicyConfig.load(config_path)
        else:
            # Default config
            self.config = PolicyConfig({
                "version": "2.0",
                "policies": [
                    {"type": "eth_value_limit", "max_value_wei": "1000000000000000000", "enabled": True},
                    {"type": "gas_limit", "max_gas": 500000, "enabled": True}
                ],
                "simulation": {"enabled": True, "fail_on_revert": True},
                "calldata_validation": {"enabled": True},
                "logging": {"level": "info"},
                "llm_validation": {"enabled": False}
            })

        # Initialize components
        log_level_str = self.config.logging.get("level", "info")
        self.logger = PolicyLogger(LogLevel(log_level_str))
        self.parser = CalldataParser()
        self.simulator = TransactionSimulator(web3_provider)
        self.chain_id = chain_id

        # Initialize validators
        self.validators = self._create_validators()

        # Initialize Tenderly simulator (optional, via environment variables)
        # Set TENDERLY_ACCESS_KEY, TENDERLY_ACCOUNT_SLUG, TENDERLY_PROJECT_SLUG to enable
        self.tenderly_simulator = None
        if TENDERLY_AVAILABLE:
            import os
            tenderly_key = os.getenv("TENDERLY_ACCESS_KEY")
            tenderly_account = os.getenv("TENDERLY_ACCOUNT_SLUG")
            tenderly_project = os.getenv("TENDERLY_PROJECT_SLUG")

            if tenderly_key and tenderly_account and tenderly_project:
                self.tenderly_simulator = TenderlySimulator(
                    access_key=tenderly_key,
                    account_slug=tenderly_account,
                    project_slug=tenderly_project,
                    endpoint=os.getenv("TENDERLY_ENDPOINT", "https://api.tenderly.co/api/v1")
                )

        # Initialize LLM validation (optional)
        self.llm_validator = None
        if self.config.llm_validation.get("enabled", False) and LLM_JUDGE_AVAILABLE:
            self.llm_validator = LLMJudge(
                provider=self.config.llm_validation.get("provider", "openai"),
                model=self.config.llm_validation.get("model", "gpt-4o-mini"),
                api_key=self.config.llm_validation.get("api_key"),
                block_threshold=self.config.llm_validation.get("block_threshold", 0.70),
                warn_threshold=self.config.llm_validation.get("warn_threshold", 0.40)
            )

    def _create_validators(self) -> List[Any]:
        """Create validator instances from config"""
        validators = []

        for policy_config in self.config.policies:
            policy_type = policy_config.get("type")

            if policy_type == "address_denylist":
                validators.append(AddressDenylistValidator(policy_config, self.logger))
            elif policy_type == "address_allowlist":
                validators.append(AddressAllowlistValidator(policy_config, self.logger))
            elif policy_type == "eth_value_limit":
                validators.append(EthValueLimitValidator(policy_config, self.logger))
            elif policy_type == "token_amount_limit":
                validators.append(TokenAmountLimitValidator(policy_config, self.logger))
            elif policy_type == "per_asset_limit":
                validators.append(PerAssetLimitValidator(policy_config, self.logger))
            elif policy_type == "function_allowlist":
                validators.append(FunctionAllowlistValidator(policy_config, self.logger))

        return validators

    def validate_transaction(self, transaction: Dict[str, Any], from_address: Optional[str] = None) -> tuple[bool, str]:
        """
        3-Stage validation pipeline

        Stage 1: Intent Judge - Parse transaction intent
        Stage 2: Calldata/Tx Validation - Validate against policies
        Stage 3: Simulation - Test execution
        Final: Judge decision - Allow/Block

        Args:
            transaction: Transaction dict
            from_address: Sender address (for simulation)

        Returns:
            (passed, reason) tuple
        """
        # ============================================================
        # GLOBAL MASTER SWITCH CHECK
        # ============================================================
        if not self.config.enabled:
            self.logger.minimal("⚠️  POLICYLAYER DISABLED: All checks bypassed")
            return True, "PolicyLayer disabled via config"

        self.logger.section("POLICYLAYER: Validating Transaction")

        # ============================================================
        # STAGE 1: INTENT JUDGE - Parse Transaction Intent
        # ============================================================
        self.logger.subsection("Stage 1: Intent Analysis")

        parsed_tx = self.parser.parse(transaction)

        # Log transaction details (compact)
        self.logger.info(f"→ To: {parsed_tx.to[:10]}...")
        self.logger.info(f"→ Value: {parsed_tx.value / 1e18:.6f} ETH")
        if parsed_tx.function_name:
            self.logger.info(f"→ Function: {parsed_tx.function_name}")

        if parsed_tx.function_selector:
            self.logger.debug(f"Selector: {parsed_tx.function_selector}")

        if parsed_tx.recipient_address:
            self.logger.debug(f"Recipient: {parsed_tx.recipient_address}")

        if parsed_tx.token_amount:
            self.logger.debug(f"Token Amount: {parsed_tx.token_amount}")

        # Print calldata
        if self.config.calldata_validation.get("enabled", True):
            calldata = transaction.get("data", "0x")
            if calldata and calldata != "0x":
                self.logger.debug(f"Calldata: {calldata[:66]}...")  # First 32 bytes
                self.logger.debug(f"Calldata length: {len(calldata)} chars")

        # ============================================================
        # STAGE 2: CALLDATA/TX VALIDATION - Policy Checks
        # ============================================================
        self.logger.subsection("Stage 2: Policy Validation")
        self.logger.debug("Running policy validators...")

        # Run all validators
        for i, validator in enumerate(self.validators, 1):
            if not validator.enabled:
                self.logger.debug(f"[{i}] {validator.name}: SKIPPED (disabled)")
                continue

            self.logger.debug(f"[{i}] Checking policy: {validator.name}")

            result = validator.validate(parsed_tx)

            if not result.passed:
                self.logger.error(f"Policy violation: {result.reason}")
                self.logger.minimal(f"❌ BLOCKED: {result.reason}")
                return False, result.reason

            self.logger.info(f"  ✓ {validator.name}: PASSED", prefix="  ")

        # Gas limit check (needs raw transaction)
        gas_limit_policy = next((p for p in self.config.policies if p.get("type") == "gas_limit" and p.get("enabled")), None)
        if gas_limit_policy:
            max_gas = int(gas_limit_policy.get("max_gas", 0))
            tx_gas = int(transaction.get("gas", 0))

            self.logger.debug(f"Checking gas limit: {tx_gas} <= {max_gas}")

            if tx_gas > max_gas:
                reason = f"Gas {tx_gas} exceeds limit {max_gas}"
                self.logger.error(f"Policy violation: {reason}")
                self.logger.minimal(f"❌ BLOCKED: {reason}")
                return False, reason

            self.logger.info(f"  ✓ gas_limit: PASSED", prefix="  ")

        # ============================================================
        # STAGE 3: SIMULATION - Test Execution
        # ============================================================
        tenderly_result = None

        # Try Tenderly simulation first (if enabled)
        if self.tenderly_simulator and from_address:
            self.logger.subsection("Stage 3: Transaction Simulation")
            self.logger.debug("Simulating transaction execution...")

            network_id = str(self.chain_id) if self.chain_id else "1"
            tenderly_result = self.tenderly_simulator.simulate(transaction, from_address, network_id=network_id)

            if tenderly_result and tenderly_result.success:
                self.logger.success(f"✓ Simulation passed (gas: {tenderly_result.gas_used})")

                # Show asset changes only in debug mode
                if tenderly_result.asset_changes:
                    self.logger.debug("Asset changes:")
                    for change in tenderly_result.asset_changes:
                        delta_sign = "+" if change.delta and not change.delta.startswith("-") else ""
                        self.logger.debug(
                            f"  {change.address[:10]}... ({change.asset_type}): {delta_sign}{change.delta}",
                            prefix="  "
                        )

                # Show trace summary
                if tenderly_result.has_data():
                    self.logger.debug(f"Call traces: {len(tenderly_result.call_trace)}, Events: {len(tenderly_result.logs)}")

                # Print detailed trace if enabled
                if self.config.simulation.get("print_trace", False):
                    self._print_tenderly_trace(tenderly_result)
            elif tenderly_result and not tenderly_result.success:
                if self.config.simulation.get("fail_on_revert", True):
                    reason = f"Tenderly simulation failed: {tenderly_result.error}"
                    self.logger.error(reason)
                    self.logger.minimal(f"❌ BLOCKED: Transaction would fail")
                    return False, reason
                else:
                    self.logger.warning(f"Tenderly simulation failed but fail_on_revert=False")

        # Fallback to basic simulation if Tenderly not available or failed
        elif self.config.simulation.get("enabled", False) and from_address:
            self.logger.subsection("Stage 3: Transaction Simulation (Basic)")
            self.logger.debug("Simulating transaction execution...")

            sim_result = self.simulator.simulate(transaction, from_address)

            if not sim_result.success:
                if self.config.simulation.get("fail_on_revert", True):
                    reason = f"Simulation failed: {sim_result.revert_reason or sim_result.error}"
                    self.logger.error(f"Simulation failure: {reason}")
                    self.logger.minimal(f"❌ BLOCKED: Transaction would revert")
                    return False, reason
                else:
                    self.logger.warning(f"Simulation failed but fail_on_revert=False: {sim_result.error}")
            else:
                self.logger.success("Simulation successful - transaction will execute")

            # Gas estimation
            if self.config.simulation.get("estimate_gas", False):
                estimated_gas = self.simulator.estimate_gas(transaction, from_address)
                if estimated_gas:
                    self.logger.debug(f"Estimated gas: {estimated_gas}")

        # ============================================================
        # STAGE 3.5: HONEYPOT DETECTION - Proactive Token Scam Detection
        # ============================================================
        # Automatically enabled when llm_validation is enabled
        honeypot_enabled = self.config.llm_validation.get("enabled", False)

        if honeypot_enabled and tenderly_result and tenderly_result.success and from_address:
            self.logger.subsection("Stage 3.5: Honeypot Detection")
            self.logger.debug("Checking if token can be sold back (honeypot detection)...")

            is_honeypot, honeypot_reason = self._check_honeypot_token(
                transaction=transaction,
                parsed_tx=parsed_tx,
                simulation_result=tenderly_result,
                from_address=from_address
            )

            if is_honeypot:
                self.logger.error(f"\n{'🚨 ' * 30}")
                self.logger.error(f"🚨 HONEYPOT TOKEN DETECTED!")
                self.logger.error(f"{'🚨 ' * 30}\n")
                self.logger.error(f"Reason: {honeypot_reason}")
                self.logger.minimal(f"\n❌ BLOCKED: {honeypot_reason}\n")
                return False, honeypot_reason
            else:
                self.logger.success("No honeypot detected - token can be sold normally")

        # ============================================================
        # STAGE 4: LLM VALIDATION - Intelligent Malicious Activity Detection
        # ============================================================
        if self.llm_validator and from_address:
            self.logger.subsection("Stage 4: LLM-based Security Validation")
            self.logger.debug("Analyzing transaction for malicious patterns...")

            # Build policy context for LLM
            policy_context = self._build_policy_context()

            llm_analysis = self.llm_validator.analyze(
                transaction=transaction,
                parsed_tx=parsed_tx,
                simulation_result=tenderly_result,
                policy_context=policy_context
            )

            if llm_analysis:
                self.logger.debug(f"LLM confidence: {llm_analysis.confidence:.2%}")
                self.logger.debug(f"Risk level: {llm_analysis.risk_level}")

                # Check if should block
                if llm_analysis.should_block(self.config.llm_validation.get("block_threshold", 0.70)):
                    self.logger.error(f"LLM detected malicious activity: {llm_analysis.reason}")
                    self.logger.minimal(f"❌ BLOCKED by LLM: {llm_analysis.reason}")
                    self.logger.minimal(f"Confidence: {llm_analysis.confidence:.0%} | Risk: {llm_analysis.risk_level}")
                    if llm_analysis.indicators:
                        self.logger.minimal(f"Indicators: {', '.join(llm_analysis.indicators)}")
                    return False, f"LLM security check failed: {llm_analysis.reason}"

                # Check if should warn
                elif llm_analysis.should_warn(self.config.llm_validation.get("warn_threshold", 0.40)):
                    self.logger.warning(f"⚠️  LLM warning: {llm_analysis.reason}")
                    self.logger.warning(f"Confidence: {llm_analysis.confidence:.0%} | Risk: {llm_analysis.risk_level}")
                    if llm_analysis.indicators:
                        self.logger.warning(f"Indicators: {', '.join(llm_analysis.indicators)}")
                    # Continue execution but log warning

                else:
                    self.logger.success(f"LLM validation: No malicious activity detected")

        # ============================================================
        # FINAL JUDGE: ALLOW
        # ============================================================
        self.logger.minimal("✅ ALLOWED: All security checks passed")
        self.logger.success("Transaction approved for execution")

        return True, "All policies passed"

    def _print_tenderly_trace(self, tenderly_result):
        """Print detailed Tenderly simulation trace"""
        self.logger.subsection("Tenderly Simulation Details")

        # Print call trace
        if tenderly_result.call_trace:
            self.logger.info("Call Trace:")
            for i, trace in enumerate(tenderly_result.call_trace, 1):
                self._print_trace_recursive(trace, indent=1, index=i, is_root=True)

        # Print asset changes
        if tenderly_result.asset_changes:
            self.logger.info("\nAsset/Balance Changes:")
            for change in tenderly_result.asset_changes:
                delta_sign = "+" if change.delta and not change.delta.startswith("-") else ""
                self.logger.info(
                    f"  {change.address[:10]}... "
                    f"({change.asset_type}): "
                    f"{delta_sign}{change.delta}",
                    prefix="  "
                )

        # Print logs/events
        if tenderly_result.logs:
            self.logger.info("\nEvents Emitted:")
            for i, log in enumerate(tenderly_result.logs, 1):
                self.logger.info(f"  [{i}] {log.name or 'Unknown'}", prefix="  ")
                if log.inputs:
                    for inp in log.inputs[:3]:  # Show first 3 inputs
                        input_name = inp.get("soltype", {}).get("name", "unknown")
                        input_value = str(inp.get("value", ""))
                        if len(input_value) > 42:
                            input_value = input_value[:42] + "..."
                        self.logger.debug(f"      {input_name}: {input_value}")

    def _build_policy_context(self) -> Dict[str, Any]:
        """Build policy context for LLM analysis"""
        context = {}

        # Extract whitelisted addresses from allowlist policy
        for policy in self.config.policies:
            if policy.get("type") == "address_allowlist":
                allowed_addresses = policy.get("allowed_addresses", [])
                if allowed_addresses:
                    # Normalize addresses to lowercase for comparison
                    context["whitelisted_addresses"] = [addr.lower() for addr in allowed_addresses]

            # Extract denied addresses from denylist policy
            elif policy.get("type") == "address_denylist":
                denied_addresses = policy.get("denied_addresses", [])
                if denied_addresses:
                    context["denied_addresses"] = [addr.lower() for addr in denied_addresses]

            # Extract ETH value limit
            elif policy.get("type") == "eth_value_limit" and policy.get("enabled"):
                max_value = policy.get("max_value_wei")
                if max_value:
                    context["max_eth_value"] = max_value

        return context

    def _check_honeypot_token(
        self,
        transaction: Dict[str, Any],
        parsed_tx: Any,
        simulation_result: Any,
        from_address: str
    ) -> tuple[bool, Optional[str]]:
        """
        Honeypot detection: Simulate buy, then simulate sell. If sell fails → HONEYPOT → Block buy.

        Args:
            transaction: The original transaction (potential BUY)
            parsed_tx: Parsed transaction details
            simulation_result: Tenderly simulation result of the BUY
            from_address: User's address

        Returns:
            (is_honeypot, reason) tuple
        """
        if not simulation_result or not simulation_result.has_data():
            return False, None

        if not self.tenderly_simulator:
            return False, None

        # Step 1: Check if user received any tokens in this transaction
        # This indicates it might be a BUY/swap
        tokens_received = []
        user_addr = from_address.lower()

        if hasattr(simulation_result, 'asset_changes'):
            for change in simulation_result.asset_changes:
                addr = change.address.lower()
                try:
                    delta = int(change.delta) if change.delta else 0
                except (ValueError, TypeError):
                    delta = 0

                # User received tokens (positive delta for ERC20)
                if addr == user_addr and delta > 0 and change.asset_type == "ERC20":
                    tokens_received.append({
                        'token_address': change.asset_address,
                        'amount': delta
                    })

        # Also check Transfer events if asset_changes is empty or incomplete
        # Transfer(address indexed from, address indexed to, uint256 value)
        # Event signature: 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
        if hasattr(simulation_result, 'logs') and simulation_result.logs:
            for log in simulation_result.logs:
                # Check if this is a Transfer event (even if Tenderly couldn't decode it)
                # Transfer events have 3 topics: [signature, from, to]
                if hasattr(log, 'raw') and log.raw:
                    topics = log.raw.get('topics', [])
                    data = log.raw.get('data', '0x')

                    # Transfer event signature
                    if len(topics) >= 3 and topics[0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                        # topics[1] = from (indexed)
                        # topics[2] = to (indexed)
                        # data = amount (non-indexed)

                        # Extract 'to' address from topics[2]
                        to_address = '0x' + topics[2][-40:]  # Last 20 bytes (40 hex chars)

                        # Check if user is the recipient
                        if to_address.lower() == user_addr:
                            # Extract amount from data
                            try:
                                amount = int(data, 16) if data and data != '0x' else 0
                            except (ValueError, TypeError):
                                amount = 0

                            # Get token contract address
                            token_address = log.raw.get('address', '').lower()

                            if amount > 0 and token_address:
                                # Check if we already have this token from asset_changes
                                already_tracked = any(
                                    t.get('token_address', '').lower() == token_address
                                    for t in tokens_received
                                )

                                if not already_tracked:
                                    self.logger.debug(f"  Detected token receipt from Transfer event: {token_address[:10]}... amount={amount}")
                                    tokens_received.append({
                                        'token_address': token_address,
                                        'amount': amount
                                    })

        # If no tokens received, not a token purchase → skip honeypot check
        if not tokens_received:
            return False, None

        self.logger.debug(f"Token BUY detected. Checking if tokens can be sold back (honeypot detection)...")

        # Whitelist of known safe tokens (skip honeypot detection)
        KNOWN_SAFE_TOKENS = {
            # WETH on various chains
            '0x4200000000000000000000000000000000000006',  # WETH on Base (official)
            '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',  # WETH on Ethereum
            '0x82af49447d8a07e3bd95bd0d56f35241523fbab1',  # WETH on Arbitrum
            '0x4200000000000000000000000000000000000006',  # WETH on Optimism
            # Major stablecoins
            '0x036cbd53842c5426634e7929541ec2318f3dcf7e',  # USDC on Base Sepolia
            '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913',  # USDC on Base
            '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',  # USDC on Ethereum
            '0xdac17f958d2ee523a2206206994597c13d831ec7',  # USDT on Ethereum
            '0x6b175474e89094c44da98b954eedeac495271d0f',  # DAI on Ethereum
        }

        # Step 2: For each token received, simulate a SELL transaction
        for token_info in tokens_received:
            token_addr = token_info.get('token_address')
            amount = token_info.get('amount')

            if not token_addr or not amount:
                continue

            # Skip honeypot check for known safe tokens
            if token_addr.lower() in KNOWN_SAFE_TOKENS:
                self.logger.debug(f"  Skipping honeypot check for known safe token {token_addr[:10]}... (whitelisted)")
                continue

            self.logger.debug(f"  Testing sell for token {token_addr[:10]}... (amount: {amount})")

            # Construct a transfer() call to simulate selling
            # transfer(address to, uint256 amount)
            # We'll transfer to a random address to test if transfer works
            test_recipient = "0x0000000000000000000000000000000000000001"  # Burn address

            # Encode transfer function call
            # Function selector: transfer(address,uint256) = 0xa9059cbb
            transfer_selector = "0xa9059cbb"
            # Pad address to 32 bytes
            recipient_padded = test_recipient[2:].zfill(64)
            # Pad amount to 32 bytes (hex)
            amount_hex = hex(amount)[2:].zfill(64)
            calldata = transfer_selector + recipient_padded + amount_hex

            # Create sell transaction
            sell_transaction = {
                'from': from_address,
                'to': token_addr,
                'data': calldata,
                'value': '0x0',
                'gas': '0x100000',  # 1M gas limit
            }

            # Step 3: Simulate the SELL
            network_id = str(self.chain_id) if self.chain_id else "1"
            sell_result = self.tenderly_simulator.simulate(
                sell_transaction,
                from_address,
                network_id=network_id
            )

            if not sell_result or not sell_result.success:
                # Sell simulation failed/reverted → might be honeypot
                self.logger.warning(f"  ⚠️  Sell simulation FAILED/REVERTED for {token_addr[:10]}...")
                reason = f"HONEYPOT DETECTED: Token {token_addr[:10]}... can be bought but cannot be sold"
                return True, reason

            # Step 4: Check sell simulation for honeypot indicators
            # 4a. Check if Transfer events were emitted
            transfer_events_found = False
            if hasattr(sell_result, 'logs'):
                transfer_events = [log for log in sell_result.logs
                                 if hasattr(log, 'name') and log.name in ['Transfer', 'TransferSingle', 'TransferBatch']]
                transfer_events_found = len(transfer_events) > 0

            if not transfer_events_found:
                # No Transfer events → honeypot (transfer called but no actual movement)
                self.logger.warning(f"  ⚠️  No Transfer events in sell simulation for {token_addr[:10]}...")
                reason = f"HONEYPOT DETECTED: Token {token_addr[:10]}... transfer() succeeds but emits no Transfer events"
                return True, reason

            # 4b. Check if user's balance actually decreased
            user_balance_decreased = False
            if hasattr(sell_result, 'asset_changes'):
                for change in sell_result.asset_changes:
                    addr = change.address.lower()
                    try:
                        delta = int(change.delta) if change.delta else 0
                    except (ValueError, TypeError):
                        delta = 0

                    # User's balance should decrease (negative delta)
                    if addr == user_addr and delta < 0:
                        user_balance_decreased = True
                        break

            if not user_balance_decreased:
                # Balance didn't decrease → honeypot
                self.logger.warning(f"  ⚠️  User balance didn't decrease in sell for {token_addr[:10]}...")
                reason = f"HONEYPOT DETECTED: Token {token_addr[:10]}... balance doesn't decrease on transfer"
                return True, reason

            self.logger.success(f"  ✓ Token {token_addr[:10]}... can be sold (not a honeypot)")

        # All tokens passed the sell test → not a honeypot
        return False, None

    def _print_trace_recursive(self, trace, indent=0, index=1, is_root=False):
        """Recursively print call trace"""
        prefix = "  " * indent

        # Format value
        value_eth = trace.value / 1e18 if trace.value else 0
        value_str = f"{value_eth:.6f} ETH" if value_eth > 0 else "0 ETH"

        # Format addresses (handle empty addresses)
        from_addr = f"{trace.from_address[:10]}..." if trace.from_address else "(empty)"
        to_addr = f"{trace.to_address[:10]}..." if trace.to_address else "(empty)"

        # Skip low-level opcodes with no meaningful data (but not the root trace)
        # Only filter deep subcalls (indent > 1) that are low-level operations
        if not is_root and indent > 1:
            if (trace.gas_used == 0 or
                (not trace.from_address and not trace.to_address) or
                trace.type in ["SLOAD", "STOP"]):
                # Don't print these low-level operations, but still recurse into their calls
                if trace.calls:
                    for i, subcall in enumerate(trace.calls, 1):
                        self._print_trace_recursive(subcall, indent, i, is_root=False)
                return

        # Print trace entry
        self.logger.info(
            f"{prefix}[{index}] {trace.type}: "
            f"{from_addr} → {to_addr} "
            f"(value: {value_str}, gas: {trace.gas_used})",
            prefix=prefix
        )

        # Print error if any
        if trace.error:
            self.logger.error(f"{prefix}    Error: {trace.error}", prefix=prefix + "    ")

        # Print subcalls
        if trace.calls:
            for i, subcall in enumerate(trace.calls, 1):
                self._print_trace_recursive(subcall, indent + 1, i, is_root=False)
