"""Tests for client node-type map behavior."""

import pytest

from unifi_topology.model.clients import build_node_type_map
from unifi_topology.model.helpers import normalize_mac
from unifi_topology.model.topology import Device

pytestmark = pytest.mark.integration


def test_build_node_type_map_skips_wireless_clients():
    devices = [
        Device(name="Gateway", model_name="", model="", mac="aa", ip="", type="udm", lldp_info=[])
    ]
    clients = [{"name": "Phone", "mac": "11:22:33:44:55:01", "is_wired": False}]
    node_types = build_node_type_map(devices, clients)
    assert normalize_mac("11:22:33:44:55:01") not in node_types


def test_build_node_type_map_only_unifi_filters_clients():
    devices = [
        Device(name="Gateway", model_name="", model="", mac="aa", ip="", type="udm", lldp_info=[])
    ]
    clients = [
        {"name": "Desk PC", "mac": "11:22:33:44:55:02", "is_wired": True, "is_unifi": False},
        {"name": "Protect Cam", "mac": "11:22:33:44:55:03", "is_wired": True, "is_unifi": True},
    ]
    node_types = build_node_type_map(devices, clients, only_unifi=True)
    assert normalize_mac("11:22:33:44:55:03") in node_types
    assert normalize_mac("11:22:33:44:55:02") not in node_types
