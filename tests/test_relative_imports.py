"""Fix #21: integration modules must import siblings via relative imports.

`from custom_components.foobar2k.X import Y` couples the integration to its
on-disk path. HA convention is `from .X import Y`.
"""
from __future__ import annotations

from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent / "custom_components" / "foobar2k"


def test_no_module_uses_absolute_self_imports():
    """Scan every .py file in the package; none should import siblings via
    the absolute `from custom_components.foobar2k...` path."""
    offenders: list[str] = []
    for py in PACKAGE.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        if "from custom_components.foobar2k" in text:
            offenders.append(py.name)

    assert not offenders, (
        f"these modules use absolute self-imports instead of relative: {offenders}"
    )
