import pytest

from tests.unifi_fetch_helpers import config, first_mapping
from unifi_topology.adapters import unifi

pytestmark = pytest.mark.integration


def test_fetch_device_stats_default_no_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"device_stats_{unifi._cache_key(config().url, config().site)}.json"
    unifi._save_cache(cache_path, [{"mac": "cached"}])
    called = {"count": 0}

    class Client:
        def get_devices(self, site, *, detailed=False):
            called["count"] += 1
            return [{"mac": "fresh"}]

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: Client())
    result = list(unifi.fetch_device_stats(config()))
    assert called["count"] == 1
    assert first_mapping(result)["mac"] == "fresh"


def test_fetch_device_stats_with_cache_enabled(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"device_stats_{unifi._cache_key(config().url, config().site)}.json"
    unifi._save_cache(cache_path, [{"mac": "cached"}])

    def fail_init(*_args, **_kwargs):
        raise AssertionError("should not fetch when cache is valid")

    monkeypatch.setattr(unifi, "_create_client", fail_init)
    result = list(unifi.fetch_device_stats(config(), use_cache=True))
    assert first_mapping(result)["mac"] == "cached"
