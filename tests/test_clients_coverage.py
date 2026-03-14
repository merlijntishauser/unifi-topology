"""Tests for clients.py to improve coverage."""

from unifi_topology.model.clients import (
    _client_vlan,
    build_client_edges,
    build_client_port_map,
    build_node_type_map,
    client_uplink_port,
    collapse_client_edges,
)
from unifi_topology.model.topology import Device, Edge

# --- _client_vlan ---


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


# --- client_uplink_port from nested dict ---


def test_client_uplink_port_nested_port_idx():
    """Port from nested uplink dict using port_idx key."""
    client = {"uplink": {"port_idx": 5}}
    assert client_uplink_port(client) == 5


def test_client_uplink_port_nested_last_uplink():
    """Port from nested last_uplink dict."""
    client = {"last_uplink": {"uplink_remote_port": 7}}
    assert client_uplink_port(client) == 7


# --- build_node_type_map with clients ---


def test_build_node_type_map_with_clients_all_mode():
    """build_node_type_map should include clients in 'all' mode."""
    devices = [
        Device(
            name="Switch",
            model_name="",
            model="",
            mac="aa",
            ip="",
            type="usw",
            lldp_info=[],
        )
    ]
    clients = [
        {"name": "Living Room TV", "is_wired": True},
        {"name": "Laptop", "is_wired": False},
    ]
    node_types = build_node_type_map(devices, clients, client_mode="all")
    assert node_types["Switch"] == "switch"
    assert node_types["Living Room TV"] == "tv"
    assert node_types["Laptop"] == "client"


def test_build_node_type_map_skips_filtered_clients():
    """build_node_type_map should skip clients that don't match filters."""
    devices = []
    clients = [
        {"name": "Wired PC", "is_wired": True, "is_unifi": False},
        {"name": "UniFi Cam", "is_wired": True, "is_unifi": True},
    ]
    node_types = build_node_type_map(devices, clients, only_unifi=True)
    assert "Wired PC" not in node_types
    assert "UniFi Cam" in node_types


def test_build_node_type_map_no_clients():
    """build_node_type_map with no clients should only have devices."""
    devices = [
        Device(
            name="Gateway",
            model_name="",
            model="",
            mac="aa",
            ip="",
            type="udm",
            lldp_info=[],
        )
    ]
    node_types = build_node_type_map(devices)
    assert node_types == {"Gateway": "gateway"}


def test_build_node_type_map_skips_client_with_no_name():
    """Clients with no display name should be skipped."""
    devices = []
    clients = [
        {"name": " ", "hostname": "", "mac": "", "is_wired": True},
    ]
    node_types = build_node_type_map(devices, clients)
    assert node_types == {}


# --- build_client_port_map ---


def test_build_client_port_map_filters_clients():
    """build_client_port_map should filter clients by mode."""
    devices = [
        Device(
            name="Switch",
            model_name="",
            model="",
            mac="aa:bb:cc:dd:ee:ff",
            ip="",
            type="usw",
            lldp_info=[],
        )
    ]
    clients = [
        {
            "name": "Wireless Client",
            "is_wired": False,
            "ap_mac": "aa:bb:cc:dd:ee:ff",
            "sw_port": 3,
        }
    ]
    port_map = build_client_port_map(devices, clients, client_mode="wired")
    assert port_map == {}


def test_build_client_port_map_builds_map():
    """build_client_port_map should build correct port map."""
    devices = [
        Device(
            name="Switch",
            model_name="",
            model="",
            mac="aa:bb:cc:dd:ee:ff",
            ip="",
            type="usw",
            lldp_info=[],
        )
    ]
    clients = [
        {
            "name": "Desktop",
            "is_wired": True,
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "sw_port": 3,
        }
    ]
    port_map = build_client_port_map(devices, clients, client_mode="wired")
    assert port_map == {"Switch": [(3, "Desktop")]}


# --- collapse_client_edges ---


def test_collapse_client_edges_collapses_generic_clients():
    """Generic clients should be collapsed into cluster nodes."""
    edges = [
        Edge(left="Switch", right="Laptop1"),
        Edge(left="Switch", right="Laptop2"),
        Edge(left="Switch", right="Laptop3"),
    ]
    node_types = {
        "Switch": "switch",
        "Laptop1": "client",
        "Laptop2": "client",
        "Laptop3": "client",
    }
    collapsed_edges, client_counts = collapse_client_edges(edges, node_types)
    assert client_counts == {"Switch": 3}
    assert len(collapsed_edges) == 1
    assert collapsed_edges[0].left == "Switch"
    assert collapsed_edges[0].right == "Switch (3 clients)"
    assert node_types["Switch (3 clients)"] == "client_cluster"
    # Original client names should be removed from node_types
    assert "Laptop1" not in node_types
    assert "Laptop2" not in node_types
    assert "Laptop3" not in node_types


def test_collapse_client_edges_preserves_non_client_edges():
    """Non-client edges should be preserved as-is."""
    edges = [
        Edge(left="Switch", right="AP One"),
        Edge(left="Switch", right="Laptop"),
    ]
    node_types = {
        "Switch": "switch",
        "AP One": "ap",
        "Laptop": "client",
    }
    collapsed_edges, client_counts = collapse_client_edges(edges, node_types)
    assert client_counts == {"Switch": 1}
    # The AP edge should be preserved
    ap_edges = [e for e in collapsed_edges if e.right == "AP One"]
    assert len(ap_edges) == 1
    # The client edge should be collapsed
    cluster_edges = [e for e in collapsed_edges if "clients" in e.right]
    assert len(cluster_edges) == 1


def test_collapse_client_edges_multiple_devices():
    """Clients from different devices should be collapsed separately."""
    edges = [
        Edge(left="Switch A", right="Client1"),
        Edge(left="Switch A", right="Client2"),
        Edge(left="Switch B", right="Client3"),
    ]
    node_types = {
        "Switch A": "switch",
        "Switch B": "switch",
        "Client1": "client",
        "Client2": "client",
        "Client3": "client",
    }
    collapsed_edges, client_counts = collapse_client_edges(edges, node_types)
    assert client_counts == {"Switch A": 2, "Switch B": 1}
    assert len(collapsed_edges) == 2


def test_collapse_client_edges_no_clients():
    """When there are no client edges, nothing should be collapsed."""
    edges = [
        Edge(left="Switch", right="AP One"),
    ]
    node_types = {
        "Switch": "switch",
        "AP One": "ap",
    }
    collapsed_edges, client_counts = collapse_client_edges(edges, node_types)
    assert client_counts == {}
    assert collapsed_edges == edges


# --- build_client_edges with VLAN ---


def test_build_client_edges_includes_vlan():
    """Client VLAN should be included in the edge."""
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {
            "name": "Desktop",
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "is_wired": True,
            "vlan": 100,
        }
    ]
    edges = build_client_edges(clients, device_index)
    assert edges[0].vlans == (100,)
    assert edges[0].active_vlans == (100,)
