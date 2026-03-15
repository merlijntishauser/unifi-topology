import json
import time

import pytest

from unifi_topology.adapters import unifi

pytestmark = pytest.mark.integration


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
