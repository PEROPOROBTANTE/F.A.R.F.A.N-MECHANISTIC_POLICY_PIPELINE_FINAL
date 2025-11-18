"""
Canonical Method Catalog - AUTO-GENERATED

This module provides the canonical, authoritative registry of all methods
in the policy analysis system. It is derived from:
    config/rules/METODOS/catalogo_completo_canonico.json

STRICT RULES:
1. This is the SINGLE SOURCE OF TRUTH for method identifiers and signatures
2. NO modifications without updating the source JSON
3. Local usage that conflicts with this catalog is WRONG
4. All aliases, misspellings, and variants must be normalized to canonical forms

Generated from catalog version: 3.0.0
Total canonical methods: 593
"""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class MethodComplexity(Enum):
    """Canonical complexity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class MethodPriority(Enum):
    """Canonical priority levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ExecutionRequirements:
    """Execution requirements for a method"""
    computational: str  # LOW, MEDIUM, HIGH
    memory: str  # LOW, MEDIUM, HIGH
    io_bound: bool
    stateful: bool


@dataclass(frozen=True)
class CanonicalMethod:
    """
    Canonical method definition.

    This is the authoritative definition of a method in the system.
    All references to this method MUST use these exact identifiers.
    """
    class_name: str
    method_name: str
    file: str
    signature: str
    complexity: MethodComplexity
    priority: MethodPriority
    line_number: int
    aptitude_score: float
    execution_requirements: ExecutionRequirements
    dependencies: list[str]
    prerequisites: list[str]
    risks: list[str]
    docstring: str
    decorators: list[str]

    @property
    def fqn(self) -> str:
        """Fully qualified name: ClassName.method_name"""
        return f"{self.class_name}.{self.method_name}"

    @property
    def catalog_key(self) -> tuple:
        """Canonical tuple key for lookups"""
        return (self.class_name, self.method_name)


