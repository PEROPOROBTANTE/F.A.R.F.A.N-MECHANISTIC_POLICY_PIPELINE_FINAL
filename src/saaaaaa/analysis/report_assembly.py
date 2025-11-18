"""
Report Assembly Module - Integrates with Questionnaire Monolith
================================================================

This module assembles comprehensive policy analysis reports by:
1. Loading questionnaire monolith via factory (I/O boundary)
2. Accessing patterns via QuestionnaireResourceProvider (single source of truth)
3. Integrating with evidence registry and QMCM hooks
4. Producing structured, traceable reports with monolith hash

Architectural Compliance:
- REQUIREMENT 1: Uses QuestionnaireResourceProvider for pattern extraction
- REQUIREMENT 2: All I/O via factory.py
- REQUIREMENT 3: Receives dependencies via dependency injection
- REQUIREMENT 6: No reimplemented logic - delegates to provider

Author: Integration Team
Version: 1.0.0
Python: 3.10+
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ReportMetadata:
    """Metadata for analysis report with monolith traceability"""

    report_id: str
    generated_at: str
    monolith_version: str
    monolith_hash: str  # SHA-256 of questionnaire_monolith.json
    plan_name: str
    total_questions: int
    questions_analyzed: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QuestionAnalysis:
    """Analysis result for a single micro question"""

    question_id: str
    question_global: int
    base_slot: str
    scoring_modality: str | None
    score: float | None
    evidence: list[str]
    patterns_applied: list[str]
    recommendation: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisReport:
    """Complete policy analysis report"""

    metadata: ReportMetadata
    micro_analyses: list[QuestionAnalysis]
    meso_clusters: dict[str, Any]
    macro_summary: dict[str, Any]
    evidence_chain_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary for JSON serialization"""
        return {
            'metadata': asdict(self.metadata),
            'micro_analyses': [asdict(q) for q in self.micro_analyses],
            'meso_clusters': self.meso_clusters,
            'macro_summary': self.macro_summary,
            'evidence_chain_hash': self.evidence_chain_hash
        }


