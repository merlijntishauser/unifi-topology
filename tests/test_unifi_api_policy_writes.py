import pytest

from tests.unifi_api_helpers import FakeResponse, FakeSession, make_client
from unifi_topology.adapters.unifi_api import UnifiWriteError

pytestmark = pytest.mark.unit


def test_update_firewall_policy(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True}, headers={"X-CSRF-Token": "tok"})
    get_resp = FakeResponse(json_data=[{"_id": "p1", "enabled": True, "name": "Test"}])
    put_resp = FakeResponse(json_data={"_id": "p1", "enabled": False, "name": "Test"})
    session = FakeSession([auth_resp, get_resp, put_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)
    result = client.update_firewall_policy("default", "p1", {"enabled": False})
    assert result["enabled"] is False
    assert session.calls[1][0] == "GET"
    assert "/firewall-policies/p1" in session.calls[1][1]
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
    client = make_client(monkeypatch, session, is_udm_pro=True)
    client.swap_firewall_policy_order("default", "pa", "pb")
    assert session.calls[2][2]["json"]["index"] == 2
    assert session.calls[3][2]["json"]["index"] == 1


def test_swap_firewall_policy_order_missing(monkeypatch):
    auth_resp = FakeResponse(json_data={"isSuperAdmin": True})
    list_resp = FakeResponse(json_data=[{"_id": "pa", "index": 1}])
    session = FakeSession([auth_resp, list_resp])
    client = make_client(monkeypatch, session, is_udm_pro=True)
    with pytest.raises(UnifiWriteError, match="Policy not found: pb"):
        client.swap_firewall_policy_order("default", "pa", "pb")
