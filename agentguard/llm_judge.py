"""
LLM-based transaction analysis for malicious activity detection

Uses LLMs to analyze transaction simulation results and detect:
- Hidden token approvals
- Unusual fund flow
- Reentrancy attacks
- Flash loan exploits
- Sandwich/MEV attacks
- Phishing attempts
- Hidden fees
- Token draining/balance wipeout
- Delegatecall to untrusted contracts
- Callback/hook attacks
- Multiple token approvals
- Fake token swaps
- Honeypot tokens
"""

import os
import json
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field

from .logger import PolicyLogger, LogLevel


@dataclass
class SecurityIndicators:
    """Deterministic security indicators extracted from simulation"""
    # Hidden Approvals
    has_approval: bool = False
    approval_amount_unlimited: bool = False
    approval_to_unknown: bool = False
    multiple_approvals: int = 0

    # Fund Flow
    unique_addresses_interacted: int = 0
    callbacks_to_sender: int = 0
    delegatecalls: int = 0
    unusual_call_pattern: bool = False

    # Balance Changes
    user_balance_decrease_pct: float = 0.0
    unexpected_recipients: List[str] = field(default_factory=list)
    hidden_fee_detected: bool = False

    # Token Behavior
    no_transfer_events: bool = False
    output_token_mismatch: bool = False
    honeypot_indicators: List[str] = field(default_factory=list)

    # Technical Patterns
    reentrancy_pattern: bool = False
    flash_loan_detected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM consumption"""
        return {
            "hidden_approvals": {
                "has_approval": self.has_approval,
                "unlimited_approval": self.approval_amount_unlimited,
                "to_unknown_address": self.approval_to_unknown,
                "multiple_approvals_count": self.multiple_approvals
            },
            "fund_flow": {
                "unique_addresses": self.unique_addresses_interacted,
                "callbacks_to_sender": self.callbacks_to_sender,
                "delegatecalls": self.delegatecalls,
                "unusual_pattern": self.unusual_call_pattern
            },
            "balance_changes": {
                "user_balance_decrease_percent": self.user_balance_decrease_pct,
                "unexpected_recipients": self.unexpected_recipients,
                "hidden_fees": self.hidden_fee_detected
            },
            "token_behavior": {
                "no_transfer_events": self.no_transfer_events,
                "output_token_mismatch": self.output_token_mismatch,
                "honeypot_indicators": self.honeypot_indicators
            },
            "technical": {
                "reentrancy_pattern": self.reentrancy_pattern,
                "flash_loan_detected": self.flash_loan_detected
            }
        }


@dataclass
class LLMAnalysis:
    """Result of LLM-based malicious activity analysis"""
    is_malicious: bool
    confidence: float  # 0.0 to 1.0
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    reason: str
    indicators: List[str]
    recommended_action: str  # ALLOW, WARN, BLOCK
    raw_response: Optional[str] = None

    def should_block(self, block_threshold: float = 0.70) -> bool:
        """Check if transaction should be blocked based on confidence"""
        return (
            self.recommended_action == "BLOCK" or
            (self.is_malicious and self.confidence >= block_threshold) or
            self.risk_level == "CRITICAL"
        )

    def should_warn(self, warn_threshold: float = 0.40) -> bool:
        """Check if transaction should warn user"""
        return (
            self.recommended_action == "WARN" or
            (self.is_malicious and self.confidence >= warn_threshold) or
            self.risk_level in ["HIGH", "MEDIUM"]
        )


class LLMJudge:
    """
    Use LLM to analyze transactions for malicious activity

    Supports multiple LLM providers:
    - OpenAI (GPT-4, GPT-4-mini)
    - Anthropic (Claude)
    - Local models via OpenAI-compatible API

    Example:
        judge = LLMJudge(
            provider="openai",
            model="gpt-4-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )

        analysis = judge.analyze(
            transaction=tx,
            parsed_tx=parsed,
            sentio_result=sentio
        )

        if analysis.should_block():
            print(f"BLOCKED: {analysis.reason}")
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4-mini",
        api_key: Optional[str] = None,
        block_threshold: float = 0.70,
        warn_threshold: float = 0.40,
        max_cost_per_analysis: float = 0.05,
        logger: Optional[PolicyLogger] = None
    ):
        """
        Initialize LLM validation

        Args:
            provider: LLM provider (openai, anthropic, local)
            model: Model name (gpt-4, gpt-4-mini, claude-opus-4, etc.)
            api_key: API key (or set OPENAI_API_KEY/ANTHROPIC_API_KEY env var)
            block_threshold: Confidence threshold to block (default: 0.70)
            warn_threshold: Confidence threshold to warn (default: 0.40)
            max_cost_per_analysis: Max cost per analysis in USD
            logger: Optional PolicyLogger instance (creates default if not provided)
        """
        self.provider = provider.lower()
        self.model = model
        self.block_threshold = block_threshold
        self.warn_threshold = warn_threshold
        self.max_cost_per_analysis = max_cost_per_analysis
        self.logger = logger or PolicyLogger()

        # Initialize client
        self._client = None
        self._warned = False

        if self.provider == "openai":
            self._api_key = api_key or os.getenv("OPENAI_API_KEY")
            if self._api_key:
                try:
                    from openai import OpenAI
                    self._client = OpenAI(api_key=self._api_key)
                except ImportError:
                    self.logger.warning("Warning: openai package not installed. Run: pip install openai")

        elif self.provider == "anthropic":
            self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if self._api_key:
                try:
                    from anthropic import Anthropic
                    self._client = Anthropic(api_key=self._api_key)
                except ImportError:
                    self.logger.warning("Warning: anthropic package not installed. Run: pip install anthropic")

        elif self.provider == "local":
            # OpenAI-compatible local API
            self._api_key = api_key or "local"
            base_url = os.getenv("LOCAL_LLM_API_URL", "http://localhost:8000/v1")
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key, base_url=base_url)
            except ImportError:
                self.logger.warning("Warning: openai package not installed. Run: pip install openai")

    def is_available(self) -> bool:
        """Check if LLM judge is available"""
        return self._client is not None

    def analyze(
        self,
        transaction: Dict[str, Any],
        parsed_tx: Any,
        simulation_result: Optional[Any] = None,
        policy_context: Optional[Dict[str, Any]] = None
    ) -> Optional[LLMAnalysis]:
        """
        Analyze transaction for malicious activity

        Args:
            transaction: Raw transaction dict
            parsed_tx: Parsed transaction from CalldataParser
            simulation_result: Optional simulation result (Tenderly or other)
            policy_context: Policy configuration context

        Returns:
            LLMAnalysis or None if LLM not available
        """
        if not self._client:
            if not self._warned:
                key_name = f"{self.provider.upper()}_API_KEY"
                self.logger.warning(f"Warning: {key_name} not set. LLM-based analysis disabled.")
                self.logger.warning(f"   Set {key_name} in .env for intelligent malicious activity detection.")
                self._warned = True
            return None

        try:
            # Step 1: Extract deterministic security indicators
            indicators = self._extract_security_indicators(
                transaction, parsed_tx, simulation_result, policy_context
            )

            # Step 2: Build prompt with indicators
            prompt = self._build_prompt(
                transaction, parsed_tx, simulation_result, policy_context, indicators
            )

            # Step 3: Query LLM
            if self.provider == "openai" or self.provider == "local":
                return self._analyze_with_openai(prompt)
            elif self.provider == "anthropic":
                return self._analyze_with_anthropic(prompt)

        except Exception as e:
            self.logger.warning(f"LLM analysis error: {str(e)}")
            return None

    def _analyze_with_openai(self, prompt: str) -> LLMAnalysis:
        """Analyze using OpenAI API"""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=1000
        )

        analysis_text = response.choices[0].message.content
        return self._parse_analysis(analysis_text)

    def _analyze_with_anthropic(self, prompt: str) -> LLMAnalysis:
        """Analyze using Anthropic API"""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0.1,
            system=self._get_system_prompt(),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        analysis_text = response.content[0].text
        return self._parse_analysis(analysis_text)

    def _parse_analysis(self, analysis_text: str) -> LLMAnalysis:
        """Parse LLM response into LLMAnalysis"""
        try:
            # Extract JSON from response
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                analysis_text = analysis_text[json_start:json_end].strip()

            analysis_json = json.loads(analysis_text)

            return LLMAnalysis(
                is_malicious=analysis_json.get("is_malicious", False),
                confidence=float(analysis_json.get("confidence", 0.0)),
                risk_level=analysis_json.get("risk_level", "LOW"),
                reason=analysis_json.get("reason", ""),
                indicators=analysis_json.get("indicators", []),
                recommended_action=analysis_json.get("recommended_action", "ALLOW"),
                raw_response=analysis_text
            )

        except json.JSONDecodeError:
            # Fallback: treat as error
            return LLMAnalysis(
                is_malicious=False,
                confidence=0.0,
                risk_level="LOW",
                reason="Failed to parse LLM response",
                indicators=[],
                recommended_action="ALLOW",
                raw_response=analysis_text
            )

    def _extract_security_indicators(
        self,
        transaction: Dict[str, Any],
        parsed_tx: Any,
        simulation_result: Optional[Any],
        policy_context: Optional[Dict[str, Any]]
    ) -> SecurityIndicators:
        """
        Extract deterministic security indicators from simulation

        Returns structured data that makes LLM analysis more reliable
        """
        indicators = SecurityIndicators()

        if not simulation_result or not simulation_result.has_data():
            return indicators

        user_address = transaction.get('from', '').lower()
        whitelisted = set(policy_context.get('whitelisted_addresses', []) if policy_context else [])

        # === HIDDEN APPROVALS DETECTION ===
        if parsed_tx.function_name == 'approve':
            indicators.has_approval = True

            # Check for unlimited approval (max uint256)
            max_uint256 = 2**256 - 1
            if parsed_tx.token_amount and parsed_tx.token_amount >= max_uint256 * 0.9:  # 90% of max
                indicators.approval_amount_unlimited = True

            # Check if spender is unknown (not whitelisted)
            spender = parsed_tx.recipient_address
            if spender and spender.lower() not in whitelisted:
                indicators.approval_to_unknown = True

        # Count multiple approvals in logs
        # Method 1: Decoded event names from logs
        approval_count = 0
        if hasattr(simulation_result, 'logs'):
            approval_count = sum(1 for log in simulation_result.logs
                               if hasattr(log, 'name') and log.name == 'Approval')

            # Method 2: Heuristic detection - count repeated CALLs to same token contract
            # When a phishing contract calls token.approve() multiple times,
            # we'll see multiple CALL operations to the same token address
            if approval_count == 0:  # Only use heuristic if we didn't decode events
                token_call_counts = {}

                def count_token_calls(trace, depth=0):
                    """Count how many times each contract is called"""
                    # Only count CALL operations (not DELEGATECALL, STATICCALL, etc.)
                    if hasattr(trace, 'type') and trace.type == 'CALL':
                        to_addr = trace.to_address.lower() if hasattr(trace, 'to_address') else ''
                        if to_addr:
                            token_call_counts[to_addr] = token_call_counts.get(to_addr, 0) + 1

                    # Recurse into subcalls
                    if hasattr(trace, 'calls'):
                        for subcall in trace.calls:
                            count_token_calls(subcall, depth + 1)

                if hasattr(simulation_result, 'call_trace'):
                    for trace in simulation_result.call_trace:
                        count_token_calls(trace)

                # If any contract was called 3+ times, it's likely multiple approvals
                # (phishing contracts typically do 3 approvals in claimAirdrop)
                max_calls_to_same_contract = max(token_call_counts.values()) if token_call_counts else 0
                if max_calls_to_same_contract >= 3:
                    approval_count = max_calls_to_same_contract

            indicators.multiple_approvals = approval_count

        # === FUND FLOW ANALYSIS ===
        if hasattr(simulation_result, 'call_trace'):
            all_addresses = set()
            callback_count = 0
            delegatecall_count = 0
            delegatecall_targets = set()
            delegatecall_with_callback = False

            def analyze_trace(trace, depth=0):
                nonlocal callback_count, delegatecall_count, delegatecall_with_callback
                if trace.from_address:
                    all_addresses.add(trace.from_address.lower())
                if trace.to_address:
                    all_addresses.add(trace.to_address.lower())

                # Detect callbacks to sender
                if trace.to_address and trace.to_address.lower() == user_address:
                    callback_count += 1
                    # Check if callback is after a delegatecall
                    if delegatecall_count > 0:
                        delegatecall_with_callback = True

                # Detect delegatecalls
                if trace.type == "DELEGATECALL":
                    delegatecall_count += 1
                    if trace.to_address:
                        delegatecall_targets.add(trace.to_address.lower())

                # Recurse into subcalls
                for subcall in trace.calls:
                    analyze_trace(subcall, depth + 1)

            for trace in simulation_result.call_trace:
                analyze_trace(trace)

            indicators.unique_addresses_interacted = len(all_addresses)
            indicators.callbacks_to_sender = callback_count
            indicators.delegatecalls = delegatecall_count

            # Unusual call pattern - more nuanced detection
            # Allow single delegatecall (proxy pattern)
            # Flag if: multiple delegatecalls to DIFFERENT targets (suspicious)
            # Flag if: delegatecall + callback (potential attack)
            # Flag if: too many unique addresses (>10)
            suspicious_delegatecall = (
                (delegatecall_count > 1 and len(delegatecall_targets) > 1) or
                delegatecall_with_callback
            )

            if len(all_addresses) > 10 or suspicious_delegatecall:
                indicators.unusual_call_pattern = True

        # === BALANCE CHANGES ANALYSIS ===
        if hasattr(simulation_result, 'asset_changes'):
            unexpected_recipients = []
            total_user_outflow = 0
            total_other_inflow = 0

            for change in simulation_result.asset_changes:
                addr = change.address.lower()
                try:
                    delta = int(change.delta) if change.delta else 0
                except (ValueError, TypeError):
                    delta = 0

                if addr == user_address and delta < 0:
                    # User lost tokens
                    total_user_outflow += abs(delta)
                elif addr != user_address and delta > 0:
                    # Someone else gained tokens
                    total_other_inflow += delta
                    if addr not in whitelisted and addr not in [parsed_tx.to.lower(), (parsed_tx.recipient_address or '').lower()]:
                        unexpected_recipients.append(addr[:10] + "...")

            indicators.unexpected_recipients = unexpected_recipients

            # Hidden fee: User loses more than expected
            if total_user_outflow > 0 and total_other_inflow > 0:
                fee_pct = (total_other_inflow - total_user_outflow) / total_user_outflow * 100
                if fee_pct > 5:  # More than 5% fee is suspicious
                    indicators.hidden_fee_detected = True

            # Calculate user balance decrease percentage
            if parsed_tx.token_amount and total_user_outflow > 0:
                indicators.user_balance_decrease_pct = (total_user_outflow / parsed_tx.token_amount) * 100

        # === TOKEN BEHAVIOR ANALYSIS ===
        if hasattr(simulation_result, 'logs'):
            transfer_events = [log for log in simulation_result.logs
                             if hasattr(log, 'name') and log.name in ['Transfer', 'TransferSingle', 'TransferBatch']]

            # Honeypot detection: No transfer events for a token transfer
            if parsed_tx.function_name in ['transfer', 'transferFrom'] and len(transfer_events) == 0:
                indicators.no_transfer_events = True
                indicators.honeypot_indicators.append("No Transfer events emitted")

            # Check for output token mismatch in swaps
            if parsed_tx.function_name and 'swap' in parsed_tx.function_name.lower():
                # In a swap, we expect at least 2 Transfer events (in and out)
                if len(transfer_events) < 2:
                    indicators.output_token_mismatch = True

        # === REENTRANCY DETECTION ===
        if hasattr(simulation_result, 'call_trace'):
            def detect_reentrancy(trace, visited_contracts=None, call_types=None):
                if visited_contracts is None:
                    visited_contracts = set()
                    call_types = {}

                contract = trace.to_address.lower() if trace.to_address else ''

                # Check if this is a reentrant call
                if contract in visited_contracts:
                    # Allow internal proxy calls (JUMPDEST, etc.)
                    # These are not true reentrancy, just internal EVM execution
                    internal_opcodes = ['JUMPDEST', 'JUMP', 'SLOAD', 'SSTORE', 'MLOAD', 'MSTORE']
                    if trace.type in internal_opcodes:
                        return False

                    # Allow if this is a DELEGATECALL within proxy pattern
                    # (same address called via delegatecall from itself)
                    if trace.type == 'DELEGATECALL' and len(visited_contracts) == 1:
                        return False

                    # Real reentrancy: external CALL back to same contract
                    if trace.type == 'CALL':
                        return True

                visited_contracts.add(contract)
                call_types[contract] = trace.type

                for subcall in trace.calls:
                    if detect_reentrancy(subcall, visited_contracts.copy(), call_types.copy()):
                        return True
                return False

            for trace in simulation_result.call_trace:
                if detect_reentrancy(trace):
                    indicators.reentrancy_pattern = True
                    break

        # === FLASH LOAN DETECTION ===
        if hasattr(simulation_result, 'logs'):
            # Common flash loan events
            flash_loan_events = ['FlashLoan', 'Flashloan', 'Borrow', 'LoanTaken']
            for log in simulation_result.logs:
                if hasattr(log, 'name') and any(fl in log.name for fl in flash_loan_events):
                    indicators.flash_loan_detected = True
                    break

        return indicators

    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""
        return """You are a blockchain security expert analyzing transactions for malicious activity.

Your task is to analyze transaction simulation results using DETERMINISTIC INDICATORS and simulation data.

ATTACK PATTERNS TO DETECT:

1. HIDDEN TOKEN APPROVALS ⚠️ CRITICAL
   - Unlimited approvals (amount == max uint256)
   - Approvals to unknown/non-whitelisted addresses
   - Multiple approvals in single transaction (3+)
   → BLOCK if: Unlimited approval to non-whitelisted address
   → BLOCK if: 3+ approvals in single transaction (phishing attack pattern)

2. TOKEN DRAINING / BALANCE WIPEOUT ⚠️ CRITICAL
   - User balance decrease > 90%
   - Unexpected recipients receiving funds
   - Balance changes don't match intended transfer
   → BLOCK if: User loses >90% of balance OR funds go to unexpected addresses

3. DELEGATECALL TO UNTRUSTED CONTRACT ⚠️ CRITICAL
   - DELEGATECALLs detected in call trace
   - Storage manipulation via delegatecall
   → LEGITIMATE: Single delegatecall (ERC-1967 proxy pattern - used by USDC, USDT, etc.)
   → LEGITIMATE: Multiple delegatecalls to same target (Multicall batching)
   → SUSPICIOUS: Multiple delegatecalls to DIFFERENT targets
   → CRITICAL: Delegatecall + callback to sender (potential attack)
   → BLOCK if: Delegatecall to multiple targets OR delegatecall + callback

4. CALLBACK TO SENDER (Hook Attack) ⚠️ HIGH
   - Contract calls back to user's address during execution
   - Potential reentrancy or state manipulation
   → SAFE: Callback without delegatecall (normal flow)
   → CRITICAL: Callback WITH delegatecall (attack vector)
   → WARN if: 1 callback alone, BLOCK if: 2+ callbacks OR callback + delegatecall

5. HIDDEN FEES ⚠️ HIGH
   - User loses more tokens than expected
   - Fee percentage > 5%
   - Undisclosed recipients
   → BLOCK if: Fee >10%, WARN if: Fee >5%

6. HONEYPOT DETECTION ⚠️ CRITICAL
   - Transfer function called but NO Transfer events emitted
   - Indicates token cannot be sold/transferred
   → BLOCK if: No Transfer events for transfer() call

7. FAKE TOKEN SWAP ⚠️ HIGH
   - Swap function but wrong output token
   - Less than 2 Transfer events in swap
   → BLOCK if: Output token doesn't match expected

8. UNUSUAL FUND FLOW ⚠️ MEDIUM
   - Interacting with >10 unique addresses
   - Complex routing through unknown intermediaries
   → WARN if: >10 addresses, BLOCK if: >20 addresses

9. REENTRANCY ATTACKS ⚠️ HIGH
   - Same contract called multiple times in call stack
   - Potential state manipulation
   → LEGITIMATE: Internal EVM opcodes (JUMPDEST, SLOAD, SSTORE) - proxy execution
   → LEGITIMATE: Single delegatecall to same address (proxy pattern)
   → CRITICAL: External CALL back to same contract (true reentrancy)
   → BLOCK if: Real reentrancy pattern detected (external CALL loop)

10. FLASH LOAN EXPLOITS ⚠️ HIGH
    - Flash loan events detected
    - Price manipulation possible
    → WARN always, BLOCK if combined with other indicators

ANALYSIS APPROACH:
1. Review SECURITY INDICATORS (pre-computed deterministic flags)
2. Review POLICY CONTEXT for whitelisted/denied addresses
3. Check SIMULATION RESULTS for additional evidence
4. Apply DETERMINISTIC RULES above
5. Calculate confidence and risk level

IMPORTANT RULES:
- The "From" address is the USER'S WALLET - NEVER flag it as suspicious
- Whitelisted addresses are TRUSTED - don't flag them
- Use the SECURITY INDICATORS section for deterministic detection
- Higher confidence when multiple indicators align
- Be aggressive with CRITICAL patterns (block immediately)
- Be conservative with MEDIUM patterns (warn only)

PROXY PATTERN RECOGNITION (CRITICAL - Don't False Positive!):
- ERC-1967 proxies (USDC, USDT, DAI) use single delegatecall to implementation - this is SAFE
- Internal opcodes (JUMPDEST, SLOAD, SSTORE) appearing multiple times is normal proxy execution - NOT reentrancy
- Multicall batching uses multiple delegatecalls to same target - this is SAFE
- Diamond Standard uses multiple delegatecalls to different facets - check if it's a known pattern
- ONLY flag delegatecall as malicious if:
  * Delegatecall + callback to user (attack vector)
  * Delegatecall to multiple DIFFERENT unknown targets (suspicious)
  * No expected events emitted despite delegatecall (honeypot)

REENTRANCY DETECTION (CRITICAL - Don't False Positive!):
- Internal EVM execution (JUMPDEST, SLOAD, SSTORE to same address) is NOT reentrancy
- Proxy pattern (delegatecall within same contract) is NOT reentrancy
- TRUE reentrancy: External CALL that returns to the SAME contract address
- Only flag if there's evidence of state manipulation or unexpected behavior

RESPONSE FORMAT (JSON):
{
  "is_malicious": boolean,
  "confidence": float between 0 and 1,
  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "reason": "Explanation citing specific indicators",
  "indicators": ["Hidden Approvals", "Delegatecall Detected", etc.],
  "recommended_action": "ALLOW" | "WARN" | "BLOCK"
}

CONFIDENCE GUIDELINES:
- 0.9-1.0: CRITICAL indicators (unlimited approval to unknown, delegatecall, honeypot, >90% balance loss)
- 0.7-0.9: HIGH indicators (multiple callbacks, hidden fees >10%, reentrancy)
- 0.4-0.7: MEDIUM indicators (unusual fund flow, flash loans, fees 5-10%)
- 0.0-0.4: LOW indicators (minor concerns, single callback)
"""

    def _build_prompt(
        self,
        transaction: Dict[str, Any],
        parsed_tx: Any,
        simulation_result: Optional[Any],
        policy_context: Optional[Dict[str, Any]] = None,
        security_indicators: Optional[SecurityIndicators] = None
    ) -> str:
        """Build analysis prompt from transaction data"""
        prompt_parts = []

        # Header
        prompt_parts.append("TRANSACTION SECURITY ANALYSIS REQUEST\n")
        prompt_parts.append("="*60)

        # Security Indicators (deterministic flags)
        if security_indicators:
            prompt_parts.append("\nSECURITY INDICATORS (Deterministic Analysis):")
            prompt_parts.append(json.dumps(security_indicators.to_dict(), indent=2))
            prompt_parts.append("")

        # Policy context (if available)
        if policy_context:
            prompt_parts.append("\nPOLICY CONTEXT:")

            # Whitelisted addresses
            if policy_context.get("whitelisted_addresses"):
                prompt_parts.append(f"Whitelisted Addresses (approved/trusted): {', '.join(policy_context['whitelisted_addresses'])}")

            # Denied addresses
            if policy_context.get("denied_addresses"):
                prompt_parts.append(f"Denied Addresses (blocked): {', '.join(policy_context['denied_addresses'])}")

            # Other policy info
            if policy_context.get("max_eth_value"):
                prompt_parts.append(f"Max ETH Value: {policy_context['max_eth_value']} wei")

            prompt_parts.append("")

        # Transaction basics
        prompt_parts.append("\nTRANSACTION DETAILS:")
        prompt_parts.append(f"From (User's Wallet - TRUSTED): {transaction.get('from', 'unknown')}")
        prompt_parts.append(f"To: {parsed_tx.to}")
        prompt_parts.append(f"Value: {parsed_tx.value} wei ({parsed_tx.value / 1e18:.4f} ETH)")
        prompt_parts.append(f"Function: {parsed_tx.function_name or 'ETH transfer'}")

        if parsed_tx.function_selector:
            prompt_parts.append(f"Function Selector: {parsed_tx.function_selector}")

        if parsed_tx.recipient_address:
            prompt_parts.append(f"Recipient (from calldata): {parsed_tx.recipient_address}")

        if parsed_tx.token_amount:
            prompt_parts.append(f"Token Amount: {parsed_tx.token_amount}")

        # Decoded parameters
        if parsed_tx.decoded_params:
            prompt_parts.append("\nDECODED PARAMETERS:")
            for key, value in parsed_tx.decoded_params.items():
                prompt_parts.append(f"  {key}: {value}")

        # Simulation results (if available)
        if simulation_result and simulation_result.has_data():
            prompt_parts.append("\n" + "="*60)
            prompt_parts.append("SIMULATION RESULTS:")
            prompt_parts.append("="*60)

            # Call trace summary
            if hasattr(simulation_result, 'call_trace') and simulation_result.call_trace:
                prompt_parts.append("\nCALL TRACE:")
                prompt_parts.append(f"Total calls: {len(simulation_result.call_trace)}")
                for i, trace in enumerate(simulation_result.call_trace[:5], 1):
                    prompt_parts.append(
                        f"{i}. {trace.type}: {trace.from_address[:10]}... → "
                        f"{trace.to_address[:10]}... "
                        f"(value: {trace.value}, gas: {trace.gas_used})"
                    )
                if len(simulation_result.call_trace) > 5:
                    prompt_parts.append(f"   ... and {len(simulation_result.call_trace) - 5} more calls")

            # Asset changes (from Tenderly) or Balance changes (legacy)
            if hasattr(simulation_result, 'asset_changes') and simulation_result.asset_changes:
                prompt_parts.append("\nASSET/BALANCE CHANGES:")
                for change in simulation_result.asset_changes:
                    change_dict = change.to_dict() if hasattr(change, 'to_dict') else change
                    profit_status = "PROFIT" if change_dict.get('profited') else "LOSS"
                    prompt_parts.append(
                        f"{change_dict.get('address', 'unknown')} {profit_status}: "
                        f"{change_dict.get('delta', 'unknown')} ({change_dict.get('type', 'unknown')})"
                    )
            elif hasattr(simulation_result, 'balance_changes') and simulation_result.balance_changes:
                prompt_parts.append("\nBALANCE CHANGES:")
                for change in simulation_result.balance_changes:
                    status = "PROFIT" if change.delta > 0 else "LOSS"
                    prompt_parts.append(
                        f"{change.address[:10]}... {status}: "
                        f"{change.human_readable_delta() if hasattr(change, 'human_readable_delta') else change.delta}"
                    )

            # Logs/Events
            log_data = None
            if hasattr(simulation_result, 'logs'):
                log_data = simulation_result.logs
            elif hasattr(simulation_result, 'events'):
                log_data = simulation_result.events

            if log_data:
                prompt_parts.append("\nEVENTS/LOGS:")
                for i, log in enumerate(log_data[:10], 1):
                    if hasattr(log, 'name'):
                        # Tenderly or Sentio style
                        log_dict = log.to_dict() if hasattr(log, 'to_dict') else {"event": log.name, "contract": getattr(log, 'address', 'unknown')[:10]}
                        prompt_parts.append(
                            f"{i}. {log_dict.get('event', 'Unknown')} "
                            f"at {log_dict.get('contract', 'unknown')}..."
                        )
                if len(log_data) > 10:
                    prompt_parts.append(f"   ... and {len(log_data) - 10} more logs")

        # Analysis instructions
        prompt_parts.append("\n" + "="*60)
        prompt_parts.append("ANALYSIS REQUIRED:")
        prompt_parts.append("="*60)
        prompt_parts.append("\nAnalyze the transaction for ALL malicious patterns defined in the system prompt.")
        prompt_parts.append("\nProvide analysis in JSON format as specified in system prompt.")

        return "\n".join(prompt_parts)
