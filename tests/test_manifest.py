"""Manifest sanity: integration_type must be set (Fix #22) and version
bump (Fix #17) for HACS to detect updates."""
from __future__ import annotations

import json
from pathlib import Path

MANIFEST = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "foobar2k"
    / "manifest.json"
)


def _manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_declares_integration_type():
    m = _manifest()
    assert "integration_type" in m, (
        "newer HA versions warn when integration_type is missing"
    )
    # 'device' is the right choice for a single hardware/software endpoint.
    assert m["integration_type"] == "device"


def test_manifest_version_bumped_past_fixed_release():
    """1.0.1 was the last shipped version. The git log mentions a '1.0.2 bug
    fix' commit but manifest stayed at 1.0.1. After this batch of fixes
    the version must be > 1.0.2 for HACS to push the update."""
    m = _manifest()
    parts = tuple(int(p) for p in m["version"].split("."))
    assert parts > (1, 0, 2), f"manifest version {m['version']} not bumped past 1.0.2"
