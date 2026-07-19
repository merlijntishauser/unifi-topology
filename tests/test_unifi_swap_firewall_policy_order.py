"""Tests for UniFi firewall policy swap wrapper."""

import pytest

from tests.unifi_mutation_helpers import make_config
from unifi_topology.adapters import unifi

pytestmark = pytest.mark.integration


def test_swap_firewall_policy_order_calls_client(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    calls: list[tuple[str, str, str, str]] = []

    class FakeClient:
        def swap_firewall_policy_order(self, site: str, id_a: str, id_b: str) -> None:
            calls.append(("swap", site, id_a, id_b))

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: FakeClient())
    unifi.swap_firewall_policy_order(make_config(), "pa", "pb")
    assert calls == [("swap", "default", "pa", "pb")]


def test_swap_preserves_client_session(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    create_calls = {"count": 0}

    class FakeClient:
        def __init__(self, **kwargs):
            create_calls["count"] += 1

        def swap_firewall_policy_order(self, site, id_a, id_b):
            pass

        def get_devices(self, site, *, detailed=False):
            return [{"name": "dev"}]

    monkeypatch.setattr(unifi, "UnifiClient", FakeClient)
    config = make_config()
    unifi.fetch_devices(config, use_cache=False)
    assert create_calls["count"] == 1
    unifi.swap_firewall_policy_order(config, "pa", "pb")
    # A successful write must not discard the authenticated session.
    unifi.fetch_devices(config, use_cache=False)
    assert create_calls["count"] == 1
