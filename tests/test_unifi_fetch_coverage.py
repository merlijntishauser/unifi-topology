"""Additional fetch-path coverage for unifi.py."""

# pyright: reportIndexIssue=false
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import json
import time
from collections.abc import Sequence
from pathlib import Path

import pytest

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


class _StubClient:
    def __init__(
        self,
        *,
        devices: list | None = None,
        clients: list | None = None,
        networks: list | None = None,
    ):
        self._devices = devices or []
        self._clients = clients or []
        self._networks = networks or []

    def get_devices(self, site: str, *, detailed: bool = False) -> list:
        return self._devices

    def get_clients(self, site: str) -> list:
        return self._clients

    def get_networkconf(self, site: str) -> list:
        return self._networks


def _patch_client(monkeypatch, client: object) -> None:
    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: client)


def test_fetch_clients_cache_hit(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"clients_{unifi._cache_key(_CONFIG.url, _CONFIG.site)}.json"
    _write_cache(cache_path, [{"mac": "aa:bb:cc:dd:ee:ff"}])

    def fail(*_a, **_k):
        raise AssertionError("should not create a client")

    monkeypatch.setattr(unifi, "_create_client", fail)
    clients = list(unifi.fetch_clients(_CONFIG))
    assert len(clients) == 1
    assert clients[0]["mac"] == "aa:bb:cc:dd:ee:ff"


def test_fetch_clients_raises_without_stale_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    class FailClient:
        def get_clients(self, site):
            raise RuntimeError("network error")

    _patch_client(monkeypatch, FailClient())
    with pytest.raises(RuntimeError, match="network error"):
        unifi.fetch_clients(_CONFIG)


def test_fetch_networks_fresh(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    _patch_client(monkeypatch, _StubClient(networks=[{"_id": "n1", "name": "LAN", "vlan": 1}]))
    networks = list(unifi.fetch_networks(_CONFIG))
    assert len(networks) == 1
    assert networks[0]["_id"] == "n1"
    assert (tmp_path / f"networks_{unifi._cache_key(_CONFIG.url, _CONFIG.site)}.json").exists()


def test_fetch_networks_cache_hit(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"networks_{unifi._cache_key(_CONFIG.url, _CONFIG.site)}.json"
    _write_cache(cache_path, [{"_id": "n1", "name": "cached"}])

    def fail(*_a, **_k):
        raise AssertionError("should not fetch")

    monkeypatch.setattr(unifi, "_create_client", fail)
    networks = list(unifi.fetch_networks(_CONFIG))
    assert len(networks) == 1
    assert networks[0]["name"] == "cached"


def test_fetch_networks_stale_fallback(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")
    cache_path = tmp_path / f"networks_{unifi._cache_key(_CONFIG.url, _CONFIG.site)}.json"
    _write_cache(cache_path, [{"_id": "n1", "name": "stale"}], age_seconds=3600)

    class FailClient:
        def get_networkconf(self, site):
            raise RuntimeError("fail")

    _patch_client(monkeypatch, FailClient())
    networks = list(unifi.fetch_networks(_CONFIG))
    assert len(networks) == 1
    assert networks[0]["name"] == "stale"


def test_fetch_networks_raises_without_stale(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    class FailClient:
        def get_networkconf(self, site):
            raise RuntimeError("network error")

    _patch_client(monkeypatch, FailClient())
    with pytest.raises(RuntimeError, match="network error"):
        unifi.fetch_networks(_CONFIG)


def test_fetch_payload_combines_all(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")
    _patch_client(
        monkeypatch,
        _StubClient(
            devices=[{"mac": "aa", "name": "switch", "type": "usw"}],
            clients=[{"mac": "bb", "name": "laptop"}],
            networks=[{"_id": "n1", "name": "LAN", "vlan": 1, "purpose": "corporate"}],
        ),
    )
    result = unifi.fetch_payload(_CONFIG)
    assert "devices" in result
    assert "clients" in result
    assert "networks" in result
    assert "vlan_info" in result
    assert len(result["devices"]) == 1
    assert len(result["clients"]) == 1


def test_fetch_payload_without_clients(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")
    _patch_client(
        monkeypatch,
        _StubClient(
            devices=[{"mac": "aa", "name": "switch", "type": "usw"}],
            networks=[{"_id": "n1", "name": "LAN"}],
        ),
    )
    result = unifi.fetch_payload(_CONFIG, include_clients=False)
    assert result["clients"] == []
    assert len(result["devices"]) == 1


def test_fetch_cached_cache_hit(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"test_resource_{unifi._cache_key(_CONFIG.url, _CONFIG.site)}.json"
    _write_cache(cache_path, [{"cached": True}])

    def fail(*_a, **_k):
        raise AssertionError("should not fetch")

    monkeypatch.setattr(unifi, "_create_client", fail)
    result = list(
        unifi._fetch_cached(
            _CONFIG,
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
    cache_path = tmp_path / f"stale_test_{unifi._cache_key(_CONFIG.url, _CONFIG.site)}.json"
    _write_cache(cache_path, [{"stale": True}], age_seconds=3600)

    class FailClient:
        pass

    _patch_client(monkeypatch, FailClient())
    result = list(
        unifi._fetch_cached(
            _CONFIG,
            cache_prefix="stale_test",
            operation="stale test",
            api_call=lambda client, site: lambda: (_ for _ in ()).throw(RuntimeError("fail")),
        )
    )
    assert len(result) == 1
    assert result[0]["stale"] is True


def test_fetch_cached_saves_with_serialize(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    _patch_client(monkeypatch, _StubClient(devices=[{"mac": "raw"}]))

    def my_serialize(data: Sequence[object]) -> Sequence[object]:
        return [{"mac": "serialized"}]

    result = list(
        unifi._fetch_cached(
            _CONFIG,
            cache_prefix="ser_test",
            operation="serialize test",
            api_call=lambda client, site: lambda: client.get_devices(site),
            serialize=my_serialize,
        )
    )
    assert result[0]["mac"] == "raw"
    cached = json.loads(
        (tmp_path / f"ser_test_{unifi._cache_key(_CONFIG.url, _CONFIG.site)}.json").read_text(
            encoding="utf-8"
        )
    )
    assert cached["data"][0]["mac"] == "serialized"


def test_fetch_cached_saves_without_serialize(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    _patch_client(monkeypatch, _StubClient(devices=[{"mac": "raw_data"}]))
    unifi._fetch_cached(
        _CONFIG,
        cache_prefix="no_ser",
        operation="no serialize",
        api_call=lambda client, site: lambda: client.get_devices(site),
    )
    cached = json.loads(
        (tmp_path / f"no_ser_{unifi._cache_key(_CONFIG.url, _CONFIG.site)}.json").read_text(
            encoding="utf-8"
        )
    )
    assert cached["data"][0]["mac"] == "raw_data"


def test_fetch_cached_raises_without_stale(monkeypatch, tmp_path):
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
