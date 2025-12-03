#!/usr/bin/env python3
"""
Script to systematically add memory safety metrics to all executor return statements.
"""
import re

def update_executors_file(filepath: str) -> None:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'(\s+)"execution_metrics": \{\s+("methods_count":.*?\n\s+"all_succeeded":.*?)\s+\}'
    
    def replacer(match):
        indent = match.group(1)
        metrics_content = match.group(2)
        
        if "memory_safety" in metrics_content:
            return match.group(0)
        
        return (
            f'{indent}"execution_metrics": {{\n'
            f'{indent}    {metrics_content},\n'
            f'{indent}    "memory_safety": self._get_memory_metrics_summary()\n'
            f'{indent}}}'
        )
    
    updated_content = re.sub(pattern, replacer, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"Updated {filepath}")

if __name__ == "__main__":
    update_executors_file("src/farfan_pipeline/core/orchestrator/executors.py")
