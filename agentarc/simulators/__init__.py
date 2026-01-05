"""
Simulators for transaction analysis

Available simulators:
- TransactionSimulator: Basic eth_call simulation
- TenderlySimulator: Advanced simulation with Tenderly API
"""

from .tenderly import TenderlySimulator, TenderlySimulationResult

__all__ = [
    "TenderlySimulator",
    "TenderlySimulationResult",
]
