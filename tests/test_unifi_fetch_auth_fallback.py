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