class CanonicalMethodCatalog:
    """
    The canonical method catalog.

    This class provides programmatic access to the authoritative method registry.
    It enforces strict canonicalization and rejects any undefined methods.
    """

    def __init__(self) -> None:
        self._methods: dict[tuple, CanonicalMethod] = {}
        self._by_class: dict[str, list[CanonicalMethod]] = {}
        self._by_file: dict[str, list[CanonicalMethod]] = {}
        self._metadata: dict = {}
        self._summary: dict = {}
        self._load_catalog()

    def find_repo_root(self, start_path: Path) -> Path:
        """Find the repository root by looking for .git or config directory"""
        current = start_path.resolve()
        while current != current.parent:
            if (current / ".git").exists() or (current / "config").exists():
                return current
            current = current.parent
        raise FileNotFoundError("Could not locate repository root")

    def _load_catalog(self) -> None:
        """Load the canonical catalog from JSON"""
        repo_root = self.find_repo_root(Path(__file__))
        catalog_path = repo_root / "config" / "rules" / "METODOS" / "catalogo_completo_canonico.json"

        if not catalog_path.exists():
            raise FileNotFoundError(
                f"Canonical catalog not found at {catalog_path}. "
                "Cannot proceed without the authoritative method registry."
            )

        with open(catalog_path, encoding='utf-8') as f:
            data = json.load(f)

        self._metadata = data.get('metadata', {})
        self._summary = data.get('summary', {})

        # Build method registry
        for file_name, file_data in data.get('files', {}).items():
            for method_data in file_data.get('methods', []):
                method = self._parse_method(method_data, file_name)

                # Register by canonical key
                # Note: catalog may have duplicates from different files
                # Use the first occurrence as canonical
                key = method.catalog_key
                if key not in self._methods:
                    self._methods[key] = method

                # Index by class
                if method.class_name not in self._by_class:
                    self._by_class[method.class_name] = []
                self._by_class[method.class_name].append(method)

                # Index by file
                if file_name not in self._by_file:
                    self._by_file[file_name] = []
                self._by_file[file_name].append(method)

    def _parse_method(self, method_data: dict, file_name: str) -> CanonicalMethod:
        """Parse method data into CanonicalMethod"""
        exec_req_data = method_data.get('execution_requirements', {})
        exec_req = ExecutionRequirements(
            computational=exec_req_data.get('computational', 'UNKNOWN'),
            memory=exec_req_data.get('memory', 'UNKNOWN'),
            io_bound=exec_req_data.get('io_bound', False),
            stateful=exec_req_data.get('stateful', False),
        )

        try:
            complexity = MethodComplexity(method_data.get('complexity', 'UNKNOWN'))
        except ValueError:
            complexity = MethodComplexity.UNKNOWN

        try:
            priority = MethodPriority(method_data.get('priority', 'UNKNOWN'))
        except ValueError:
            priority = MethodPriority.UNKNOWN

        return CanonicalMethod(
            class_name=method_data.get('class', ''),
            method_name=method_data.get('method_name', ''),
            file=file_name,
            signature=method_data.get('signature', ''),
            complexity=complexity,
            priority=priority,
            line_number=method_data.get('line_number', 0),
            aptitude_score=method_data.get('aptitude_score', 0.0),
            execution_requirements=exec_req,
            dependencies=method_data.get('dependencies', []),
            prerequisites=method_data.get('prerequisites', []),
            risks=method_data.get('risks', []),
            docstring=method_data.get('docstring', 'No documentation available'),
            decorators=method_data.get('decorators', []),
        )

    def get_method(self, class_name: str, method_name: str) -> CanonicalMethod | None:
        """
        Retrieve a canonical method definition.

        Args:
            class_name: Exact class name
            method_name: Exact method name

        Returns:
            CanonicalMethod if found, None otherwise
        """
        return self._methods.get((class_name, method_name))

    def is_canonical(self, class_name: str, method_name: str) -> bool:
        """Check if a method is in the canonical catalog"""
        return (class_name, method_name) in self._methods

    def get_methods_by_class(self, class_name: str) -> list[CanonicalMethod]:
        """Get all canonical methods for a class"""
        return self._by_class.get(class_name, [])

    def get_methods_by_file(self, file_name: str) -> list[CanonicalMethod]:
        """Get all canonical methods from a file"""
        return self._by_file.get(file_name, [])

    def all_methods(self) -> list[CanonicalMethod]:
        """Return all canonical methods"""
        return list(self._methods.values())

    def all_classes(self) -> set[str]:
        """Return all canonical class names"""
        return set(self._by_class.keys())

    def all_files(self) -> set[str]:
        """Return all canonical file names"""
        return set(self._by_file.keys())

    @property
    def total_methods(self) -> int:
        """Total number of canonical methods"""
        return len(self._methods)

    @property
    def catalog_version(self) -> str:
        """Catalog version"""
        return self._metadata.get('version', 'unknown')

    @property
    def generated_at(self) -> str:
        """Catalog generation timestamp"""
        return self._metadata.get('generated_at', 'unknown')

    def validate_method_reference(self, class_name: str, method_name: str) -> bool:
        """
        Validate that a method reference matches the canonical catalog.

        Raises:
            ValueError: If method is not in canonical catalog

        Returns:
            True if valid
        """
        if not self.is_canonical(class_name, method_name):
            raise ValueError(
                f"Method {class_name}.{method_name} is NOT in the canonical catalog. "
                f"This is a DEFECT. Either:\n"
                f"  1. The method name/class is misspelled (fix the reference)\n"
                f"  2. The method is new (add to catalog first)\n"
                f"  3. The catalog is outdated (regenerate it)\n"
                f"Canonical catalog has {self.total_methods} methods. "
                f"Use CATALOG.all_classes() to see available classes."
            )
        return True

    def get_summary_stats(self) -> dict:
        """Get summary statistics about the catalog"""
        return {
            "total_methods": self.total_methods,
            "total_classes": len(self.all_classes()),
            "total_files": len(self.all_files()),
            "by_complexity": self._summary.get('by_complexity', {}),
            "by_priority": self._summary.get('by_priority', {}),
            "version": self.catalog_version,
            "generated_at": self.generated_at,
        }


# Global singleton instance
CATALOG = CanonicalMethodCatalog()


def get_canonical_method(class_name: str, method_name: str) -> CanonicalMethod | None:
    """
    Get a canonical method definition.

    This is the primary entry point for method lookups.

    Args:
        class_name: Exact canonical class name
        method_name: Exact canonical method name

    Returns:
        CanonicalMethod if found, None otherwise
    """
    return CATALOG.get_method(class_name, method_name)


def validate_method_is_canonical(class_name: str, method_name: str) -> bool:
    """
    Validate that a method is in the canonical catalog.

    Raises ValueError if not found.
    """
    return CATALOG.validate_method_reference(class_name, method_name)


def get_all_canonical_methods() -> list[CanonicalMethod]:
    """Get all canonical methods"""
    return CATALOG.all_methods()


def get_catalog_summary() -> dict:
    """Get catalog summary statistics"""
    return CATALOG.get_summary_stats()
