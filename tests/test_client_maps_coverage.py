"""Coverage tests for client node and port maps."""

from unifi_topology.model.clients import build_client_port_map, build_node_type_map
from unifi_topology.model.topology import Device


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
