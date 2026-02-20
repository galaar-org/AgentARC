"""
Simulation Stage - Test transaction execution.

This stage simulates the transaction before execution:
- Uses Tenderly if available (with detailed traces)
- Falls back to basic eth_call simulation
- Optionally fails on revert
"""

from typing import Any, Optional, Tuple

from ..pipeline import PipelineStage
from ..context import ValidationContext
from ...core.config import PolicyConfig
from ...core.events import ValidationStage
from ...core.interfaces import SimulatorProtocol


class SimulationStage(PipelineStage):
    """
    Simulate transaction execution.

    This stage:
    1. Tries Tenderly simulation first (if available)
    2. Falls back to basic eth_call simulation
    3. Stores result in context.tenderly_result or context.simulation_result
    4. Optionally fails if simulation reverts

    Attributes:
        simulator: Basic TransactionSimulator
        tenderly_simulator: TenderlySimulator (optional)
        config: PolicyConfig for simulation settings
        chain_id: Chain ID for Tenderly simulation
    """

    def __init__(
        self,
        simulator: Optional[SimulatorProtocol] = None,
        tenderly_simulator: Optional[Any] = None,
        config: Optional[PolicyConfig] = None,
        chain_id: Optional[int] = None,
    ):
        super().__init__(
            name="Transaction Simulation",
            stage_type=ValidationStage.SIMULATION,
        )
        self.simulator = simulator
        self.tenderly_simulator = tenderly_simulator
        self.config = config
        self.chain_id = chain_id

    def execute(self, context: ValidationContext) -> Tuple[bool, Optional[str]]:
        """
        Simulate transaction execution.

        Args:
            context: ValidationContext with transaction data

        Returns:
            (True, None) if simulation passes or is skipped
            (False, reason) if simulation fails and fail_on_revert=True
        """
        if not context.from_address:
            if self.logger:
                self.logger.debug("Skipping simulation - no from_address")
            return True, None

        # Try Tenderly first
        if self.tenderly_simulator:
            return self._run_tenderly_simulation(context)

        # Fall back to basic simulation
        if self.simulator and self.config and self.config.simulation.get("enabled"):
            return self._run_basic_simulation(context)

        return True, None

    def _run_tenderly_simulation(self, context: ValidationContext) -> Tuple[bool, Optional[str]]:
        """Run Tenderly simulation."""
        self.emit_started("Simulating with Tenderly")

        if self.logger:
            self.logger.debug("Simulating transaction execution...")

        network_id = str(self.chain_id) if self.chain_id else "1"
        result = self.tenderly_simulator.simulate(
            context.transaction,
            context.from_address,
            network_id=network_id,
        )

        context.tenderly_result = result

        if result and result.success:
            if self.logger:
                self.logger.success(f"Simulation passed (gas: {result.gas_used})")

            self.emit_passed(
                f"Simulation passed (gas: {result.gas_used})",
                {
                    "gas_used": result.gas_used,
                    "success": True,
                    "asset_changes": len(result.asset_changes) if result.asset_changes else 0,
                    "logs": len(result.logs) if result.logs else 0,
                },
            )

            # Log asset changes in debug mode
            if result.asset_changes and self.logger:
                self.logger.debug("Asset changes:")
                for change in result.asset_changes:
                    delta_sign = "+" if change.delta and not change.delta.startswith("-") else ""
                    self.logger.debug(
                        f"  {change.address[:10]}... ({change.asset_type}): {delta_sign}{change.delta}",
                        prefix="  ",
                    )

            # Print trace if enabled
            if self.config and self.config.simulation.get("print_trace", False):
                self._print_tenderly_trace(result)

            return True, None

        elif result and not result.success:
            if self.config and self.config.simulation.get("fail_on_revert", True):
                reason = f"Tenderly simulation failed: {result.error}"

                if self.logger:
                    self.logger.error(reason)
                    self.logger.minimal("BLOCKED: Transaction would fail")

                self.emit_failed(
                    "Transaction would revert",
                    {"error": result.error, "success": False},
                )
                return False, reason
            else:
                if self.logger:
                    self.logger.warning("Tenderly simulation failed but fail_on_revert=False")

                self.emit_warning(
                    "Simulation failed but continuing (fail_on_revert=False)",
                    {"error": result.error},
                )
                return True, None

        return True, None

    def _run_basic_simulation(self, context: ValidationContext) -> Tuple[bool, Optional[str]]:
        """Run basic eth_call simulation."""
        if self.logger:
            self.logger.subsection("Transaction Simulation (Basic)")
            self.logger.debug("Simulating transaction execution...")

        result = self.simulator.simulate(context.transaction, context.from_address)
        context.simulation_result = result

        if not result.success:
            if self.config and self.config.simulation.get("fail_on_revert", True):
                reason = f"Simulation failed: {result.revert_reason or result.error}"

                if self.logger:
                    self.logger.error(f"Simulation failure: {reason}")
                    self.logger.minimal("BLOCKED: Transaction would revert")

                return False, reason
            else:
                if self.logger:
                    self.logger.warning(f"Simulation failed but fail_on_revert=False: {result.error}")
        else:
            if self.logger:
                self.logger.success("Simulation successful - transaction will execute")

        # Gas estimation
        if self.config and self.config.simulation.get("estimate_gas", False):
            estimated_gas = self.simulator.estimate_gas(context.transaction, context.from_address)
            if estimated_gas and self.logger:
                self.logger.debug(f"Estimated gas: {estimated_gas}")

        return True, None

    def _print_tenderly_trace(self, result: Any) -> None:
        """Print detailed Tenderly simulation trace."""
        if not self.logger:
            return

        self.logger.subsection("Tenderly Simulation Details")

        # Print call trace
        if result.call_trace:
            self.logger.info("Call Trace:")
            for i, trace in enumerate(result.call_trace, 1):
                self._print_trace_recursive(trace, indent=1, index=i, is_root=True)

        # Print asset changes
        if result.asset_changes:
            self.logger.info("\nAsset/Balance Changes:")
            for change in result.asset_changes:
                delta_sign = "+" if change.delta and not change.delta.startswith("-") else ""
                self.logger.info(
                    f"  {change.address[:10]}... ({change.asset_type}): {delta_sign}{change.delta}",
                    prefix="  ",
                )

        # Print logs/events
        if result.logs:
            self.logger.info("\nEvents Emitted:")
            for i, log in enumerate(result.logs, 1):
                self.logger.info(f"  [{i}] {log.name or 'Unknown'}", prefix="  ")
                if log.inputs:
                    for inp in log.inputs[:3]:
                        input_name = inp.get("soltype", {}).get("name", "unknown")
                        input_value = str(inp.get("value", ""))
                        if len(input_value) > 42:
                            input_value = input_value[:42] + "..."
                        self.logger.debug(f"      {input_name}: {input_value}")

    def _print_trace_recursive(self, trace: Any, indent: int = 0, index: int = 1, is_root: bool = False) -> None:
        """Recursively print call trace."""
        if not self.logger:
            return

        prefix = "  " * indent

        # Format value
        value_eth = trace.value / 1e18 if trace.value else 0
        value_str = f"{value_eth:.6f} ETH" if value_eth > 0 else "0 ETH"

        # Format addresses
        from_addr = f"{trace.from_address[:10]}..." if trace.from_address else "(empty)"
        to_addr = f"{trace.to_address[:10]}..." if trace.to_address else "(empty)"

        # Skip low-level opcodes
        if not is_root and indent > 1:
            if (trace.gas_used == 0 or
                (not trace.from_address and not trace.to_address) or
                trace.type in ["SLOAD", "STOP"]):
                if trace.calls:
                    for i, subcall in enumerate(trace.calls, 1):
                        self._print_trace_recursive(subcall, indent, i, is_root=False)
                return

        # Print trace entry
        self.logger.info(
            f"{prefix}[{index}] {trace.type}: {from_addr} -> {to_addr} (value: {value_str}, gas: {trace.gas_used})",
            prefix=prefix,
        )

        # Print error if any
        if trace.error:
            self.logger.error(f"{prefix}    Error: {trace.error}", prefix=prefix + "    ")

        # Print subcalls
        if trace.calls:
            for i, subcall in enumerate(trace.calls, 1):
                self._print_trace_recursive(subcall, indent + 1, i, is_root=False)
