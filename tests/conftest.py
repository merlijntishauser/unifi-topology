from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

for name in list(sys.modules):
    if name == "unifi_topology" or name.startswith("unifi_topology."):
        del sys.modules[name]


def pytest_collection_modifyitems(items: list) -> None:
    """Automatically mark tests without specific markers as unit tests."""
    import pytest

    specific_markers = {"integration", "contract", "acceptance"}
    for item in items:
        item_markers = {marker.name for marker in item.iter_markers()}
        if not item_markers & specific_markers:
            item.add_marker(pytest.mark.unit)
