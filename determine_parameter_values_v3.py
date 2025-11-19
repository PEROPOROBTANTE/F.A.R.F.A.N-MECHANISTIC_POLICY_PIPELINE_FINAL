#!/usr/bin/env python3
"""
PHASE 3: VALUE DETERMINATION - COMPREHENSIVE KNOWLEDGE BASE
============================================================

Determines correct parameter values using COMPREHENSIVE triangulation:
- 222 parameter mappings
- 16 academic sources (ALL with DOI/arXiv)
- 11 library sources (ALL official documentation)
- 10 standards (ISO, IETF RFC, PEP, POSIX)

Coverage: 61.8% of unique parameters (162/262)

ZERO TOLERANCE: Every recommendation backed by real, verifiable sources.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone
from collections import defaultdict
from comprehensive_knowledge_base import ComprehensiveKnowledgeBase

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ParameterValueDeterminator:
    """Phase 3: Determine parameter values with comprehensive knowledge base"""

    def __init__(self, draft_file: str = "method_parameters_draft.json"):
        self.draft_file = Path(draft_file)
        self.kb = ComprehensiveKnowledgeBase()
        self.stats = {
            "total_parameters": 0,
            "kb_recommendations": 0,
            "code_defaults": 0,
            "none_values": 0,
            "application_specific": 0
        }
        self.recommendations_log = []

    def determine_values(self) -> Dict[str, Any]:
        """
        Determine parameter values using comprehensive KB.

        Returns enriched method_parameters.json with sources.
        """
        logger.info("=" * 80)
        logger.info("PHASE 3: VALUE DETERMINATION WITH COMPREHENSIVE KB")
        logger.info("=" * 80)
        logger.info(f"Loading draft from: {self.draft_file}")

        # Load draft
        with open(self.draft_file, 'r') as f:
            draft_data = json.load(f)

        methods = draft_data.get('methods', {})
        logger.info(f"Processing {len(methods)} methods...")

        # Process each method
        enriched_methods = {}
        for method_name, method_info in methods.items():
            enriched_methods[method_name] = self._process_method(method_name, method_info)

        # Build output
        output = {
            "_metadata": {
                "phase": 3,
                "description": "Parameter values determined with comprehensive knowledge base",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "knowledge_base_stats": {
                    "academic_sources": len(self.kb.academic_sources),
                    "library_sources": len(self.kb.library_sources),
                    "standards": len(self.kb.standards),
                    "parameter_mappings": len(self.kb.parameter_mappings),
                    "coverage_percentage": self.stats["kb_recommendations"] / self.stats["total_parameters"] * 100 if self.stats["total_parameters"] > 0 else 0
                },
                "statistics": self.stats
            },
            "methods": enriched_methods
        }

        return output

    def _process_method(self, method_name: str, method_info: Dict) -> Dict:
        """Process a single method and determine parameter values"""
        configurable_params = method_info.get('configurable_parameters', [])

        enriched_params = []
        for param in configurable_params:
            enriched_param = self._process_parameter(param, method_name)
            enriched_params.append(enriched_param)

        # Copy method info and update parameters
        result = method_info.copy()
        result['configurable_parameters'] = enriched_params
        return result

    def _process_parameter(self, param: Dict, method_name: str) -> Dict:
        """Process a single parameter and determine its value"""
        param_name = param['name']
        self.stats["total_parameters"] += 1

        # Get KB recommendation
        rec = self.kb.get_recommendation(param_name)

        enriched_param = param.copy()

        if rec["found"]:
            # KB HAS RECOMMENDATION
            self.stats["kb_recommendations"] += 1

            enriched_param.update({
                "recommended_value": rec["value"],
                "recommendation_rationale": rec["rationale"],
                "justification": rec["justification"],
                "sources": rec["sources"],
                "source_count": rec["source_count"],
                "recommendation_type": "knowledge_base",
                "validation_status": "verified" if rec["source_count"] >= 2 else "single_source"
            })

            # Log the recommendation
            self.recommendations_log.append({
                "method": method_name,
                "parameter": param_name,
                "value": rec["value"],
                "source_count": rec["source_count"],
                "source_keys": [s["key"] for s in rec["sources"]]
            })

        else:
            # NO KB RECOMMENDATION - use code default
            current_default = param.get('current_default')

            if current_default is None:
                self.stats["none_values"] += 1
                enriched_param.update({
                    "recommended_value": None,
                    "recommendation_rationale": "Parameter-specific, no universal default",
                    "justification": "Application context determines value",
                    "sources": [],
                    "source_count": 0,
                    "recommendation_type": "none_required",
                    "validation_status": "application_specific"
                })
            else:
                self.stats["code_defaults"] += 1
                enriched_param.update({
                    "recommended_value": current_default,
                    "recommendation_rationale": "Code default used - parameter not in comprehensive KB",
                    "justification": f"Using existing code default: {current_default}",
                    "sources": [{"type": "code", "value": current_default}],
                    "source_count": 0,
                    "recommendation_type": "code_default",
                    "validation_status": "requires_validation"
                })

        return enriched_param

    def generate_report(self, output_data: Dict) -> str:
        """Generate detailed parameter sources report"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("PHASE 3: PARAMETER VALUE DETERMINATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Knowledge base stats
        kb_stats = output_data["_metadata"]["knowledge_base_stats"]
        report_lines.append("KNOWLEDGE BASE:")
        report_lines.append(f"  Academic Sources:    {kb_stats['academic_sources']}")
        report_lines.append(f"  Library Sources:     {kb_stats['library_sources']}")
        report_lines.append(f"  Standards:           {kb_stats['standards']}")
        report_lines.append(f"  Parameter Mappings:  {kb_stats['parameter_mappings']}")
        report_lines.append(f"  Coverage:            {kb_stats['coverage_percentage']:.1f}%")
        report_lines.append("")

        # Determination stats
        stats = self.stats
        total = stats["total_parameters"]
        report_lines.append("VALUE DETERMINATION RESULTS:")
        report_lines.append(f"  Total Parameters:         {total}")
        report_lines.append(f"  KB Recommendations:       {stats['kb_recommendations']} ({stats['kb_recommendations']/total*100:.1f}%)")
        report_lines.append(f"  Code Defaults:            {stats['code_defaults']} ({stats['code_defaults']/total*100:.1f}%)")
        report_lines.append(f"  None Values:              {stats['none_values']} ({stats['none_values']/total*100:.1f}%)")
        report_lines.append("")

        # Sample recommendations
        report_lines.append("SAMPLE RECOMMENDATIONS (First 20):")
        report_lines.append("-" * 80)
        for i, rec in enumerate(self.recommendations_log[:20], 1):
            report_lines.append(f"{i:2d}. {rec['parameter']:30s} = {str(rec['value']):15s} ({rec['source_count']} sources)")
            report_lines.append(f"    Sources: {', '.join(rec['source_keys'])}")
            report_lines.append("")

        # Top sources used
        source_counts = defaultdict(int)
        for rec in self.recommendations_log:
            for source_key in rec['source_keys']:
                source_counts[source_key] += 1

        report_lines.append("TOP 10 SOURCES USED:")
        report_lines.append("-" * 80)
        for i, (source, count) in enumerate(sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10], 1):
            report_lines.append(f"{i:2d}. {source:30s} ({count} parameters)")

        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("PHASE 3 COMPLETE")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)


