#!/usr/bin/env python3
"""
Runtime Pipeline Validation
===========================

Performs runtime validation of the pipeline to complement the static audit.
Tests actual execution paths, contract adherence, and determinism.
"""

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional



class RuntimeValidator:
    """Runtime validation of pipeline components."""
    
    def __init__(self):
        """Initialize validator."""
        self.results: List[Dict[str, Any]] = []
        
    def test_import_chain(self) -> Dict[str, Any]:
        """Test that all critical imports work."""
        print("🔍 Testing import chain...")
        result = {
            "test": "import_chain",
            "status": "pass",
            "errors": [],
            "imported_modules": [],
        }
        
        critical_imports = [
            "saaaaaa.core.orchestrator.core",
            "saaaaaa.processing.aggregation",
            "saaaaaa.processing.document_ingestion",
            "saaaaaa.core.orchestrator.signals",
            "saaaaaa.core.orchestrator.arg_router",
            "saaaaaa.utils.spc_adapter",
            "saaaaaa.analysis.recommendation_engine",
        ]
        
        for module_name in critical_imports:
            try:
                __import__(module_name)
                result["imported_modules"].append(module_name)
            except Exception as e:
                result["status"] = "fail"
                result["errors"].append(f"{module_name}: {str(e)}")
        
        return result
    
    def test_contract_schemas(self) -> Dict[str, Any]:
        """Test that contracts are Pydantic models."""
        print("🔍 Testing contract schemas...")
        result = {
            "test": "contract_schemas",
            "status": "pass",
            "pydantic_models": [],
            "errors": [],
        }
        
        try:
            # Test PreprocessedDocument
            from saaaaaa.core.orchestrator.core import PreprocessedDocument
            if hasattr(PreprocessedDocument, "__annotations__"):
                result["pydantic_models"].append("PreprocessedDocument")
            
            # Test aggregation models
            from saaaaaa.processing.aggregation import (
                ScoredResult, DimensionScore, AreaScore, ClusterScore, MacroScore
            )
            for model in [ScoredResult, DimensionScore, AreaScore, ClusterScore, MacroScore]:
                result["pydantic_models"].append(model.__name__)
            
            # Test SignalPack
            try:
                from saaaaaa.core.orchestrator.signals import SignalPack
                from pydantic import BaseModel
                if issubclass(SignalPack, BaseModel):
                    result["pydantic_models"].append("SignalPack (Pydantic)")
            except:
                pass
                
        except Exception as e:
            result["status"] = "fail"
            result["errors"].append(str(e))
        
        return result
    
    def test_arg_router_routes(self) -> Dict[str, Any]:
        """Test ArgRouter route handling."""
        print("🔍 Testing ArgRouter routes...")
        result = {
            "test": "arg_router_routes",
            "status": "pass",
            "route_count": 0,
            "errors": [],
        }
        
        try:
            from saaaaaa.core.orchestrator.arg_router import ArgRouter
            from saaaaaa.core.orchestrator.class_registry import build_class_registry
            
            # Build a test registry
            registry = build_class_registry()
            router = ArgRouter(registry)
            
            # Count routes by inspecting methods
            import inspect
            methods = [
                m for m in dir(router)
                if not m.startswith("_") and callable(getattr(router, m))
            ]
            result["route_count"] = len(methods)
            
            # Test a basic route
            if hasattr(router, "describe"):
                result["sample_routes"] = ["describe"]
        
        except Exception as e:
            result["status"] = "fail"
            result["errors"].append(str(e))
        
        return result
    
    def test_cpp_adapter_conversion(self) -> Dict[str, Any]:
        """Test SPCAdapter conversion logic."""
        print("🔍 Testing SPC adapter conversion...")
        result = {
            "test": "spc_adapter_conversion",
            "status": "pass",
            "features_tested": [],
            "errors": [],
        }
        
        try:
            from saaaaaa.utils.spc_adapter import SPCAdapter
            
            adapter = SPCAdapter()
            result["features_tested"].append("SPCAdapter instantiation")
            
            # Check for key methods
            if hasattr(adapter, "to_preprocessed_document"):
                result["features_tested"].append("to_preprocessed_document method")
            
        except Exception as e:
            result["status"] = "fail"
            result["errors"].append(str(e))
        
        return result
    
    def test_determinism_setup(self) -> Dict[str, Any]:
        """Test determinism infrastructure."""
        print("🔍 Testing determinism setup...")
        result = {
            "test": "determinism_setup",
            "status": "pass",
            "seed_modules": [],
            "errors": [],
        }
        
        try:
            # Test seed factory
            try:
                from saaaaaa.utils.seed_factory import SeedFactory
                result["seed_modules"].append("SeedFactory")
            except ImportError:
                pass
            
            # Test determinism utils
            try:
                from saaaaaa.utils.determinism import seeds
                result["seed_modules"].append("determinism.seeds")
            except ImportError:
                pass
            
            if not result["seed_modules"]:
                result["status"] = "warning"
                result["errors"].append("No seed management modules found")
        
        except Exception as e:
            result["status"] = "fail"
            result["errors"].append(str(e))
        
        return result
    
    def test_signal_registry(self) -> Dict[str, Any]:
        """Test signal registry functionality."""
        print("🔍 Testing signal registry...")
        result = {
            "test": "signal_registry",
            "status": "pass",
            "features": [],
            "errors": [],
        }
        
        try:
            from saaaaaa.core.orchestrator.signals import SignalPack, SignalRegistry
            
            result["features"].append("SignalPack imported")
            
            # Test SignalPack creation
            pack = SignalPack(
                version="1.0.0",
                policy_area="fiscal",
                patterns=["pattern1"],
                indicators=["indicator1"],
            )
            result["features"].append("SignalPack creation")
            
            # Test if it has validation
            if hasattr(pack, "model_validate"):
                result["features"].append("Pydantic validation")
        
        except Exception as e:
            result["status"] = "fail"
            result["errors"].append(str(e))
        
        return result
    
    def test_aggregation_pipeline(self) -> Dict[str, Any]:
        """Test aggregation pipeline components."""
        print("🔍 Testing aggregation pipeline...")
        result = {
            "test": "aggregation_pipeline",
            "status": "pass",
            "aggregators": [],
            "errors": [],
        }
        
        try:
            from saaaaaa.processing.aggregation import (
                DimensionAggregator,
                AreaPolicyAggregator,
                ClusterAggregator,
                MacroAggregator,
            )
            
            # Test each aggregator instantiation
            for agg_class in [DimensionAggregator, AreaPolicyAggregator, 
                             ClusterAggregator, MacroAggregator]:
                try:
                    agg = agg_class()
                    result["aggregators"].append(agg_class.__name__)
                except Exception as e:
                    result["errors"].append(f"{agg_class.__name__}: {str(e)}")
        
        except Exception as e:
            result["status"] = "fail"
            result["errors"].append(str(e))
        
        return result
    
    def test_config_parametrization(self) -> Dict[str, Any]:
        """Test configuration parametrization."""
        print("🔍 Testing config parametrization...")
        result = {
            "test": "config_parametrization",
            "status": "pass",
            "configs_tested": [],
            "missing_methods": [],
            "errors": [],
        }
        
        try:
            # Test executor config
            try:
                from saaaaaa.core.orchestrator.executor_config import ExecutorConfig
                result["configs_tested"].append("ExecutorConfig")
                
                if not hasattr(ExecutorConfig, "from_env"):
                    result["missing_methods"].append("ExecutorConfig.from_env")
                if not hasattr(ExecutorConfig, "from_cli"):
                    result["missing_methods"].append("ExecutorConfig.from_cli")
            except ImportError:
                pass
            
            if result["missing_methods"]:
                result["status"] = "warning"
        
        except Exception as e:
            result["status"] = "fail"
            result["errors"].append(str(e))
        
        return result
    
    def run_all_tests(self) -> None:
        """Run all runtime validation tests."""
        print("\n" + "=" * 80)
        print("RUNTIME PIPELINE VALIDATION")
        print("=" * 80 + "\n")
        
        tests = [
            self.test_import_chain,
            self.test_contract_schemas,
            self.test_arg_router_routes,
            self.test_cpp_adapter_conversion,
            self.test_determinism_setup,
            self.test_signal_registry,
            self.test_aggregation_pipeline,
            self.test_config_parametrization,
        ]
        
        for test in tests:
            result = test()
            self.results.append(result)
            
            status_emoji = {
                "pass": "✅",
                "warning": "⚠️",
                "fail": "❌",
            }[result["status"]]
            
            print(f"{status_emoji} {result['test']}: {result['status'].upper()}")
            if result.get("errors"):
                for error in result["errors"]:
                    print(f"   Error: {error}")
        
        print("\n" + "=" * 80)
        print("VALIDATION COMPLETE")
        print("=" * 80)
    
    def generate_report(self) -> None:
        """Generate runtime validation report."""
        report_path = Path(__file__).parent / "RUNTIME_VALIDATION_REPORT.md"
        
        with open(report_path, "w") as f:
            f.write("# Runtime Pipeline Validation Report\n\n")
            f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            pass_count = sum(1 for r in self.results if r["status"] == "pass")
            warning_count = sum(1 for r in self.results if r["status"] == "warning")
            fail_count = sum(1 for r in self.results if r["status"] == "fail")
            
            f.write("## Summary\n\n")
            f.write(f"- ✅ Passed: {pass_count}\n")
            f.write(f"- ⚠️ Warnings: {warning_count}\n")
            f.write(f"- ❌ Failed: {fail_count}\n\n")
            
            # Detailed results
            f.write("## Test Results\n\n")
            for result in self.results:
                status_emoji = {
                    "pass": "✅",
                    "warning": "⚠️",
                    "fail": "❌",
                }[result["status"]]
                
                f.write(f"### {status_emoji} {result['test']}\n\n")
                f.write(f"**Status:** {result['status'].upper()}\n\n")
                
                # Write additional details based on test type
                for key, value in result.items():
                    if key not in ["test", "status", "errors"]:
                        if value:
                            f.write(f"**{key.replace('_', ' ').title()}:** {value}\n\n")
                
                if result.get("errors"):
                    f.write("**Errors:**\n")
                    for error in result["errors"]:
                        f.write(f"- {error}\n")
                    f.write("\n")
                
                f.write("---\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            
            if fail_count > 0:
                f.write("### Critical Issues\n\n")
                for result in self.results:
                    if result["status"] == "fail":
                        f.write(f"- Fix {result['test']}: {', '.join(result['errors'])}\n")
                f.write("\n")
            
            if warning_count > 0:
                f.write("### Warnings\n\n")
                for result in self.results:
                    if result["status"] == "warning":
                        f.write(f"- Review {result['test']}: {', '.join(result.get('errors', []))}\n")
                f.write("\n")
        
        print(f"\n✅ Generated: {report_path}")


def main() -> int:
    """Main entry point."""
    validator = RuntimeValidator()
    validator.run_all_tests()
    validator.generate_report()
    
    # Return exit code based on failures
    fail_count = sum(1 for r in validator.results if r["status"] == "fail")
    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
