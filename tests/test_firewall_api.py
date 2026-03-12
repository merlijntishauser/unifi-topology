"""Tests for firewall-related UnifiClient methods."""

import pytest
import requests

from unifi_topology.adapters.unifi_api import UnifiApiError, UnifiClient

pytestmark = pytest.mark.unit


class FakeResponse:
    """Minimal stand-in for ``requests.Response``."""

    def __init__(self, status_code=200, json_data=None, *, ok=True):
        self.status_code = status_code
        self._json_data = json_data
        self.ok = ok

    def json(self):
        if self._json_data is None:
            raise ValueError("No JSON")
        return self._json_data


class FakeSession:
    """Captures requests made through a ``requests.Session``."""

    def __init__(self, responses=None):
        self.calls: list[tuple[str, str, dict]] = []
        self._responses = list(responses or [])
        self._index = 0

    def post(self, url, *, json=None, verify=True):
        self.calls.append(("POST", url, {"json": json, "verify": verify}))
        return self._next()

    def get(self, url, *, verify=True):
        self.calls.append(("GET", url, {"verify": verify}))
        return self._next()

    def _next(self):
        resp = self._responses[self._index]
        self._index += 1
        return resp


def _make_client(monkeypatch, session, *, is_udm_pro=False):
    """Construct a ``UnifiClient`` with a pre-built fake session."""
    monkeypatch.setattr(requests, "Session", lambda: session)
    return UnifiClient(
        url="https://unifi.local",
        username="admin",
        password="secret",
        is_udm_pro=is_udm_pro,
        verify_ssl=True,
    )


# ------------------------------------------------------------------
# Firewall zone endpoints
# ------------------------------------------------------------------


def test_get_firewall_zones_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data=[{"_id": "z1", "name": "LAN"}])
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session)

    result = client.get_firewall_zones("default")
    assert result == [{"_id": "z1", "name": "LAN"}]
    assert session.calls[1][1] == "https://unifi.local/v2/api/site/default/firewall/zone"


def test_get_firewall_zones_udm_pro_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    data_resp = FakeResponse(json_data=[{"_id": "z1", "name": "WAN"}])
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)

    result = client.get_firewall_zones("default")
    assert result == [{"_id": "z1", "name": "WAN"}]
    assert (
        session.calls[1][1] == "https://unifi.local/proxy/network/v2/api/site/default/firewall/zone"
    )


# ------------------------------------------------------------------
# Firewall policy endpoints
# ------------------------------------------------------------------


def test_get_firewall_policies_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data=[{"_id": "p1", "name": "Block IoT"}])
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session)

    result = client.get_firewall_policies("default")
    assert result == [{"_id": "p1", "name": "Block IoT"}]
    assert session.calls[1][1] == "https://unifi.local/v2/api/site/default/firewall-policies"


# ------------------------------------------------------------------
# Firewall group endpoints
# ------------------------------------------------------------------


def test_get_firewall_groups_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"_id": "g1", "name": "DNS"}]})
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session)

    result = client.get_firewall_groups("default")
    assert result == [{"_id": "g1", "name": "DNS"}]
    assert session.calls[1][1] == "https://unifi.local/api/s/default/rest/firewallgroup"


# ------------------------------------------------------------------
# _get_v2 response handling
# ------------------------------------------------------------------


def test_get_v2_plain_list(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data=[{"a": 1}, {"b": 2}])
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session)

    result = client._get_v2("/v2/api/site/default/test")
    assert result == [{"a": 1}, {"b": 2}]


def test_get_v2_data_envelope(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"x": 1}]})
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session)

    result = client._get_v2("/v2/api/site/default/test")
    assert result == [{"x": 1}]


def test_get_v2_single_dict(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"id": "single"})
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session)

    result = client._get_v2("/v2/api/site/default/test")
    assert result == [{"id": "single"}]


def test_get_v2_reauth_on_401(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    unauthorized = FakeResponse(status_code=401, json_data={}, ok=False)
    reauth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data=[{"ok": True}])
    session = FakeSession([auth_resp, unauthorized, reauth_resp, data_resp])
    client = _make_client(monkeypatch, session)

    result = client._get_v2("/v2/api/site/default/test")
    assert result == [{"ok": True}]
    # calls: initial auth POST, GET (401), re-auth POST, GET (success)
    assert len(session.calls) == 4
    assert session.calls[2][0] == "POST"


def test_get_v2_http_error(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    error_resp = FakeResponse(status_code=500, json_data={}, ok=False)
    session = FakeSession([auth_resp, error_resp])
    client = _make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError, match="failed \\(HTTP 500\\)"):
        client._get_v2("/v2/api/site/default/test")


def test_get_v2_non_json(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    html_resp = FakeResponse(status_code=200, json_data=None, ok=True)
    session = FakeSession([auth_resp, html_resp])
    client = _make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError, match="Non-JSON response"):
        client._get_v2("/v2/api/site/default/test")
