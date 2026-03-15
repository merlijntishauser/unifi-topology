"""Tests for UniFi client cache reuse behavior."""

import pytest

from tests.unifi_mutation_helpers import make_config
from unifi_topology.adapters import unifi
from unifi_topology.adapters.config import Config

pytestmark = pytest.mark.integration


def test_client_cache_reuses_same_client(monkeypatch):
    instances: list[object] = []

    class FakeClient:
        def __init__(self, **kwargs):
            instances.append(self)

    monkeypatch.setattr(unifi, "UnifiClient", FakeClient)
    config = make_config()
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
    config = make_config()
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
    config = make_config()
    unifi.fetch_devices(config, use_cache=False)
    unifi.fetch_clients(config, use_cache=False)
    assert create_calls["count"] == 1
