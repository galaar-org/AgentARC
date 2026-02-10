"""
Intent Analysis Stage - Parse and understand transaction intent.

This stage parses the transaction calldata to extract:
- Function name and selector
- Recipient address
- Token amounts
- Decoded parameters
"""

from typing import Optional, Tuple

from ..pipeline import PipelineStage
from ..context import ValidationContext
from ...core.config import PolicyConfig
from ...core.events import ValidationStage
from ...core.interfaces import CalldataParserProtocol


class IntentAnalysisStage(PipelineStage):
    """
    Parse transaction calldata to understand intent.

    This stage:
    1. Parses the transaction using CalldataParser
    2. Extracts function name, recipient, token amounts
    3. Stores parsed data in context.parsed_tx

    Attributes:
        parser: CalldataParser instance
        config: PolicyConfig for calldata validation settings
    """

    def __init__(
        self,
        parser: CalldataParserProtocol,
        config: Optional[PolicyConfig] = None,
    ):
        super().__init__(
            name="Intent Analysis",
            stage_type=ValidationStage.INTENT_ANALYSIS,
        )
        self.parser = parser
        self.config = config

    def execute(self, context: ValidationContext) -> Tuple[bool, Optional[str]]:
        """
        Parse transaction and store in context.

        Args:
            context: ValidationContext with transaction data

        Returns:
            Always returns (True, None) - this stage doesn't fail
        """
        self.emit_started("Analyzing transaction intent")

        # Parse transaction
        parsed_tx = self.parser.parse(context.transaction)
        context.parsed_tx = parsed_tx

        # Log transaction details
        if self.logger:
            self.logger.info(f"To: {parsed_tx.to[:10]}...")
            self.logger.info(f"Value: {parsed_tx.value / 1e18:.6f} ETH")
            if parsed_tx.function_name:
                self.logger.info(f"Function: {parsed_tx.function_name}")
            if parsed_tx.function_selector:
                self.logger.debug(f"Selector: {parsed_tx.function_selector}")
            if parsed_tx.recipient_address:
                self.logger.debug(f"Recipient: {parsed_tx.recipient_address}")
            if parsed_tx.token_amount:
                self.logger.debug(f"Token Amount: {parsed_tx.token_amount}")

        # Log calldata if enabled
        if self.config and self.config.calldata_validation.get("enabled", True):
            calldata = context.data
            if calldata and calldata != "0x":
                self.logger.debug(f"Calldata: {calldata[:66]}...")
                self.logger.debug(f"Calldata length: {len(calldata)} chars")

        # Emit success event
        self.emit_passed(
            f"Transaction to {parsed_tx.to[:10]}...",
            {
                "to": parsed_tx.to,
                "value_eth": parsed_tx.value / 1e18,
                "function": parsed_tx.function_name or "unknown",
                "recipient": parsed_tx.recipient_address,
                "token_amount": str(parsed_tx.token_amount) if parsed_tx.token_amount else None,
            },
        )

        return True, None
