"""Tests for client node-type map behavior."""

import pytest

from unifi_topology.model.clients import build_node_type_map
from unifi_topology.model.topology import Device

pytestmark = pytest.mark.integration


def test_build_node_type_map_skips_wireless_clients():
    devices = [
        Device(name="Gateway", model_name="", model="", mac="aa", ip="", type="udm", lldp_info=[])
    ]
    clients = [{"name": "Phone", "is_wired": False}]
    node_types = build_node_type_map(devices, clients)
    assert "Phone" not in node_types


def test_build_node_type_map_only_unifi_filters_clients():
    devices = [
        Device(name="Gateway", model_name="", model="", mac="aa", ip="", type="udm", lldp_info=[])
    ]
    clients = [
        {"name": "Desk PC", "is_wired": True, "is_unifi": False},
        {"name": "Protect Cam", "is_wired": True, "is_unifi": True},
    ]
    node_types = build_node_type_map(devices, clients, only_unifi=True)
    assert "Protect Cam" in node_types
    assert "Desk PC" not in node_types
