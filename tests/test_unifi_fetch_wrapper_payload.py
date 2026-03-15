"""Wrapper fetch coverage for payload assembly."""

# pyright: reportIndexIssue=false
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from tests.unifi_fetch_coverage_helpers import CONFIG, StubClient, patch_client
from unifi_topology.adapters import unifi


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
