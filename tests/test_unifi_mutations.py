import pytest

from unifi_topology.adapters import unifi
from unifi_topology.adapters.config import Config

pytestmark = pytest.mark.integration


def _config() -> Config:
    return Config(
        url="https://example",
        site="default",
        user="user",
        password="pass",
        verify_ssl=True,
    )


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
    unifi.toggle_firewall_policy(_config(), "p1", enabled=False)
    assert calls == [("update", "default", "p1", {"enabled": False})]


def test_swap_firewall_policy_order_calls_client(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    calls: list[tuple[str, str, str, str]] = []

    class FakeClient:
        def swap_firewall_policy_order(self, site: str, id_a: str, id_b: str) -> None:
            calls.append(("swap", site, id_a, id_b))

    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: FakeClient())
    unifi.swap_firewall_policy_order(_config(), "pa", "pb")
    assert calls == [("swap", "default", "pa", "pb")]


def test_toggle_invalidates_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    config = _config()
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


def test_client_cache_reuses_same_client(monkeypatch):
    instances: list[object] = []

    class FakeClient:
        def __init__(self, **kwargs):
            instances.append(self)

    monkeypatch.setattr(unifi, "UnifiClient", FakeClient)
    config = _config()
    client_a = unifi._get_or_create_client(config, is_udm_pro=True)
    client_b = unifi._get_or_create_client(config, is_udm_pro=True)
    assert client_a is client_b
    assert len(instances) == 1


def test_clear_client_cache_forces_new_client(monkeypatch):
    instances: list[object] = []

    class FakeClient:
        def __init__(self, **kwargs):
            instances.append(self)

    monkeypatch.setattr(unifi, "UnifiClient", FakeClient)
    config = _config()
    client_a = unifi._get_or_create_client(config, is_udm_pro=True)
    unifi.clear_client_cache()
    client_b = unifi._get_or_create_client(config, is_udm_pro=True)
    assert client_a is not client_b
    assert len(instances) == 2


def test_different_configs_get_different_clients(monkeypatch):
    instances: list[object] = []

    class FakeClient:
        def __init__(self, **kwargs):
            instances.append(self)

    monkeypatch.setattr(unifi, "UnifiClient", FakeClient)
    config_a = Config(
        url="https://example-a",
        site="default",
        user="user_a",
        password="pass",
        verify_ssl=True,
    )
    config_b = Config(
        url="https://example-b",
        site="default",
        user="user_b",
        password="pass",
        verify_ssl=True,
    )
    client_a = unifi._get_or_create_client(config_a, is_udm_pro=True)
    client_b = unifi._get_or_create_client(config_b, is_udm_pro=True)
    assert client_a is not client_b
    assert len(instances) == 2


def test_connect_and_fetch_reuses_cached_client(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "0")
    create_calls = {"count": 0}

    class FakeClient:
        def __init__(self, **kwargs):
            create_calls["count"] += 1

        def get_devices(self, site, *, detailed=False):
            return [{"name": "dev"}]

        def get_clients(self, site):
            return [{"name": "cli"}]

    monkeypatch.setattr(unifi, "UnifiClient", FakeClient)
    config = _config()
    unifi.fetch_devices(config, use_cache=False)
    unifi.fetch_clients(config, use_cache=False)
    assert create_calls["count"] == 1


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
    config = _config()
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
    config = _config()
    unifi.fetch_devices(config, use_cache=False)
    assert create_calls["count"] == 1
    unifi.swap_firewall_policy_order(config, "pa", "pb")
    assert create_calls["count"] == 1
    unifi.fetch_devices(config, use_cache=False)
    assert create_calls["count"] == 2
