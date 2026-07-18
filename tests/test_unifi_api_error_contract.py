"""Tests that HTTP failures surface as UnifiError with status codes."""

import pytest
import requests

from tests.unifi_api_helpers import FakeResponse, FakeSession, make_client
from unifi_topology.adapters import unifi
from unifi_topology.adapters.unifi_api import UnifiApiError, UnifiAuthError, UnifiError

pytestmark = pytest.mark.unit


class RaisingSession(FakeSession):
    def __init__(self, exc, responses=None):
        super().__init__(responses=responses)
        self._exc = exc

    def get(self, url, *, verify=True, timeout=None):
        raise self._exc


def test_get_wraps_connection_error_as_unifi_error(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    session = RaisingSession(requests.ConnectionError("host down"), responses=[auth_resp])
    client = make_client(monkeypatch, session)

    with pytest.raises(UnifiError):
        client.get_clients("mysite")


def test_http_error_carries_status_code(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    error_resp = FakeResponse(status_code=429, ok=False)
    session = FakeSession([auth_resp, error_resp])
    client = make_client(monkeypatch, session)

    with pytest.raises(UnifiApiError) as excinfo:
        client.get_clients("mysite")
    assert excinfo.value.status_code == 429


def test_is_rate_limited_uses_status_code():
    limited = UnifiAuthError("nope", status_code=429)
    not_limited = UnifiAuthError("connect to unifi-429.local failed")
    assert unifi._is_rate_limited(limited) is True
    assert unifi._is_rate_limited(not_limited) is False
