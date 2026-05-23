"""Pytest config: install HA stubs and make custom_components importable."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests import ha_stubs  # noqa: E402

ha_stubs.install()
