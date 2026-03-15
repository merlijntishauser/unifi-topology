import pytest
import requests

from unifi_topology.adapters.unifi_api import (
    UnifiApiError,
    UnifiAuthError,
    UnifiClient,
    UnifiWriteError,
)

pytestmark = pytest.mark.unit


class FakeResponse:
    """Minimal stand-in for ``requests.Response``."""

    def __init__(self, status_code=200, json_data=None, *, ok=True, headers=None):
        self.status_code = status_code
        self._json_data = json_data
        self.ok = ok
        self.headers = headers or {}
        self.text = ""

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

    def post(self, url, *, json=None, verify=True, timeout=None):
        self.calls.append(("POST", url, {"json": json, "verify": verify, "timeout": timeout}))
        return self._next()

    def get(self, url, *, verify=True, timeout=None):
        self.calls.append(("GET", url, {"verify": verify, "timeout": timeout}))
        return self._next()

    def put(self, url, *, json=None, headers=None, verify=True, timeout=None):
        self.calls.append(
            ("PUT", url, {"json": json, "headers": headers, "verify": verify, "timeout": timeout})
        )
        return self._next()

    def _next(self):
        resp = self._responses[self._index]
        self._index += 1
        return resp


def _make_client(monkeypatch, session, *, is_udm_pro=False, request_timeout=None):
    """Construct a ``UnifiClient`` with a pre-built fake session."""
    monkeypatch.setattr(requests, "Session", lambda: session)
    return UnifiClient(
        url="https://unifi.local",
        username="admin",
        password="secret",
        is_udm_pro=is_udm_pro,
        verify_ssl=True,
        request_timeout=request_timeout,
    )


# ------------------------------------------------------------------
# Authentication
# ------------------------------------------------------------------


def test_authenticate_udm_pro(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    data_resp = FakeResponse(json_data={"data": [{"name": "switch"}]})
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)

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
    client = _make_client(monkeypatch, session, is_udm_pro=False)

    assert session.calls[0] == (
        "POST",
        "https://unifi.local/api/login",
        {"json": {"username": "admin", "password": "secret"}, "verify": True, "timeout": None},
    )
    assert client._api_base == "https://unifi.local"


def test_authenticate_error_payload(monkeypatch):
    error_resp = FakeResponse(
        json_data={"code": "AUTH_FAILED", "message": "Invalid credentials"},
    )
    session = FakeSession([error_resp])
    with pytest.raises(UnifiAuthError, match="AUTH_FAILED"):
        _make_client(monkeypatch, session)


def test_authenticate_unknown_format(monkeypatch):
    odd_resp = FakeResponse(json_data={"something": "unexpected"})
    session = FakeSession([odd_resp])
    with pytest.raises(UnifiAuthError, match="Unknown auth response"):
        _make_client(monkeypatch, session)


def test_authenticate_request_failure(monkeypatch):
    class FailSession:
        def post(self, url, *, json=None, verify=True, timeout=None):
            raise requests.RequestException("connection refused")

    monkeypatch.setattr(requests, "Session", lambda: FailSession())
    with pytest.raises(UnifiAuthError, match="Login request failed"):
        UnifiClient(
            url="https://unifi.local",
            username="admin",
            password="secret",
        )


# ------------------------------------------------------------------
# Data fetching
# ------------------------------------------------------------------


def test_get_devices_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    detailed_resp = FakeResponse(json_data={"data": [{"mac": "aa"}]})
    basic_resp = FakeResponse(json_data={"data": [{"mac": "bb"}]})
    session = FakeSession([auth_resp, detailed_resp, basic_resp])
    client = _make_client(monkeypatch, session)

    result = client.get_devices("default", detailed=True)
    assert result == [{"mac": "aa"}]
    assert session.calls[1][1] == "https://unifi.local/api/s/default/stat/device"

    result = client.get_devices("default", detailed=False)
    assert result == [{"mac": "bb"}]
    assert session.calls[2][1] == "https://unifi.local/api/s/default/stat/device-basic"


def test_get_clients_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"mac": "cc"}]})
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session)

    result = client.get_clients("mysite")
    assert result == [{"mac": "cc"}]
    assert session.calls[1][1] == "https://unifi.local/api/s/mysite/stat/sta"


def test_get_networkconf_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"_id": "net1"}]})
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session)

    result = client.get_networkconf("default")
    assert result == [{"_id": "net1"}]
    assert session.calls[1][1] == "https://unifi.local/api/s/default/rest/networkconf"


