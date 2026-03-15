"""Additional tests for unifi.py to boost code coverage to 90%+.

Covers: serialization helpers, cache edge cases, fetch functions (clients,
networks, payload), _fetch_cached generic helper, firewall fetch wrappers,
_evict_client, _fetch_payload_clients, and error paths.
"""

# pyright: reportIndexIssue=false
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import json
import stat
import time
from collections.abc import Sequence
from pathlib import Path
from unittest.mock import patch

import pytest

from unifi_topology.adapters import unifi
from unifi_topology.adapters.config import Config

# All tests get auto-marked as unit by conftest.py.

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONFIG = Config(
    url="https://example",
    site="default",
    user="user",
    password="pass",
    verify_ssl=True,
)


def _write_cache(path: Path, data: list[object], *, age_seconds: float = 0.0) -> None:
    """Write a cache file with a timestamp ``age_seconds`` in the past."""
    payload = {"timestamp": time.time() - age_seconds, "data": data}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")


class _StubClient:
    """Minimal client stub with configurable return values per method."""

    def __init__(
        self,
        *,
        devices: list | None = None,
        clients: list | None = None,
        networks: list | None = None,
        firewall_zones: list | None = None,
        firewall_policies: list | None = None,
        firewall_groups: list | None = None,
    ):
        self._devices = devices or []
        self._clients = clients or []
        self._networks = networks or []
        self._fw_zones = firewall_zones or []
        self._fw_policies = firewall_policies or []
        self._fw_groups = firewall_groups or []

    def get_devices(self, site: str, *, detailed: bool = False) -> list:
        return self._devices

    def get_clients(self, site: str) -> list:
        return self._clients

    def get_networkconf(self, site: str) -> list:
        return self._networks

    def get_firewall_zones(self, site: str) -> list:
        return self._fw_zones

    def get_firewall_policies(self, site: str) -> list:
        return self._fw_policies

    def get_firewall_groups(self, site: str) -> list:
        return self._fw_groups


def _patch_client(monkeypatch, client: object) -> None:
    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: client)


# ===========================================================================
# 1. _device_lldp_value branch coverage (lines 118->120, 120->122)
# ===========================================================================


def test_device_lldp_value_prefers_lldp_info():
    """When ``lldp_info`` is present it should be returned directly."""
    device = {"lldp_info": [{"chassis_id": "aa"}], "lldp": "ignored"}
    result = unifi._device_lldp_value(device)
    assert result == [{"chassis_id": "aa"}]


def test_device_lldp_value_falls_back_to_lldp():
    """When ``lldp_info`` is None, fall back to ``lldp``."""
    device = {"lldp": [{"chassis_id": "bb"}]}
    result = unifi._device_lldp_value(device)
    assert result == [{"chassis_id": "bb"}]


def test_device_lldp_value_falls_back_to_lldp_table():
    """When both ``lldp_info`` and ``lldp`` are None, fall back to ``lldp_table``."""
    device = {"lldp_table": [{"chassis_id": "cc"}]}
    result = unifi._device_lldp_value(device)
    assert result == [{"chassis_id": "cc"}]


def test_device_lldp_value_returns_none_when_all_missing():
    """When none of the three fields exist, return None."""
    result = unifi._device_lldp_value({})
    assert result is None


# ===========================================================================
# 2. _serialize_network_for_cache / _serialize_networks_for_cache (165, 176)
# ===========================================================================


def test_serialize_network_for_cache():
    network = {
        "_id": "net1",
        "name": "LAN",
        "vlan": 10,
        "vlan_enabled": True,
        "purpose": "corporate",
        "enabled": True,
    }
    result = unifi._serialize_network_for_cache(network)
    assert result["_id"] == "net1"
    assert result["name"] == "LAN"
    assert result["vlan"] == 10
    assert result["vlan_enabled"] is True
    assert result["purpose"] == "corporate"
    assert result["enabled"] is True


