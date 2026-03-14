from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

for name in list(sys.modules):
    if name == "unifi_topology" or name.startswith("unifi_topology."):
        del sys.modules[name]


@pytest.fixture(autouse=True)
def _clear_client_cache() -> None:
    """Clear the UniFi client cache between tests."""
    from unifi_topology.adapters.unifi import clear_client_cache

    clear_client_cache()


def pytest_collection_modifyitems(items: list) -> None:
    """Automatically mark tests without specific markers as unit tests."""
    specific_markers = {"integration", "contract", "acceptance"}
    for item in items:
        item_markers = {marker.name for marker in item.iter_markers()}
        if not item_markers & specific_markers:
            item.add_marker(pytest.mark.unit)
