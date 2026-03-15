"""Tests for UniFi firewall mutation wrappers."""

import pytest

from tests.unifi_mutation_helpers import make_config
from unifi_topology.adapters import unifi

pytestmark = pytest.mark.integration


def test_toggle_firewall_policy_calls_client(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    calls: list[tuple[str, str, str, dict[str, object]]] = []

    class FakeClient:
        def update_firewall_policy(
            self, site: str, policy_id: str, updates: dict[str, object]
        ) -> dict[str, object]:
            calls.append(("update", site, policy_id, updates))
            return {"_id": policy_id, **updates}

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: FakeClient())
    unifi.toggle_firewall_policy(make_config(), "p1", enabled=False)
    assert calls == [("update", "default", "p1", {"enabled": False})]


def test_swap_firewall_policy_order_calls_client(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    calls: list[tuple[str, str, str, str]] = []

    class FakeClient:
        def swap_firewall_policy_order(self, site: str, id_a: str, id_b: str) -> None:
            calls.append(("swap", site, id_a, id_b))

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: FakeClient())
    unifi.swap_firewall_policy_order(make_config(), "pa", "pb")
    assert calls == [("swap", "default", "pa", "pb")]


def test_toggle_invalidates_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    config = make_config()
    cache_path = tmp_path / f"fw_policies_{unifi._cache_key(config.url, config.site)}.json"
    unifi._save_cache(cache_path, [{"_id": "p1"}])

    class FakeClient:
        def update_firewall_policy(
            self, site: str, policy_id: str, updates: dict[str, object]
        ) -> dict[str, object]:
            return {"_id": policy_id}

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: FakeClient())
    unifi.toggle_firewall_policy(config, "p1", enabled=False)
    assert not cache_path.exists()


def test_toggle_clears_client_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    create_calls = {"count": 0}

    class FakeClient:
        def __init__(self, **kwargs):
            create_calls["count"] += 1

        def update_firewall_policy(self, site, policy_id, updates):
            return {"_id": policy_id}

        def get_devices(self, site, *, detailed=False):
            return [{"name": "dev"}]

    monkeypatch.setattr(unifi, "UnifiClient", FakeClient)
    config = make_config()
    unifi.fetch_devices(config, use_cache=False)
    assert create_calls["count"] == 1
    unifi.toggle_firewall_policy(config, "p1", enabled=False)
    assert create_calls["count"] == 1
    unifi.fetch_devices(config, use_cache=False)
    assert create_calls["count"] == 2


def test_swap_clears_client_cache(monkeypatch, tmp_path):
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
    assert create_calls["count"] == 1
    unifi.fetch_devices(config, use_cache=False)
    assert create_calls["count"] == 2