def test_serialize_network_for_cache_uses_fallback_fields():
    """Fallback field names like ``network_name``, ``vlan_id`` should work."""
    network = {"id": "net2", "network_name": "IoT", "vlan_id": 20}
    result = unifi._serialize_network_for_cache(network)
    assert result["_id"] == "net2"
    assert result["name"] == "IoT"
    assert result["vlan"] == 20


def test_serialize_networks_for_cache():
    networks = [
        {"_id": "n1", "name": "LAN", "vlan": 1, "purpose": "corporate"},
        {"_id": "n2", "name": "Guest", "vlan": 100, "purpose": "guest"},
    ]
    result = unifi._serialize_networks_for_cache(networks)
    assert len(result) == 2
    assert result[0]["_id"] == "n1"
    assert result[1]["_id"] == "n2"


# ===========================================================================
# 3. Skip Windows lock code (185-187, 196-198) -- cannot run on macOS
# ===========================================================================

# ===========================================================================
# 4. _release_cache_lock OSError path (lines 216-217)
# ===========================================================================


def test_cache_lock_release_oserror_is_swallowed(tmp_path):
    """If _release_cache_lock raises OSError, _cache_lock should not propagate."""
    lock_target = tmp_path / "test.json"
    lock_target.write_text("{}", encoding="utf-8")

    with patch.object(unifi, "_release_cache_lock", side_effect=OSError("boom")):
        # Should not raise despite the OSError on release
        with unifi._cache_lock(lock_target):
            pass


# ===========================================================================
# 5. _is_cache_dir_safe -- stat failure and world-writable (222, 225-227)
# ===========================================================================


def test_is_cache_dir_safe_returns_true_for_nonexistent(tmp_path):
    """A non-existent directory is considered safe (will be created later)."""
    assert unifi._is_cache_dir_safe(tmp_path / "does_not_exist") is True


def test_is_cache_dir_safe_stat_failure(tmp_path):
    """If stat() raises OSError, the directory is unsafe."""
    target = tmp_path / "dir"
    target.mkdir()

    with (
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "stat", side_effect=OSError("permission denied")),
    ):
        assert unifi._is_cache_dir_safe(target) is False


def test_is_cache_dir_safe_world_writable(tmp_path):
    """A world-writable directory is unsafe."""
    target = tmp_path / "unsafe"
    target.mkdir()
    target.chmod(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0o777
    assert unifi._is_cache_dir_safe(target) is False
    # Reset permissions for cleanup
    target.chmod(stat.S_IRWXU)


# ===========================================================================
# 6. _load_cache_with_age -- corrupt cache file (lines 266-268)
# ===========================================================================


def test_load_cache_with_age_corrupt_file(tmp_path):
    """A corrupt (non-JSON) cache file returns (None, None)."""
    cache_path = tmp_path / "corrupt.json"
    cache_path.write_text("not valid json {{{", encoding="utf-8")
    data, age = unifi._load_cache_with_age(cache_path)
    assert data is None
    assert age is None


# ===========================================================================
# 7. invalidate_cache OSError (lines 316-317)
# ===========================================================================


def test_invalidate_cache_oserror(monkeypatch, tmp_path):
    """invalidate_cache handles OSError when unlinking the cache file."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    config = _CONFIG

    cache_path = tmp_path / f"fw_policies_{unifi._cache_key(config.url, config.site)}.json"
    _write_cache(cache_path, [{"_id": "p1"}])

    original_cache_lock = unifi._cache_lock

    from contextlib import contextmanager

    @contextmanager
    def _failing_lock(path):
        with original_cache_lock(path):
            raise OSError("cannot unlink")

    monkeypatch.setattr(unifi, "_cache_lock", _failing_lock)
    removed = unifi.invalidate_cache(config)
    assert removed == 0


# ===========================================================================
# 8. _evict_client (lines 409-410)
# ===========================================================================


def test_evict_client_removes_cached_entry(monkeypatch):
    """_evict_client removes the cached client for the given config."""

    class FakeClient:
        def __init__(self, **kwargs):
            pass

    monkeypatch.setattr(unifi, "UnifiClient", FakeClient)
    config = _CONFIG

    client = unifi._get_or_create_client(config, is_udm_pro=True)
    assert client is not None

    unifi._evict_client(config, is_udm_pro=True)

    # Next call should create a new instance
    client2 = unifi._get_or_create_client(config, is_udm_pro=True)
    assert client2 is not client


def test_evict_client_noop_when_not_cached():
    """_evict_client does nothing when there is no cached entry."""
    config = Config(
        url="https://no-such-host",
        site="default",
        user="nobody",
        password="none",
        verify_ssl=True,
    )
    # Should not raise
    unifi._evict_client(config, is_udm_pro=True)


# ===========================================================================
# 9. fetch_clients -- cache hit (502-503) and re-raise without stale (522)
# ===========================================================================


def test_fetch_clients_cache_hit(monkeypatch, tmp_path):
    """fetch_clients returns cached data without contacting the controller."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")

    config = _CONFIG
    cache_path = tmp_path / f"clients_{unifi._cache_key(config.url, config.site)}.json"
    _write_cache(cache_path, [{"mac": "aa:bb:cc:dd:ee:ff"}])

    def fail(*_a, **_k):
        raise AssertionError("should not create a client")

    monkeypatch.setattr(unifi, "_create_client", fail)
    clients = list(unifi.fetch_clients(config))
    assert len(clients) == 1
    assert clients[0]["mac"] == "aa:bb:cc:dd:ee:ff"


