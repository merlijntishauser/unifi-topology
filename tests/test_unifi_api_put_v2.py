import pytest

from tests.unifi_api_helpers import FakeResponse, FakeSession, make_client
from unifi_topology.adapters.unifi_api import UnifiWriteError

pytestmark = pytest.mark.unit


def test_put_v2_sends_csrf_token(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True}, headers={"X-CSRF-Token": "csrf1"})
    put_resp = FakeResponse(json_data={"_id": "p1", "enabled": False})
    session = FakeSession([auth_resp, put_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)
    client._put_v2("/v2/api/site/default/firewall-policies/p1", {"enabled": False})
    put_call = session.calls[1]
    assert put_call[0] == "PUT"
    assert put_call[2]["headers"]["X-CSRF-Token"] == "csrf1"


def test_put_v2_no_csrf_when_absent(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    put_resp = FakeResponse(json_data={"_id": "p1"})
    session = FakeSession([auth_resp, put_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)
    client._put_v2("/v2/api/site/default/firewall-policies/p1", {"enabled": True})
    put_call = session.calls[1]
    assert put_call[2]["headers"] == {}


def test_put_v2_http_error(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    error_resp = FakeResponse(status_code=403, json_data={"error": "Forbidden"}, ok=False)
    session = FakeSession([auth_resp, error_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)
    with pytest.raises(UnifiWriteError, match="failed \\(HTTP 403\\)"):
        client._put_v2("/path", {"a": 1})


def test_put_v2_reauth_on_401(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True}, headers={"X-CSRF-Token": "old"})
    unauthorized = FakeResponse(status_code=401, json_data={}, ok=False)
    reauth_resp = FakeResponse(json_data={"isSuperAdmin": True}, headers={"X-CSRF-Token": "new"})
    put_resp = FakeResponse(json_data={"_id": "p1"})
    session = FakeSession([auth_resp, unauthorized, reauth_resp, put_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)
    client._put_v2("/path", {"x": 1})
    assert len(session.calls) == 4
    assert session.calls[2][0] == "POST"
    assert session.calls[3][2]["headers"]["X-CSRF-Token"] == "new"


def test_put_v2_returns_payload(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    put_resp = FakeResponse(json_data={"_id": "p1", "enabled": False})
    session = FakeSession([auth_resp, put_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)
    result = client._put_v2("/path", {"enabled": False})
    assert result == {"_id": "p1", "enabled": False}


def test_put_v2_passes_request_timeout(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    put_resp = FakeResponse(json_data={"_id": "p1", "enabled": False})
    session = FakeSession([auth_resp, put_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True, request_timeout=7.5)

    client._put_v2("/path", {"enabled": False})
    assert session.calls[1][2]["timeout"] == 7.5


def test_put_v2_non_json_response(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    bad_resp = FakeResponse(json_data=None)
    session = FakeSession([auth_resp, bad_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)
    with pytest.raises(UnifiWriteError, match="Non-JSON response"):
        client._put_v2("/path", {"a": 1})
