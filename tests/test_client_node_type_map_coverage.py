"""Coverage tests for client node type mapping."""

from tests.client_map_helpers import gateway_device, switch_device
from unifi_topology.model.clients import build_node_type_map


def test_build_node_type_map_with_clients_all_mode():
    """build_node_type_map should include clients in 'all' mode."""
    devices = [switch_device()]
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
    node_types = build_node_type_map([gateway_device()])
    assert node_types == {"Gateway": "gateway"}


def test_build_node_type_map_skips_client_with_no_name():
    """Clients with no display name should be skipped."""
    devices = []
    clients = [
        {"name": " ", "hostname": "", "mac": "", "is_wired": True},
    ]
    node_types = build_node_type_map(devices, clients)
    assert node_types == {}