def test_fetch_clients_raises_without_stale_cache(monkeypatch, tmp_path):
    """fetch_clients re-raises when no stale cache is available."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    class FailClient:
        def get_clients(self, site):
            raise RuntimeError("network error")

    _patch_client(monkeypatch, FailClient())
    with pytest.raises(RuntimeError, match="network error"):
        unifi.fetch_clients(_CONFIG)


# ===========================================================================
# 10. fetch_networks -- entire function (lines 536-567)
# ===========================================================================


def test_fetch_networks_fresh(monkeypatch, tmp_path):
    """fetch_networks fetches from controller and saves to cache."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")

    stub = _StubClient(networks=[{"_id": "n1", "name": "LAN", "vlan": 1}])
    _patch_client(monkeypatch, stub)

    networks = list(unifi.fetch_networks(_CONFIG))
    assert len(networks) == 1
    assert networks[0]["_id"] == "n1"

    # Verify cache was written
    cache_path = tmp_path / f"networks_{unifi._cache_key(_CONFIG.url, _CONFIG.site)}.json"
    assert cache_path.exists()


def test_fetch_networks_cache_hit(monkeypatch, tmp_path):
    """fetch_networks returns cached data when fresh."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")

    config = _CONFIG
    cache_path = tmp_path / f"networks_{unifi._cache_key(config.url, config.site)}.json"
    _write_cache(cache_path, [{"_id": "n1", "name": "cached"}])

    def fail(*_a, **_k):
        raise AssertionError("should not fetch")

    monkeypatch.setattr(unifi, "_create_client", fail)
    networks = list(unifi.fetch_networks(config))
    assert len(networks) == 1
    assert networks[0]["name"] == "cached"


def test_fetch_networks_stale_fallback(monkeypatch, tmp_path):
    """fetch_networks falls back to stale cache on fetch failure."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")

    config = _CONFIG
    cache_path = tmp_path / f"networks_{unifi._cache_key(config.url, config.site)}.json"
    _write_cache(cache_path, [{"_id": "n1", "name": "stale"}], age_seconds=3600)

    class FailClient:
        def get_networkconf(self, site):
            raise RuntimeError("fail")

    _patch_client(monkeypatch, FailClient())
    networks = list(unifi.fetch_networks(config))
    assert len(networks) == 1
    assert networks[0]["name"] == "stale"


