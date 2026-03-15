import pytest

from tests.unifi_api_helpers import FakeResponse, FakeSession, make_client
from unifi_topology.adapters.unifi_api import UnifiApiError

pytestmark = pytest.mark.unit


def test_reauth_on_401(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    unauthorized = FakeResponse(status_code=401, json_data={}, ok=False)
    reauth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"ok": True}]})
    session = FakeSession([auth_resp, unauthorized, reauth_resp, data_resp])
    client = make_client(monkeypatch, session)

    result = client.get_clients("default")
    assert result == [{"ok": True}]
    assert len(session.calls) == 4
    assert session.calls[2][0] == "POST"


def test_missing_data_field(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    bad_resp = FakeResponse(json_data={"result": "wrong"})
    session = FakeSession([auth_resp, bad_resp])
    client = make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError, match="Missing 'data' field"):
        client.get_clients("default")


def test_get_http_error(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    error_resp = FakeResponse(status_code=500, json_data={}, ok=False)
    session = FakeSession([auth_resp, error_resp])
    client = make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError, match="failed \\(HTTP 500\\)"):
        client.get_devices("default")


def test_get_non_json_response(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    html_resp = FakeResponse(status_code=200, json_data=None, ok=True)
    session = FakeSession([auth_resp, html_resp])
    client = make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError, match="Non-JSON response"):
        client.get_clients("default")


def test_reauth_succeeds_but_retry_fails(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    unauthorized = FakeResponse(status_code=401, json_data={}, ok=False)
    reauth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    forbidden = FakeResponse(status_code=403, json_data={}, ok=False)
    session = FakeSession([auth_resp, unauthorized, reauth_resp, forbidden])
    client = make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError, match="failed \\(HTTP 403\\)"):
        client.get_clients("default")


def test_get_v2_single_returns_dict(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    data_resp = FakeResponse(json_data=[{"_id": "p1"}])
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)
    result = client._get_v2_single("/path")
    assert result == {"_id": "p1"}


def test_get_v2_single_raises_on_multiple(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    data_resp = FakeResponse(json_data=[{"_id": "p1"}, {"_id": "p2"}])
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)
    with pytest.raises(UnifiApiError, match="Expected single resource"):
        client._get_v2_single("/path")
