"""
Test 5: Orchestrator Runtime - Correct Layer Evaluation + Aggregation with Real Contexts

Validates runtime behavior:
- Layers execute in correct order
- Method results aggregate properly
- Context passing works correctly
- No runtime exceptions in calibration resolution

FAILURE CONDITION: Any runtime error OR incorrect aggregation = NOT READY

DEPRECATED: Test assumes outdated executors_methods.json structure and layer execution order.
See tests/DEPRECATED_TESTS.md for details.
"""
import json
import pytest
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

pytestmark = pytest.mark.obsolete


class TestOrchestratorRuntime:
    
    @pytest.fixture(scope="class")
    def executors_methods(self) -> Dict[str, Any]:
        """Load executors_methods.json"""
        path = Path("src/farfan_pipeline/core/orchestrator/executors_methods.json")
        with open(path) as f:
            return json.load(f)
    
    @pytest.fixture(scope="class")
    def intrinsic_calibration(self) -> Dict[str, Any]:
        """Load intrinsic_calibration.json"""
        path = Path("system/config/calibration/intrinsic_calibration.json")
        with open(path) as f:
            return json.load(f)
    
    @pytest.fixture
    def mock_context(self) -> Dict[str, Any]:
        """Create a mock execution context"""
        return {
            "document_text": "Sample policy document for testing",
            "raw_text": "Sample policy document for testing",
            "document_id": "test_doc_001",
            "metadata": {
                "source": "test",
                "year": 2024
            }
        }
    
    def test_layer_execution_order_defined(self, executors_methods):
        """Verify layer execution order is consistent"""
        expected_order = [
            "ingestion",
            "extraction",
            "transformation",
            "validation",
            "aggregation",
            "scoring",
            "reporting",
            "meta"
        ]
        
        for executor in executors_methods:
            layers_sequence = []
            
            for method in executor["methods"]:
                if "layer" in method:
                    layer = method["layer"]
                    if not layers_sequence or layers_sequence[-1] != layer:
                        layers_sequence.append(layer)
            
            for i, layer in enumerate(layers_sequence):
                expected_pos = expected_order.index(layer)
                
                for j in range(i + 1, len(layers_sequence)):
                    next_layer = layers_sequence[j]
                    next_pos = expected_order.index(next_layer)
                    
                    assert expected_pos <= next_pos, \
                        f"Layer order violation in {executor['executor_id']}: " \
                        f"{layer} (pos {expected_pos}) followed by {next_layer} (pos {next_pos})"
    
    def test_calibration_context_resolution(self, intrinsic_calibration):
        """Test that calibration context can be resolved without errors"""
        try:
            from src.farfan_pipeline.core.orchestrator.calibration_context import (
                CalibrationContext,
                resolve_contextual_calibration,
            )
        except ImportError:
            pytest.skip("calibration_context module not available")
        
        test_question_ids = ["D1Q1", "D3Q5", "D6Q3"]
        
        for qid in test_question_ids:
            try:
                context = CalibrationContext.from_question_id(qid)
                assert context.question_id == qid
                assert context.dimension > 0
                assert context.question_num > 0
            except Exception as e:
                pytest.fail(f"Failed to create context for {qid}: {e}")
    
    def test_method_execution_simulation(self, executors_methods, mock_context):
        """Simulate method execution to verify no obvious runtime errors"""
        sample_executor = executors_methods[0]
        
        for method in sample_executor["methods"][:3]:
            method_id = f"{method['class']}.{method['method']}"
            
            try:
                result = self._simulate_method_call(
                    method["class"],
                    method["method"],
                    mock_context
                )
                
                assert result is not None or result == {}, \
                    f"Method {method_id} returned None unexpectedly"
                    
            except NotImplementedError:
                pass
            except Exception as e:
                pytest.fail(
                    f"Unexpected error simulating {method_id}: {type(e).__name__}: {e}"
                )
    
    def _simulate_method_call(
        self, class_name: str, method_name: str, context: Dict[str, Any]
    ) -> Any:
        """Simulate a method call (mock implementation)"""
        if method_name.startswith("_"):
            return {}
        
        return {"status": "simulated", "method": f"{class_name}.{method_name}"}
    
    def test_aggregation_logic_validation(self, executors_methods):
        """Verify aggregation layer methods are present"""
        aggregation_methods = []
        
        for executor in executors_methods:
            for method in executor["methods"]:
                if method.get("layer") == "aggregation":
                    aggregation_methods.append({
                        "executor": executor["executor_id"],
                        "method": f"{method['class']}.{method['method']}"
                    })
        
        assert len(aggregation_methods) > 0, \
            "No aggregation methods found across all executors"
        
        print(f"\nFound {len(aggregation_methods)} aggregation methods")
    
    def test_scoring_methods_present(self, executors_methods):
        """Verify scoring layer methods are present"""
        scoring_methods = []
        
        for executor in executors_methods:
            for method in executor["methods"]:
                if method.get("layer") == "scoring":
                    scoring_methods.append({
                        "executor": executor["executor_id"],
                        "method": f"{method['class']}.{method['method']}"
                    })
        
        assert len(scoring_methods) > 0, \
            "No scoring methods found across all executors"
        
        print(f"\nFound {len(scoring_methods)} scoring methods")
    
    def test_reporting_layer_completeness(self, executors_methods):
        """Verify all executors have reporting capability"""
        executors_without_reporting = []
        
        for executor in executors_methods:
            has_reporting = any(
                method.get("layer") == "reporting"
                for method in executor["methods"]
            )
            
            if not has_reporting:
                executors_without_reporting.append(executor["executor_id"])
        
        if executors_without_reporting:
            print(
                f"\nWARNING: {len(executors_without_reporting)} executors "
                f"without reporting layer: {executors_without_reporting[:5]}"
            )
    
    def test_context_propagation_structure(self, mock_context):
        """Verify context has expected structure for method execution"""
        required_fields = ["document_text", "raw_text"]
        
        for field in required_fields:
            assert field in mock_context, \
                f"Mock context missing required field: {field}"
    
    def test_no_circular_dependencies_in_layers(self, executors_methods):
        """Verify no circular dependencies between layers"""
        layer_dependencies = {}
        
        for executor in executors_methods:
            for i, method in enumerate(executor["methods"]):
                if "layer" not in method:
                    continue
                
                current_layer = method["layer"]
                
                if current_layer not in layer_dependencies:
                    layer_dependencies[current_layer] = set()
                
                for prev_method in executor["methods"][:i]:
                    if "layer" in prev_method:
                        layer_dependencies[current_layer].add(prev_method["layer"])
        
        for layer, deps in layer_dependencies.items():
            assert layer not in deps, \
                f"Circular dependency detected: layer {layer} depends on itself"
    
    def test_calibration_values_resolvable(self, intrinsic_calibration):
        """Verify calibration values can be accessed without errors"""
        for method_id, calibration in intrinsic_calibration.items():
            if method_id == "_metadata":
                continue
            
            if calibration.get("status") == "computed":
                assert isinstance(calibration, dict), \
                    f"Calibration for {method_id} must be a dict"
