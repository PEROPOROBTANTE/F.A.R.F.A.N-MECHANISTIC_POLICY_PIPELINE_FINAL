#!/usr/bin/env python3
# recommendation_cli.py - CLI for Recommendation Engine
# coding=utf-8
"""
Recommendation CLI - Command-line interface for generating recommendations

Usage:
    python recommendation_cli.py micro --scores scores.json
    python recommendation_cli.py meso --clusters clusters.json
    python recommendation_cli.py macro --macro-data macro.json
    python recommendation_cli.py all --input all_data.json
    python recommendation_cli.py demo

Examples:
    # Generate MICRO recommendations
    python recommendation_cli.py micro --scores micro_scores.json -o micro_recs.json

    # Generate all recommendations
    python recommendation_cli.py all --input sample_data.json -o all_recs.md --format markdown

    # Run demonstration
    python recommendation_cli.py demo
"""

import argparse
import json
import logging
import sys
from typing import Any

from saaaaaa.analysis.recommendation_engine import load_recommendation_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> dict[str, Any]:
    """Load JSON data from file"""
    try:
        with open(filepath, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        sys.exit(1)

def generate_micro(args):
    """Generate MICRO-level recommendations"""
    logger.info("Generating MICRO-level recommendations...")

    # Load scores
    scores = load_json_file(args.scores)

    # Load engine
    engine = load_recommendation_engine(args.rules, args.schema)

    # Generate recommendations
    rec_set = engine.generate_micro_recommendations(scores)

    # Output
    logger.info(f"Generated {rec_set.rules_matched} recommendations from {rec_set.total_rules_evaluated} rules")

    if args.output:
        engine.export_recommendations(
            {'MICRO': rec_set},
            args.output,
            format=args.format
        )
        logger.info(f"Saved to {args.output}")
    else:
        # Print to stdout
        if args.format == 'json':
            print(json.dumps(rec_set.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(engine._format_as_markdown({'MICRO': rec_set}))

def generate_meso(args):
    """Generate MESO-level recommendations"""
    logger.info("Generating MESO-level recommendations...")

    # Load cluster data
    cluster_data = load_json_file(args.clusters)

    # Load engine
    engine = load_recommendation_engine(args.rules, args.schema)

    # Generate recommendations
    rec_set = engine.generate_meso_recommendations(cluster_data)

    # Output
    logger.info(f"Generated {rec_set.rules_matched} recommendations from {rec_set.total_rules_evaluated} rules")

    if args.output:
        engine.export_recommendations(
            {'MESO': rec_set},
            args.output,
            format=args.format
        )
        logger.info(f"Saved to {args.output}")
    else:
        # Print to stdout
        if args.format == 'json':
            print(json.dumps(rec_set.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(engine._format_as_markdown({'MESO': rec_set}))

def generate_macro(args):
    """Generate MACRO-level recommendations"""
    logger.info("Generating MACRO-level recommendations...")

    # Load macro data
    macro_data = load_json_file(args.macro_data)

    # Load engine
    engine = load_recommendation_engine(args.rules, args.schema)

    # Generate recommendations
    rec_set = engine.generate_macro_recommendations(macro_data)

    # Output
    logger.info(f"Generated {rec_set.rules_matched} recommendations from {rec_set.total_rules_evaluated} rules")

    if args.output:
        engine.export_recommendations(
            {'MACRO': rec_set},
            args.output,
            format=args.format
        )
        logger.info(f"Saved to {args.output}")
    else:
        # Print to stdout
        if args.format == 'json':
            print(json.dumps(rec_set.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(engine._format_as_markdown({'MACRO': rec_set}))

def generate_all(args):
    """Generate recommendations at all levels"""
    logger.info("Generating recommendations at all levels...")

    # Load input data
    data = load_json_file(args.input)

    micro_scores = data.get('micro_scores', {})
    cluster_data = data.get('cluster_data', {})
    macro_data = data.get('macro_data', {})

    # Load engine
    engine = load_recommendation_engine(args.rules, args.schema)

    # Generate all recommendations
    all_recs = engine.generate_all_recommendations(
        micro_scores, cluster_data, macro_data
    )

    # Output summary
    logger.info(f"MICRO: {all_recs['MICRO'].rules_matched} recommendations")
    logger.info(f"MESO: {all_recs['MESO'].rules_matched} recommendations")
    logger.info(f"MACRO: {all_recs['MACRO'].rules_matched} recommendations")

    if args.output:
        engine.export_recommendations(all_recs, args.output, format=args.format)
        logger.info(f"Saved to {args.output}")
    else:
        # Print to stdout
        if args.format == 'json':
            output = {level: rec_set.to_dict() for level, rec_set in all_recs.items()}
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            print(engine._format_as_markdown(all_recs))

def run_demo(args):
    """Run demonstration with sample data"""
    logger.info("Running demonstration...")

    # Sample MICRO scores
    micro_scores = {
        'PA01-DIM01': 1.2,  # Below threshold
        'PA02-DIM02': 1.5,  # Below threshold
        'PA03-DIM05': 1.4,  # Below threshold
        'PA04-DIM03': 2.0,  # Above threshold
    }

    # Sample cluster data
    cluster_data = {
        'CL01': {
            'score': 72.0,
            'variance': 0.25,
            'weak_pa': 'PA02'
        },
        'CL02': {
            'score': 58.0,
            'variance': 0.12,
        },
        'CL03': {
            'score': 65.0,
            'variance': 0.28,
            'weak_pa': 'PA04'
        }
    }

    # Sample macro data
    macro_data = {
        'macro_band': 'SATISFACTORIO',
        'clusters_below_target': ['CL02', 'CL03'],
        'variance_alert': 'MODERADA',
        'priority_micro_gaps': ['PA01-DIM05', 'PA05-DIM04', 'PA04-DIM04', 'PA08-DIM05']
    }

    # Load engine
    engine = load_recommendation_engine(args.rules, args.schema)

    # Generate all recommendations
    all_recs = engine.generate_all_recommendations(
        micro_scores, cluster_data, macro_data
    )

    # Display results
    print("\n" + "=" * 80)
    print("DEMONSTRATION: Recommendation Engine")
    print("=" * 80)

    print("\n📊 INPUT DATA:")
    print(f"  MICRO Scores: {len(micro_scores)} PA-DIM combinations")
    print(f"  MESO Clusters: {len(cluster_data)} clusters")
    print(f"  MACRO Band: {macro_data['macro_band']}")

    print("\n📋 RESULTS:")
    print(f"  MICRO: {all_recs['MICRO'].rules_matched} recommendations (from {all_recs['MICRO'].total_rules_evaluated} rules)")
    print(f"  MESO:  {all_recs['MESO'].rules_matched} recommendations (from {all_recs['MESO'].total_rules_evaluated} rules)")
    print(f"  MACRO: {all_recs['MACRO'].rules_matched} recommendations (from {all_recs['MACRO'].total_rules_evaluated} rules)")

    # Show sample MICRO recommendations
    if all_recs['MICRO'].recommendations:
        print("\n" + "-" * 80)
        print("SAMPLE MICRO RECOMMENDATION:")
        print("-" * 80)
        rec = all_recs['MICRO'].recommendations[0]
        print(f"Rule ID: {rec.rule_id}")
        print(f"Problem: {rec.problem[:200]}...")
        print(f"Intervention: {rec.intervention[:200]}...")
        print(f"Responsible: {rec.responsible['entity']}")
        print(f"Horizon: {rec.horizon['start']} → {rec.horizon['end']}")

    # Show sample MESO recommendations
    if all_recs['MESO'].recommendations:
        print("\n" + "-" * 80)
        print("SAMPLE MESO RECOMMENDATION:")
        print("-" * 80)
        rec = all_recs['MESO'].recommendations[0]
        print(f"Rule ID: {rec.rule_id}")
        print(f"Cluster: {rec.metadata.get('cluster_id')}")
        print(f"Score: {rec.metadata.get('score'):.1f} ({rec.metadata.get('score_band')})")
        print(f"Intervention: {rec.intervention[:200]}...")

    # Show sample MACRO recommendations
    if all_recs['MACRO'].recommendations:
        print("\n" + "-" * 80)
        print("SAMPLE MACRO RECOMMENDATION:")
        print("-" * 80)
        rec = all_recs['MACRO'].recommendations[0]
        print(f"Rule ID: {rec.rule_id}")
        print(f"Band: {rec.metadata.get('macro_band')}")
        print(f"Intervention: {rec.intervention[:200]}...")

    print("\n" + "=" * 80)

    # Optionally save
    if args.output:
        engine.export_recommendations(all_recs, args.output, format=args.format)
        logger.info(f"Full report saved to {args.output}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Generate rule-based recommendations for policy plans',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Global arguments
    parser.add_argument(
        '--rules',
        default='config/recommendation_rules.json',
        help='Path to recommendation rules JSON file'
    )
    parser.add_argument(
        '--schema',
        default='rules/recommendation_rules.schema.json',
        help='Path to rules schema JSON file'
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # MICRO command
    micro_parser = subparsers.add_parser('micro', help='Generate MICRO-level recommendations')
    micro_parser.add_argument('--scores', required=True, help='Path to scores JSON file')
    micro_parser.add_argument('-o', '--output', help='Output file path')
    micro_parser.add_argument('--format', choices=['json', 'markdown'], default='json', help='Output format')
    micro_parser.set_defaults(func=generate_micro)

    # MESO command
    meso_parser = subparsers.add_parser('meso', help='Generate MESO-level recommendations')
    meso_parser.add_argument('--clusters', required=True, help='Path to cluster data JSON file')
    meso_parser.add_argument('-o', '--output', help='Output file path')
    meso_parser.add_argument('--format', choices=['json', 'markdown'], default='json', help='Output format')
    meso_parser.set_defaults(func=generate_meso)

    # MACRO command
    macro_parser = subparsers.add_parser('macro', help='Generate MACRO-level recommendations')
    macro_parser.add_argument('--macro-data', required=True, help='Path to macro data JSON file')
    macro_parser.add_argument('-o', '--output', help='Output file path')
    macro_parser.add_argument('--format', choices=['json', 'markdown'], default='json', help='Output format')
    macro_parser.set_defaults(func=generate_macro)

    # ALL command
    all_parser = subparsers.add_parser('all', help='Generate recommendations at all levels')
    all_parser.add_argument('--input', required=True, help='Path to combined input JSON file')
    all_parser.add_argument('-o', '--output', help='Output file path')
    all_parser.add_argument('--format', choices=['json', 'markdown'], default='json', help='Output format')
    all_parser.set_defaults(func=generate_all)

    # DEMO command
    demo_parser = subparsers.add_parser('demo', help='Run demonstration with sample data')
    demo_parser.add_argument('-o', '--output', help='Output file path')
    demo_parser.add_argument('--format', choices=['json', 'markdown'], default='markdown', help='Output format')
    demo_parser.set_defaults(func=run_demo)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    args.func(args)

if __name__ == '__main__':
    main()
