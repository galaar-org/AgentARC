"""
LLM Analysis Stage - AI-powered security analysis.

This stage uses an LLM to detect sophisticated attack patterns
that rule-based validators might miss:
- Hidden approvals
- Reentrancy attacks
- Token draining
- Phishing patterns
"""

from typing import Any, Dict, Optional, Tuple

from ..pipeline import PipelineStage
from ..context import ValidationContext
from ...core.config import PolicyConfig
from ...core.events import ValidationStage
from ...core.interfaces import LLMJudgeProtocol


class LLMAnalysisStage(PipelineStage):
    """
    AI-powered security analysis using LLM.

    This stage:
    1. Sends transaction data to LLM for analysis
    2. Checks confidence against block/warn thresholds
    3. Blocks or warns based on LLM analysis

    Attributes:
        llm_judge: LLMJudge instance for analysis
        config: PolicyConfig for threshold settings
        policy_context: Context about configured policies
    """

    def __init__(
        self,
        llm_judge: LLMJudgeProtocol,
        config: Optional[PolicyConfig] = None,
        policy_context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            name="LLM Security Analysis",
            stage_type=ValidationStage.LLM_VALIDATION,
        )
        self.llm_judge = llm_judge
        self.config = config
        self.policy_context = policy_context or {}

    def execute(self, context: ValidationContext) -> Tuple[bool, Optional[str]]:
        """
        Analyze transaction with LLM.

        Args:
            context: ValidationContext with transaction data

        Returns:
            (True, None) if LLM approves or is not configured
            (False, reason) if LLM detects malicious activity
        """
        if not context.from_address:
            return True, None

        self.emit_started("Analyzing transaction for malicious patterns")

        if self.logger:
            self.logger.debug("Analyzing transaction for malicious patterns...")

        # Run LLM analysis
        analysis = self.llm_judge.analyze(
            transaction=context.transaction,
            parsed_tx=context.parsed_tx,
            simulation_result=context.tenderly_result,
            policy_context=self.policy_context,
        )

        if not analysis:
            if self.logger:
                self.logger.success("LLM validation: No issues detected")
            self.emit_passed("No malicious activity detected")
            return True, None

        context.llm_analysis = analysis

        if self.logger:
            self.logger.debug(f"LLM confidence: {analysis.confidence:.2%}")
            self.logger.debug(f"Risk level: {analysis.risk_level}")

        # Get thresholds from config
        block_threshold = 0.70
        warn_threshold = 0.40

        if self.config:
            block_threshold = self.config.llm_validation.get("block_threshold", 0.70)
            warn_threshold = self.config.llm_validation.get("warn_threshold", 0.40)

        # Check if should block
        if analysis.should_block(block_threshold):
            if self.logger:
                self.logger.error(f"LLM detected malicious activity: {analysis.reason}")
                self.logger.minimal(f"BLOCKED by LLM: {analysis.reason}")
                self.logger.minimal(f"Confidence: {analysis.confidence:.0%} | Risk: {analysis.risk_level}")
                if analysis.indicators:
                    self.logger.minimal(f"Indicators: {', '.join(analysis.indicators)}")

            self.emit_failed(
                f"LLM detected malicious activity: {analysis.reason}",
                {
                    "confidence": analysis.confidence,
                    "risk_level": analysis.risk_level,
                    "indicators": analysis.indicators,
                    "reason": analysis.reason,
                },
            )
            return False, f"LLM security check failed: {analysis.reason}"

        # Check if should warn
        if analysis.should_warn(warn_threshold):
            if self.logger:
                self.logger.warning(f"LLM warning: {analysis.reason}")
                self.logger.warning(f"Confidence: {analysis.confidence:.0%} | Risk: {analysis.risk_level}")
                if analysis.indicators:
                    self.logger.warning(f"Indicators: {', '.join(analysis.indicators)}")

            self.emit_warning(
                f"LLM warning: {analysis.reason}",
                {
                    "confidence": analysis.confidence,
                    "risk_level": analysis.risk_level,
                    "indicators": analysis.indicators,
                },
            )
            # Continue execution but log warning
            return True, None

        # LLM approved
        if self.logger:
            self.logger.success("LLM validation: No malicious activity detected")

        self.emit_passed("No malicious activity detected")
        return True, None