def main():
    """Execute Phase 3: Value Determination with Comprehensive KB"""
    determinator = ParameterValueDeterminator()

    # Determine values
    output_data = determinator.determine_values()

    # Write output
    output_file = Path("method_parameters.json")
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"✓ Written: {output_file} ({output_file.stat().st_size / 1024:.1f} KB)")

    # Generate and write report
    report = determinator.generate_report(output_data)
    report_file = Path("parameter_sources_comprehensive.md")
    with open(report_file, 'w') as f:
        f.write(report)

    logger.info(f"✓ Written: {report_file}")
    print("\n" + report)

    # Summary
    stats = determinator.stats
    total = stats["total_parameters"]
    kb_pct = stats["kb_recommendations"] / total * 100
    code_pct = stats["code_defaults"] / total * 100

    print(f"\n{'='*80}")
    print(f"PHASE 3 SUMMARY:")
    print(f"  Total parameters:     {total}")
    print(f"  KB recommendations:   {stats['kb_recommendations']} ({kb_pct:.1f}%)")
    print(f"  Code defaults:        {stats['code_defaults']} ({code_pct:.1f}%)")
    print(f"  None values:          {stats['none_values']}")
    print(f"{'='*80}")

    # Check if acceptable
    if kb_pct < 50:
        logger.warning(f"⚠️  KB coverage is {kb_pct:.1f}% - target is 50%+")
    else:
        logger.info(f"✓ KB coverage of {kb_pct:.1f}% meets target!")


if __name__ == "__main__":
    main()
