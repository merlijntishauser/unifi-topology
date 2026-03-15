"""Coverage for cache hit and stale fallback paths in ``_fetch_cached``."""

# pyright: reportIndexIssue=false
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import pytest

from tests.unifi_fetch_coverage_helpers import CONFIG, patch_client, write_cache
from unifi_topology.adapters import unifi


def test_fetch_cached_cache_hit(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"test_resource_{unifi._cache_key(CONFIG.url, CONFIG.site)}.json"
    write_cache(cache_path, [{"cached": True}])

    def fail(*_a, **_k):
        raise AssertionError("should not fetch")

    monkeypatch.setattr(unifi, "_create_client", fail)
    result = list(
        unifi._fetch_cached(
            CONFIG,
            cache_prefix="test_resource",
            operation="test resource",
            api_call=lambda client, site: lambda: client.get_devices(site),
        )
    )
    assert len(result) == 1
    assert result[0]["cached"] is True


def test_fetch_cached_stale_fallback(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")
    cache_path = tmp_path / f"stale_test_{unifi._cache_key(CONFIG.url, CONFIG.site)}.json"
    write_cache(cache_path, [{"stale": True}], age_seconds=3600)

    class FailClient:
        pass

    patch_client(monkeypatch, FailClient())
    result = list(
        unifi._fetch_cached(
            CONFIG,
            cache_prefix="stale_test",
            operation="stale test",
            api_call=lambda client, site: lambda: (_ for _ in ()).throw(RuntimeError("fail")),
        )
    )
    assert len(result) == 1
    assert result[0]["stale"] is True


def test_fetch_cached_raises_without_stale(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    class FailClient:
        def get_devices(self, site, *, detailed=False):
            raise RuntimeError("fail")

    patch_client(monkeypatch, FailClient())
    with pytest.raises(RuntimeError, match="fail"):
        unifi._fetch_cached(
            CONFIG,
            cache_prefix="raise_test",
            operation="raise test",
            api_call=lambda client, site: lambda: client.get_devices(site),
        )
