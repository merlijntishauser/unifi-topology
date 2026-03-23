"""Coverage tests for client port mapping."""

from tests.client_map_helpers import switch_device
from unifi_topology.model.clients import build_client_port_map
from unifi_topology.model.helpers import normalize_mac


def test_build_client_port_map_filters_clients():
    """build_client_port_map should filter clients by mode."""
    devices = [switch_device()]
    clients = [
        {
            "name": "Wireless Client",
            "mac": "11:22:33:44:55:01",
            "is_wired": False,
            "ap_mac": "aa:bb:cc:dd:ee:ff",
            "sw_port": 3,
        }
    ]
    port_map = build_client_port_map(devices, clients, client_mode="wired")
    assert port_map == {}


def test_build_client_port_map_builds_map():
    """build_client_port_map should build correct port map."""
    devices = [switch_device()]
    clients = [
        {
            "name": "Desktop",
            "mac": "11:22:33:44:55:02",
            "is_wired": True,
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "sw_port": 3,
        }
    ]
    port_map = build_client_port_map(devices, clients, client_mode="wired")
    assert port_map == {
        normalize_mac("aa:bb:cc:dd:ee:ff"): [(3, normalize_mac("11:22:33:44:55:02"))]
    }
