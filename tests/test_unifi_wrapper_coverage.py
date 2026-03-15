"""Additional wrapper coverage for unifi.py."""

# pyright: reportIndexIssue=false
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

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


class _StubClient:
    def __init__(
        self,
        *,
        firewall_zones: list | None = None,
        firewall_policies: list | None = None,
        firewall_groups: list | None = None,
        clients: list | None = None,
    ):
        self._fw_zones = firewall_zones or []
        self._fw_policies = firewall_policies or []
        self._fw_groups = firewall_groups or []
        self._clients = clients or []

    def get_firewall_zones(self, site: str) -> list:
        return self._fw_zones

    def get_firewall_policies(self, site: str) -> list:
        return self._fw_policies

    def get_firewall_groups(self, site: str) -> list:
        return self._fw_groups

    def get_clients(self, site: str) -> list:
        return self._clients


def _patch_client(monkeypatch, client: object) -> None:
    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: client)


def test_fetch_firewall_zones(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")
    _patch_client(monkeypatch, _StubClient(firewall_zones=[{"_id": "z1", "name": "LAN"}]))
    result = list(unifi.fetch_firewall_zones(_CONFIG))
    assert len(result) == 1
    assert result[0]["_id"] == "z1"


def test_fetch_firewall_policies(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")
    _patch_client(monkeypatch, _StubClient(firewall_policies=[{"_id": "p1", "name": "Block"}]))
    result = list(unifi.fetch_firewall_policies(_CONFIG))
    assert len(result) == 1
    assert result[0]["_id"] == "p1"


def test_fetch_firewall_groups(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")
    _patch_client(monkeypatch, _StubClient(firewall_groups=[{"_id": "g1", "name": "DNS Servers"}]))
    result = list(unifi.fetch_firewall_groups(_CONFIG))
    assert len(result) == 1
    assert result[0]["_id"] == "g1"


def test_fetch_payload_clients_excluded():
    assert (
        unifi._fetch_payload_clients(_CONFIG, site=None, include_clients=False, use_cache=False)
        == []
    )


def test_fetch_payload_clients_included(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")
    _patch_client(monkeypatch, _StubClient(clients=[{"mac": "cl1"}]))
    result = unifi._fetch_payload_clients(_CONFIG, site=None, include_clients=True, use_cache=False)
    assert len(result) == 1
    assert result[0]["mac"] == "cl1"


def test_call_with_retries_zero_attempts(monkeypatch):
    monkeypatch.setenv("UNIFI_RETRY_ATTEMPTS", "1")
    monkeypatch.setenv("UNIFI_RETRY_BACKOFF_SECONDS", "0")
    monkeypatch.setattr(unifi, "_retry_attempts", lambda: 0)
    with pytest.raises(RuntimeError, match="Failed test_op"):
        unifi._call_with_retries("test_op", lambda: "ok")
