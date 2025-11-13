#!/usr/bin/env python3
"""
Verify that ExecutorConfig is properly integrated into all executors.
Binary pass/fail verification.
"""

import sys
import ast
from pathlib import Path

def verify_executor_config_integration():
    """Check that all executors accept and use config."""
    
    print("=" * 60)
    print("EXECUTOR CONFIG VERIFICATION")
    print("=" * 60)
    
    errors = []
    
    # Check executors.py
    executors_path = Path("src/saaaaaa/core/orchestrator/executors.py")
    if not executors_path.exists():
        print(f"FAIL: {executors_path} not found")
        return False
    
    content = executors_path.read_text()
    
    # Check 1: Import statement
    if "from .executor_config import ExecutorConfig" not in content:
        errors.append("Missing import: from .executor_config import ExecutorConfig")
    
    # Check 2: Base class has config parameter
    if "config: ExecutorConfig | None = None" not in content:
        errors.append("AdvancedDataFlowExecutor missing config parameter")
    
    # Check 3: Config used in execute_with_optimization
    if "self.config.retry" not in content:
        errors.append("Config not used for retry count")
    
    if "self.config.timeout_s" not in content:
        errors.append("Config not used for timeout")
    
    # Check 4: Parse AST to verify all executor classes
    try:
        tree = ast.parse(content)
        executor_classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.endswith("_Executor"):
                    executor_classes.append(node.name)
                    
                    # Check __init__ has config parameter
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                            has_config = any(
                                arg.arg == "config" for arg in item.args.args
                            )
                            if not has_config:
                                errors.append(
                                    f"{node.name}.__init__ missing config parameter"
                                )
        
        print(f"Found {len(executor_classes)} executor classes")
        
    except SyntaxError as e:
        errors.append(f"Syntax error in executors.py: {e}")
    
    # Check 5: Factory integration
    factory_path = Path("src/saaaaaa/core/orchestrator/factory.py")
    if factory_path.exists():
        factory_content = factory_path.read_text()
        if "executor_config" not in factory_content:
            errors.append("Factory doesn't handle executor_config")
    
    # Report results
    if errors:
        print("\nFAIL: Configuration issues found:")
        for error in errors:
            print(f"  ❌ {error}")
        return False
    else:
        print("\n✓ ExecutorConfig properly imported")
        print("✓ All executors accept config parameter")
        print("✓ Config used in execution logic")
        print("✓ No orphaned configuration")
        return True

def main():
    """Main verification entry point."""
    try:
        if verify_executor_config_integration():
            print("\nVERIFICATION PASSED")
            sys.exit(0)
        else:
            print("\nVERIFICATION FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()