class ReportAssembler:
    """
    Assembles comprehensive policy analysis reports.

    This class demonstrates proper architectural patterns:
    - Dependency injection for all external resources
    - No direct file I/O (delegates to factory)
    - Pattern extraction via QuestionnaireResourceProvider
    - Traceability via monolith hash
    """

    def __init__(
        self,
        questionnaire_provider,
        evidence_registry=None,
        qmcm_recorder=None,
        orchestrator=None
    ) -> None:
        """
        Initialize report assembler.

        Args:
            questionnaire_provider: QuestionnaireResourceProvider instance (required)
            evidence_registry: EvidenceRegistry for traceability (optional)
            qmcm_recorder: QMCMRecorder for quality monitoring (optional)
            orchestrator: Orchestrator instance for execution results (optional)

        ARCHITECTURAL NOTE: All dependencies injected, no direct I/O.
        """
        self.questionnaire_provider = questionnaire_provider
        self.evidence_registry = evidence_registry
        self.qmcm_recorder = qmcm_recorder
        self.orchestrator = orchestrator

        logger.info("ReportAssembler initialized with dependency injection")

    def assemble_report(
        self,
        plan_name: str,
        execution_results: dict[str, Any],
        report_id: str | None = None
    ) -> AnalysisReport:
        """
        Assemble complete analysis report.

        Args:
            plan_name: Name of the development plan
            execution_results: Results from orchestrator execution
            report_id: Optional report identifier

        Returns:
            Structured AnalysisReport with full traceability
        """
        # Generate report ID if not provided
        if report_id is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            report_id = f"report_{plan_name}_{timestamp}"

        # Get questionnaire data and compute hash
        questionnaire_data = self.questionnaire_provider.get_data()

        # Import factory for hash computation (not for I/O)
        from ..core.orchestrator.factory import compute_monolith_hash
        monolith_hash = compute_monolith_hash(questionnaire_data)

        # Extract metadata
        version = questionnaire_data.get('version', 'unknown')
        blocks = questionnaire_data.get('blocks', {})
        micro_questions = blocks.get('micro_questions', [])

        # Create report metadata
        metadata = ReportMetadata(
            report_id=report_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            monolith_version=version,
            monolith_hash=monolith_hash,
            plan_name=plan_name,
            total_questions=len(micro_questions),
            questions_analyzed=len(execution_results.get('questions', {}))
        )

        # Assemble micro analyses
        micro_analyses = self._assemble_micro_analyses(
            micro_questions,
            execution_results
        )

        # Assemble meso clusters
        meso_clusters = self._assemble_meso_clusters(execution_results)

        # Assemble macro summary
        macro_summary = self._assemble_macro_summary(execution_results)

        # Get evidence chain hash if available
        evidence_chain_hash = None
        if self.evidence_registry is not None:
            records = self.evidence_registry.records
            if records:
                evidence_chain_hash = records[-1].entry_hash

        report = AnalysisReport(
            metadata=metadata,
            micro_analyses=micro_analyses,
            meso_clusters=meso_clusters,
            macro_summary=macro_summary,
            evidence_chain_hash=evidence_chain_hash
        )

        logger.info(
            f"Report assembled: {report_id} "
            f"({len(micro_analyses)} questions, hash: {monolith_hash[:16]}...)"
        )

        return report

    def _assemble_micro_analyses(
        self,
        micro_questions: list[dict[str, Any]],
        execution_results: dict[str, Any]
    ) -> list[QuestionAnalysis]:
        """Assemble micro-level question analyses"""
        analyses = []
        question_results = execution_results.get('questions', {})

        for question in micro_questions:
            question_id = question.get('question_id', '')
            result = question_results.get(question_id, {})

            # Extract patterns applied using QuestionnaireResourceProvider
            patterns = self.questionnaire_provider.get_patterns_by_question(question_id)
            pattern_names = [p.get('pattern_id', '') for p in patterns] if patterns else []

            analysis = QuestionAnalysis(
                question_id=question_id,
                question_global=question.get('question_global', 0),
                base_slot=question.get('base_slot', ''),
                scoring_modality=question.get('scoring', {}).get('modality'),
                score=result.get('score'),
                evidence=result.get('evidence', []),
                patterns_applied=pattern_names,
                recommendation=result.get('recommendation'),
                metadata={
                    'dimension': question.get('dimension'),
                    'policy_area': question.get('policy_area')
                }
            )
            analyses.append(analysis)

        return analyses

    def _assemble_meso_clusters(
        self,
        execution_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Assemble meso-level cluster analyses"""
        return execution_results.get('meso_clusters', {})

    def _assemble_macro_summary(
        self,
        execution_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Assemble macro-level summary"""
        return execution_results.get('macro_summary', {})

    def export_report(
        self,
        report: AnalysisReport,
        output_path: Path,
        format: str = 'json'
    ) -> None:
        """
        Export report to file.

        Args:
            report: AnalysisReport to export
            output_path: Path to output file
            format: Output format ('json' or 'markdown')

        NOTE: This delegates I/O to factory for architectural compliance.
        """
        # Delegate to factory for I/O
        from .factory import save_json, write_text_file

        if format == 'json':
            save_json(report.to_dict(), str(output_path))
        elif format == 'markdown':
            markdown = self._format_as_markdown(report)
            write_text_file(markdown, str(output_path))
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Report exported to {output_path} in {format} format")

    def _format_as_markdown(self, report: AnalysisReport) -> str:
        """Format report as Markdown"""
        lines = [
            f"# Policy Analysis Report: {report.metadata.plan_name}\n",
            f"**Report ID:** {report.metadata.report_id}\n",
            f"**Generated:** {report.metadata.generated_at}\n",
            f"**Monolith Version:** {report.metadata.monolith_version}\n",
            f"**Monolith Hash:** {report.metadata.monolith_hash[:16]}...\n",
            f"**Questions Analyzed:** {report.metadata.questions_analyzed}/{report.metadata.total_questions}\n",
            "\n## Micro-Level Analyses\n"
        ]

        for analysis in report.micro_analyses[:10]:  # Show first 10
            lines.append(f"\n### {analysis.question_id}\n")
            lines.append(f"- **Slot:** {analysis.base_slot}\n")
            lines.append(f"- **Score:** {analysis.score}\n")
            lines.append(f"- **Patterns:** {', '.join(analysis.patterns_applied)}\n")

        if len(report.micro_analyses) > 10:
            lines.append(f"\n_...and {len(report.micro_analyses) - 10} more questions_\n")

        lines.append("\n## Meso-Level Clusters\n")
        lines.append(f"```json\n{report.meso_clusters}\n```\n")

        lines.append("\n## Macro Summary\n")
        lines.append(f"```json\n{report.macro_summary}\n```\n")

        if report.evidence_chain_hash:
            lines.append(f"\n**Evidence Chain Hash:** {report.evidence_chain_hash}\n")

        return "\n".join(lines)


def create_report_assembler(
    questionnaire_provider,
    evidence_registry=None,
    qmcm_recorder=None,
    orchestrator=None
) -> ReportAssembler:
    """
    Factory function to create ReportAssembler with dependencies.

    Args:
        questionnaire_provider: QuestionnaireResourceProvider instance
        evidence_registry: Optional EvidenceRegistry
        qmcm_recorder: Optional QMCMRecorder
        orchestrator: Optional Orchestrator

    Returns:
        Configured ReportAssembler
    """
    return ReportAssembler(
        questionnaire_provider=questionnaire_provider,
        evidence_registry=evidence_registry,
        qmcm_recorder=qmcm_recorder,
        orchestrator=orchestrator
    )


__all__ = [
    'ReportMetadata',
    'QuestionAnalysis',
    'AnalysisReport',
    'ReportAssembler',
    'create_report_assembler',
]