def test_fetch_networks_raises_without_stale(monkeypatch, tmp_path):
    """fetch_networks raises when fetch fails and no stale cache exists."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    class FailClient:
        def get_networkconf(self, site):
            raise RuntimeError("network error")

    _patch_client(monkeypatch, FailClient())
    with pytest.raises(RuntimeError, match="network error"):
        unifi.fetch_networks(_CONFIG)


# ===========================================================================
# 11. fetch_payload (lines 578-588)
# ===========================================================================


def test_fetch_payload_combines_all(monkeypatch, tmp_path):
    """fetch_payload returns devices, clients, networks, and vlan_info."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    stub = _StubClient(
        devices=[{"mac": "aa", "name": "switch", "type": "usw"}],
        clients=[{"mac": "bb", "name": "laptop"}],
        networks=[{"_id": "n1", "name": "LAN", "vlan": 1, "purpose": "corporate"}],
    )
    _patch_client(monkeypatch, stub)

    result = unifi.fetch_payload(_CONFIG)
    assert "devices" in result
    assert "clients" in result
    assert "networks" in result
    assert "vlan_info" in result
    assert len(result["devices"]) == 1
    assert len(result["clients"]) == 1


def test_fetch_payload_without_clients(monkeypatch, tmp_path):
    """fetch_payload with include_clients=False returns empty clients list."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    stub = _StubClient(
        devices=[{"mac": "aa", "name": "switch", "type": "usw"}],
        networks=[{"_id": "n1", "name": "LAN"}],
    )
    _patch_client(monkeypatch, stub)

    result = unifi.fetch_payload(_CONFIG, include_clients=False)
    assert result["clients"] == []
    assert len(result["devices"]) == 1


# ===========================================================================
# 12. _fetch_cached generic helper (lines 613-634)
# ===========================================================================


def test_fetch_cached_cache_hit(monkeypatch, tmp_path):
    """_fetch_cached returns fresh cached data."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")

    config = _CONFIG
    cache_path = tmp_path / f"test_resource_{unifi._cache_key(config.url, config.site)}.json"
    _write_cache(cache_path, [{"cached": True}])

    def fail(*_a, **_k):
        raise AssertionError("should not fetch")

    monkeypatch.setattr(unifi, "_create_client", fail)

    result = list(
        unifi._fetch_cached(
            config,
            cache_prefix="test_resource",
            operation="test resource",
            api_call=lambda client, site: lambda: client.get_devices(site),
        )
    )
    assert len(result) == 1
    assert result[0]["cached"] is True


def test_fetch_cached_stale_fallback(monkeypatch, tmp_path):
    """_fetch_cached uses stale cache when fetch fails."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")

    config = _CONFIG
    cache_path = tmp_path / f"stale_test_{unifi._cache_key(config.url, config.site)}.json"
    _write_cache(cache_path, [{"stale": True}], age_seconds=3600)

    class FailClient:
        pass  # no methods -- will raise AttributeError

    _patch_client(monkeypatch, FailClient())

    result = list(
        unifi._fetch_cached(
            config,
            cache_prefix="stale_test",
            operation="stale test",
            api_call=lambda client, site: lambda: (_ for _ in ()).throw(RuntimeError("fail")),
        )
    )
    assert len(result) == 1
    assert result[0]["stale"] is True


def test_fetch_cached_saves_with_serialize(monkeypatch, tmp_path):
    """_fetch_cached applies serialize function before saving to cache."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")

    config = _CONFIG
    stub = _StubClient(devices=[{"mac": "raw"}])
    _patch_client(monkeypatch, stub)

    def my_serialize(data: Sequence[object]) -> Sequence[object]:
        return [{"mac": "serialized"}]

    result = list(
        unifi._fetch_cached(
            config,
            cache_prefix="ser_test",
            operation="serialize test",
            api_call=lambda client, site: lambda: client.get_devices(site),
            serialize=my_serialize,
        )
    )
    assert result[0]["mac"] == "raw"  # returned data is the original, not serialized

    # But the cache file should contain the serialized version
    cache_path = tmp_path / f"ser_test_{unifi._cache_key(config.url, config.site)}.json"
    cached = json.loads(cache_path.read_text(encoding="utf-8"))
    assert cached["data"][0]["mac"] == "serialized"


