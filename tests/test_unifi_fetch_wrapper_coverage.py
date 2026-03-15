"""Additional wrapper fetch coverage for ``unifi.py``."""

# pyright: reportIndexIssue=false
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import pytest

from tests.unifi_fetch_coverage_helpers import CONFIG, StubClient, patch_client, write_cache
from unifi_topology.adapters import unifi


def test_fetch_clients_cache_hit(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"clients_{unifi._cache_key(CONFIG.url, CONFIG.site)}.json"
    write_cache(cache_path, [{"mac": "aa:bb:cc:dd:ee:ff"}])

    def fail(*_a, **_k):
        raise AssertionError("should not create a client")

    monkeypatch.setattr(unifi, "_create_client", fail)
    clients = list(unifi.fetch_clients(CONFIG))
    assert len(clients) == 1
    assert clients[0]["mac"] == "aa:bb:cc:dd:ee:ff"


def test_fetch_clients_raises_without_stale_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    class FailClient:
        def get_clients(self, site):
            raise RuntimeError("network error")

    patch_client(monkeypatch, FailClient())
    with pytest.raises(RuntimeError, match="network error"):
        unifi.fetch_clients(CONFIG)


def test_fetch_networks_fresh(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    patch_client(monkeypatch, StubClient(networks=[{"_id": "n1", "name": "LAN", "vlan": 1}]))
    networks = list(unifi.fetch_networks(CONFIG))
    assert len(networks) == 1
    assert networks[0]["_id"] == "n1"
    assert (tmp_path / f"networks_{unifi._cache_key(CONFIG.url, CONFIG.site)}.json").exists()


def test_fetch_networks_cache_hit(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "3600")
    cache_path = tmp_path / f"networks_{unifi._cache_key(CONFIG.url, CONFIG.site)}.json"
    write_cache(cache_path, [{"_id": "n1", "name": "cached"}])

    def fail(*_a, **_k):
        raise AssertionError("should not fetch")

    monkeypatch.setattr(unifi, "_create_client", fail)
    networks = list(unifi.fetch_networks(CONFIG))
    assert len(networks) == 1
    assert networks[0]["name"] == "cached"


def test_fetch_networks_stale_fallback(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")
    cache_path = tmp_path / f"networks_{unifi._cache_key(CONFIG.url, CONFIG.site)}.json"
    write_cache(cache_path, [{"_id": "n1", "name": "stale"}], age_seconds=3600)

    class FailClient:
        def get_networkconf(self, site):
            raise RuntimeError("fail")

    patch_client(monkeypatch, FailClient())
    networks = list(unifi.fetch_networks(CONFIG))
    assert len(networks) == 1
    assert networks[0]["name"] == "stale"


def test_fetch_networks_raises_without_stale(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")

    class FailClient:
        def get_networkconf(self, site):
            raise RuntimeError("network error")

    patch_client(monkeypatch, FailClient())
    with pytest.raises(RuntimeError, match="network error"):
        unifi.fetch_networks(CONFIG)


def test_fetch_payload_combines_all(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")
    patch_client(
        monkeypatch,
        StubClient(
            devices=[{"mac": "aa", "name": "switch", "type": "usw"}],
            clients=[{"mac": "bb", "name": "laptop"}],
            networks=[{"_id": "n1", "name": "LAN", "vlan": 1, "purpose": "corporate"}],
        ),
    )
    result = unifi.fetch_payload(CONFIG)
    assert "devices" in result
    assert "clients" in result
    assert "networks" in result
    assert "vlan_info" in result
    assert len(result["devices"]) == 1
    assert len(result["clients"]) == 1


def test_fetch_payload_without_clients(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")
    patch_client(
        monkeypatch,
        StubClient(
            devices=[{"mac": "aa", "name": "switch", "type": "usw"}],
            networks=[{"_id": "n1", "name": "LAN"}],
        ),
    )
    result = unifi.fetch_payload(CONFIG, include_clients=False)
    assert result["clients"] == []
    assert len(result["devices"]) == 1
