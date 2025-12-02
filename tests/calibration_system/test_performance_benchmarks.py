"""
Test 7: Performance Benchmarks - Load Times and Calibration Speed

Validates system performance:
- Load intrinsic.json: < 1 second
- Calibrate 30 executors: < 5 seconds
- Calibrate 200 methods: < 30 seconds

FAILURE CONDITION: Any performance threshold exceeded = NOT READY

DEPRECATED: Test uses hardcoded paths to system/config/calibration/intrinsic_calibration.json.
See tests/DEPRECATED_TESTS.md for details.
"""
import json
import time
import pytest
from pathlib import Path
from typing import Dict, Any, List

pytestmark = pytest.mark.obsolete


class TestPerformanceBenchmarks:
    
    MAX_LOAD_TIME_SECONDS = 1.0
    MAX_30_EXECUTORS_SECONDS = 5.0
    MAX_200_METHODS_SECONDS = 30.0
    
    @pytest.fixture(scope="class")
    def intrinsic_path(self) -> Path:
        """Path to intrinsic_calibration.json"""
        return Path("system/config/calibration/intrinsic_calibration.json")
    
    @pytest.fixture(scope="class")
    def executors_path(self) -> Path:
        """Path to executors_methods.json"""
        return Path("src/farfan_pipeline/core/orchestrator/executors_methods.json")
    
    def test_load_intrinsic_json_performance(self, intrinsic_path):
        """CRITICAL: Load intrinsic_calibration.json in < 1 second"""
        assert intrinsic_path.exists(), f"File not found: {intrinsic_path}"
        
        start_time = time.time()
        
        with open(intrinsic_path) as f:
            data = json.load(f)
        
        load_time = time.time() - start_time
        
        assert load_time < self.MAX_LOAD_TIME_SECONDS, \
            f"Loading intrinsic_calibration.json took {load_time:.3f}s, " \
            f"exceeds limit of {self.MAX_LOAD_TIME_SECONDS}s"
        
        print(f"\nLoaded intrinsic_calibration.json in {load_time:.3f}s")
        print(f"File size: {intrinsic_path.stat().st_size / 1024:.1f} KB")
        print(f"Number of methods: {len([k for k in data.keys() if k != '_metadata'])}")
    
    def test_load_executors_methods_performance(self, executors_path):
        """Load executors_methods.json performance"""
        assert executors_path.exists(), f"File not found: {executors_path}"
        
        start_time = time.time()
        
        with open(executors_path) as f:
            data = json.load(f)
        
        load_time = time.time() - start_time
        
        assert load_time < self.MAX_LOAD_TIME_SECONDS, \
            f"Loading executors_methods.json took {load_time:.3f}s, " \
            f"exceeds limit of {self.MAX_LOAD_TIME_SECONDS}s"
        
        print(f"\nLoaded executors_methods.json in {load_time:.3f}s")
        print(f"Number of executors: {len(data)}")
    
    def test_calibrate_30_executors_performance(
        self, intrinsic_path, executors_path
    ):
        """CRITICAL: Calibrate all 30 executors in < 5 seconds"""
        with open(intrinsic_path) as f:
            calibrations = json.load(f)
        
        with open(executors_path) as f:
            executors = json.load(f)
        
        assert len(executors) == 30, f"Expected 30 executors, found {len(executors)}"
        
        start_time = time.time()
        
        calibrated_count = 0
        for executor in executors:
            for method in executor["methods"]:
                method_id = f"{method['class']}.{method['method']}"
                
                if method_id in calibrations:
                    calibration = calibrations[method_id]
                    
                    _ = calibration.get("status")
                    _ = calibration.get("b_theory")
                    _ = calibration.get("b_impl")
                    _ = calibration.get("b_deploy")
                    
                    calibrated_count += 1
        
        calibration_time = time.time() - start_time
        
        assert calibration_time < self.MAX_30_EXECUTORS_SECONDS, \
            f"Calibrating 30 executors took {calibration_time:.3f}s, " \
            f"exceeds limit of {self.MAX_30_EXECUTORS_SECONDS}s"
        
        print(f"\nCalibrated {calibrated_count} methods across 30 executors in {calibration_time:.3f}s")
        print(f"Average: {calibration_time / 30:.3f}s per executor")
    
    def test_calibrate_200_methods_performance(self, intrinsic_path):
        """CRITICAL: Calibrate 200 methods in < 30 seconds"""
        with open(intrinsic_path) as f:
            calibrations = json.load(f)
        
        methods = [k for k in calibrations.keys() if k != "_metadata"]
        
        if len(methods) < 200:
            pytest.skip(f"Only {len(methods)} methods available, need 200 for benchmark")
        
        test_methods = methods[:200]
        
        start_time = time.time()
        
        for method_id in test_methods:
            calibration = calibrations[method_id]
            
            _ = calibration.get("status")
            _ = calibration.get("b_theory", 0.0)
            _ = calibration.get("b_impl", 0.0)
            _ = calibration.get("b_deploy", 0.0)
            
            if calibration.get("status") == "computed":
                _ = calibration.get("evidence", {})
        
        calibration_time = time.time() - start_time
        
        assert calibration_time < self.MAX_200_METHODS_SECONDS, \
            f"Calibrating 200 methods took {calibration_time:.3f}s, " \
            f"exceeds limit of {self.MAX_200_METHODS_SECONDS}s"
        
        print(f"\nCalibrated 200 methods in {calibration_time:.3f}s")
        print(f"Average: {calibration_time / 200 * 1000:.3f}ms per method")
    
    def test_json_parsing_overhead(self, intrinsic_path):
        """Measure JSON parsing overhead"""
        content = intrinsic_path.read_text()
        
        iterations = 10
        start_time = time.time()
        
        for _ in range(iterations):
            _ = json.loads(content)
        
        total_time = time.time() - start_time
        avg_time = total_time / iterations
        
        print(f"\nJSON parsing: {avg_time * 1000:.3f}ms per parse (avg of {iterations})")
    
    def test_calibration_lookup_performance(self, intrinsic_path):
        """Measure calibration lookup performance"""
        with open(intrinsic_path) as f:
            calibrations = json.load(f)
        
        methods = [k for k in calibrations.keys() if k != "_metadata"]
        
        if not methods:
            pytest.skip("No methods in calibration file")
        
        iterations = 10000
        test_method = methods[0]
        
        start_time = time.time()
        
        for _ in range(iterations):
            _ = calibrations.get(test_method)
        
        total_time = time.time() - start_time
        avg_time = total_time / iterations
        
        print(f"\nDictionary lookup: {avg_time * 1000000:.3f}μs per lookup (avg of {iterations})")
    
    def test_file_size_reasonable(self, intrinsic_path):
        """Verify intrinsic_calibration.json size is reasonable"""
        MAX_SIZE_MB = 10
        
        size_bytes = intrinsic_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        
        assert size_mb < MAX_SIZE_MB, \
            f"intrinsic_calibration.json is {size_mb:.2f}MB, exceeds {MAX_SIZE_MB}MB limit"
        
        print(f"\nFile size: {size_mb:.2f}MB")
    
    def test_concurrent_access_simulation(self, intrinsic_path):
        """Simulate concurrent access to calibration data"""
        import threading
        
        results = []
        
        def load_calibrations():
            with open(intrinsic_path) as f:
                data = json.load(f)
            results.append(len(data))
        
        threads = []
        num_threads = 5
        
        start_time = time.time()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=load_calibrations)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        assert len(results) == num_threads, \
            f"Expected {num_threads} results, got {len(results)}"
        
        print(f"\n{num_threads} concurrent loads completed in {total_time:.3f}s")
    
    def test_memory_footprint(self, intrinsic_path):
        """Estimate memory footprint of calibration data"""
        import sys
        
        with open(intrinsic_path) as f:
            data = json.load(f)
        
        size_estimate = sys.getsizeof(data)
        
        for key, value in data.items():
            size_estimate += sys.getsizeof(key)
            size_estimate += sys.getsizeof(value)
            
            if isinstance(value, dict):
                for k, v in value.items():
                    size_estimate += sys.getsizeof(k) + sys.getsizeof(v)
        
        size_mb = size_estimate / (1024 * 1024)
        
        print(f"\nEstimated memory footprint: {size_mb:.2f}MB")
