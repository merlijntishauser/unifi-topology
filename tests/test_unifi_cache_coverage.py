"""Additional cache and serialization coverage for unifi.py."""

# pyright: reportIndexIssue=false
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import json
import stat
import time
from pathlib import Path
from unittest.mock import patch

from unifi_topology.adapters import unifi
from unifi_topology.adapters.config import Config

_CONFIG = Config(
    url="https://example",
    site="default",
    user="user",
    password="pass",
    verify_ssl=True,
)


def _write_cache(path: Path, data: list[object], *, age_seconds: float = 0.0) -> None:
    payload = {"timestamp": time.time() - age_seconds, "data": data}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")


def test_device_lldp_value_prefers_lldp_info():
    assert unifi._device_lldp_value({"lldp_info": [{"chassis_id": "aa"}], "lldp": "ignored"}) == [
        {"chassis_id": "aa"}
    ]


def test_device_lldp_value_falls_back_to_lldp():
    assert unifi._device_lldp_value({"lldp": [{"chassis_id": "bb"}]}) == [{"chassis_id": "bb"}]


def test_device_lldp_value_falls_back_to_lldp_table():
    assert unifi._device_lldp_value({"lldp_table": [{"chassis_id": "cc"}]}) == [
        {"chassis_id": "cc"}
    ]


def test_device_lldp_value_returns_none_when_all_missing():
    assert unifi._device_lldp_value({}) is None


def test_serialize_network_for_cache():
    result = unifi._serialize_network_for_cache(
        {
            "_id": "net1",
            "name": "LAN",
            "vlan": 10,
            "vlan_enabled": True,
            "purpose": "corporate",
            "enabled": True,
        }
    )
    assert result["_id"] == "net1"
    assert result["name"] == "LAN"
    assert result["vlan"] == 10
    assert result["vlan_enabled"] is True
    assert result["purpose"] == "corporate"
    assert result["enabled"] is True


def test_serialize_network_for_cache_uses_fallback_fields():
    result = unifi._serialize_network_for_cache({"id": "net2", "network_name": "IoT", "vlan_id": 20})
    assert result["_id"] == "net2"
    assert result["name"] == "IoT"
    assert result["vlan"] == 20


def test_serialize_networks_for_cache():
    result = unifi._serialize_networks_for_cache(
        [
            {"_id": "n1", "name": "LAN", "vlan": 1, "purpose": "corporate"},
            {"_id": "n2", "name": "Guest", "vlan": 100, "purpose": "guest"},
        ]
    )
    assert len(result) == 2
    assert result[0]["_id"] == "n1"
    assert result[1]["_id"] == "n2"


def test_cache_lock_release_oserror_is_swallowed(tmp_path):
    lock_target = tmp_path / "test.json"
    lock_target.write_text("{}", encoding="utf-8")
    with patch.object(unifi, "_release_cache_lock", side_effect=OSError("boom")):
        with unifi._cache_lock(lock_target):
            pass


def test_is_cache_dir_safe_returns_true_for_nonexistent(tmp_path):
    assert unifi._is_cache_dir_safe(tmp_path / "does_not_exist") is True


def test_is_cache_dir_safe_stat_failure(tmp_path):
    target = tmp_path / "dir"
    target.mkdir()
    with (
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "stat", side_effect=OSError("permission denied")),
    ):
        assert unifi._is_cache_dir_safe(target) is False


def test_is_cache_dir_safe_world_writable(tmp_path):
    target = tmp_path / "unsafe"
    target.mkdir()
    target.chmod(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    assert unifi._is_cache_dir_safe(target) is False
    target.chmod(stat.S_IRWXU)


def test_load_cache_with_age_corrupt_file(tmp_path):
    cache_path = tmp_path / "corrupt.json"
    cache_path.write_text("not valid json {{{", encoding="utf-8")
    data, age = unifi._load_cache_with_age(cache_path)
    assert data is None
    assert age is None


def test_invalidate_cache_oserror(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    cache_path = tmp_path / f"fw_policies_{unifi._cache_key(_CONFIG.url, _CONFIG.site)}.json"
    _write_cache(cache_path, [{"_id": "p1"}])
    original_cache_lock = unifi._cache_lock

    from contextlib import contextmanager

    @contextmanager
    def _failing_lock(path):
        with original_cache_lock(path):
            raise OSError("cannot unlink")

    monkeypatch.setattr(unifi, "_cache_lock", _failing_lock)
    assert unifi.invalidate_cache(_CONFIG) == 0


def test_evict_client_removes_cached_entry(monkeypatch):
    class FakeClient:
        def __init__(self, **kwargs):
            pass

    monkeypatch.setattr(unifi, "UnifiClient", FakeClient)
    client = unifi._get_or_create_client(_CONFIG, is_udm_pro=True)
    assert client is not None
    unifi._evict_client(_CONFIG, is_udm_pro=True)
    assert unifi._get_or_create_client(_CONFIG, is_udm_pro=True) is not client


def test_evict_client_noop_when_not_cached():
    config = Config(
        url="https://no-such-host",
        site="default",
        user="nobody",
        password="none",
        verify_ssl=True,
    )
    unifi._evict_client(config, is_udm_pro=True)


def test_cache_dir_without_pytest_env(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("UNIFI_CACHE_DIR", raising=False)
    assert ".cache/unifi_network_maps" in str(unifi._cache_dir())
