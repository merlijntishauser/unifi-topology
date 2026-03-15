import json
import time

import pytest

from unifi_topology.adapters import unifi
from unifi_topology.adapters.config import Config

pytestmark = pytest.mark.integration


def _config() -> Config:
    return Config(
        url="https://example",
        site="default",
        user="user",
        password="pass",
        verify_ssl=True,
    )


def test_load_cache_with_age_requires_dict_payload(tmp_path):
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
    data, age = unifi._load_cache_with_age(cache_path)
    assert data is None
    assert age is None


def test_load_cache_with_age_requires_timestamp(tmp_path):
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"data": []}), encoding="utf-8")
    data, age = unifi._load_cache_with_age(cache_path)
    assert data is None
    assert age is None


def test_load_cache_with_age_requires_list_data(tmp_path):
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"timestamp": time.time(), "data": {}}), encoding="utf-8")
    data, age = unifi._load_cache_with_age(cache_path)
    assert data is None
    assert age is None


def test_load_cache_respects_ttl(tmp_path):
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(
        json.dumps({"timestamp": time.time() - 10, "data": [{"ok": True}]}),
        encoding="utf-8",
    )
    assert unifi._load_cache(cache_path, ttl_seconds=0) is None
    assert unifi._load_cache(cache_path, ttl_seconds=1) is None


def test_cache_ttl_seconds_invalid_uses_default(monkeypatch):
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "nope")
    assert unifi._cache_ttl_seconds() == 3600


def test_retry_attempts_invalid_uses_default(monkeypatch):
    monkeypatch.setenv("UNIFI_RETRY_ATTEMPTS", "nope")
    assert unifi._retry_attempts() == 2


def test_retry_backoff_invalid_uses_default(monkeypatch):
    monkeypatch.setenv("UNIFI_RETRY_BACKOFF_SECONDS", "nope")
    assert unifi._retry_backoff_seconds() == 0.5


def test_request_timeout_invalid_returns_none(monkeypatch):
    monkeypatch.setenv("UNIFI_REQUEST_TIMEOUT_SECONDS", "nope")
    assert unifi._request_timeout_seconds() is None


def test_serialize_lldp_entries_filters_missing_fields():
    class Entry:
        def __init__(self, chassis_id=None, port_id=None):
            self.chassis_id = chassis_id
            self.port_id = port_id

    entries = [Entry(chassis_id="aa", port_id="1"), Entry(chassis_id="bb")]
    serialized = unifi._serialize_lldp_entries(entries)
    assert len(serialized) == 1
    assert serialized[0]["chassis_id"] == "aa"


def test_serialize_lldp_entries_accepts_single_object():
    serialized = unifi._serialize_lldp_entries({"chassis_id": "aa", "port_id": "1"})
    assert serialized[0]["port_id"] == "1"


def test_serialize_uplink_returns_none_when_empty():
    assert unifi._serialize_uplink({"uplink_mac": None, "uplink_device_name": None}) is None


def test_serialize_uplink_reads_fallback_fields():
    data = unifi._serialize_uplink(
        {"uplink_device_mac": "aa", "uplink_name": "Core", "port_idx": 3}
    )
    assert data == {"uplink_mac": "aa", "uplink_device_name": "Core", "uplink_remote_port": 3}


def test_serialize_port_entry_reads_aggregation_group():
    data = unifi._serialize_port_entry({"port_idx": 1, "agg_id": "agg2"})
    assert data["aggregation_group"] == "agg2"


def test_is_rate_limited_detects_429():
    assert unifi._is_rate_limited(Exception("HTTP 429 Too Many Requests"))
    assert not unifi._is_rate_limited(Exception("Invalid credentials"))


def test_invalidate_cache_removes_file(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    config = _config()
    cache_path = tmp_path / f"fw_policies_{unifi._cache_key(config.url, config.site)}.json"
    unifi._save_cache(cache_path, [{"_id": "p1"}])
    assert cache_path.exists()
    removed = unifi.invalidate_cache(config)
    assert removed == 1
    assert not cache_path.exists()


def test_invalidate_cache_returns_zero_when_no_file(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    removed = unifi.invalidate_cache(_config())
    assert removed == 0


def test_invalidate_cache_multiple_prefixes(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    config = _config()
    for prefix in ("fw_policies", "fw_zones"):
        cache_path = tmp_path / f"{prefix}_{unifi._cache_key(config.url, config.site)}.json"
        unifi._save_cache(cache_path, [{"data": True}])
    removed = unifi.invalidate_cache(config, prefixes=("fw_policies", "fw_zones"))
    assert removed == 2
