"""Method Registry with lazy instantiation and injection pattern.

This module implements a method injection factory that:
1. Loads only the methods needed (not full classes)
2. Instantiates classes lazily (only when first method is called)
3. Caches instances for reuse
4. Isolates errors per method (failures don't cascade)
5. Allows direct function injection (bypassing classes)

Architecture:
    MethodRegistry
        ├─ _class_paths: mapping of class names to import paths
        ├─ _instance_cache: lazily instantiated class instances
        ├─ _direct_methods: directly injected functions
        └─ get_method(): returns callable for (class_name, method_name)

Benefits:
- No upfront class loading (lightweight imports)
- Failed classes don't block working methods
- Direct function injection for custom implementations
- Instance reuse through caching
"""
from __future__ import annotations

import logging
import threading
from importlib import import_module
from typing import Any, Callable

logger = logging.getLogger(__name__)


class MethodRegistryError(RuntimeError):
    """Raised when a method cannot be retrieved."""


class MethodRegistry:
    """Registry for lazy method injection without full class instantiation."""

    def __init__(self, class_paths: dict[str, str] | None = None) -> None:
        """Initialize the method registry.

        Args:
            class_paths: Optional mapping of class names to import paths.
                        If None, uses default paths from class_registry.
        """
        # Import class paths from existing registry
        if class_paths is None:
            from .class_registry import get_class_paths
            class_paths = dict(get_class_paths())

        self._class_paths = class_paths
        self._instance_cache: dict[str, Any] = {}
        self._direct_methods: dict[tuple[str, str], Callable[..., Any]] = {}
        self._failed_classes: set[str] = set()
        self._lock = threading.Lock()

        # Special instantiation rules (from original MethodExecutor)
        self._special_instantiation: dict[str, Callable[[type], Any]] = {}

    def inject_method(
        self,
        class_name: str,
        method_name: str,
        method: Callable[..., Any],
    ) -> None:
        """Directly inject a method without needing a class.

        This allows bypassing class instantiation entirely.

        Args:
            class_name: Virtual class name for routing
            method_name: Method name
            method: Callable to inject
        """
        key = (class_name, method_name)
        self._direct_methods[key] = method
        logger.info(
            "method_injected_directly",
            class_name=class_name,
            method_name=method_name,
        )

    def register_instantiation_rule(
        self,
        class_name: str,
        instantiator: Callable[[type], Any],
    ) -> None:
        """Register special instantiation logic for a class.

        Args:
            class_name: Class name requiring special instantiation
            instantiator: Function that takes class type and returns instance
        """
        self._special_instantiation[class_name] = instantiator
        logger.debug(
            "instantiation_rule_registered",
            class_name=class_name,
        )

    def _load_class(self, class_name: str) -> type:
        """Load a class type from import path.

        Args:
            class_name: Name of class to load

        Returns:
            Class type

        Raises:
            MethodRegistryError: If class cannot be loaded
        """
        if class_name not in self._class_paths:
            raise MethodRegistryError(
                f"Class '{class_name}' not found in registry paths"
            )

        path = self._class_paths[class_name]
        module_name, _, attr_name = path.rpartition(".")

        if not module_name:
            raise MethodRegistryError(
                f"Invalid path for '{class_name}': {path}"
            )

        try:
            module = import_module(module_name)
            cls = getattr(module, attr_name)

            if not isinstance(cls, type):
                raise MethodRegistryError(
                    f"'{class_name}' is not a class: {type(cls).__name__}"
                )

            return cls

        except ImportError as exc:
            raise MethodRegistryError(
                f"Cannot import class '{class_name}' from {path}: {exc}"
            ) from exc
        except AttributeError as exc:
            raise MethodRegistryError(
                f"Class '{attr_name}' not found in module {module_name}: {exc}"
            ) from exc

    def _instantiate_class(self, class_name: str, cls: type) -> Any:
        """Instantiate a class using special rules or default constructor.

        Args:
            class_name: Name of class (for special rule lookup)
            cls: Class type to instantiate

        Returns:
            Instance of the class

        Raises:
            MethodRegistryError: If instantiation fails
        """
        # Use special instantiation rule if registered
        if class_name in self._special_instantiation:
            try:
                instantiator = self._special_instantiation[class_name]
                instance = instantiator(cls)
                logger.debug(
                    "class_instantiated_with_special_rule",
                    class_name=class_name,
                )
                return instance
            except Exception as exc:
                raise MethodRegistryError(
                    f"Special instantiation failed for '{class_name}': {exc}"
                ) from exc

        # Default instantiation (no-args constructor)
        try:
            instance = cls()
            logger.debug(
                "class_instantiated_default",
                class_name=class_name,
            )
            return instance
        except Exception as exc:
            raise MethodRegistryError(
                f"Default instantiation failed for '{class_name}': {exc}"
            ) from exc

    def _get_instance(self, class_name: str) -> Any:
        """Get or create instance of a class (lazy + cached).

        Args:
            class_name: Name of class to instantiate

        Returns:
            Instance of the class

        Raises:
            MethodRegistryError: If class cannot be instantiated
        """
        # Check if already failed
        if class_name in self._failed_classes:
            raise MethodRegistryError(
                f"Class '{class_name}' previously failed to instantiate"
            )

        # Use a lock to ensure thread-safe instantiation
        with self._lock:
            # Double-check if another thread instantiated it while waiting for the lock
            if class_name in self._instance_cache:
                return self._instance_cache[class_name]

            # Load and instantiate class
            try:
                cls = self._load_class(class_name)
                instance = self._instantiate_class(class_name, cls)
                self._instance_cache[class_name] = instance
                logger.info(
                    "class_instantiated_lazy",
                    class_name=class_name,
                )
                return instance

            except MethodRegistryError:
                # Mark as failed to avoid repeated attempts
                self._failed_classes.add(class_name)
                raise

    def get_method(
        self,
        class_name: str,
        method_name: str,
    ) -> Callable[..., Any]:
        """Get method callable with lazy instantiation.

        This is the main entry point for retrieving methods.

        Args:
            class_name: Name of class containing the method
            method_name: Name of method to retrieve

        Returns:
            Callable method (bound or injected)

        Raises:
            MethodRegistryError: If method cannot be retrieved
        """
        # Check for directly injected method first
        key = (class_name, method_name)
        if key in self._direct_methods:
            logger.debug(
                "method_retrieved_direct",
                class_name=class_name,
                method_name=method_name,
            )
            return self._direct_methods[key]

        # Get instance (lazy) and retrieve method
        try:
            instance = self._get_instance(class_name)
            method = getattr(instance, method_name)

            if not callable(method):
                raise MethodRegistryError(
                    f"'{class_name}.{method_name}' is not callable"
                )

            logger.debug(
                "method_retrieved_from_instance",
                class_name=class_name,
                method_name=method_name,
            )
            return method

        except AttributeError as exc:
            raise MethodRegistryError(
                f"Method '{method_name}' not found on class '{class_name}'"
            ) from exc

    def has_method(self, class_name: str, method_name: str) -> bool:
        """Check if a method is available (without instantiating).

        Args:
            class_name: Name of class
            method_name: Name of method

        Returns:
            True if method exists (or is directly injected)
        """
        # Check direct injection
        key = (class_name, method_name)
        if key in self._direct_methods:
            return True

        # Check if class is known and not failed
        if class_name in self._failed_classes:
            return False

        if class_name not in self._class_paths:
            return False

        # If instance exists, check method
        if class_name in self._instance_cache:
            instance = self._instance_cache[class_name]
            return hasattr(instance, method_name)

        # Otherwise, assume it exists (lazy check)
        # Full validation happens on first get_method() call
        return True

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics.

        Returns:
            Dictionary with registry stats
        """
        return {
            "total_classes_registered": len(self._class_paths),
            "instantiated_classes": len(self._instance_cache),
            "failed_classes": len(self._failed_classes),
            "direct_methods_injected": len(self._direct_methods),
            "instantiated_class_names": list(self._instance_cache.keys()),
            "failed_class_names": list(self._failed_classes),
        }


def setup_default_instantiation_rules(registry: MethodRegistry) -> None:
    """Setup default special instantiation rules.

    These rules replicate the logic from the original MethodExecutor
    for classes that need non-default instantiation.

    Args:
        registry: MethodRegistry to configure
    """
    # MunicipalOntology - shared instance pattern
    ontology_instance = None

    def instantiate_ontology(cls: type) -> Any:
        nonlocal ontology_instance
        if ontology_instance is None:
            ontology_instance = cls()
        return ontology_instance

    registry.register_instantiation_rule("MunicipalOntology", instantiate_ontology)

    # SemanticAnalyzer, PerformanceAnalyzer, TextMiningEngine - need ontology
    def instantiate_with_ontology(cls: type) -> Any:
        if ontology_instance is None:
            raise MethodRegistryError(
                f"Cannot instantiate {cls.__name__}: MunicipalOntology not available"
            )
        return cls(ontology_instance)

    for class_name in ["SemanticAnalyzer", "PerformanceAnalyzer", "TextMiningEngine"]:
        registry.register_instantiation_rule(class_name, instantiate_with_ontology)

    # PolicyTextProcessor - needs ProcessorConfig
    def instantiate_policy_processor(cls: type) -> Any:
        try:
            from saaaaaa.processing.policy_processor import ProcessorConfig
            return cls(ProcessorConfig())
        except ImportError as exc:
            raise MethodRegistryError(
                "Cannot instantiate PolicyTextProcessor: ProcessorConfig unavailable"
            ) from exc

    registry.register_instantiation_rule("PolicyTextProcessor", instantiate_policy_processor)


__all__ = [
    "MethodRegistry",
    "MethodRegistryError",
    "setup_default_instantiation_rules",
]
