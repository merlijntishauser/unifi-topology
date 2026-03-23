"""Tests for core client edge building behavior."""

import pytest

from unifi_topology.model.clients import build_client_edges
from unifi_topology.model.helpers import normalize_mac

pytestmark = pytest.mark.integration


def test_build_client_edges_maps_ap_mac():
    device_index = {"aa:bb:cc:dd:ee:ff": "AP One"}
    clients = [
        {
            "name": "Laptop",
            "mac": "11:22:33:44:55:01",
            "ap_mac": "aa:bb:cc:dd:ee:ff",
            "is_wired": True,
        }
    ]
    edges = build_client_edges(clients, device_index)
    assert edges[0].left == "aa:bb:cc:dd:ee:ff"


def test_build_client_edges_uses_hostname_fallback():
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {
            "hostname": "phone",
            "mac": "11:22:33:44:55:02",
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "is_wired": True,
        }
    ]
    edges = build_client_edges(clients, device_index)
    assert edges[0].right == normalize_mac("11:22:33:44:55:02")


def test_build_client_edges_skips_unknown_uplink():
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {
            "name": "tablet",
            "mac": "11:22:33:44:55:03",
            "sw_mac": "11:22:33:44:55:66",
            "is_wired": True,
        }
    ]
    edges = build_client_edges(clients, device_index)
    assert edges == []


def test_build_client_edges_skips_wireless_clients():
    device_index = {"aa:bb:cc:dd:ee:ff": "AP One"}
    clients = [
        {
            "name": "Laptop",
            "mac": "11:22:33:44:55:04",
            "ap_mac": "aa:bb:cc:dd:ee:ff",
            "is_wired": False,
        }
    ]
    edges = build_client_edges(clients, device_index)
    assert edges == []


def test_build_client_edges_includes_wireless_when_requested():
    device_index = {"aa:bb:cc:dd:ee:ff": "AP One"}
    clients = [
        {
            "name": "Laptop",
            "mac": "11:22:33:44:55:05",
            "ap_mac": "aa:bb:cc:dd:ee:ff",
            "is_wired": False,
        }
    ]
    edges = build_client_edges(clients, device_index, client_mode="wireless")
    assert edges[0].wireless is True


def test_build_client_edges_includes_channel_for_wireless():
    device_index = {"aa:bb:cc:dd:ee:ff": "AP One"}
    clients = [
        {
            "name": "Phone",
            "mac": "11:22:33:44:55:06",
            "ap_mac": "aa:bb:cc:dd:ee:ff",
            "is_wired": False,
            "channel": 36,
        }
    ]
    edges = build_client_edges(clients, device_index, client_mode="wireless")
    assert edges[0].channel == 36


def test_build_client_edges_includes_uplink_port_label():
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    node_names = {"aa:bb:cc:dd:ee:ff": "Switch A", "11:22:33:44:55:07": "Laptop"}
    clients = [
        {
            "name": "Laptop",
            "mac": "11:22:33:44:55:07",
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "is_wired": True,
            "last_uplink": {"uplink_remote_port": 3},
        }
    ]
    edges = build_client_edges(clients, device_index, include_ports=True, node_names=node_names)
    assert edges[0].label == "Switch A: Port 3 <-> Laptop"
