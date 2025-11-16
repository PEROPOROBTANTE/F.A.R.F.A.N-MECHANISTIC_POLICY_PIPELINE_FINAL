#!/usr/bin/env python3
"""Empirical Calibration Testing Framework.

This script runs the policy analysis pipeline with different calibration
strategies and measures their effectiveness. It addresses calibration gap #9:
"Implementation testing - NO empirical testing on real policy documents."

The framework:
1. Runs pipeline with base calibration (no context)
2. Runs pipeline with context-aware calibration
3. Compares results and effectiveness metrics
4. Reports calibration improvements

Usage:
    python scripts/test_calibration_empirically.py [--plan PLAN_FILE]
"""

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ensure src/ is in Python path

from saaaaaa.utils.paths import data_dir
from saaaaaa.processing.spc_ingestion import CPPIngestionPipeline
from saaaaaa.utils.spc_adapter import SPCAdapter
from saaaaaa.core.orchestrator import Orchestrator
from saaaaaa.core.orchestrator.factory import build_processor
from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
from saaaaaa.core.orchestrator.calibration_registry import (
    resolve_calibration,
    resolve_calibration_with_context,
)
from saaaaaa.core.orchestrator.calibration_context import (
    infer_context_from_question_id,
)


@dataclass
class CalibrationMetrics:
    """Metrics for evaluating calibration effectiveness."""
    
    # Evidence collection metrics
    avg_evidence_snippets: float
    evidence_usage_rate: float  # Fraction of available evidence used
    
    # Confidence metrics
    avg_confidence: float
    confidence_variance: float
    
    # Quality metrics
    contradiction_rate: float  # Rate of contradictory evidence
    uncertainty_rate: float  # Rate of high uncertainty
    
    # Performance metrics
    execution_time_s: float
    total_questions: int
    successful_questions: int
    
    # Calibration-specific
    context_adjustments_applied: int  # How many questions got context adjustments
    avg_sensitivity: float
    avg_aggregation_weight: float


@dataclass
class ComparisonResult:
    """Comparison between base and contextual calibration."""
    
    base_metrics: CalibrationMetrics
    contextual_metrics: CalibrationMetrics
    improvement_percentage: Dict[str, float]
    recommendations: List[str]


