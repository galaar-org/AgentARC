"""
Honeypot Detection Stage - Detect scam tokens.

This stage detects honeypot tokens by simulating a sell
after detecting a token purchase. Honeypot tokens can be
bought but not sold.
"""

from typing import Any, Dict, List, Optional, Tuple

from ..pipeline import PipelineStage
from ..context import ValidationContext
from ...core.events import ValidationStage


# Known safe tokens (skip honeypot detection)
KNOWN_SAFE_TOKENS = {
    # WETH on various chains
    "0x4200000000000000000000000000000000000006",  # WETH on Base/Optimism
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH on Ethereum
    "0x82af49447d8a07e3bd95bd0d56f35241523fbab1",  # WETH on Arbitrum
    # Major stablecoins
    "0x036cbd53842c5426634e7929541ec2318f3dcf7e",  # USDC on Base Sepolia
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # USDC on Base
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC on Ethereum
    "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT on Ethereum
    "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI on Ethereum
}


class HoneypotDetectionStage(PipelineStage):
    """
    Detect honeypot tokens by simulating sell transactions.

    Detection Algorithm:
    1. Detect token purchase from simulation asset changes
    2. Skip known safe tokens (WETH, stablecoins)
    3. Simulate sell for each token received
    4. Check for honeypot indicators:
       - Sell simulation reverts
       - No Transfer events in sell
       - User balance unchanged after sell

    Attributes:
        tenderly_simulator: TenderlySimulator for sell simulation
        chain_id: Chain ID for simulation
    """

    def __init__(
        self,
        tenderly_simulator: Any,
        chain_id: Optional[int] = None,
    ):
        super().__init__(
            name="Honeypot Detection",
            stage_type=ValidationStage.HONEYPOT_DETECTION,
        )
        self.tenderly_simulator = tenderly_simulator
        self.chain_id = chain_id

    def execute(self, context: ValidationContext) -> Tuple[bool, Optional[str]]:
        """
        Check if purchased tokens are honeypots.

        Args:
            context: ValidationContext with Tenderly simulation result

        Returns:
            (True, None) if no honeypot detected or not a token purchase
            (False, reason) if honeypot detected
        """
        tenderly_result = context.tenderly_result

        if not tenderly_result or not tenderly_result.has_data():
            return True, None

        if not context.from_address:
            return True, None

        self.emit_started("Checking for honeypot tokens")

        # Detect tokens received in this transaction
        tokens_received = self._detect_tokens_received(
            tenderly_result,
            context.from_address,
        )

        if not tokens_received:
            return True, None

        if self.logger:
            self.logger.debug("Token BUY detected. Checking if tokens can be sold...")

        # Check each token for honeypot indicators
        for token_info in tokens_received:
            token_addr = token_info.get("token_address", "").lower()
            amount = token_info.get("amount", 0)

            if not token_addr or not amount:
                continue

            # Skip known safe tokens
            if token_addr in KNOWN_SAFE_TOKENS:
                if self.logger:
                    self.logger.debug(f"  Skipping {token_addr[:10]}... (whitelisted)")
                continue

            # Simulate sell
            is_honeypot, reason = self._check_token_sellable(
                token_addr,
                amount,
                context.from_address,
            )

            if is_honeypot:
                if self.logger:
                    self.logger.error("\n" + "HONEYPOT TOKEN DETECTED!" * 3 + "\n")
                    self.logger.error(f"Reason: {reason}")
                    self.logger.minimal(f"\nBLOCKED: {reason}\n")

                self.emit_failed(
                    "HONEYPOT TOKEN DETECTED!",
                    {"is_honeypot": True, "reason": reason, "token": token_addr},
                )
                return False, reason

            if self.logger:
                self.logger.success(f"  Token {token_addr[:10]}... can be sold (not a honeypot)")

        # All tokens passed
        self.emit_passed(
            "No honeypot detected - token can be sold normally",
            {"is_honeypot": False},
        )
        return True, None

    def _detect_tokens_received(
        self,
        simulation_result: Any,
        from_address: str,
    ) -> List[Dict[str, Any]]:
        """Detect tokens received in this transaction."""
        tokens_received = []
        user_addr = from_address.lower()

        # Check asset_changes
        if hasattr(simulation_result, "asset_changes"):
            for change in simulation_result.asset_changes:
                addr = change.address.lower()
                try:
                    delta = int(change.delta) if change.delta else 0
                except (ValueError, TypeError):
                    delta = 0

                # User received ERC20 tokens
                if addr == user_addr and delta > 0 and change.asset_type == "ERC20":
                    tokens_received.append({
                        "token_address": change.asset_address,
                        "amount": delta,
                    })

        # Also check Transfer events
        if hasattr(simulation_result, "logs") and simulation_result.logs:
            for log in simulation_result.logs:
                if not hasattr(log, "raw") or not log.raw:
                    continue

                topics = log.raw.get("topics", [])
                data = log.raw.get("data", "0x")

                # Transfer event signature
                transfer_sig = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                if len(topics) >= 3 and topics[0] == transfer_sig:
                    # Extract 'to' address from topics[2]
                    to_address = "0x" + topics[2][-40:]

                    if to_address.lower() == user_addr:
                        try:
                            amount = int(data, 16) if data and data != "0x" else 0
                        except (ValueError, TypeError):
                            amount = 0

                        token_address = log.raw.get("address", "").lower()

                        if amount > 0 and token_address:
                            # Avoid duplicates
                            already_tracked = any(
                                t.get("token_address", "").lower() == token_address
                                for t in tokens_received
                            )
                            if not already_tracked:
                                if self.logger:
                                    self.logger.debug(f"  Detected token from Transfer: {token_address[:10]}...")
                                tokens_received.append({
                                    "token_address": token_address,
                                    "amount": amount,
                                })

        return tokens_received

    def _check_token_sellable(
        self,
        token_address: str,
        amount: int,
        from_address: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a token can be sold by simulating a transfer.

        Returns:
            (True, reason) if honeypot detected
            (False, None) if token is sellable
        """
        if self.logger:
            self.logger.debug(f"  Testing sell for {token_address[:10]}... (amount: {amount})")

        # Construct transfer() call
        # transfer(address to, uint256 amount) = 0xa9059cbb
        test_recipient = "0x0000000000000000000000000000000000000001"
        transfer_selector = "0xa9059cbb"
        recipient_padded = test_recipient[2:].zfill(64)
        amount_hex = hex(amount)[2:].zfill(64)
        calldata = transfer_selector + recipient_padded + amount_hex

        sell_tx = {
            "from": from_address,
            "to": token_address,
            "data": calldata,
            "value": "0x0",
            "gas": "0x100000",
        }

        # Simulate sell
        network_id = str(self.chain_id) if self.chain_id else "1"
        sell_result = self.tenderly_simulator.simulate(
            sell_tx,
            from_address,
            network_id=network_id,
        )

        # Check 1: Sell reverted
        if not sell_result or not sell_result.success:
            if self.logger:
                self.logger.warning(f"  Sell simulation FAILED for {token_address[:10]}...")
            return True, f"HONEYPOT DETECTED: Token {token_address[:10]}... cannot be sold"

        # Check 2: No Transfer events
        transfer_events_found = False
        if hasattr(sell_result, "logs"):
            transfer_events = [
                log for log in sell_result.logs
                if hasattr(log, "name") and log.name in ["Transfer", "TransferSingle", "TransferBatch"]
            ]
            transfer_events_found = len(transfer_events) > 0

        if not transfer_events_found:
            if self.logger:
                self.logger.warning(f"  No Transfer events for {token_address[:10]}...")
            return True, f"HONEYPOT DETECTED: Token {token_address[:10]}... transfer emits no events"

        # Check 3: User balance unchanged
        user_balance_decreased = False
        user_addr = from_address.lower()
        if hasattr(sell_result, "asset_changes"):
            for change in sell_result.asset_changes:
                addr = change.address.lower()
                try:
                    delta = int(change.delta) if change.delta else 0
                except (ValueError, TypeError):
                    delta = 0

                if addr == user_addr and delta < 0:
                    user_balance_decreased = True
                    break

        if not user_balance_decreased:
            if self.logger:
                self.logger.warning(f"  Balance unchanged for {token_address[:10]}...")
            return True, f"HONEYPOT DETECTED: Token {token_address[:10]}... balance doesn't decrease"

        return False, None
