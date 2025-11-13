"""
Meta Layer (@m) - Full Implementation.

Evaluates governance compliance using weighted formula:
x_@m = 0.5·m_transp + 0.4·m_gov + 0.1·m_cost
"""
import logging
from typing import Optional
from .config import MetaLayerConfig

logger = logging.getLogger(__name__)


class MetaLayerEvaluator:
    """
    Evaluates governance and meta-properties of methods.

    Attributes:
        config: MetaLayerConfig with weights and thresholds
    """

    def __init__(self, config: MetaLayerConfig):
        """
        Initialize evaluator with meta layer config.

        Args:
            config: MetaLayerConfig instance
        """
        self.config = config
        logger.info(
            "meta_evaluator_initialized",
            extra={
                "w_transparency": config.w_transparency,
                "w_governance": config.w_governance,
                "w_cost": config.w_cost
            }
        )

    def evaluate(
        self,
        method_id: str,
        method_version: str,
        config_hash: str,
        formula_exported: bool = False,
        full_trace: bool = False,
        logs_conform: bool = False,
        signature_valid: bool = False,
        execution_time_s: Optional[float] = None
    ) -> float:
        """
        Compute the weighted score x_@m = w_transparency·m_transp + w_governance·m_gov + w_cost·m_cost,
        where `w_transparency`, `w_governance`, and `w_cost` come from the provided `config`.

        Args:
            method_id: Method identifier
            method_version: Method version string
            config_hash: Configuration hash
            formula_exported: Has formula been documented?
            full_trace: Is full execution trace available?
            logs_conform: Do logs conform to standard?
            signature_valid: Is cryptographic signature valid?
            execution_time_s: Runtime in seconds

        Returns:
            x_@m ∈ [0.0, 1.0]
        """
        logger.info(
            "meta_evaluation_start",
            extra={
                "method": method_id,
                "version": method_version
            }
        )

        # Component 1: Transparency (m_transp)
        m_transp = self._compute_transparency(
            formula_exported, full_trace, logs_conform
        )
        logger.debug("m_transp_computed", extra={"score": m_transp})

        # Component 2: Governance (m_gov)
        m_gov = self._compute_governance(
            method_version, config_hash, signature_valid
        )
        logger.debug("m_gov_computed", extra={"score": m_gov})

        # Component 3: Cost (m_cost)
        m_cost = self._compute_cost(execution_time_s)
        logger.debug("m_cost_computed", extra={"score": m_cost})

        # Weighted sum
        x_m = (
            self.config.w_transparency * m_transp +
            self.config.w_governance * m_gov +
            self.config.w_cost * m_cost
        )

        logger.info(
            "meta_computed",
            extra={
                "x_m": x_m,
                "m_transp": m_transp,
                "m_gov": m_gov,
                "m_cost": m_cost,
                "method": method_id
            }
        )

        return x_m

    def _compute_transparency(
        self,
        formula: bool,
        trace: bool,
        logs: bool
    ) -> float:
        """
        Compute m_transp based on observability.

        Scoring:
            1.0: All 3 conditions met
            0.7: 2/3 conditions met
            0.4: 1/3 conditions met
            0.0: 0/3 conditions met

        Returns:
            m_transp ∈ {0.0, 0.4, 0.7, 1.0}
        """
        count = sum([formula, trace, logs])

        if count == 3:
            return 1.0
        elif count == 2:
            return 0.7
        elif count == 1:
            return 0.4
        else:
            return 0.0

    def _compute_governance(
        self,
        version: str,
        config_hash: str,
        signature: bool
    ) -> float:
        """
        Compute m_gov based on governance compliance.

        Scoring:
            1.0: All 3 conditions met
            0.66: 2/3 conditions met
            0.33: 1/3 conditions met
            0.0: 0/3 conditions met

        Returns:
            m_gov ∈ {0.0, 0.33, 0.66, 1.0}
        """
        # Check version
        has_version = bool(version and version != "unknown" and version != "1.0")

        # Check config hash
        has_hash = bool(config_hash and len(config_hash) > 0)

        # Count conditions
        count = sum([has_version, has_hash, signature])

        if count == 3:
            return 1.0
        elif count == 2:
            return 0.66
        elif count == 1:
            return 0.33
        else:
            return 0.0

    def _compute_cost(self, execution_time_s: Optional[float] = None) -> float:
        """
        Compute m_cost based on runtime.

        Scoring:
            1.0: < threshold_fast (e.g., <1s)
            0.8: < threshold_acceptable (e.g., <5s)
            0.5: >= threshold_acceptable
            0.0: timeout/OOM (not provided)

        Returns:
            m_cost ∈ {0.0, 0.5, 0.8, 1.0}
        """
        if execution_time_s is None:
            logger.warning("meta_timing_not_available")
            return 0.5  # Default: acceptable

        if execution_time_s < 0:
            logger.error("meta_negative_time", extra={"time": execution_time_s})
            return 0.0

        if execution_time_s < self.config.threshold_fast:
            return 1.0  # Fast
        elif execution_time_s < self.config.threshold_acceptable:
            return 0.8  # Acceptable
        else:
            logger.warning(
                "meta_slow_execution",
                extra={
                    "runtime": execution_time_s,
                    "threshold": self.config.threshold_acceptable
                }
            )
            return 0.5  # Slow but usable
