"""Import-safe placeholder for domain contracts.

Real contract models will be introduced in follow-up iterations. The module
exists today so that other packages can import :mod:`core.contracts` without
triggering ``ImportError`` at runtime.
"""

from __future__ import annotations

__all__ = []