def test_reauth_on_401(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    unauthorized = FakeResponse(status_code=401, json_data={}, ok=False)
    reauth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"ok": True}]})
    session = FakeSession([auth_resp, unauthorized, reauth_resp, data_resp])
    client = _make_client(monkeypatch, session)

    result = client.get_clients("default")
    assert result == [{"ok": True}]
    # calls: initial auth POST, GET (401), re-auth POST, GET (success)
    assert len(session.calls) == 4
    assert session.calls[2][0] == "POST"


def test_parse_data_field(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"a": 1}, {"b": 2}]})
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session)

    result = client.get_clients("default")
    assert len(result) == 2
    assert result[0] == {"a": 1}


def test_missing_data_field(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    bad_resp = FakeResponse(json_data={"result": "wrong"})
    session = FakeSession([auth_resp, bad_resp])
    client = _make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError, match="Missing 'data' field"):
        client.get_clients("default")


def test_get_http_error(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    error_resp = FakeResponse(status_code=500, json_data={}, ok=False)
    session = FakeSession([auth_resp, error_resp])
    client = _make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError, match="failed \\(HTTP 500\\)"):
        client.get_devices("default")


def test_get_non_json_response(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    html_resp = FakeResponse(status_code=200, json_data=None, ok=True)
    session = FakeSession([auth_resp, html_resp])
    client = _make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError, match="Non-JSON response"):
        client.get_clients("default")


def test_reauth_succeeds_but_retry_fails(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    unauthorized = FakeResponse(status_code=401, json_data={}, ok=False)
    reauth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    forbidden = FakeResponse(status_code=403, json_data={}, ok=False)
    session = FakeSession([auth_resp, unauthorized, reauth_resp, forbidden])
    client = _make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError, match="failed \\(HTTP 403\\)"):
        client.get_clients("default")


def test_ssl_warning_suppressed(monkeypatch):
    calls = []
    monkeypatch.setattr("urllib3.disable_warnings", lambda *a: calls.append(a))
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    session = FakeSession([auth_resp])
    monkeypatch.setattr(requests, "Session", lambda: session)

    UnifiClient(
        url="https://unifi.local",
        username="admin",
        password="secret",
        verify_ssl=False,
    )
    assert len(calls) == 1


def test_authenticate_http_error_does_not_treat_roles_as_success(monkeypatch):
    error_resp = FakeResponse(status_code=403, json_data={"roles": ["admin"]}, ok=False)
    session = FakeSession([error_resp])
    with pytest.raises(UnifiAuthError, match="HTTP 403"):
        _make_client(monkeypatch, session)


def test_request_timeout_is_passed_to_auth_and_get(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"mac": "cc"}]})
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session, request_timeout=5.0)

    client.get_clients("mysite")
    assert session.calls[0][2]["timeout"] == 5.0
    assert session.calls[1][2]["timeout"] == 5.0


# ------------------------------------------------------------------
# CSRF token
# ------------------------------------------------------------------


def test_csrf_token_captured_on_auth(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True}, headers={"X-CSRF-Token": "tok123"})
    data_resp = FakeResponse(json_data=[{"_id": "p1", "enabled": True}])
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    assert client._csrf_token == "tok123"


