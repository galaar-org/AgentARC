"""
Policy Validation Stage - Check against configured policies.

This stage runs all configured policy validators:
- Address denylist/allowlist
- ETH value limits
- Token amount limits
- Gas limits
- Function allowlist
"""

from typing import Any, List, Optional, Tuple

from ..pipeline import PipelineStage
from ..context import ValidationContext
from ...core.config import PolicyConfig
from ...core.events import ValidationStage


class PolicyValidationStage(PipelineStage):
    """
    Validate transaction against configured policies.

    This stage:
    1. Runs all enabled policy validators
    2. Checks gas limit separately (needs raw transaction)
    3. Fails on first policy violation

    Attributes:
        validators: List of PolicyValidator instances
        config: PolicyConfig for gas limit policy
    """

    def __init__(
        self,
        validators: List[Any],
        config: Optional[PolicyConfig] = None,
    ):
        super().__init__(
            name="Policy Validation",
            stage_type=ValidationStage.POLICY_VALIDATION,
        )
        self.validators = validators
        self.config = config

    def execute(self, context: ValidationContext) -> Tuple[bool, Optional[str]]:
        """
        Run all policy validators.

        Args:
            context: ValidationContext with parsed transaction

        Returns:
            (True, None) if all policies pass
            (False, reason) if any policy fails
        """
        self.emit_started("Running policy validators")

        if self.logger:
            self.logger.debug("Running policy validators...")

        parsed_tx = context.parsed_tx
        if not parsed_tx:
            return False, "Transaction not parsed (intent analysis failed)"

        # Run all validators
        for i, validator in enumerate(self.validators, 1):
            if not validator.enabled:
                if self.logger:
                    self.logger.debug(f"[{i}] {validator.name}: SKIPPED (disabled)")
                continue

            if self.logger:
                self.logger.debug(f"[{i}] Checking policy: {validator.name}")

            result = validator.validate(parsed_tx)

            if not result.passed:
                if self.logger:
                    self.logger.error(f"Policy violation: {result.reason}")
                    self.logger.minimal(f"BLOCKED: {result.reason}")

                self.emit_failed(
                    f"Policy violation: {validator.name}",
                    {"rule": validator.name, "reason": result.reason},
                )
                return False, result.reason

            if self.logger:
                self.logger.info(f"  {validator.name}: PASSED", prefix="  ")

            self.emit_info(
                f"{validator.name}: PASSED",
                {"rule": validator.name, "status": "passed"},
            )

        # Check gas limit (needs raw transaction)
        passed, reason = self._check_gas_limit(context)
        if not passed:
            return False, reason

        self.emit_passed("All policy validators passed")
        return True, None

    def _check_gas_limit(self, context: ValidationContext) -> Tuple[bool, Optional[str]]:
        """Check gas limit policy separately."""
        if not self.config:
            return True, None

        gas_limit_policy = next(
            (p for p in self.config.policies
             if p.get("type") == "gas_limit" and p.get("enabled", True)),
            None
        )

        if not gas_limit_policy:
            return True, None

        max_gas = int(gas_limit_policy.get("max_gas", 0))
        tx_gas = context.gas

        if self.logger:
            self.logger.debug(f"Checking gas limit: {tx_gas} <= {max_gas}")

        if tx_gas > max_gas:
            reason = f"Gas {tx_gas} exceeds limit {max_gas}"

            if self.logger:
                self.logger.error(f"Policy violation: {reason}")
                self.logger.minimal(f"BLOCKED: {reason}")

            self.emit_failed(
                "Gas limit exceeded",
                {"rule": "gas_limit", "max_gas": max_gas, "tx_gas": tx_gas, "reason": reason},
            )
            return False, reason

        if self.logger:
            self.logger.info("  gas_limit: PASSED", prefix="  ")

        self.emit_info(
            "gas_limit: PASSED",
            {"rule": "gas_limit", "status": "passed"},
        )

        return True, None