def test_fetch_cached_saves_without_serialize(monkeypatch, tmp_path):
    """_fetch_cached saves raw data when no serialize function is given."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")

    config = _CONFIG
    stub = _StubClient(devices=[{"mac": "raw_data"}])
    _patch_client(monkeypatch, stub)

    unifi._fetch_cached(
        config,
        cache_prefix="no_ser",
        operation="no serialize",
        api_call=lambda client, site: lambda: client.get_devices(site),
    )

    cache_path = tmp_path / f"no_ser_{unifi._cache_key(config.url, config.site)}.json"
    cached = json.loads(cache_path.read_text(encoding="utf-8"))
    assert cached["data"][0]["mac"] == "raw_data"


def test_fetch_cached_raises_without_stale(monkeypatch, tmp_path):
    """_fetch_cached raises when fetch fails and no stale cache."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    class FailClient:
        def get_devices(self, site, *, detailed=False):
            raise RuntimeError("fail")

    _patch_client(monkeypatch, FailClient())

    with pytest.raises(RuntimeError, match="fail"):
        unifi._fetch_cached(
            _CONFIG,
            cache_prefix="raise_test",
            operation="raise test",
            api_call=lambda client, site: lambda: client.get_devices(site),
        )


# ===========================================================================
# 13. fetch_firewall_* thin wrappers (lines 646, 663, 680)
# ===========================================================================


def test_fetch_firewall_zones(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    stub = _StubClient(firewall_zones=[{"_id": "z1", "name": "LAN"}])
    _patch_client(monkeypatch, stub)

    result = list(unifi.fetch_firewall_zones(_CONFIG))
    assert len(result) == 1
    assert result[0]["_id"] == "z1"


def test_fetch_firewall_policies(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    stub = _StubClient(firewall_policies=[{"_id": "p1", "name": "Block"}])
    _patch_client(monkeypatch, stub)

    result = list(unifi.fetch_firewall_policies(_CONFIG))
    assert len(result) == 1
    assert result[0]["_id"] == "p1"


def test_fetch_firewall_groups(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    stub = _StubClient(firewall_groups=[{"_id": "g1", "name": "DNS Servers"}])
    _patch_client(monkeypatch, stub)

    result = list(unifi.fetch_firewall_groups(_CONFIG))
    assert len(result) == 1
    assert result[0]["_id"] == "g1"


# ===========================================================================
# 14. _fetch_payload_clients with include_clients=False (lines 697-699)
# ===========================================================================


def test_fetch_payload_clients_excluded():
    """_fetch_payload_clients returns empty list when include_clients=False."""
    result = unifi._fetch_payload_clients(
        _CONFIG, site=None, include_clients=False, use_cache=False
    )
    assert result == []


def test_fetch_payload_clients_included(monkeypatch, tmp_path):
    """_fetch_payload_clients delegates to fetch_clients when included."""
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    stub = _StubClient(clients=[{"mac": "cl1"}])
    _patch_client(monkeypatch, stub)

    result = unifi._fetch_payload_clients(_CONFIG, site=None, include_clients=True, use_cache=False)
    assert len(result) == 1
    assert result[0]["mac"] == "cl1"


# ===========================================================================
# Extra: _call_with_retries last_exc is None fallback (line 380)
# ===========================================================================


def test_call_with_retries_zero_attempts(monkeypatch):
    """When retry_attempts returns 0, RuntimeError is raised from line 380."""
    monkeypatch.setenv("UNIFI_RETRY_ATTEMPTS", "1")
    monkeypatch.setenv("UNIFI_RETRY_BACKOFF_SECONDS", "0")

    # Force 0 attempts by patching _retry_attempts
    monkeypatch.setattr(unifi, "_retry_attempts", lambda: 0)

    with pytest.raises(RuntimeError, match="Failed test_op"):
        unifi._call_with_retries("test_op", lambda: "ok")


# ===========================================================================
# _cache_dir PYTEST_CURRENT_TEST branch (line 32->34)
# ===========================================================================


def test_cache_dir_without_pytest_env(monkeypatch):
    """When PYTEST_CURRENT_TEST is not set, default cache dir is used."""
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("UNIFI_CACHE_DIR", raising=False)
    result = unifi._cache_dir()
    assert ".cache/unifi_network_maps" in str(result)
