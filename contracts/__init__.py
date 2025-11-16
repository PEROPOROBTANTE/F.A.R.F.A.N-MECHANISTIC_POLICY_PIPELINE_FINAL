"""
Legacy compatibility shim for the deprecated top-level `contracts` package.

Historically, downstream tooling imported `contracts` from the repository root.
The canonical contract definitions now live in `saaaaaa.core.contracts`.
This shim keeps those imports functional and ensures that architectural tooling
placed under the `contracts/` directory (such as importlinter configs) does not
shadow or break runtime behavior.
"""

from saaaaaa.core.contracts import *  # noqa: F401,F403
