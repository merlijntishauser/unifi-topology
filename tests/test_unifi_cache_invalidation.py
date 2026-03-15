import pytest

from tests.unifi_cache_helpers import make_config
from unifi_topology.adapters import unifi

pytestmark = pytest.mark.integration


def test_invalidate_cache_removes_file(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    config = make_config()
    cache_path = tmp_path / f"fw_policies_{unifi._cache_key(config.url, config.site)}.json"
    unifi._save_cache(cache_path, [{"_id": "p1"}])
    assert cache_path.exists()
    removed = unifi.invalidate_cache(config)
    assert removed == 1
    assert not cache_path.exists()


def test_invalidate_cache_returns_zero_when_no_file(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    removed = unifi.invalidate_cache(make_config())
    assert removed == 0


def test_invalidate_cache_multiple_prefixes(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    config = make_config()
    for prefix in ("fw_policies", "fw_zones"):
        cache_path = tmp_path / f"{prefix}_{unifi._cache_key(config.url, config.site)}.json"
        unifi._save_cache(cache_path, [{"data": True}])
    removed = unifi.invalidate_cache(config, prefixes=("fw_policies", "fw_zones"))
    assert removed == 2
