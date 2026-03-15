"""Tests for firewall V2 response handling."""

import pytest

from tests.firewall_api_helpers import FakeResponse, FakeSession, make_client
from unifi_topology.adapters.unifi_api import UnifiApiError

pytestmark = pytest.mark.unit


def test_get_v2_plain_list(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data=[{"a": 1}, {"b": 2}])
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session)

    result = client._get_v2("/v2/api/site/default/test")
    assert result == [{"a": 1}, {"b": 2}]


def test_get_v2_data_envelope(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"x": 1}]})
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session)

    result = client._get_v2("/v2/api/site/default/test")
    assert result == [{"x": 1}]


def test_get_v2_single_dict(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"id": "single"})
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session)

    result = client._get_v2("/v2/api/site/default/test")
    assert result == [{"id": "single"}]


def test_get_v2_reauth_on_401(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    unauthorized = FakeResponse(status_code=401, json_data={}, ok=False)
    reauth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data=[{"ok": True}])
    session = FakeSession([auth_resp, unauthorized, reauth_resp, data_resp])
    client = make_client(monkeypatch, session)

    result = client._get_v2("/v2/api/site/default/test")
    assert result == [{"ok": True}]
    assert len(session.calls) == 4
    assert session.calls[2][0] == "POST"


def test_get_v2_http_error(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    error_resp = FakeResponse(status_code=500, json_data={}, ok=False)
    session = FakeSession([auth_resp, error_resp])
    client = make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError, match="failed \\(HTTP 500\\)"):
        client._get_v2("/v2/api/site/default/test")


def test_get_v2_non_json(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    html_resp = FakeResponse(status_code=200, json_data=None, ok=True)
    session = FakeSession([auth_resp, html_resp])
    client = make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError, match="Non-JSON response"):
        client._get_v2("/v2/api/site/default/test")
