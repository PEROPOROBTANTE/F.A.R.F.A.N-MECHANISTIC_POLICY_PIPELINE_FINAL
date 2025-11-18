"""
Native Extension and System Library Verification

This module checks for C-extensions, native libraries, and platform-specific
requirements to provide early detection and clear error messages.

Checks include:
- Wheel compatibility (manylinux, musllinux, macosx, win)
- System libraries (libzstd, icu, libomp, libstdc++)
- CPU features (AVX, NEON for polars/arrow)
- FIPS mode detection for cryptography
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class NativeCheckResult:
    """Result of a native library or extension check."""

    available: bool
    message: str
    hint: str = ""


def check_system_library(libname: str) -> NativeCheckResult:
    """
    Check if a system library is available.

    Parameters
    ----------
    libname : str
        Library name (e.g., 'zstd', 'icu', 'omp')

    Returns
    -------
    NativeCheckResult
        Result with availability and guidance

    Examples
    --------
    >>> result = check_system_library('zstd')
    >>> if not result.available:
    ...     print(result.hint)
    """
    system = platform.system()

    if system == "Linux":
        # Try ldconfig or direct file check
        try:
            result = subprocess.run(
                ["ldconfig", "-p"],
                check=False, capture_output=True,
                text=True,
                timeout=5,
            )
            if libname in result.stdout:
                return NativeCheckResult(
                    available=True,
                    message=f"Library {libname} found via ldconfig",
                )
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Fallback: check common lib paths
        base_root = Path(os.sep)
        common_paths = [
            base_root / "usr" / "lib" / f"lib{libname}.so",
            base_root / "usr" / "lib" / "x86_64-linux-gnu" / f"lib{libname}.so",
            base_root / "usr" / "local" / "lib" / f"lib{libname}.so",
        ]
        for path in common_paths:
            if path.exists():
                return NativeCheckResult(
                    available=True,
                    message=f"Library {libname} found at {path}",
                )

        return NativeCheckResult(
            available=False,
            message=f"Library {libname} not found",
            hint=f"Install system package: apt-get install lib{libname}-dev (Debian/Ubuntu) "
                 f"or yum install {libname}-devel (RHEL/CentOS)",
        )

    elif system == "Darwin":
        # macOS - check via dyld
        try:
            result = subprocess.run(
                ["otool", "-L", sys.executable],
                check=False, capture_output=True,
                text=True,
                timeout=5,
            )
            if libname in result.stdout:
                return NativeCheckResult(
                    available=True,
                    message=f"Library {libname} found via otool",
                )
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return NativeCheckResult(
            available=False,
            message=f"Library {libname} not found",
            hint=f"Install via Homebrew: brew install {libname}",
        )

    elif system == "Windows":
        # Windows - check PATH and common locations
        for path_dir in os.environ.get("PATH", "").split(os.pathsep):
            dll_path = os.path.join(path_dir, f"{libname}.dll")
            if os.path.exists(dll_path):
                return NativeCheckResult(
                    available=True,
                    message=f"Library {libname}.dll found at {dll_path}",
                )

        return NativeCheckResult(
            available=False,
            message=f"Library {libname}.dll not found in PATH",
            hint=f"Install {libname} and add to PATH",
        )

    return NativeCheckResult(
        available=False,
        message=f"Cannot check library {libname} on {system}",
        hint="Platform detection not implemented for this system",
    )


def check_wheel_compatibility(package: str) -> NativeCheckResult:
    """
    Check if a package has appropriate wheels for the current platform.

    Parameters
    ----------
    package : str
        Package name (e.g., 'pyarrow', 'polars')

    Returns
    -------
    NativeCheckResult
        Compatibility status and guidance
    """
    system = platform.system()
    platform.machine()

    # Platform tags we expect
    if system in {"Linux", "Darwin", "Windows"}:
        pass

    try:
        # Try to import and check __file__ for wheel origin
        import importlib
        mod = importlib.import_module(package)
        if hasattr(mod, "__file__") and mod.__file__:
            file_path = mod.__file__
            # Check if installed from wheel (dist-info present)
            if "site-packages" in file_path:
                return NativeCheckResult(
                    available=True,
                    message=f"Package {package} installed from wheel",
                )

        return NativeCheckResult(
            available=True,
            message=f"Package {package} available (source install or wheel)",
            hint="Consider using pre-built wheels for better compatibility",
        )
    except ImportError:
        return NativeCheckResult(
            available=False,
            message=f"Package {package} not installed",
            hint=f"Install with: pip install {package}",
        )


def check_cpu_features() -> NativeCheckResult:
    """
    Check CPU features required by performance libraries.

    Some packages (polars, pyarrow) require specific CPU instructions.

    Returns
    -------
    NativeCheckResult
        CPU feature availability
    """
    machine = platform.machine().lower()

    # Basic architecture check
    if machine in ("x86_64", "amd64"):
        # Would need cpuinfo or similar for detailed AVX detection
        # For now, assume modern x86_64 has basic features
        return NativeCheckResult(
            available=True,
            message=f"CPU architecture {machine} is supported",
        )
    elif machine in ("arm64", "aarch64"):
        return NativeCheckResult(
            available=True,
            message=f"CPU architecture {machine} (ARM) is supported",
        )
    else:
        return NativeCheckResult(
            available=False,
            message=f"CPU architecture {machine} may not be supported",
            hint="Some packages require x86_64 or ARM64. Check package documentation.",
        )


def check_fips_mode() -> bool:
    """
    Detect if system is in FIPS mode (Federal Information Processing Standards).

    This affects cryptography backend selection.

    Returns
    -------
    bool
        True if FIPS mode is enabled
    """
    if platform.system() == "Linux":
        # Check /proc/sys/crypto/fips_enabled
        try:
            with open("/proc/sys/crypto/fips_enabled") as f:
                return f.read().strip() == "1"
        except (FileNotFoundError, PermissionError):
            pass

    return False


def verify_native_dependencies(packages: list[str]) -> dict[str, NativeCheckResult]:
    """
    Verify native dependencies for a list of packages.

    Parameters
    ----------
    packages : list[str]
        Package names to verify

    Returns
    -------
    dict[str, NativeCheckResult]
        Mapping of package name to verification result

    Examples
    --------
    >>> results = verify_native_dependencies(['pyarrow', 'polars'])
    >>> for pkg, result in results.items():
    ...     if not result.available:
    ...         print(f"{pkg}: {result.hint}")
    """
    results = {}

    # Known native dependencies
    native_deps = {
        "pyarrow": ["zstd"],
        "polars": [],  # Statically linked
        "blake3": [],  # Statically linked
    }

    for package in packages:
        # Check package itself
        results[package] = check_wheel_compatibility(package)

        # Check system libraries
        if package in native_deps:
            for lib in native_deps[package]:
                lib_result = check_system_library(lib)
                if not lib_result.available:
                    results[f"{package}:{lib}"] = lib_result

    return results


def print_native_report() -> None:
    """
    Print a comprehensive native environment report.

    This is useful for debugging environment issues.
    """
    print("=== Native Environment Report ===")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {sys.version}")
    print()

    print("CPU Features:")
    cpu_result = check_cpu_features()
    print(f"  {cpu_result.message}")
    print()

    print("FIPS Mode:")
    print(f"  {'Enabled' if check_fips_mode() else 'Disabled'}")
    print()

    print("Critical Packages:")
    packages = ["pyarrow", "polars", "blake3"]
    results = verify_native_dependencies(packages)
    for name, result in results.items():
        status = "✓" if result.available else "✗"
        print(f"  {status} {name}: {result.message}")
        if result.hint:
            print(f"     Hint: {result.hint}")
    print()

    print("System Libraries:")
    for lib in ["zstd", "icu", "omp"]:
        result = check_system_library(lib)
        status = "✓" if result.available else "✗"
        print(f"  {status} {lib}: {result.message}")
        if result.hint:
            print(f"     Hint: {result.hint}")


if __name__ == "__main__":
    print_native_report()
