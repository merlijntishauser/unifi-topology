"""Tests for UniFi firewall policy toggle wrapper."""

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


def test_toggle_preserves_client_session(monkeypatch, tmp_path):
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
    # A successful write must not discard the authenticated session.
    unifi.fetch_devices(config, use_cache=False)
    assert create_calls["count"] == 1


def test_firewall_writes_use_remembered_legacy_auth(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    unifi.clear_client_cache()
    config = make_config()
    styles: list[bool] = []

    class FakeClient:
        def update_firewall_policy(self, *_args: object) -> dict[str, object]:
            return {}

        def swap_firewall_policy_order(self, *_args: object) -> None:
            return None

    def create(_config: object, *, is_udm_pro: bool) -> FakeClient:
        styles.append(is_udm_pro)
        return FakeClient()

    monkeypatch.setattr(unifi, "_create_client", create)
    monkeypatch.setitem(unifi._auth_style_cache, config.url, False)
    unifi.toggle_firewall_policy(config, "p1", enabled=False)
    unifi.swap_firewall_policy_order(config, "pa", "pb")
    unifi.clear_client_cache()
    assert styles == [False]
