"""
Tenderly Simulation API integration

Provides advanced transaction simulation with:
- Full execution traces
- Asset/balance changes tracking
- State modifications
- Event log decoding
- Gas cost predictions
"""

import os
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from ..logger import PolicyLogger, LogLevel


@dataclass
class TenderlyTrace:
    """Decoded call trace entry from Tenderly"""
    type: str  # CALL, DELEGATECALL, STATICCALL, CREATE
    from_address: str
    to_address: str
    value: int
    gas_used: int
    input_data: str
    output_data: str
    error: Optional[str] = None
    calls: List['TenderlyTrace'] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM consumption"""
        return {
            "type": self.type,
            "from": self.from_address[:10] + "..." if len(self.from_address) > 10 else self.from_address,
            "to": self.to_address[:10] + "..." if len(self.to_address) > 10 else self.to_address,
            "value": self.value,
            "gas_used": self.gas_used,
            "error": self.error,
            "num_subcalls": len(self.calls)
        }


@dataclass
class TenderlyAssetChange:
    """Asset/balance change for an address"""
    address: str
    asset_type: str  # "native", "erc20", "erc721", "erc1155"
    asset_address: Optional[str] = None
    token_id: Optional[str] = None
    before_balance: Optional[str] = None
    after_balance: Optional[str] = None
    delta: Optional[str] = None
    dollar_value: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM consumption"""
        return {
            "address": self.address[:10] + "...",
            "type": self.asset_type,
            "delta": self.delta,
            "dollar_value": self.dollar_value,
            "profited": self.delta and (self.delta.startswith("+") if isinstance(self.delta, str) else self.delta > 0)
        }


