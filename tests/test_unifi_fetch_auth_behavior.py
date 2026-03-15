import pytest

from tests.unifi_fetch_helpers import config
from unifi_topology.adapters import unifi
from unifi_topology.adapters.config import Config
from unifi_topology.adapters.unifi_api import UnifiAuthError

pytestmark = pytest.mark.integration


def test_fetch_devices_falls_back_on_auth_error(monkeypatch):
    def fake_create_client(config, *, is_udm_pro):
        if is_udm_pro:
            raise UnifiAuthError("bad auth")

        class Client:
            def get_devices(self, site, *, detailed=False):
                return [object(), object()]

        return Client()

    monkeypatch.setattr(unifi, "_create_client", fake_create_client)
    devices = list(unifi.fetch_devices(config()))
    assert len(devices) == 2


def test_create_client_passes_config(monkeypatch):
    captured = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(unifi, "UnifiClient", FakeClient)
    client_config = Config(
        url="https://example", site="default", user="user", password="pass", verify_ssl=False
    )
    unifi._create_client(client_config, is_udm_pro=True)
    assert captured["verify_ssl"] is False


def test_fetch_clients_falls_back_on_auth_error(monkeypatch):
    def fake_create_client(config, *, is_udm_pro):
        if is_udm_pro:
            raise UnifiAuthError("bad auth")

        class Client:
            def get_clients(self, site):
                return [object()]

        return Client()

    monkeypatch.setattr(unifi, "_create_client", fake_create_client)
    clients = list(unifi.fetch_clients(config()))
    assert len(clients) == 1


def test_rate_limited_auth_error_skips_legacy_retry(monkeypatch, tmp_path):
    import json
    import time

    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")
    calls = {"init_count": 0}

    def fake_create_client(config, *, is_udm_pro):
        calls["init_count"] += 1
        raise UnifiAuthError("HTTP 429 Too Many Requests")

    monkeypatch.setattr(unifi, "_create_client", fake_create_client)
    cache_path = tmp_path / f"devices_{unifi._cache_key(config().url, config().site, 'True')}.json"
    cache_path.write_text(
        json.dumps({"timestamp": time.time() - 3600, "data": [{"stale": True}]}),
        encoding="utf-8",
    )
    devices = list(unifi.fetch_devices(config()))
    assert calls["init_count"] == 1
    from tests.unifi_fetch_helpers import first_mapping

    assert first_mapping(devices)["stale"] is True


def test_rate_limited_auth_error_raises_without_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("UNIFI_CACHE_TTL_SECONDS", "1")

    def fake_create_client(config, *, is_udm_pro):
        raise UnifiAuthError("HTTP 429 Too Many Requests")

    monkeypatch.setattr(unifi, "_create_client", fake_create_client)
    with pytest.raises(UnifiAuthError, match="429"):
        unifi.fetch_devices(config())


def test_non_429_auth_error_retries_legacy(monkeypatch, tmp_path):
    monkeypatch.setenv("UNIFI_CACHE_DIR", str(tmp_path))

    def fake_create_client(config, *, is_udm_pro):
        if is_udm_pro:
            raise UnifiAuthError("Invalid credentials")

        class Client:
            def get_devices(self, site, *, detailed=False):
                return [{"ok": True}]

        return Client()

    monkeypatch.setattr(unifi, "_create_client", fake_create_client)
    devices = list(unifi.fetch_devices(config()))
    assert len(devices) == 1
