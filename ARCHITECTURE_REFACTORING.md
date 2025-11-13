# Architecture Refactoring Documentation

## Hexagonal Architecture (Ports & Adapters)

This document describes the architectural transformation from a monolithic, I/O-coupled system to a clean hexagonal architecture.

## Overview

The system is being refactored to follow the **Hexagonal Architecture** (also known as **Ports and Adapters**) pattern. This ensures:

1. **Business logic is pure** - No I/O in core modules
2. **Testability** - Easy to test with in-memory adapters
3. **Flexibility** - Easy to swap implementations (e.g., local files → S3)
4. **Maintainability** - Clear boundaries and dependencies

## Architecture Layers

### Core Layer (Business Logic)

**Location:** `src/saaaaaa/core/`, `src/saaaaaa/analysis/`, `src/saaaaaa/processing/`

**Purpose:** Pure business logic with no external dependencies

**Rules:**
- ✅ Can depend on Ports (abstractions)
- ✅ Can depend on TypedDict contracts
- ❌ Cannot perform I/O directly
- ❌ Cannot import from `infrastructure/`
- ❌ Cannot have import-time side effects

**Example:**
```python
from saaaaaa.core.ports import FilePort, JsonPort
from saaaaaa.utils.core_contracts import SemanticAnalyzerInputContract

class SemanticAnalyzer:
    def __init__(self, file_port: FilePort, json_port: JsonPort):
        self.file_port = file_port  # Injected dependency
        self.json_port = json_port
    
    def analyze(self, contract: SemanticAnalyzerInputContract) -> dict:
        # Pure business logic - no I/O
        # If I/O needed, delegate to ports
        ...
```

### Ports Layer (Abstractions)

**Location:** `src/saaaaaa/core/ports.py`

**Purpose:** Define abstract interfaces for external interactions

**Rules:**
- ✅ Use `Protocol` for structural subtyping
- ✅ Document expected behavior in docstrings
- ❌ No implementation details
- ❌ No external dependencies

**Example:**
```python
from typing import Protocol

class FilePort(Protocol):
    """Abstract interface for file operations."""
    
    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read text from file. Raises FileNotFoundError if missing."""
        ...
    
    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """Write text to file. Raises PermissionError if cannot write."""
        ...
```

### Infrastructure Layer (Adapters)

**Location:** `src/saaaaaa/infrastructure/`

**Purpose:** Concrete implementations of ports

**Rules:**
- ✅ Implement port protocols
- ✅ Can have external dependencies (pathlib, requests, etc.)
- ✅ Provide both real and test implementations
- ❌ Should not contain business logic

**Production Adapters:**
- `LocalFileAdapter` - Real file system using pathlib
- `SystemEnvAdapter` - Real environment variables
- `SystemClockAdapter` - Real time
- `StandardLogAdapter` - Real logging

**Test Adapters:**
- `InMemoryFileAdapter` - In-memory file storage
- `InMemoryEnvAdapter` - In-memory environment
- `FrozenClockAdapter` - Controllable time
- `InMemoryLogAdapter` - Log message capture

**Example:**
```python
# Production adapter
class LocalFileAdapter:
    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        return Path(path).read_text(encoding=encoding)
    
    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        Path(path).write_text(content, encoding=encoding)

# Test adapter
class InMemoryFileAdapter:
    def __init__(self):
        self._files: dict[str, bytes] = {}
    
    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._files[path].decode(encoding)
    
    def write_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        self._files[path] = content.encode(encoding)
```

### Orchestrator Layer (Composition)

**Location:** `src/saaaaaa/core/orchestrator/`

**Purpose:** Compose pure functions and manage I/O at edges

**Rules:**
- ✅ Create and inject adapters
- ✅ Perform I/O at system boundaries
- ✅ Validate contracts at entry/exit
- ❌ Minimal business logic (delegate to core)

**Example:**
```python
from saaaaaa.infrastructure.filesystem import LocalFileAdapter, JsonAdapter
from saaaaaa.core.analysis import SemanticAnalyzer

def analyze_document_file(file_path: str) -> dict:
    # Create adapters (dependency injection)
    file_port = LocalFileAdapter()
    json_port = JsonAdapter()
    
    # Load data at boundary (I/O happens here)
    text = file_port.read_text(file_path)
    
    # Create contract
    contract = SemanticAnalyzerInputContract(
        text=text,
        schema_version="sem-1.0"
    )
    
    # Call pure business logic
    analyzer = SemanticAnalyzer(file_port, json_port)
    result = analyzer.analyze(contract)
    
    return result
```

### Contracts Layer (Type Safety)

**Location:** `src/saaaaaa/utils/`

**Purpose:** Define type-safe boundaries between modules

**Files:**
- `core_contracts.py` - TypedDict definitions (16 contracts)
- `contracts_runtime.py` - Pydantic validators (16 models)

**Example:**
```python
# TypedDict (compile-time checking)
class SemanticAnalyzerInputContract(TypedDict):
    text: str
    segments: NotRequired[List[str]]
    ontology_params: NotRequired[Dict[str, Any]]

# Pydantic (runtime validation)
class SemanticAnalyzerInputModel(BaseModel):
    text: str = Field(min_length=1)
    segments: List[str] = Field(default_factory=list)
    ontology_params: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = Field(pattern=r"^sem-\d+\.\d+$")
```

## Dependency Flow

