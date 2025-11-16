#!/usr/bin/env python3
"""Count methods in Producer classes"""
import ast
import json
from pathlib import Path

def count_methods_in_class(filepath: Path, class_name: str) -> dict[str, int]:
    """Count public and private methods in a class"""
    with open(filepath, encoding='utf-8') as f:
        tree = ast.parse(f.read())

    method_counts = {
        "public": 0,
        "private": 0,
        "total": 0
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if not item.name.startswith('_'):
                        method_counts["public"] += 1
                    else:
                        method_counts["private"] += 1
                    method_counts["total"] += 1

    return method_counts

# Count methods in each Producer
producers = {
    "SemanticChunkingProducer": "semantic_chunking_policy.py",
    "EmbeddingPolicyProducer": "embedding_policy.py",
    "DerekBeachProducer": "derek_beach.py",
    "ReportAssemblyProducer": "report_assembly.py"
}

results = {}
total_public = 0

for class_name, filepath in producers.items():
    counts = count_methods_in_class(Path(filepath), class_name)
    results[class_name] = counts
    total_public += counts["public"]
    print(f"{class_name}: {counts['public']} public methods, {counts['private']} private, {counts['total']} total")

print(f"\nTotal public methods across all producers: {total_public}")

# Save results
with open('method_counts.json', 'w') as f:
    json.dump({
        "producers": results,
        "total_public_methods": total_public
    }, f, indent=2)

print("\nResults saved to method_counts.json")
