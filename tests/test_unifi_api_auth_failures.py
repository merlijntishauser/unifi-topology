import pytest
import requests

from tests.unifi_api_helpers import FakeResponse, FakeSession, make_client
from unifi_topology.adapters.unifi_api import UnifiAuthError, UnifiClient

pytestmark = pytest.mark.unit


def test_authenticate_error_payload(monkeypatch):
    error_resp = FakeResponse(
        json_data={"code": "AUTH_FAILED", "message": "Invalid credentials"},
    )
    session = FakeSession([error_resp])
    with pytest.raises(UnifiAuthError, match="AUTH_FAILED"):
        make_client(monkeypatch, session)


def test_authenticate_unknown_format(monkeypatch):
    odd_resp = FakeResponse(json_data={"something": "unexpected"})
    session = FakeSession([odd_resp])
    with pytest.raises(UnifiAuthError, match="Unknown auth response"):
        make_client(monkeypatch, session)


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


def test_insecure_client_does_not_mutate_global_warnings(monkeypatch):
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
    # Suppression is scoped per-request now, so the process-global
    # disable_warnings is never invoked.
    assert calls == []


def test_authenticate_http_error_does_not_treat_roles_as_success(monkeypatch):
    error_resp = FakeResponse(status_code=403, json_data={"roles": ["admin"]}, ok=False)
    session = FakeSession([error_resp])
    with pytest.raises(UnifiAuthError, match="HTTP 403"):
        make_client(monkeypatch, session)
