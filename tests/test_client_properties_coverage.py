"""Coverage tests for low-level client property helpers."""

from unifi_topology.model.clients import _client_vlan, client_uplink_port


def test_client_vlan_returns_int_value():
    """VLAN as positive integer should be returned."""
    client = {"vlan": 100}
    assert _client_vlan(client) == 100


def test_client_vlan_returns_string_value():
    """VLAN as numeric string should be parsed and returned."""
    client = {"vlan": "200"}
    assert _client_vlan(client) == 200


def test_client_vlan_skips_zero_int():
    """VLAN of 0 should not be returned."""
    client = {"vlan": 0}
    assert _client_vlan(client) is None


def test_client_vlan_skips_zero_string():
    """VLAN string of '0' should not be returned."""
    client = {"vlan": "0"}
    assert _client_vlan(client) is None


def test_client_vlan_tries_alternative_keys():
    """Should try vlan_id, vlanId, vlanid keys."""
    assert _client_vlan({"vlan_id": 10}) == 10
    assert _client_vlan({"vlanId": 20}) == 20
    assert _client_vlan({"vlanid": 30}) == 30


def test_client_uplink_port_nested_port_idx():
    """Port from nested uplink dict using port_idx key."""
    client = {"uplink": {"port_idx": 5}}
    assert client_uplink_port(client) == 5


def test_client_uplink_port_nested_last_uplink():
    """Port from nested last_uplink dict."""
    client = {"last_uplink": {"uplink_remote_port": 7}}
    assert client_uplink_port(client) == 7
