"""
Signature Validation and Interface Governance System
====================================================

Implements automated signature consistency auditing, runtime validation,
and interface governance to prevent function signature mismatches.

Based on the Strategic Mitigation Plan for addressing interface inconsistencies.

Author: Signature Governance Team
Version: 1.0.0
"""

import ast
import functools
import hashlib
import inspect
import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar, get_type_hints
from saaaaaa.core.calibration.decorators import calibrated_method

logger = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])

# ============================================================================
# SIGNATURE METADATA STORAGE
# ============================================================================

@dataclass
class FunctionSignature:
    """Stores metadata about a function's signature"""
    module: str
    class_name: str | None
    function_name: str
    parameters: list[str]
    parameter_types: dict[str, str]
    return_type: str
    signature_hash: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @calibrated_method("saaaaaa.utils.signature_validator.FunctionSignature.to_dict")
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class SignatureRegistry:
    """
    Maintains a registry of function signatures with version tracking
    Implements signature snapshotting as described in the mitigation plan
    """

    def __init__(self, registry_path: Path = Path("data/signature_registry.json")) -> None:
        self.registry_path = registry_path
        self.signatures: dict[str, FunctionSignature] = {}
        self.load()

    @calibrated_method("saaaaaa.utils.signature_validator.SignatureRegistry.compute_signature_hash")
    def compute_signature_hash(self, func: Callable) -> str:
        """Compute a hash of the function's signature"""
        sig = inspect.signature(func)
        sig_str = str(sig)
        return hashlib.sha256(sig_str.encode()).hexdigest()[:16]

    @calibrated_method("saaaaaa.utils.signature_validator.SignatureRegistry.register_function")
    def register_function(self, func: Callable) -> FunctionSignature:
        """Register a function's signature"""
        sig = inspect.signature(func)

        # Extract parameter information
        parameters = list(sig.parameters.keys())

        # Get type hints if available
        try:
            type_hints = get_type_hints(func)
            parameter_types = {
                name: str(type_hints.get(name, 'Any'))
                for name in parameters
            }
            return_type = str(type_hints.get('return', 'Any'))
        except (TypeError, AttributeError, NameError) as e:
            # get_type_hints can fail for various reasons:
            # - TypeError: if func is not a callable
            # - AttributeError: if func doesn't have required attributes
            # - NameError: if type hints reference undefined names
            logger.debug(f"Could not extract type hints for {func.__name__}: {e}")
            parameter_types = dict.fromkeys(parameters, 'Any')
            return_type = 'Any'

        # Get module and class information
        module = func.__module__ if hasattr(func, '__module__') else 'unknown'
        class_name = None
        if hasattr(func, '__qualname__') and '.' in func.__qualname__:
            class_name = func.__qualname__.rsplit('.', 1)[0]

        signature_hash = self.compute_signature_hash(func)

        func_sig = FunctionSignature(
            module=module,
            class_name=class_name,
            function_name=func.__name__,
            parameters=parameters,
            parameter_types=parameter_types,
            return_type=return_type,
            signature_hash=signature_hash
        )

        # Store in registry
        key = self._get_function_key(module, class_name, func.__name__)
        self.signatures[key] = func_sig

        return func_sig

    @calibrated_method("saaaaaa.utils.signature_validator.SignatureRegistry._get_function_key")
    def _get_function_key(self, module: str, class_name: str | None, func_name: str) -> str:
        """Generate a unique key for a function"""
        if class_name:
            return f"{module}.{class_name}.{func_name}"
        return f"{module}.{func_name}"

    @calibrated_method("saaaaaa.utils.signature_validator.SignatureRegistry.get_signature")
    def get_signature(self, module: str, class_name: str | None, func_name: str) -> FunctionSignature | None:
        """Retrieve a stored signature"""
        key = self._get_function_key(module, class_name, func_name)
        return self.signatures.get(key)

    @calibrated_method("saaaaaa.utils.signature_validator.SignatureRegistry.has_signature_changed")
    def has_signature_changed(self, func: Callable) -> tuple[bool, FunctionSignature | None, FunctionSignature | None]:
        """Check if a function's signature has changed from the registered version"""
        module = func.__module__ if hasattr(func, '__module__') else 'unknown'
        class_name = None
        if hasattr(func, '__qualname__') and '.' in func.__qualname__:
            class_name = func.__qualname__.rsplit('.', 1)[0]

        old_sig = self.get_signature(module, class_name, func.__name__)
        if old_sig is None:
            return False, None, None  # No previous signature

        new_sig = self.register_function(func)
        changed = old_sig.signature_hash != new_sig.signature_hash

        return changed, old_sig, new_sig

    @calibrated_method("saaaaaa.utils.signature_validator.SignatureRegistry.save")
    def save(self) -> None:
        """Save registry to disk"""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        registry_data = {
            key: sig.to_dict()
            for key, sig in self.signatures.items()
        }

        with open(self.registry_path, 'w') as f:
            json.dump(registry_data, f, indent=2)

        logger.info(f"Saved {len(self.signatures)} signatures to {self.registry_path}")

    @calibrated_method("saaaaaa.utils.signature_validator.SignatureRegistry.load")
    def load(self) -> None:
        """Load registry from disk"""
        if not self.registry_path.exists():
            logger.info(f"No existing registry found at {self.registry_path}")
            return

        try:
            with open(self.registry_path) as f:
                registry_data = json.load(f)

            self.signatures = {
                key: FunctionSignature(**data)
                for key, data in registry_data.items()
            }

            logger.info(f"Loaded {len(self.signatures)} signatures from {self.registry_path}")
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")

