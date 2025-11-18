"""
Domain-Specific Exceptions - Contract Violation Errors
======================================================

Provides domain-specific exception hierarchy for contract violations.

Exception Hierarchy:
    ContractViolationError (base)
    ├── DataContractError (data/payload violations)
    └── SystemContractError (system/configuration violations)

Author: Policy Analytics Research Unit
Version: 1.0.0
License: Proprietary
"""


class ContractViolationError(Exception):
    """
    Base exception for all contract violations.

    Use this as the base class for specific contract violation types.

    Examples:
        >>> try:
        ...     raise ContractViolationError("Contract violated")
        ... except ContractViolationError as e:
        ...     print(f"Caught: {e}")
        Caught: Contract violated
    """
    pass


class DataContractError(ContractViolationError):
    """
    Exception for data/payload contract violations.

    Raised when:
    - Payload schema is invalid
    - Required fields are missing
    - Field values are out of range
    - Data integrity checks fail (e.g., digest mismatch)

    Examples:
        >>> try:
        ...     raise DataContractError("Invalid payload schema")
        ... except DataContractError as e:
        ...     print(f"Data error: {e}")
        Data error: Invalid payload schema
    """
    pass


class SystemContractError(ContractViolationError):
    """
    Exception for system/configuration contract violations.

    Raised when:
    - System configuration is invalid
    - Required resources are unavailable
    - Environment preconditions are not met
    - Infrastructure failures occur

    Examples:
        >>> try:
        ...     raise SystemContractError("Configuration missing")
        ... except SystemContractError as e:
        ...     print(f"System error: {e}")
        System error: Configuration missing
    """
    pass


if __name__ == "__main__":
    import doctest

    # Run doctests
    print("Running doctests...")
    doctest.testmod(verbose=True)

    # Integration tests
    print("\n" + "="*60)
    print("Domain Exceptions Integration Tests")
    print("="*60)

    print("\n1. Testing exception hierarchy:")
    assert issubclass(DataContractError, ContractViolationError)
    assert issubclass(SystemContractError, ContractViolationError)
    print("   ✓ DataContractError inherits from ContractViolationError")
    print("   ✓ SystemContractError inherits from ContractViolationError")

    print("\n2. Testing exception catching:")
    try:
        raise DataContractError("Test data error")
    except ContractViolationError as e:
        assert isinstance(e, DataContractError)
        print("   ✓ DataContractError caught as ContractViolationError")

    try:
        raise SystemContractError("Test system error")
    except ContractViolationError as e:
        assert isinstance(e, SystemContractError)
        print("   ✓ SystemContractError caught as ContractViolationError")

    print("\n3. Testing specific exception catching:")
    try:
        raise DataContractError("Payload validation failed")
    except DataContractError as e:
        assert str(e) == "Payload validation failed"
        print("   ✓ DataContractError caught specifically")

    try:
        raise SystemContractError("Config file not found")
    except SystemContractError as e:
        assert str(e) == "Config file not found"
        print("   ✓ SystemContractError caught specifically")

    print("\n4. Testing error differentiation:")
    errors = []

    try:
        raise DataContractError("Data issue")
    except ContractViolationError as e:
        errors.append(("data", type(e).__name__))

    try:
        raise SystemContractError("System issue")
    except ContractViolationError as e:
        errors.append(("system", type(e).__name__))

    assert errors[0] == ("data", "DataContractError")
    assert errors[1] == ("system", "SystemContractError")
    print("   ✓ Data and system errors are distinguishable")

    print("\n" + "="*60)
    print("Domain exceptions doctest OK - All tests passed!")
    print("="*60)