```
                    ┌─────────────┐
                    │   CLI / UI  │
                    └──────┬──────┘
                           │
                           ▼
                ┌──────────────────────┐
                │   Orchestrator       │ ◄─── Creates adapters
                │   (Composition Root) │      Injects into core
                └──────────┬───────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌─────────┐      ┌─────────┐      ┌─────────┐
    │ Adapter │      │ Adapter │      │ Adapter │
    │ (File)  │      │ (Env)   │      │ (Clock) │
    └────┬────┘      └────┬────┘      └────┬────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
                          ▼
                    ┌───────────┐
                    │   Ports   │ ◄─── Abstract interfaces
                    └─────┬─────┘
                          │
                          ▼
                ┌─────────────────┐
                │  Core Modules   │ ◄─── Pure business logic
                │  (Analysis,     │      No I/O
                │   Processing)   │      TypedDict contracts
                └─────────────────┘
```

## Migration Pattern

### Before (Coupled to I/O)

```python
class Analyzer:
    def analyze_document(self, document_path: str) -> dict:
        # I/O coupled to business logic
        with open(document_path, 'r') as f:
            text = f.read()
        
        # Business logic
        result = self._process(text)
        
        # More I/O
        with open('output.json', 'w') as f:
            json.dump(result, f)
        
        return result
```

### After (Pure with Dependency Injection)

```python
class Analyzer:
    def __init__(self, file_port: FilePort):
        self.file_port = file_port  # Injected
    
    def analyze(self, contract: AnalyzerInputContract) -> AnalyzerOutputContract:
        # Pure business logic only
        text = contract.text
        result = self._process(text)
        
        return AnalyzerOutputContract(
            result=result,
            schema_version="sem-1.0"
        )

# Orchestrator handles I/O
def analyze_document_file(file_path: str) -> dict:
    file_port = LocalFileAdapter()
    
    # I/O at boundary
    text = file_port.read_text(file_path)
    
    # Create contract
    contract = AnalyzerInputContract(text=text, schema_version="sem-1.0")
    
    # Pure business logic
    analyzer = Analyzer(file_port)
    output = analyzer.analyze(contract)
    
    # I/O at boundary
    file_port.write_text('output.json', json.dumps(output))
    
    return output
```

## Testing Strategy

### Unit Tests (Core Modules)

Use in-memory adapters for fast, isolated tests:

```python
def test_analyzer():
    # Arrange
    file_port = InMemoryFileAdapter()
    file_port.write_text("input.txt", "Sample text")
    
    analyzer = Analyzer(file_port)
    contract = AnalyzerInputContract(text="Sample text", schema_version="sem-1.0")
    
    # Act
    result = analyzer.analyze(contract)
    
    # Assert
    assert result.schema_version == "sem-1.0"
    assert len(result.result) > 0
```

### Integration Tests (Orchestrator)

Use temporary directories for real I/O tests:

```python
def test_analyze_document_file(tmp_path):
    # Arrange
    file_path = tmp_path / "input.txt"
    file_path.write_text("Sample municipal plan")
    
    # Act
    result = analyze_document_file(str(file_path))
    
    # Assert
    assert result is not None
```

### Contract Tests

Validate runtime contract enforcement:

```python
def test_contract_validation():
    # Valid contract
    model = SemanticAnalyzerInputModel(
        text="Sample text",
        schema_version="sem-1.0"
    )
    assert model.text == "Sample text"
    
    # Invalid contract (empty text)
    with pytest.raises(ValidationError):
        SemanticAnalyzerInputModel(
            text="",
            schema_version="sem-1.0"
        )
```

## Boundary Enforcement

The `tools/scan_boundaries.py` scanner ensures:

1. **No `__main__` blocks** in core modules
2. **No I/O operations** (open, json.load, etc.) in core modules
3. **No subprocess calls** in core modules
4. **No network calls** in core modules

Usage:

```bash
# Scan core modules
python tools/scan_boundaries.py --root src/saaaaaa/core

# Generate SARIF report for CI
python tools/scan_boundaries.py --root src/saaaaaa/core \
    --sarif out/boundaries.sarif \
    --json out/violations.json

# Fail on specific violation types
python tools/scan_boundaries.py --root src/saaaaaa/core \
    --fail-on io,main,subprocess
```

## Benefits

1. **Testability**: Easy to test with in-memory adapters (no disk I/O)
2. **Flexibility**: Swap file system for S3, GCS, or Azure Blob
3. **Performance**: Can cache, batch, or parallelize I/O in adapters
4. **Reliability**: Pure functions are deterministic and easier to reason about
5. **Maintainability**: Clear boundaries make changes safer
6. **Type Safety**: Contracts catch errors at boundaries
7. **Documentation**: Ports document expected behavior

## Anti-Patterns to Avoid

❌ **Don't import infrastructure in core:**
```python
# BAD
from saaaaaa.infrastructure.filesystem import LocalFileAdapter

class Analyzer:
    def __init__(self):
        self.file_port = LocalFileAdapter()  # Tight coupling!
```

✅ **Do inject ports:**
```python
# GOOD
from saaaaaa.core.ports import FilePort

class Analyzer:
    def __init__(self, file_port: FilePort):
        self.file_port = file_port  # Dependency injection!
```

❌ **Don't perform I/O in core:**
```python
# BAD
class Analyzer:
    def analyze(self, path: str):
        with open(path) as f:  # I/O in core!
            text = f.read()
```

✅ **Do use contracts:**
```python
# GOOD
class Analyzer:
    def analyze(self, contract: AnalyzerInputContract):
        text = contract.text  # Data passed in!
```

## References

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Dependency Injection](https://martinfowler.com/articles/injection.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Functional Core, Imperative Shell](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell)