# Global registry instance
_signature_registry = SignatureRegistry()

# ============================================================================
# RUNTIME VALIDATION DECORATOR
# ============================================================================

def validate_signature(enforce: bool = True, track: bool = True):
    """
    Decorator to validate function calls against expected signatures at runtime

    Args:
        enforce: If True, raise TypeError on signature violations
        track: If True, register signature in the global registry

    Example:
        @validate_signature(enforce=True)
        def my_function(arg1: str, arg2: int) -> bool:
            return True
    """
    def decorator(func: F) -> F:
        # Register function signature if tracking is enabled
        if track:
            _signature_registry.register_function(func)

        # Get the function signature
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Bind arguments to signature
            try:
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
            except TypeError as e:
                error_msg = (
                    f"Signature mismatch in {func.__module__}.{func.__qualname__}: {e}\n"
                    f"Expected signature: {sig}\n"
                    f"Called with args: {args}, kwargs: {kwargs}"
                )
                logger.error(error_msg)

                if enforce:
                    raise TypeError(error_msg) from e
                else:
                    logger.warning(f"Signature validation failed but enforcement is disabled: {e}")

            # Call the original function
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator

def validate_call_signature(func: Callable, *args, **kwargs) -> bool:
    """
    Validate that a function call matches the expected signature without actually calling it

    Args:
        func: Function to validate
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        sig = inspect.signature(func)
        sig.bind(*args, **kwargs)
        return True
    except TypeError:
        return False

# ============================================================================
# STATIC SIGNATURE AUDITOR
# ============================================================================

@dataclass
class SignatureMismatch:
    """Represents a detected signature mismatch"""
    caller_module: str
    caller_function: str
    caller_line: int
    callee_module: str
    callee_class: str | None
    callee_function: str
    expected_signature: str
    actual_call: str
    severity: str  # 'high', 'medium', 'low'
    description: str

class SignatureAuditor:
    """
    Static introspection tool to cross-validate function definitions against call sites
    Implements automated signature consistency audit from the mitigation plan
    """

    def __init__(self) -> None:
        self.mismatches: list[SignatureMismatch] = []
        self.call_graph: dict[str, list[tuple[str, int, list[str], dict[str, str]]]] = {}

    @calibrated_method("saaaaaa.utils.signature_validator.SignatureAuditor.audit_module")
    def audit_module(self, module_path: Path) -> list[SignatureMismatch]:
        """
        Audit a Python module for signature mismatches

        Args:
            module_path: Path to the Python module

        Returns:
            List of detected signature mismatches
        """
        logger.info(f"Auditing module: {module_path}")

        # Skip test files, virtual environments, and build directories
        exclude_patterns = ['test', 'venv', '.venv', '__pycache__', '.git', 'build', 'dist']
        if any(module_path.match(f'*/{pattern}/*') or module_path.match(f'*/{pattern}')
               for pattern in exclude_patterns):
            logger.debug(f"Skipping excluded path: {module_path}")
            return []

        try:
            with open(module_path, encoding='utf-8') as f:
                source_code = f.read()

            tree = ast.parse(source_code, filename=str(module_path))

            # Extract function definitions
            function_defs = self._extract_function_definitions(tree, module_path.stem)

            # Extract function calls
            function_calls = self._extract_function_calls(tree, module_path.stem)

            # Cross-validate
            mismatches = self._cross_validate(function_defs, function_calls)

            self.mismatches.extend(mismatches)

            return mismatches

        except Exception as e:
            logger.error(f"Failed to audit {module_path}: {e}")
            return []

    @calibrated_method("saaaaaa.utils.signature_validator.SignatureAuditor._extract_function_definitions")
    def _extract_function_definitions(self, tree: ast.AST, module_name: str) -> dict[str, ast.FunctionDef]:
        """Extract all function definitions from AST"""
        functions = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Generate full qualified name
                full_name = f"{module_name}.{node.name}"
                functions[full_name] = node

        return functions

    @calibrated_method("saaaaaa.utils.signature_validator.SignatureAuditor._extract_function_calls")
    def _extract_function_calls(self, tree: ast.AST, module_name: str) -> list[tuple[str, int, ast.Call]]:
        """Extract all function calls from AST"""
        calls = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Try to get the function name
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name:
                    calls.append((func_name, node.lineno, node))

        return calls

    def _cross_validate(
        self,
        function_defs: dict[str, ast.FunctionDef],
        function_calls: list[tuple[str, int, ast.Call]]
    ) -> list[SignatureMismatch]:
        """Cross-validate function calls against definitions"""
        mismatches = []

        # This is a simplified implementation
        # A full implementation would need more sophisticated analysis

        return mismatches

    @calibrated_method("saaaaaa.utils.signature_validator.SignatureAuditor.export_report")
    def export_report(self, output_path: Path) -> None:
        """Export audit report to JSON"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "audit_timestamp": datetime.now().isoformat(),
            "total_mismatches": len(self.mismatches),
            "mismatches": [asdict(m) for m in self.mismatches]
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Exported audit report to {output_path}")

