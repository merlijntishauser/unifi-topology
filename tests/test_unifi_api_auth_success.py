import pytest

from tests.unifi_api_helpers import FakeResponse, FakeSession, make_client

pytestmark = pytest.mark.unit


def test_authenticate_udm_pro(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    data_resp = FakeResponse(json_data={"data": [{"name": "switch"}]})
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)

    assert session.calls[0] == (
        "POST",
        "https://unifi.local/api/auth/login",
        {"json": {"username": "admin", "password": "secret"}, "verify": True, "timeout": None},
    )
    assert client._api_base == "https://unifi.local/proxy/network"


def test_authenticate_legacy(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": []})
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session, is_udm_pro=False)

    assert session.calls[0] == (
        "POST",
        "https://unifi.local/api/login",
        {"json": {"username": "admin", "password": "secret"}, "verify": True, "timeout": None},
    )
    assert client._api_base == "https://unifi.local"


def test_csrf_token_captured_on_auth(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True}, headers={"X-CSRF-Token": "tok123"})
    data_resp = FakeResponse(json_data=[{"_id": "p1", "enabled": True}])
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)
    assert client._csrf_token == "tok123"


def test_csrf_token_none_when_absent(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    session = FakeSession([auth_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)
    assert client._csrf_token is None
