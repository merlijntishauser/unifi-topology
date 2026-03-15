import pytest

from tests.unifi_fetch_helpers import config
from unifi_topology.adapters import unifi

pytestmark = pytest.mark.integration


def test_fetch_device_stats_calls_get_devices_detailed(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    calls: list[tuple[str, bool]] = []

    class Client:
        def get_devices(self, site, *, detailed=False):
            calls.append((site, detailed))
            return [{"mac": "aa", "type": "usw"}]

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    result = list(unifi.fetch_device_stats(config()))
    assert len(result) == 1
    assert calls == [("default", True)]
