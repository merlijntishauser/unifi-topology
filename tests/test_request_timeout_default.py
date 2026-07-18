"""Tests for the default HTTP request timeout."""

import pytest

from tests.unifi_api_helpers import FakeResponse, FakeSession, make_client
from unifi_topology.adapters._retry import _request_timeout_seconds

pytestmark = pytest.mark.unit


def test_request_timeout_defaults_to_finite_value(monkeypatch):
    monkeypatch.delenv("UNIFI_REQUEST_TIMEOUT_SECONDS", raising=False)
    assert _request_timeout_seconds() == 30.0


def test_request_timeout_env_override(monkeypatch):
    monkeypatch.setenv("UNIFI_REQUEST_TIMEOUT_SECONDS", "5")
    assert _request_timeout_seconds() == 5.0


def test_client_passes_default_timeout_to_requests(monkeypatch):
    monkeypatch.delenv("UNIFI_REQUEST_TIMEOUT_SECONDS", raising=False)
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"mac": "cc"}]})
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session, request_timeout=_request_timeout_seconds())

    client.get_clients("mysite")
    assert session.calls[0][2]["timeout"] == 30.0
    assert session.calls[1][2]["timeout"] == 30.0
