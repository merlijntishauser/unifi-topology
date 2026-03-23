"""Coverage tests for client node type mapping."""

from tests.client_map_helpers import gateway_device, switch_device
from unifi_topology.model.clients import build_node_type_map
from unifi_topology.model.helpers import normalize_mac


def test_build_node_type_map_with_clients_all_mode():
    """build_node_type_map should include clients in 'all' mode."""
    devices = [switch_device()]
    clients = [
        {"name": "Living Room TV", "mac": "11:22:33:44:55:01", "is_wired": True},
        {"name": "Laptop", "mac": "11:22:33:44:55:02", "is_wired": False},
    ]
    node_types = build_node_type_map(devices, clients, client_mode="all")
    assert node_types[normalize_mac("aa:bb:cc:dd:ee:ff")] == "switch"
    assert node_types[normalize_mac("11:22:33:44:55:01")] == "tv"
    assert node_types[normalize_mac("11:22:33:44:55:02")] == "client"


def test_build_node_type_map_skips_filtered_clients():
    """build_node_type_map should skip clients that don't match filters."""
    devices = []
    clients = [
        {"name": "Wired PC", "mac": "11:22:33:44:55:03", "is_wired": True, "is_unifi": False},
        {"name": "UniFi Cam", "mac": "11:22:33:44:55:04", "is_wired": True, "is_unifi": True},
    ]
    node_types = build_node_type_map(devices, clients, only_unifi=True)
    assert normalize_mac("11:22:33:44:55:03") not in node_types
    assert normalize_mac("11:22:33:44:55:04") in node_types


def test_build_node_type_map_no_clients():
    """build_node_type_map with no clients should only have devices."""
    node_types = build_node_type_map([gateway_device()])
    assert node_types == {normalize_mac("aa"): "gateway"}


def test_build_node_type_map_skips_client_with_no_name():
    """Clients with no display name should be skipped."""
    devices = []
    clients = [
        {"name": " ", "hostname": "", "mac": "", "is_wired": True},
    ]
    node_types = build_node_type_map(devices, clients)
    assert node_types == {}
