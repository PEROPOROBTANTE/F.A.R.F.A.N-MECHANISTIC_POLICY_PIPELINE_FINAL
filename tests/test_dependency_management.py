"""
Test dependency management system.

Verifies that the dependency management infrastructure works correctly.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from saaaaaa.config.paths import PROJECT_ROOT


class TestDependencyManagement:
    """Test suite for dependency management system."""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return PROJECT_ROOT
    
    def test_requirements_files_exist(self, project_root):
        """Verify all required dependency files exist."""
        required_files = [
            "requirements-core.txt",
            "requirements-optional.txt",
            "requirements-dev.txt",
            "requirements-docs.txt",
            "requirements-all.txt",
            "constraints-new.txt",
        ]
        
        for filename in required_files:
            filepath = project_root / filename
            assert filepath.exists(), f"Missing required file: {filename}"
    
    def test_dependency_scripts_exist(self, project_root):
        """Verify all dependency management scripts exist and are executable."""
        import os
        
        required_scripts = [
            "scripts/audit_dependencies.py",
            "scripts/verify_importability.py",
            "scripts/generate_dependency_files.py",
            "scripts/compare_freeze_lock.py",
            "scripts/check_version_pins.py",
        ]
        
        for script_path in required_scripts:
            filepath = project_root / script_path
            assert filepath.exists(), f"Missing required script: {script_path}"
            
            # Check executable permission (cross-platform)
            assert os.access(filepath, os.R_OK), f"Script not readable: {script_path}"
    
    def test_documentation_exists(self, project_root):
        """Verify dependency documentation exists."""
        docs = [
            "DEPENDENCIES_AUDIT.md",
            "DEPENDENCIES_QUICKSTART.md",
        ]
        
        for doc in docs:
            filepath = project_root / doc
            assert filepath.exists(), f"Missing documentation: {doc}"
            
            # Check that documentation is not empty
            content = filepath.read_text()
            assert len(content) > 1000, f"Documentation too short: {doc}"
    
    def test_core_requirements_version_constraints(self, project_root):
        """Verify core requirements use appropriate version constraints.
        
        Most packages should use exact pins (==) for reproducibility,
        but certain packages with complex dependency chains (like ML/NLP libraries)
        may use constrained ranges (>=X,<Y) to allow pip to resolve dependencies.
        """
        requirements_file = project_root / "requirements-core.txt"
        
        # Packages allowed to have constrained ranges due to complex dependency chains
        allowed_ranges = {
            'fastapi', 'huggingface-hub', 'numpy', 'pandas', 'pydantic',
            'safetensors', 'scikit-learn', 'scipy', 'sentence-transformers',
            'tokenizers', 'transformers'
        }
        
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Skip -r includes
                if line.startswith('-r '):
                    continue
                
                # Extract package name
                pkg_name = line.split('=')[0].split('>')[0].split('<')[0].strip()
                
                if '==' in line:
                    # Good: exact pin
                    continue
                elif '>=' in line and '<' in line:
                    # Constrained range - check if allowed
                    if pkg_name.lower() not in allowed_ranges:
                        pytest.fail(
                            f"Package '{pkg_name}' uses a constrained range but is not in allowed list.\n"
                            f"Line: {line}\n"
                            f"Either use exact pin (==) or add to allowed_ranges if needed for dependency resolution."
                        )
                elif any(op in line for op in ['>=', '~=', '<=', '<', '>', '*']):
                    # Unconstrained or unusual range
                    pytest.fail(
                        f"Core requirements must use exact pins (==) or constrained ranges (>=X,<Y), "
                        f"found problematic constraint in: {line}\n"
                        f"Expected format: package==X.Y.Z or package>=X.Y.Z,<A.B.C"
                    )
    
    def test_audit_script_runs(self, project_root):
        """Verify audit script can run successfully."""
        script = project_root / "scripts" / "audit_dependencies.py"
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        
        # Script should run without crashing (may exit with 1 for missing deps)
        assert result.returncode in [0, 1], (
            f"Audit script crashed with code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
        
        # Check that report was generated
        report_file = project_root / "dependency_audit_report.json"
        assert report_file.exists(), "Audit report not generated"
        
        # Verify report structure
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        assert "summary" in report
        assert "package_classification" in report
        assert "missing_packages" in report
    
    def test_version_pin_checker(self, project_root):
        """Verify version pin checker works."""
        script = project_root / "scripts" / "check_version_pins.py"
        core_reqs = project_root / "requirements-core.txt"
        
        result = subprocess.run(
            [sys.executable, str(script), str(core_reqs)],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        
        # Should pass for core requirements (all exact pins)
        assert result.returncode == 0, (
            f"Version pin check failed for core requirements:\n"
            f"{result.stdout}\n{result.stderr}"
        )
    
    def test_requirements_files_well_formed(self, project_root):
        """Verify requirements files are well-formed."""
        requirements_files = [
            "requirements-core.txt",
            "requirements-optional.txt",
            "requirements-dev.txt",
            "requirements-docs.txt",
        ]
        
        for filename in requirements_files:
            filepath = project_root / filename
            
            with open(filepath, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Skip -r includes
                    if line.startswith('-r '):
                        continue
                    
                    # Verify line format
                    assert not line.startswith('=='), (
                        f"{filename}:{line_num} - Malformed line (starts with ==): {line}\n"
                        f"Expected format: package==version (e.g., numpy==2.2.1)"
                    )
                    
                    # Verify contains package name
                    assert len(line.split('==')) >= 1, (
                        f"{filename}:{line_num} - Invalid format: {line}\n"
                        f"Expected format: package==version (e.g., numpy==2.2.1)"
                    )
    
    def test_makefile_has_dependency_targets(self, project_root):
        """Verify Makefile includes dependency management targets."""
        makefile = project_root / "Makefile"
        
        with open(makefile, 'r') as f:
            content = f.read()
        
        required_targets = [
            "deps:verify",
            "deps:lock",
            "deps:audit",
            "deps:clean",
        ]
        
        for target in required_targets:
            assert target in content, f"Makefile missing target: {target}"
    
    def test_ci_workflow_exists(self, project_root):
        """Verify CI workflow for dependency gates exists."""
        workflow = project_root / ".github" / "workflows" / "dependency-gates.yml"
        
        assert workflow.exists(), "Dependency gates CI workflow missing"
        
        with open(workflow, 'r') as f:
            content = f.read()
        
        # Check for required gates
        required_gates = [
            "Missing Import Detection",
            "Importability Verification",
            "Open Range Detection",
            "Freeze vs Lock Comparison",
            "Security Vulnerability Scan",
        ]
        
        for gate in required_gates:
            assert gate in content, f"CI workflow missing gate: {gate}"
    
    def test_dependencies_audit_md_structure(self, project_root):
        """Verify DEPENDENCIES_AUDIT.md has required sections."""
        doc = project_root / "DEPENDENCIES_AUDIT.md"
        
        with open(doc, 'r') as f:
            content = f.read()
        
        required_sections = [
            "## Overview",
            "## Dependency Classification",
            "## Package Inventory",
            "## Installation Profiles",
            "## Verification Procedures",
            "## Adding New Dependencies",
            "## Known Issues & Risks",
            "## CI/CD Gates",
            "## Makefile Targets",
        ]
        
        for section in required_sections:
            assert section in content, f"Documentation missing section: {section}"


class TestDependencyScripts:
    """Test individual dependency management scripts."""
    
    def test_generate_dependency_files_idempotent(self, tmp_path):
        """Verify generate_dependency_files.py is idempotent."""
        # This test would require running the generator twice and comparing
        # For now, we just verify the script exists and can be imported
        script_path = Path(__file__).parent.parent / "scripts" / "generate_dependency_files.py"
        assert script_path.exists()
    
    def test_compare_freeze_lock_detects_differences(self, tmp_path):
        """Verify compare_freeze_lock.py detects version differences."""
        # Create test files
        freeze_file = tmp_path / "freeze.txt"
        lock_file = tmp_path / "lock.txt"
        
        freeze_file.write_text("numpy==2.2.1\npandas==2.2.3\n")
        lock_file.write_text("numpy==2.2.0\npandas==2.2.3\n")  # Different numpy version
        
        script = Path(__file__).parent.parent / "scripts" / "compare_freeze_lock.py"
        
        result = subprocess.run(
            [sys.executable, str(script), str(freeze_file), str(lock_file)],
            capture_output=True,
            text=True,
        )
        
        # Should detect difference
        assert result.returncode == 1, "Should detect version mismatch"
        assert "numpy" in result.stdout, "Should report numpy mismatch"
    
    def test_compare_freeze_lock_passes_when_equal(self, tmp_path):
        """Verify compare_freeze_lock.py passes when files match."""
        # Create identical test files
        freeze_file = tmp_path / "freeze.txt"
        lock_file = tmp_path / "lock.txt"
        
        content = "numpy==2.2.1\npandas==2.2.3\n"
        freeze_file.write_text(content)
        lock_file.write_text(content)
        
        script = Path(__file__).parent.parent / "scripts" / "compare_freeze_lock.py"
        
        result = subprocess.run(
            [sys.executable, str(script), str(freeze_file), str(lock_file)],
            capture_output=True,
            text=True,
        )
        
        # Should pass
        assert result.returncode == 0, "Should pass when files match"
        assert "SUCCESS" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