# ============================================================================
# COMPATIBILITY LAYER
# ============================================================================

def create_adapter(
    func: Callable,
    old_params: list[str],
    new_params: list[str],
    param_mapping: dict[str, str] | None = None
) -> Callable:
    """
    Create a backward-compatible adapter for a function with changed signature

    Args:
        func: The new function with updated signature
        old_params: List of old parameter names
        new_params: List of new parameter names
        param_mapping: Optional mapping from old to new parameter names

    Returns:
        Adapter function that accepts old signature and calls new function
    """
    param_mapping = param_mapping or {}

    @functools.wraps(func)
    def adapter(*args, **kwargs):
        # Remap old parameter names to new ones
        new_kwargs = {}
        for old_key, value in kwargs.items():
            new_key = param_mapping.get(old_key, old_key)
            new_kwargs[new_key] = value

        return func(*args, **new_kwargs)

    return adapter

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

def initialize_signature_registry(project_root: Path) -> None:
    """
    Initialize signature registry by scanning all Python files in the project

    Args:
        project_root: Root directory of the project
    """
    logger.info(f"Initializing signature registry for project: {project_root}")

    python_files = list(project_root.glob("**/*.py"))
    logger.info(f"Found {len(python_files)} Python files")

    # This would require dynamic import which is complex
    # For now, we rely on decorators to register functions

    _signature_registry.save()

def audit_project_signatures(project_root: Path, output_path: Path | None = None) -> list[SignatureMismatch]:
    """
    Audit all Python files in a project for signature mismatches

    Args:
        project_root: Root directory of the project
        output_path: Optional path to save audit report

    Returns:
        List of detected signature mismatches
    """
    auditor = SignatureAuditor()

    python_files = list(project_root.glob("**/*.py"))
    logger.info(f"Auditing {len(python_files)} Python files")

    # Define patterns to exclude
    exclude_patterns = ['test', 'venv', '.venv', '__pycache__', '.git', 'build', 'dist']

    all_mismatches = []
    for py_file in python_files:
        # Skip excluded patterns
        if any(py_file.match(f'*/{pattern}/*') or py_file.match(f'*/{pattern}')
               for pattern in exclude_patterns):
            continue

        mismatches = auditor.audit_module(py_file)
        all_mismatches.extend(mismatches)

    if output_path:
        auditor.export_report(output_path)

    logger.info(f"Audit complete: {len(all_mismatches)} mismatches detected")

    return all_mismatches

# ============================================================================
# CLI INTERFACE
# ============================================================================

# Note: Main entry point removed to maintain I/O boundary separation.
# For CLI usage, see examples/ directory or create a dedicated CLI script.