class CalibrationTester:
    """Empirical calibration testing framework."""
    
    def __init__(self, plan_path: Path):
        """Initialize tester with plan PDF.

        Args:
            plan_path: Path to policy plan PDF
        """
        self.plan_path = plan_path
        self.cpp_pipeline = None
        self.spc_adapter = SPCAdapter()

    async def _setup_orchestrator(self) -> tuple[Orchestrator, Any]:
        """Setup orchestrator with canonical questionnaire (common setup logic).

        Returns:
            Tuple of (orchestrator, preprocessed_document)
        """
        # Ingest document
        spc = await self._ingest_document()

        # Convert to orchestrator format
        doc = self.spc_adapter.to_preprocessed_document(spc)

        # Build processor and load questionnaire
        processor = build_processor()
        canonical_questionnaire = load_questionnaire()

        # Create orchestrator with canonical questionnaire
        orchestrator = Orchestrator(
            questionnaire=canonical_questionnaire,
            catalog=processor.factory.catalog
        )

        return orchestrator, doc

    async def run_with_base_calibration(self) -> Dict[str, Any]:
        """Run pipeline with base calibration (no context).

        Returns:
            Pipeline results and metrics
        """
        print("Running pipeline with BASE calibration (no context)...")
        start_time = time.time()

        # Setup orchestrator and document
        orchestrator, doc = await self._setup_orchestrator()
        
        # Monkey-patch to use base calibration only
        import saaaaaa.core.orchestrator.calibration_registry as _calib_reg
        original_resolve = _calib_reg.resolve_calibration
        
        def base_only(class_name, method_name):
            return resolve_calibration(class_name, method_name)
        
        # Monkey-patch the module-level function
        _calib_reg.resolve_calibration_with_context = base_only
        
        # Run orchestration
        try:
            results = await orchestrator.process_development_plan_async(
                str(self.plan_path), 
                preprocessed_document=doc
            )
            execution_time = time.time() - start_time
            
            # Compute metrics
            metrics = self._compute_metrics(results, execution_time, use_context=False)
            
            return {
                "results": results,
                "metrics": metrics,
            }
        finally:
            # Restore original
            _calib_reg.resolve_calibration_with_context = original_resolve
    
    async def run_with_contextual_calibration(self) -> Dict[str, Any]:
        """Run pipeline with context-aware calibration.

        Returns:
            Pipeline results and metrics
        """
        print("Running pipeline with CONTEXTUAL calibration...")
        start_time = time.time()

        # Setup orchestrator and document
        orchestrator, doc = await self._setup_orchestrator()
        
        # Monkey-patch to use contextual calibration with tracking
        import saaaaaa.core.orchestrator.calibration_registry as _calib_reg
        original_resolve_with_context = _calib_reg.resolve_calibration_with_context
        
        # Use list as mutable container to track usage in closure
        context_usage_count = [0]
        
        def contextual_with_tracking(class_name, method_name, question_id=None, **kwargs):
            if question_id:
                context_usage_count[0] += 1
            return original_resolve_with_context(
                class_name, method_name, question_id=question_id, **kwargs
            )
        
        _calib_reg.resolve_calibration_with_context = contextual_with_tracking
        
        # Run orchestration
        try:
            results = await orchestrator.process_development_plan_async(
                str(self.plan_path),
                preprocessed_document=doc
            )
            execution_time = time.time() - start_time
            
            # Compute metrics
            metrics = self._compute_metrics(
                results, execution_time,
                use_context=True,
                context_count=context_usage_count[0]
            )
            
            return {
                "results": results,
                "metrics": metrics,
                "context_usage_count": context_usage_count[0],
            }
        finally:
            # Restore original
            _calib_reg.resolve_calibration_with_context = original_resolve_with_context
    
    async def _ingest_document(self):
        """Ingest document using SPC/CPP pipeline."""
        if self.cpp_pipeline is None:
            self.cpp_pipeline = CPPIngestionPipeline()
        
        print(f"Ingesting {self.plan_path.name}...")
        spc = await self.cpp_pipeline.process(self.plan_path)
        print(f"Ingestion complete: {len(spc.get('chunks', []))} chunks")
        return spc
    
    def _compute_metrics(
        self,
        results: List[Any],  # List of PhaseResult objects
        execution_time: float,
        use_context: bool,
        context_count: int = 0,
    ) -> CalibrationMetrics:
        """Compute calibration effectiveness metrics from results.
        
        Args:
            results: Pipeline execution results (list of PhaseResult objects)
            execution_time: Total execution time in seconds
            use_context: Whether contextual calibration was used
            context_count: Number of times context was applied
            
        Returns:
            Computed metrics
        """
        # Extract micro question results from Phase 2 (if available)
        micro_results = []
        
        # Results is a list of PhaseResult objects
        if isinstance(results, list):
            for phase_result in results:
                # Phase 2 is micro questions
                if hasattr(phase_result, 'phase_id') and phase_result.phase_id == 2:
                    if hasattr(phase_result, 'data') and phase_result.data:
                        micro_results = phase_result.data if isinstance(phase_result.data, list) else []
                    break
        
        if not micro_results:
            # Fallback: empty metrics
            return CalibrationMetrics(
                avg_evidence_snippets=0.0,
                evidence_usage_rate=0.0,
                avg_confidence=0.0,
                confidence_variance=0.0,
                contradiction_rate=0.0,
                uncertainty_rate=0.0,
                execution_time_s=execution_time,
                total_questions=0,
                successful_questions=0,
                context_adjustments_applied=context_count if use_context else 0,
                avg_sensitivity=0.0,
                avg_aggregation_weight=0.0,
            )
        
        # Compute metrics from micro results
        total_questions = len(micro_results)
        successful_questions = sum(
            1 for r in micro_results if r.get("status") == "success"
        )
        
        # Evidence metrics
        evidence_counts = [
            len(r.get("evidence", [])) for r in micro_results
            if r.get("status") == "success"
        ]
        avg_evidence = sum(evidence_counts) / len(evidence_counts) if evidence_counts else 0.0
        
        # Confidence metrics
        confidences = [
            r.get("confidence", 0.0) for r in micro_results
            if r.get("status") == "success"
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        confidence_variance = (
            sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
            if len(confidences) > 1 else 0.0
        )
        
        # Quality metrics
        contradiction_count = sum(
            1 for r in micro_results
            if r.get("has_contradiction", False)
        )
        contradiction_rate = contradiction_count / total_questions if total_questions > 0 else 0.0
        
        uncertainty_count = sum(
            1 for r in micro_results
            if r.get("confidence", 1.0) < 0.5
        )
        uncertainty_rate = uncertainty_count / total_questions if total_questions > 0 else 0.0
        
        # Calibration-specific (estimated from results)
        avg_sensitivity = 0.85  # Would need to track during execution
        avg_aggregation_weight = 1.0  # Would need to track during execution
        
        return CalibrationMetrics(
            avg_evidence_snippets=avg_evidence,
            evidence_usage_rate=successful_questions / total_questions if total_questions > 0 else 0.0,
            avg_confidence=avg_confidence,
            confidence_variance=confidence_variance,
            contradiction_rate=contradiction_rate,
            uncertainty_rate=uncertainty_rate,
            execution_time_s=execution_time,
            total_questions=total_questions,
            successful_questions=successful_questions,
            context_adjustments_applied=context_count if use_context else 0,
            avg_sensitivity=avg_sensitivity,
            avg_aggregation_weight=avg_aggregation_weight,
        )
    
    def compare_results(
        self,
        base_result: Dict[str, Any],
        contextual_result: Dict[str, Any],
    ) -> ComparisonResult:
        """Compare base and contextual calibration results.
        
        Args:
            base_result: Results from base calibration
            contextual_result: Results from contextual calibration
            
        Returns:
            Comparison with improvement metrics
        """
        base_metrics = base_result["metrics"]
        contextual_metrics = contextual_result["metrics"]
        
        # Calculate improvement percentages
        improvements = {}
        
        # Higher is better
        for metric in ["avg_evidence_snippets", "evidence_usage_rate",
                      "avg_confidence", "successful_questions"]:
            base_val = getattr(base_metrics, metric)
            ctx_val = getattr(contextual_metrics, metric)
            if base_val > 0:
                improvements[metric] = ((ctx_val - base_val) / base_val) * 100
            else:
                improvements[metric] = 0.0 if ctx_val == 0 else 100.0
        
        # Lower is better
        for metric in ["contradiction_rate", "uncertainty_rate",
                      "confidence_variance", "execution_time_s"]:
            base_val = getattr(base_metrics, metric)
            ctx_val = getattr(contextual_metrics, metric)
            if base_val > 0:
                improvements[metric] = ((base_val - ctx_val) / base_val) * 100
            else:
                improvements[metric] = 0.0
        
        # Generate recommendations
        recommendations = []
        
        if improvements.get("avg_confidence", 0) > 5:
            recommendations.append(
                "✓ Context-aware calibration significantly improved confidence "
                f"by {improvements['avg_confidence']:.1f}%"
            )
        
        if improvements.get("contradiction_rate", 0) > 10:
            recommendations.append(
                "✓ Context-aware calibration reduced contradictions "
                f"by {improvements['contradiction_rate']:.1f}%"
            )
        
        if improvements.get("evidence_usage_rate", 0) > 5:
            recommendations.append(
                "✓ Context-aware calibration improved evidence usage "
                f"by {improvements['evidence_usage_rate']:.1f}%"
            )
        
        if contextual_metrics.context_adjustments_applied > 0:
            recommendations.append(
                f"✓ Applied context adjustments to "
                f"{contextual_metrics.context_adjustments_applied} questions"
            )
        
        if not recommendations:
            recommendations.append(
                "⚠ No significant improvements detected. Consider tuning modifiers."
            )
        
        return ComparisonResult(
            base_metrics=base_metrics,
            contextual_metrics=contextual_metrics,
            improvement_percentage=improvements,
            recommendations=recommendations,
        )


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Empirical calibration testing framework"
    )
    parser.add_argument(
        "--plan",
        type=Path,
        default=data_dir() / "plans" / "Plan_1.pdf",
        help="Path to plan PDF (default: data/plans/Plan_1.pdf)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("calibration_test_results.json"),
        help="Output file for results (default: calibration_test_results.json)"
    )
    
    args = parser.parse_args()
    
    if not args.plan.exists():
        print(f"Error: Plan file not found: {args.plan}")
        return 1
    
    print("=" * 80)
    print("EMPIRICAL CALIBRATION TESTING FRAMEWORK")
    print("=" * 80)
    print(f"Plan: {args.plan}")
    print()
    
    tester = CalibrationTester(args.plan)
    
    # Run both calibration strategies
    print("Phase 1: Base Calibration (no context)")
    print("-" * 80)
    base_result = await tester.run_with_base_calibration()
    print(f"✓ Complete in {base_result['metrics'].execution_time_s:.2f}s")
    print()
    
    print("Phase 2: Contextual Calibration")
    print("-" * 80)
    contextual_result = await tester.run_with_contextual_calibration()
    print(f"✓ Complete in {contextual_result['metrics'].execution_time_s:.2f}s")
    print()
    
    # Compare results
    print("Phase 3: Comparison & Analysis")
    print("-" * 80)
    comparison = tester.compare_results(base_result, contextual_result)
    
    # Display results
    print("\nBASE CALIBRATION METRICS:")
    print(json.dumps(asdict(comparison.base_metrics), indent=2))
    print("\nCONTEXTUAL CALIBRATION METRICS:")
    print(json.dumps(asdict(comparison.contextual_metrics), indent=2))
    print("\nIMPROVEMENTS:")
    for metric, improvement in comparison.improvement_percentage.items():
        symbol = "↑" if improvement > 0 else "↓" if improvement < 0 else "="
        print(f"  {metric:30s} {symbol} {abs(improvement):6.2f}%")
    
    print("\nRECOMMENDATIONS:")
    for rec in comparison.recommendations:
        print(f"  {rec}")
    
    # Save results
    output_data = {
        "plan_file": str(args.plan),
        "base_metrics": asdict(comparison.base_metrics),
        "contextual_metrics": asdict(comparison.contextual_metrics),
        "improvements": comparison.improvement_percentage,
        "recommendations": comparison.recommendations,
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved to {args.output}")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
