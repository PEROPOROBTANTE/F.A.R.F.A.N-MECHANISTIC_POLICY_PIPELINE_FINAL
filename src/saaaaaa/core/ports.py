"""
Port interfaces for dependency injection.

Ports define abstract interfaces for external interactions (I/O, time, environment).
These are implemented by adapters in the infrastructure layer.

This follows the Ports and Adapters (Hexagonal) architecture pattern:
- Ports are in the core layer (no dependencies)
- Adapters are in the infrastructure layer (can import anything)
- Core modules depend on ports (abstractions), not adapters (implementations)

Version: 1.0.0
"""

from datetime import datetime
from typing import Any, Protocol


class FilePort(Protocol):
    """Port for file system operations.

    Implementations provide access to file reading and writing.
    Core modules receive a FilePort instance via dependency injection.
    """

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read text from a file.

        Args:
            path: File path to read
            encoding: Text encoding (default: utf-8)

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file cannot be read
        """
        ...

    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """Write text to a file.

        Args:
            path: File path to write
            content: Text content to write
            encoding: Text encoding (default: utf-8)

        Raises:
            PermissionError: If file cannot be written
        """
        ...

    def read_bytes(self, path: str) -> bytes:
        """Read bytes from a file.

        Args:
            path: File path to read

        Returns:
            File contents as bytes

        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file cannot be read
        """
        ...

    def write_bytes(self, path: str, content: bytes) -> None:
        """Write bytes to a file.

        Args:
            path: File path to write
            content: Bytes content to write

        Raises:
            PermissionError: If file cannot be written
        """
        ...

    def exists(self, path: str) -> bool:
        """Check if a file or directory exists.

        Args:
            path: Path to check

        Returns:
            True if path exists, False otherwise
        """
        ...

    def mkdir(self, path: str, parents: bool = False, exist_ok: bool = False) -> None:
        """Create a directory.

        Args:
            path: Directory path to create
            parents: Create parent directories if needed
            exist_ok: Don't raise error if directory exists

        Raises:
            FileExistsError: If directory exists and exist_ok is False
        """
        ...

class JsonPort(Protocol):
    """Port for JSON serialization/deserialization.

    Separates JSON operations from file I/O for better composability.
    """

    def loads(self, text: str) -> Any:
        """Parse JSON from string.

        Args:
            text: JSON string

        Returns:
            Parsed Python object

        Raises:
            ValueError: If JSON is invalid
        """
        ...

    def dumps(self, obj: Any, indent: int | None = None) -> str:
        """Serialize object to JSON string.

        Args:
            obj: Python object to serialize
            indent: Indentation spaces (None for compact)

        Returns:
            JSON string

        Raises:
            TypeError: If object is not serializable
        """
        ...

class EnvPort(Protocol):
    """Port for environment variable access.

    Allows core modules to access configuration without direct os.environ coupling.
    """

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get environment variable.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Environment variable value or default
        """
        ...

    def get_required(self, key: str) -> str:
        """Get required environment variable.

        Args:
            key: Environment variable name

        Returns:
            Environment variable value

        Raises:
            ValueError: If environment variable is not set
        """
        ...

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get environment variable as boolean.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Boolean value (true/false/yes/no/1/0)
        """
        ...

class ClockPort(Protocol):
    """Port for time operations.

    Allows core modules to get current time without direct datetime.now() calls.
    Enables time manipulation in tests.
    """

    def now(self) -> datetime:
        """Get current datetime.

        Returns:
            Current datetime
        """
        ...

    def utcnow(self) -> datetime:
        """Get current UTC datetime.

        Returns:
            Current UTC datetime
        """
        ...

class LogPort(Protocol):
    """Port for logging operations.

    Allows core modules to log without coupling to specific logging framework.
    """

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        ...

class PortCPPIngest(Protocol):
    """Port for CPP (Canon Policy Package) ingestion.

    Ingests documents and produces Canon Policy Packages with complete provenance.
    """

    def ingest(self, input_uri: str) -> Any:
        """Ingest document from URI and produce Canon Policy Package.

        Args:
            input_uri: URI to document (file://, http://, etc.)

        Returns:
            CanonPolicyPackage with complete chunk graph and metadata

        Requires:
            - Valid input URI
            - Accessible document at URI

        Ensures:
            - chunk_graph is not None
            - policy_manifest is not None
            - provenance_completeness == 1.0
        """
        ...


class PortCPPAdapter(Protocol):
    """Port for CPP to PreprocessedDocument adaptation.

    Converts Canon Policy Package to orchestrator's PreprocessedDocument format.

    Note: CPP is the legacy name. Use PortSPCAdapter for new code.
    """

    def to_preprocessed_document(self, cpp: Any, document_id: str) -> Any:
        """Convert CPP to PreprocessedDocument.

        Args:
            cpp: Canon Policy Package from ingestion
            document_id: Unique document identifier

        Returns:
            PreprocessedDocument for orchestrator

        Requires:
            - cpp with valid chunk_graph
            - cpp.policy_manifest exists
            - document_id is non-empty

        Ensures:
            - sentence_metadata is not empty
            - resolution_index is consistent
            - provenance_completeness == 1.0
        """
        ...


class PortSPCAdapter(Protocol):
    """Port for SPC (Smart Policy Chunks) to PreprocessedDocument adaptation.

    Converts Smart Policy Chunks to orchestrator's PreprocessedDocument format.
    This is the preferred terminology for new code.
    """

    def to_preprocessed_document(self, spc: Any, document_id: str) -> Any:
        """Convert SPC to PreprocessedDocument.

        Args:
            spc: Smart Policy Chunks package from ingestion
            document_id: Unique document identifier

        Returns:
            PreprocessedDocument for orchestrator

        Requires:
            - spc with valid chunk_graph
            - spc.policy_manifest exists
            - document_id is non-empty

        Ensures:
            - sentence_metadata is not empty
            - resolution_index is consistent
            - provenance_completeness == 1.0
        """
        ...


class PortSignalsClient(Protocol):
    """Port for fetching strategic signals.

    Retrieves policy-aware signals from memory or HTTP sources.
    Sematics: None return = 304 Not Modified or circuit breaker open.
    """

    def fetch(self, policy_area: str) -> Any | None:
        """Fetch signals for policy area.

        Args:
            policy_area: Policy domain (fiscal, salud, ambiente, etc.)

        Returns:
            SignalPack if available, None if 304/breaker open

        Requires:
            - policy_area is valid PolicyArea literal

        Ensures:
            - If not None, returns valid SignalPack with version
            - None is justified (304 or breaker state)
        """
        ...


class PortSignalsRegistry(Protocol):
    """Port for signal registry with TTL and LRU.

    Manages in-memory cache of strategic signals with expiration.
    """

    def put(self, pack: Any) -> None:
        """Store signal pack in registry.

        Args:
            pack: SignalPack to store

        Requires:
            - pack is valid SignalPack
            - pack.version is present
        """
        ...

    def get(self, policy_area: str) -> dict[str, Any] | None:
        """Retrieve signals for policy area.

        Args:
            policy_area: Policy domain

        Returns:
            Signal data if cached and not expired, None otherwise
        """
        ...

    def fingerprint(self) -> str:
        """Compute registry fingerprint for drift detection.

        Returns:
            BLAKE3 hash of current registry state
        """
        ...


class PortArgRouter(Protocol):
    """Port for argument routing and validation.

    Routes method calls with strict parameter validation.
    """

    def route(
        self,
        class_name: str,
        method_name: str,
        payload: dict[str, Any]
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """Route method call to (args, kwargs).

        Args:
            class_name: Target class name
            method_name: Target method name
            payload: Input parameters

        Returns:
            Tuple of (args, kwargs) for method call

        Requires:
            - class_name exists in registry
            - method_name exists on class
            - method signature is known or has **kwargs

        Ensures:
            - No silent parameter drops
            - All required args present
            - No unexpected kwargs (unless **kwargs in signature)
        """
        ...


class PortExecutor(Protocol):
    """Port for executing methods with configuration.

    Executes methods with injected executor config and signals.
    """

    def run(self, prompt: str, overrides: Any | None = None) -> Any:
        """Execute with prompt and optional config overrides.

        Args:
            prompt: Execution prompt/input
            overrides: Optional ExecutorConfig overrides

        Returns:
            Result with metadata including used_signals

        Requires:
            - ExecutorConfig is injected
            - SignalRegistry is available

        Ensures:
            - Result includes used_signals metadata
            - Execution is deterministic if seed is set
        """
        ...


class PortAggregate(Protocol):
    """Port for aggregating enriched chunks.

    Aggregates processed chunks into PyArrow tables.
    """

    def aggregate(self, enriched_chunks: list[dict[str, Any]]) -> Any:
        """Aggregate enriched chunks to PyArrow table.

        Args:
            enriched_chunks: List of enriched chunk dictionaries

        Returns:
            PyArrow Table with aggregated data

        Requires:
            - enriched_chunks has required fields
            - All chunks have consistent schema

        Ensures:
            - Returns valid pa.Table
            - All required columns present
        """
        ...


class PortScore(Protocol):
    """Port for scoring features.

    Computes scores from feature tables with specified metrics.
    """

    def score(self, features: Any, metrics: list[str]) -> Any:
        """Score features using specified metrics.

        Args:
            features: PyArrow Table with features
            metrics: List of metric names to compute

        Returns:
            Polars DataFrame with scores

        Requires:
            - features is valid pa.Table
            - metrics are declared and implemented
            - Required columns present in features

        Ensures:
            - Returns valid pl.DataFrame
            - All requested metrics computed
        """
        ...


class PortReport(Protocol):
    """Port for generating reports.

    Generates output reports from scores and manifest.
    """

    def report(self, scores: Any, manifest: Any) -> dict[str, str]:
        """Generate reports from scores and manifest.

        Args:
            scores: Polars DataFrame with computed scores
            manifest: Document manifest with metadata

        Returns:
            Dictionary mapping report name to output URI

        Requires:
            - scores is valid pl.DataFrame
            - manifest has required metadata

        Ensures:
            - All declared reports generated
            - URIs are accessible
        """
        ...


__all__ = [
    'FilePort',
    'JsonPort',
    'EnvPort',
    'ClockPort',
    'LogPort',
    'PortCPPIngest',
    'PortCPPAdapter',
    'PortSPCAdapter',
    'PortSignalsClient',
    'PortSignalsRegistry',
    'PortArgRouter',
    'PortExecutor',
    'PortAggregate',
    'PortScore',
    'PortReport',
]
