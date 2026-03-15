"""Cache invalidation and client eviction coverage for unifi.py."""

# pyright: reportIndexIssue=false
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import json
import time
from pathlib import Path

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
