"""Coverage for cache serialization paths in ``_fetch_cached``."""

# pyright: reportIndexIssue=false
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import json
from collections.abc import Sequence

from tests.unifi_fetch_coverage_helpers import CONFIG, StubClient, patch_client
from unifi_topology.adapters import unifi


def test_fetch_cached_saves_with_serialize(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    patch_client(monkeypatch, StubClient(devices=[{"mac": "raw"}]))

    def my_serialize(data: Sequence[object]) -> Sequence[object]:
        return [{"mac": "serialized"}]

    result = list(
        unifi._fetch_cached(
            CONFIG,
            cache_prefix="ser_test",
            operation="serialize test",
            api_call=lambda client, site: lambda: client.get_devices(site),
            serialize=my_serialize,
        )
    )
    assert result[0]["mac"] == "raw"
    cached = json.loads(
        (tmp_path / f"ser_test_{unifi._cache_key(CONFIG.url, CONFIG.site)}.json").read_text(
            encoding="utf-8"
        )
    )
    assert cached["data"][0]["mac"] == "serialized"


def test_fetch_cached_saves_without_serialize(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    patch_client(monkeypatch, StubClient(devices=[{"mac": "raw_data"}]))
    unifi._fetch_cached(
        CONFIG,
        cache_prefix="no_ser",
        operation="no serialize",
        api_call=lambda client, site: lambda: client.get_devices(site),
    )
    cached = json.loads(
        (tmp_path / f"no_ser_{unifi._cache_key(CONFIG.url, CONFIG.site)}.json").read_text(
            encoding="utf-8"
        )
    )
    assert cached["data"][0]["mac"] == "raw_data"
