#!/usr/bin/env python3
"""
Utility script to analyze and work with the executor methods mapping.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def load_mapping(filepath: str = "executor_methods_mapping.json") -> Dict:
    """Load the executor methods mapping from JSON."""
    with open(filepath, 'r') as f:
        return json.load(f)


def get_statistics(mapping: Dict) -> Dict:
    """Calculate comprehensive statistics from the mapping."""
    stats = {
        'total_executors': len(mapping),
        'total_methods': sum(len(methods) for methods in mapping.values()),
        'methods_per_executor': {},
        'class_usage': Counter(),
        'method_usage': Counter(),
        'executors_per_class': defaultdict(list)
    }

    for base_slot, methods in mapping.items():
        stats['methods_per_executor'][base_slot] = len(methods)

        for method_info in methods:
            class_name = method_info['class']
            method_name = method_info['method']

            stats['class_usage'][class_name] += 1
            stats['method_usage'][f"{class_name}.{method_name}"] += 1
            stats['executors_per_class'][class_name].append(base_slot)

    return stats


def find_executors_using_class(mapping: Dict, class_name: str) -> List[str]:
    """Find all executors that use a specific class."""
    executors = []
    for base_slot, methods in mapping.items():
        if any(m['class'] == class_name for m in methods):
            executors.append(base_slot)
    return executors


def find_executors_using_method(mapping: Dict, class_name: str, method_name: str) -> List[str]:
    """Find all executors that use a specific method."""
    executors = []
    for base_slot, methods in mapping.items():
        if any(m['class'] == class_name and m['method'] == method_name for m in methods):
            executors.append(base_slot)
    return executors


def get_shared_methods(mapping: Dict, executor1: str, executor2: str) -> List[Tuple[str, str]]:
    """Find methods shared between two executors."""
    methods1 = {(m['class'], m['method']) for m in mapping[executor1]}
    methods2 = {(m['class'], m['method']) for m in mapping[executor2]}
    return sorted(methods1 & methods2)


def get_unique_methods(mapping: Dict, executor: str) -> List[Tuple[str, str]]:
    """Find methods unique to a specific executor."""
    executor_methods = {(m['class'], m['method']) for m in mapping[executor]}
    all_other_methods = set()

    for base_slot, methods in mapping.items():
        if base_slot != executor:
            all_other_methods.update((m['class'], m['method']) for m in methods)

    return sorted(executor_methods - all_other_methods)


def print_statistics(stats: Dict):
    """Print formatted statistics."""
    print("=" * 80)
    print("EXECUTOR METHODS MAPPING STATISTICS")
    print("=" * 80)
    print(f"\nTotal Executors: {stats['total_executors']}")
    print(f"Total Methods: {stats['total_methods']}")
    print(f"Average Methods per Executor: {stats['total_methods'] / stats['total_executors']:.1f}")

    print("\n" + "=" * 80)
    print("TOP 10 MOST USED CLASSES")
    print("=" * 80)
    for class_name, count in stats['class_usage'].most_common(10):
        print(f"{class_name:50} {count:3} methods")

    print("\n" + "=" * 80)
    print("MOST COMPLEX EXECUTORS (by method count)")
    print("=" * 80)
    sorted_executors = sorted(stats['methods_per_executor'].items(),
                             key=lambda x: x[1], reverse=True)
    for base_slot, count in sorted_executors[:10]:
        print(f"{base_slot:10} {count:3} methods")

    print("\n" + "=" * 80)
    print("SIMPLEST EXECUTORS (by method count)")
    print("=" * 80)
    for base_slot, count in sorted_executors[-10:]:
        print(f"{base_slot:10} {count:3} methods")

    print("\n" + "=" * 80)
    print("TOP 20 MOST FREQUENTLY USED METHODS")
    print("=" * 80)
    for method_name, count in stats['method_usage'].most_common(20):
        print(f"{method_name:70} {count:2}x")


def export_class_usage_report(mapping: Dict, output_file: str = "class_usage_report.txt"):
    """Export a detailed class usage report."""
    stats = get_statistics(mapping)

    with open(output_file, 'w') as f:
        f.write("CLASS USAGE REPORT\n")
        f.write("=" * 80 + "\n\n")

        for class_name in sorted(stats['class_usage'].keys()):
            executors = stats['executors_per_class'][class_name]
            f.write(f"\n{class_name}\n")
            f.write("-" * 80 + "\n")
            f.write(f"Used in {len(executors)} executor(s): {', '.join(sorted(executors))}\n")

            # List all methods from this class
            methods_from_class = set()
            for base_slot in executors:
                for method_info in mapping[base_slot]:
                    if method_info['class'] == class_name:
                        methods_from_class.add(method_info['method'])

            f.write(f"Methods used: {', '.join(sorted(methods_from_class))}\n")

    print(f"\nClass usage report exported to: {output_file}")


def export_executor_dependency_matrix(mapping: Dict, output_file: str = "executor_dependencies.csv"):
    """Export a CSV matrix showing which classes each executor depends on."""
    # Get all unique classes
    all_classes = set()
    for methods in mapping.values():
        all_classes.update(m['class'] for m in methods)

    all_classes = sorted(all_classes)

    with open(output_file, 'w') as f:
        # Header
        f.write("Executor," + ",".join(all_classes) + "\n")

        # Data rows
        for base_slot in sorted(mapping.keys()):
            executor_classes = {m['class'] for m in mapping[base_slot]}
            row = [base_slot]
            for class_name in all_classes:
                row.append("1" if class_name in executor_classes else "0")
            f.write(",".join(row) + "\n")

    print(f"\nDependency matrix exported to: {output_file}")


def main():
    """Main analysis function."""
    # Load the mapping
    mapping = load_mapping()

    # Calculate and print statistics
    stats = get_statistics(mapping)
    print_statistics(stats)

    # Export reports
    print("\n" + "=" * 80)
    print("EXPORTING REPORTS")
    print("=" * 80)
    export_class_usage_report(mapping)
    export_executor_dependency_matrix(mapping)

    # Example queries
    print("\n" + "=" * 80)
    print("EXAMPLE QUERIES")
    print("=" * 80)

    # Find executors using PDETMunicipalPlanAnalyzer
    executors = find_executors_using_class(mapping, "PDETMunicipalPlanAnalyzer")
    print(f"\nExecutors using PDETMunicipalPlanAnalyzer ({len(executors)}):")
    print(", ".join(executors))

    # Find executors using a specific method
    executors = find_executors_using_method(mapping, "FinancialAuditor", "_calculate_sufficiency")
    print(f"\nExecutors using FinancialAuditor._calculate_sufficiency ({len(executors)}):")
    print(", ".join(executors))

    # Find shared methods between two executors
    shared = get_shared_methods(mapping, "D1-Q1", "D1-Q2")
    print(f"\nShared methods between D1-Q1 and D1-Q2 ({len(shared)}):")
    for class_name, method_name in shared[:5]:
        print(f"  - {class_name}.{method_name}")
    if len(shared) > 5:
        print(f"  ... and {len(shared) - 5} more")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