def test_csrf_token_none_when_absent(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    session = FakeSession([auth_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    assert client._csrf_token is None


# ------------------------------------------------------------------
# PUT V2
# ------------------------------------------------------------------


def test_put_v2_sends_csrf_token(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True}, headers={"X-CSRF-Token": "csrf1"})
    put_resp = FakeResponse(json_data={"_id": "p1", "enabled": False})
    session = FakeSession([auth_resp, put_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    client._put_v2("/v2/api/site/default/firewall-policies/p1", {"enabled": False})
    put_call = session.calls[1]
    assert put_call[0] == "PUT"
    assert put_call[2]["headers"]["X-CSRF-Token"] == "csrf1"


def test_put_v2_no_csrf_when_absent(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    put_resp = FakeResponse(json_data={"_id": "p1"})
    session = FakeSession([auth_resp, put_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    client._put_v2("/v2/api/site/default/firewall-policies/p1", {"enabled": True})
    put_call = session.calls[1]
    assert put_call[2]["headers"] == {}


def test_put_v2_http_error(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    error_resp = FakeResponse(status_code=403, json_data={"error": "Forbidden"}, ok=False)
    session = FakeSession([auth_resp, error_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    with pytest.raises(UnifiWriteError, match="failed \\(HTTP 403\\)"):
        client._put_v2("/path", {"a": 1})


def test_put_v2_reauth_on_401(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True}, headers={"X-CSRF-Token": "old"})
    unauthorized = FakeResponse(status_code=401, json_data={}, ok=False)
    reauth_resp = FakeResponse(json_data={"isSuperAdmin": True}, headers={"X-CSRF-Token": "new"})
    put_resp = FakeResponse(json_data={"_id": "p1"})
    session = FakeSession([auth_resp, unauthorized, reauth_resp, put_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    client._put_v2("/path", {"x": 1})
    # calls: initial auth POST, PUT (401), re-auth POST, PUT (success)
    assert len(session.calls) == 4
    assert session.calls[2][0] == "POST"
    # After reauth, the new CSRF token should be used
    assert session.calls[3][2]["headers"]["X-CSRF-Token"] == "new"


def test_put_v2_returns_payload(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    put_resp = FakeResponse(json_data={"_id": "p1", "enabled": False})
    session = FakeSession([auth_resp, put_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    result = client._put_v2("/path", {"enabled": False})
    assert result == {"_id": "p1", "enabled": False}


def test_put_v2_passes_request_timeout(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    put_resp = FakeResponse(json_data={"_id": "p1", "enabled": False})
    session = FakeSession([auth_resp, put_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True, request_timeout=7.5)

    client._put_v2("/path", {"enabled": False})
    assert session.calls[1][2]["timeout"] == 7.5


def test_put_v2_non_json_response(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    bad_resp = FakeResponse(json_data=None)
    session = FakeSession([auth_resp, bad_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    with pytest.raises(UnifiWriteError, match="Non-JSON response"):
        client._put_v2("/path", {"a": 1})


# ------------------------------------------------------------------
# GET V2 single
# ------------------------------------------------------------------


def test_get_v2_single_returns_dict(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    data_resp = FakeResponse(json_data=[{"_id": "p1"}])
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    result = client._get_v2_single("/path")
    assert result == {"_id": "p1"}


def test_get_v2_single_raises_on_multiple(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    data_resp = FakeResponse(json_data=[{"_id": "p1"}, {"_id": "p2"}])
    session = FakeSession([auth_resp, data_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    with pytest.raises(UnifiApiError, match="Expected single resource"):
        client._get_v2_single("/path")


# ------------------------------------------------------------------
# Update / Swap firewall policies
# ------------------------------------------------------------------


def test_update_firewall_policy(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True}, headers={"X-CSRF-Token": "tok"})
    get_resp = FakeResponse(json_data=[{"_id": "p1", "enabled": True, "name": "Test"}])
    put_resp = FakeResponse(json_data={"_id": "p1", "enabled": False, "name": "Test"})
    session = FakeSession([auth_resp, get_resp, put_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    result = client.update_firewall_policy("default", "p1", {"enabled": False})
    assert result["enabled"] is False
    # Verify GET was called
    assert session.calls[1][0] == "GET"
    assert "/firewall-policies/p1" in session.calls[1][1]
    # Verify PUT was called with merged payload
    put_call = session.calls[2]
    assert put_call[0] == "PUT"
    assert put_call[2]["json"]["enabled"] is False
    assert put_call[2]["json"]["name"] == "Test"


def test_swap_firewall_policy_order(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True}, headers={"X-CSRF-Token": "tok"})
    list_resp = FakeResponse(
        json_data=[
            {"_id": "pa", "index": 1, "name": "A"},
            {"_id": "pb", "index": 2, "name": "B"},
        ]
    )
    put_a_resp = FakeResponse(json_data={"_id": "pa", "index": 2})
    put_b_resp = FakeResponse(json_data={"_id": "pb", "index": 1})
    session = FakeSession([auth_resp, list_resp, put_a_resp, put_b_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    client.swap_firewall_policy_order("default", "pa", "pb")
    # Two PUTs with swapped indices
    assert session.calls[2][2]["json"]["index"] == 2
    assert session.calls[3][2]["json"]["index"] == 1


def test_swap_firewall_policy_order_missing(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    list_resp = FakeResponse(json_data=[{"_id": "pa", "index": 1}])
    session = FakeSession([auth_resp, list_resp])
    client = _make_client(monkeypatch, session, is_udm_pro=True)
    with pytest.raises(UnifiWriteError, match="Policy not found: pb"):
        client.swap_firewall_policy_order("default", "pa", "pb")
