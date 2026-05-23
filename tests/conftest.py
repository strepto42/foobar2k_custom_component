"""Pytest config: install HA stubs and make custom_components importable."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests import ha_stubs  # noqa: E402

ha_stubs.install()

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_ha_state():
    """Reset stub state that bleeds between tests (unique_id registry)."""
    from homeassistant.config_entries import ConfigFlow
    ConfigFlow._unique_ids_in_use.clear()
    yield
    ConfigFlow._unique_ids_in_use.clear()
