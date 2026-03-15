"""Tests for firewall-related endpoint selection."""

import pytest

from tests.firewall_api_helpers import FakeResponse, FakeSession, make_client

pytestmark = pytest.mark.unit


def test_get_firewall_zones_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data=[{"_id": "z1", "name": "LAN"}])
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session)

    result = client.get_firewall_zones("default")
    assert result == [{"_id": "z1", "name": "LAN"}]
    assert session.calls[1][1] == "https://unifi.local/v2/api/site/default/firewall/zone"


def test_get_firewall_zones_udm_pro_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    data_resp = FakeResponse(json_data=[{"_id": "z1", "name": "WAN"}])
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)

    result = client.get_firewall_zones("default")
    assert result == [{"_id": "z1", "name": "WAN"}]
    assert (
        session.calls[1][1] == "https://unifi.local/proxy/network/v2/api/site/default/firewall/zone"
    )


def test_get_firewall_policies_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data=[{"_id": "p1", "name": "Block IoT"}])
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session)

    result = client.get_firewall_policies("default")
    assert result == [{"_id": "p1", "name": "Block IoT"}]
    assert session.calls[1][1] == "https://unifi.local/v2/api/site/default/firewall-policies"


def test_get_firewall_groups_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"_id": "g1", "name": "DNS"}]})
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session)

    result = client.get_firewall_groups("default")
    assert result == [{"_id": "g1", "name": "DNS"}]
    assert session.calls[1][1] == "https://unifi.local/api/s/default/rest/firewallgroup"