@dataclass
class TenderlyLog:
    """Decoded event log"""
    address: str
    name: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None
    inputs: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM consumption"""
        return {
            "contract": self.address[:10] + "...",
            "event": self.name or "Unknown",
            "inputs": self._simplify_inputs() if self.inputs else []
        }

    def _simplify_inputs(self) -> List[Dict[str, Any]]:
        """Simplify inputs for LLM"""
        if not self.inputs:
            return []
        simplified = []
        for inp in self.inputs[:5]:  # Limit to first 5
            value = inp.get("value", "")
            if isinstance(value, str) and value.startswith("0x") and len(value) > 20:
                value = value[:10] + "..."
            simplified.append({
                "name": inp.get("soltype", {}).get("name", "unknown"),
                "value": value
            })
        return simplified


@dataclass
class TenderlySimulationResult:
    """Complete result from Tenderly simulation"""
    success: bool
    error: Optional[str] = None
    call_trace: List[TenderlyTrace] = field(default_factory=list)
    asset_changes: List[TenderlyAssetChange] = field(default_factory=list)
    logs: List[TenderlyLog] = field(default_factory=list)
    gas_used: Optional[int] = None
    raw_response: Optional[Dict[str, Any]] = None

    def has_data(self) -> bool:
        """Check if simulation has meaningful data"""
        return bool(
            self.call_trace or
            self.asset_changes or
            self.logs
        )

    def to_summary(self) -> Dict[str, Any]:
        """Create summary for LLM analysis"""
        return {
            "success": self.success,
            "gas_used": self.gas_used,
            "num_traces": len(self.call_trace),
            "num_asset_changes": len(self.asset_changes),
            "num_logs": len(self.logs),
            "call_trace": [trace.to_dict() for trace in self.call_trace[:10]],
            "asset_changes": [change.to_dict() for change in self.asset_changes],
            "logs": [log.to_dict() for log in self.logs[:20]]
        }


class TenderlySimulator:
    """
    Simulate transactions using Tenderly API

    Provides advanced transaction simulation with full context:
    - Call traces (internal calls)
    - Asset/balance changes (with dollar values)
    - State modifications
    - Event logs (decoded)
    - Gas predictions

    Example:
        simulator = TenderlySimulator(
            access_key=os.getenv("TENDERLY_ACCESS_KEY"),
            account_slug="my-account",
            project_slug="my-project"
        )
        result = simulator.simulate(transaction, from_address, network_id="1")

        if result.success:
            print(f"Asset changes: {result.asset_changes}")
            print(f"Gas used: {result.gas_used}")
    """

    def __init__(
        self,
        access_key: Optional[str] = None,
        account_slug: Optional[str] = None,
        project_slug: Optional[str] = None,
        endpoint: str = "https://api.tenderly.co/api/v1",
        timeout: int = 30,
        logger: Optional[PolicyLogger] = None
    ):
        """
        Initialize Tenderly simulator

        Args:
            access_key: Tenderly access key (or set TENDERLY_ACCESS_KEY env var)
            account_slug: Tenderly account slug (or set TENDERLY_ACCOUNT_SLUG env var)
            project_slug: Tenderly project slug (or set TENDERLY_PROJECT_SLUG env var)
            endpoint: Tenderly API endpoint
            timeout: Request timeout in seconds
            logger: Optional PolicyLogger instance (creates default if not provided)
        """
        self.access_key = access_key or os.getenv("TENDERLY_ACCESS_KEY")
        self.account_slug = account_slug or os.getenv("TENDERLY_ACCOUNT_SLUG")
        self.project_slug = project_slug or os.getenv("TENDERLY_PROJECT_SLUG")
        self.endpoint = endpoint
        self.timeout = timeout
        self.logger = logger or PolicyLogger()
        self._warned = False

    def is_available(self) -> bool:
        """Check if Tenderly API is available (has required config)"""
        return bool(self.access_key and self.account_slug and self.project_slug)

    def simulate(
        self,
        tx: Dict[str, Any],
        from_address: str,
        network_id: str = "1",
        block_number: str = "latest",
        simulation_type: str = "full"
    ) -> TenderlySimulationResult:
        """
        Simulate transaction using Tenderly API

        Args:
            tx: Transaction dict (to, value, data, gas, etc.)
            from_address: Sender address
            network_id: Network ID (1=mainnet, 8453=base, 84532=base-sepolia, etc.)
            block_number: Block number or "latest"
            simulation_type: "full", "quick", or "abi"

        Returns:
            TenderlySimulationResult with full context
        """
        if not self.access_key or not self.account_slug or not self.project_slug:
            if not self._warned:
                missing = []
                if not self.access_key:
                    missing.append("TENDERLY_ACCESS_KEY")
                if not self.account_slug:
                    missing.append("TENDERLY_ACCOUNT_SLUG")
                if not self.project_slug:
                    missing.append("TENDERLY_PROJECT_SLUG")

                self.logger.warning(f"Warning: {', '.join(missing)} not set. Tenderly simulation disabled.")
                self.logger.warning("   Set these in .env for detailed trace analysis and asset change tracking.")
                self._warned = True

            return TenderlySimulationResult(
                success=False,
                error=f"Tenderly not configured: {', '.join(missing)}"
            )

        try:
            # Prepare request - minimal required fields
            request_data = {
                "network_id": str(network_id),
                "from": from_address,
                "to": tx.get("to"),
                "input": tx.get("data", "0x"),
                "gas": int(tx.get("gas", 8000000)) if tx.get("gas") else 8000000,
                "gas_price": "0",
                "value": str(tx.get("value", 0)),
                "save": True,  # Save simulation to get full details
                "save_if_fails": True,  # Save even if simulation fails
                "simulation_type": "full"  # Request full simulation with logs
            }

            # Only add block_number if it's not "latest" (use None for latest)
            if block_number and block_number != "latest":
                request_data["block_number"] = int(block_number) if isinstance(block_number, str) else block_number

            # Add gas_price if specified
            if "gas_price" in tx and tx["gas_price"]:
                request_data["gas_price"] = str(tx["gas_price"])
            elif "maxFeePerGas" in tx and tx["maxFeePerGas"]:
                request_data["gas_price"] = str(tx["maxFeePerGas"])

            # Make request
            url = f"{self.endpoint}/account/{self.account_slug}/project/{self.project_slug}/simulate"

            response = requests.post(
                url,
                json=request_data,
                headers={
                    "X-Access-Key": self.access_key,
                    "Content-Type": "application/json"
                },
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            # Parse response
            return self._parse_response(result)

        except requests.exceptions.Timeout:
            return TenderlySimulationResult(
                success=False,
                error="Tenderly API timeout"
            )
        except requests.exceptions.HTTPError as e:
            error_text = e.response.text if hasattr(e.response, 'text') else str(e)
            return TenderlySimulationResult(
                success=False,
                error=f"Tenderly API error: {e.response.status_code} - {error_text[:200]}"
            )
        except Exception as e:
            return TenderlySimulationResult(
                success=False,
                error=f"Tenderly simulation failed: {str(e)}"
            )

    def _parse_response(self, response: Dict[str, Any]) -> TenderlySimulationResult:
        """Parse Tenderly API response"""
        try:
            # Get transaction info
            transaction = response.get("transaction", {}) if response else {}

            tx_info = transaction.get("transaction_info", {}) if transaction else {}

            # Check if simulation succeeded
            success = transaction.get("status", False)
            error_message = transaction.get("error_message")

            # Parse call trace - it's directly in transaction, not in transaction_info!
            call_trace_data = transaction.get("call_trace", [])

            # Fallback: check transaction_info if not found
            if not call_trace_data and tx_info:
                call_trace_data = tx_info.get("call_trace", [])

            # Handle both list and dict formats
            if isinstance(call_trace_data, list):
                # It's a list of traces - parse each one
                call_trace = [self._parse_single_trace(t) for t in call_trace_data]

                # Get state_diff from the first trace if available
                state_diff = call_trace_data[0].get("state_diff", []) if call_trace_data else []
            elif isinstance(call_trace_data, dict):
                # It's a single trace object
                call_trace = [self._parse_single_trace(call_trace_data)] if call_trace_data else []
                state_diff = call_trace_data.get("state_diff", [])
            else:
                call_trace = []
                state_diff = []

            # Parse asset/balance changes from state_diff
            asset_changes = self._parse_state_diff(state_diff if state_diff is not None else [])

            # Parse logs - check multiple possible locations
            logs = []

            # Try getting logs from call_trace first
            if isinstance(call_trace_data, list) and call_trace_data:
                # It's a list - check first trace for logs
                if "logs" in call_trace_data[0]:
                    logs = self._parse_logs(call_trace_data[0].get("logs") or [])
            elif isinstance(call_trace_data, dict) and call_trace_data:
                # It's a dict - check directly
                if "logs" in call_trace_data:
                    logs = self._parse_logs(call_trace_data.get("logs") or [])

            # If no logs found, check transaction level
            if not logs and "logs" in transaction:
                logs = self._parse_logs(transaction.get("logs") or [])

            # If still no logs, check tx_info level
            if not logs and "logs" in tx_info:
                logs = self._parse_logs(tx_info.get("logs") or [])

            # Parse gas used
            gas_used = transaction.get("gas_used")
            if isinstance(gas_used, str):
                gas_used = int(gas_used)
            elif isinstance(gas_used, int):
                pass
            else:
                gas_used = None

            return TenderlySimulationResult(
                success=success,
                error=error_message,
                call_trace=call_trace,
                asset_changes=asset_changes,
                logs=logs,
                gas_used=gas_used,
                raw_response=response
            )

        except Exception as e:
            return TenderlySimulationResult(
                success=False,
                error=f"Failed to parse Tenderly response: {str(e)}",
                raw_response=response
            )

    def _parse_single_trace(self, trace: Dict[str, Any]) -> TenderlyTrace:
        """Parse a single trace entry"""
        try:
            # Handle calls field - can be None or a list
            calls_data = trace.get("calls")
            subcalls = []
            if calls_data is not None:
                subcalls = [self._parse_single_trace(c) for c in calls_data]

            # Parse value - can be hex string or int
            value_raw = trace.get("value", 0)
            if isinstance(value_raw, str) and value_raw.startswith("0x"):
                value = int(value_raw, 16)
            elif isinstance(value_raw, str):
                value = int(value_raw) if value_raw else 0
            else:
                value = int(value_raw) if value_raw else 0

            # Parse gas_used - can be hex string or int
            gas_used_raw = trace.get("gas_used", 0)
            if isinstance(gas_used_raw, str) and gas_used_raw.startswith("0x"):
                gas_used = int(gas_used_raw, 16)
            elif isinstance(gas_used_raw, str):
                gas_used = int(gas_used_raw) if gas_used_raw else 0
            else:
                gas_used = int(gas_used_raw) if gas_used_raw else 0

            return TenderlyTrace(
                type=trace.get("call_type", "CALL"),
                from_address=trace.get("from", ""),
                to_address=trace.get("to", ""),
                value=value,
                gas_used=gas_used,
                input_data=trace.get("input", ""),
                output_data=trace.get("output", ""),
                error=trace.get("error"),
                calls=subcalls
            )
        except Exception:
            return TenderlyTrace(
                type="CALL",
                from_address="",
                to_address="",
                value=0,
                gas_used=0,
                input_data="",
                output_data="",
                calls=[]
            )

    def _parse_call_trace(self, trace_data: List[Dict]) -> List[TenderlyTrace]:
        """Parse call trace from Tenderly response (legacy)"""
        return [self._parse_single_trace(t) for t in trace_data]

    def _parse_state_diff(self, state_diff: List[Dict]) -> List[TenderlyAssetChange]:
        """Parse state diff to extract balance changes"""
        changes = []

        # Handle None or non-list input
        if state_diff is None or not isinstance(state_diff, list):
            return changes

        for diff in state_diff:
            try:
                address = diff.get("address", "")
                original = diff.get("original", {})
                dirty = diff.get("dirty", {})

                # Helper to flatten nested mappings
                def flatten_mapping(mapping, path=[]):
                    """Recursively flatten nested mappings"""
                    items = []
                    if isinstance(mapping, dict):
                        for key, value in mapping.items():
                            if isinstance(value, dict):
                                # Nested mapping - recurse
                                items.extend(flatten_mapping(value, path + [key]))
                            else:
                                # Leaf value
                                items.append((path + [key], value))
                    return items

                # Flatten both original and dirty
                original_flat = {tuple(k): v for k, v in flatten_mapping(original)}
                dirty_flat = {tuple(k): v for k, v in flatten_mapping(dirty)}

                # Extract changes
                all_keys = set(original_flat.keys()) | set(dirty_flat.keys())
                for key_path in all_keys:
                    before = original_flat.get(key_path, "0")
                    after = dirty_flat.get(key_path, "0")

                    # Convert to int for comparison
                    try:
                        before_int = int(before) if isinstance(before, (str, int)) else 0
                        after_int = int(after) if isinstance(after, (str, int)) else 0
                        delta = after_int - before_int

                        if delta != 0:  # Only add if there's a change
                            # Use the first address in the key path as the account
                            account_addr = key_path[0] if len(key_path) > 0 else address
                            changes.append(TenderlyAssetChange(
                                address=account_addr,
                                asset_type="erc20",
                                asset_address=address,
                                before_balance=str(before_int),
                                after_balance=str(after_int),
                                delta=str(delta)
                            ))
                    except (ValueError, TypeError):
                        continue
            except Exception:
                continue

        return changes

    def _parse_asset_changes(self, changes_data: List[Dict]) -> List[TenderlyAssetChange]:
        """Parse asset changes from Tenderly response (legacy format)"""
        changes = []

        for change in changes_data:
            try:
                changes.append(TenderlyAssetChange(
                    address=change.get("address", ""),
                    asset_type=change.get("type", "native"),
                    asset_address=change.get("token_info", {}).get("contract_address"),
                    token_id=change.get("token_id"),
                    before_balance=change.get("raw_before_balance"),
                    after_balance=change.get("raw_after_balance"),
                    delta=change.get("dollar_value"),
                    dollar_value=change.get("dollar_value")
                ))
            except Exception:
                continue

        return changes

    def _parse_logs(self, logs_data: List[Dict]) -> List[TenderlyLog]:
        """Parse event logs from Tenderly response"""
        logs = []

        # Handle None or non-list input
        if logs_data is None or not isinstance(logs_data, list):
            return logs

        for log in logs_data:
            try:
                # Extract address from raw if not directly available
                address = log.get("address", "")
                if not address and "raw" in log:
                    address = log["raw"].get("address", "")

                logs.append(TenderlyLog(
                    address=address,
                    name=log.get("name"),
                    raw=log.get("raw"),
                    inputs=log.get("inputs", [])
                ))
            except Exception:
                continue

        return logs
