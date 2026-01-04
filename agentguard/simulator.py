"""
Transaction simulation engine
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from web3 import Web3


@dataclass
class SimulationResult:
    """Result of transaction simulation"""
    success: bool
    error: Optional[str] = None
    return_data: Optional[bytes] = None
    gas_used: Optional[int] = None
    revert_reason: Optional[str] = None


class TransactionSimulator:
    """Simulate transactions before execution"""

    def __init__(self, web3_provider: Optional[Any] = None):
        """
        Initialize simulator

        Args:
            web3_provider: Web3 instance or wallet provider with web3 access
        """
        self.web3_provider = web3_provider

    def simulate(self, tx: Dict[str, Any], from_address: str) -> SimulationResult:
        """
        Simulate transaction using eth_call

        Args:
            tx: Transaction dict (to, data, value, etc.)
            from_address: Address sending the transaction

        Returns:
            SimulationResult with success/failure information
        """
        # Check if we have a web3 provider
        if not self.web3_provider:
            return SimulationResult(
                success=True,
                error="Simulation skipped - no web3 provider available"
            )

        # Get web3 instance
        try:
            if hasattr(self.web3_provider, 'web3'):
                web3 = self.web3_provider.web3
            elif isinstance(self.web3_provider, Web3):
                web3 = self.web3_provider
            else:
                return SimulationResult(
                    success=True,
                    error="Simulation skipped - incompatible provider"
                )
        except Exception:
            return SimulationResult(
                success=True,
                error="Simulation skipped - could not access web3"
            )

        # Prepare transaction for simulation
        sim_tx = {
            "from": from_address,
            "to": tx.get("to"),
            "value": tx.get("value", 0),
        }

        if "data" in tx and tx["data"]:
            sim_tx["data"] = tx["data"]

        if "gas" in tx:
            sim_tx["gas"] = tx["gas"]

        # Try to simulate using eth_call
        try:
            result = web3.eth.call(sim_tx)

            return SimulationResult(
                success=True,
                return_data=result,
                error=None
            )

        except Exception as e:
            error_msg = str(e)

            # Try to extract revert reason
            revert_reason = self._extract_revert_reason(error_msg)

            return SimulationResult(
                success=False,
                error=error_msg,
                revert_reason=revert_reason or error_msg
            )

    def _extract_revert_reason(self, error_msg: str) -> Optional[str]:
        """
        Extract human-readable revert reason from error message

        Args:
            error_msg: Error message from eth_call

        Returns:
            Revert reason if found, None otherwise
        """
        # Common patterns for revert reasons
        patterns = [
            "execution reverted: ",
            "revert ",
            "Error: "
        ]

        for pattern in patterns:
            if pattern in error_msg:
                idx = error_msg.find(pattern)
                reason = error_msg[idx + len(pattern):].strip()
                # Remove trailing quotes if present
                if reason.startswith('"') and reason.endswith('"'):
                    reason = reason[1:-1]
                return reason

        return None

    def estimate_gas(self, tx: Dict[str, Any], from_address: str) -> Optional[int]:
        """
        Estimate gas for transaction

        Args:
            tx: Transaction dict
            from_address: Sender address

        Returns:
            Estimated gas or None if estimation fails
        """
        if not self.web3_provider:
            return None

        try:
            if hasattr(self.web3_provider, 'web3'):
                web3 = self.web3_provider.web3
            elif isinstance(self.web3_provider, Web3):
                web3 = self.web3_provider
            else:
                return None

            sim_tx = {
                "from": from_address,
                "to": tx.get("to"),
                "value": tx.get("value", 0),
            }

            if "data" in tx and tx["data"]:
                sim_tx["data"] = tx["data"]

            gas_estimate = web3.eth.estimate_gas(sim_tx)
            return int(gas_estimate)

        except Exception:
            return None
