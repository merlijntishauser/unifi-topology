"""Tests for UniFi OS X-API-KEY authentication."""

import pytest
import requests

from tests.unifi_api_helpers import FakeResponse, FakeSession
from unifi_topology.adapters.config import Config
from unifi_topology.adapters.unifi_api import UnifiAuthError, UnifiClient

pytestmark = pytest.mark.unit


def _make_api_key_client(monkeypatch, session, *, is_udm_pro=True):
    monkeypatch.setattr(requests, "Session", lambda: session)
    return UnifiClient(
        url="https://unifi.local",
        api_key="secret-key",
        is_udm_pro=is_udm_pro,
        verify_ssl=True,
    )


def test_api_key_client_skips_authenticate(monkeypatch):
    session = FakeSession()
    _make_api_key_client(monkeypatch, session)
    assert session.calls == []


def test_api_key_client_sets_header(monkeypatch):
    session = FakeSession()
    _make_api_key_client(monkeypatch, session)
    assert session.headers["X-API-KEY"] == "secret-key"


def test_api_key_client_get_includes_header(monkeypatch):
    devices_resp = FakeResponse(json_data={"data": [{"name": "ap"}]})
    session = FakeSession([devices_resp])
    client = _make_api_key_client(monkeypatch, session)
    result = client.get_devices("default")
    assert result == [{"name": "ap"}]
    assert session.headers["X-API-KEY"] == "secret-key"
    assert session.calls[0][0] == "GET"


def test_api_key_401_raises_without_reauth(monkeypatch):
    unauthorized = FakeResponse(status_code=401, json_data={}, ok=False)
    session = FakeSession([unauthorized])
    client = _make_api_key_client(monkeypatch, session)
    with pytest.raises(UnifiAuthError, match="API key rejected"):
        client.get_devices("default")
    assert [call[0] for call in session.calls] == ["GET"]


def test_config_api_key_only_is_valid():
    config = Config(url="https://x", site="default", api_key="k")
    assert config.api_key == "k"
    assert config.user is None
    assert config.password is None


def test_config_rejects_api_key_with_credentials():
    with pytest.raises(ValueError, match="exactly one of api_key"):
        Config(url="https://x", site="default", user="u", password="p", api_key="k")


def test_config_requires_some_auth():
    with pytest.raises(ValueError, match="exactly one of api_key"):
        Config(url="https://x", site="default")


def test_config_from_env_uses_api_key(monkeypatch):
    monkeypatch.setenv("UNIFI_URL", "https://example.local")
    monkeypatch.setenv("UNIFI_API_KEY", "abc123")
    monkeypatch.delenv("UNIFI_USER", raising=False)
    monkeypatch.delenv("UNIFI_PASS", raising=False)
    config = Config.from_env()
    assert config.api_key == "abc123"
    assert config.user is None


def test_config_from_env_prefers_api_key_over_credentials(monkeypatch):
    monkeypatch.setenv("UNIFI_URL", "https://example.local")
    monkeypatch.setenv("UNIFI_API_KEY", "abc123")
    monkeypatch.setenv("UNIFI_USER", "u")
    monkeypatch.setenv("UNIFI_PASS", "p")
    config = Config.from_env()
    assert config.api_key == "abc123"
    assert config.user is None
    assert config.password is None
