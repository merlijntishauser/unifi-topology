"""Tests for UniFi-specific client edge filtering behavior."""

import pytest

from unifi_topology.model.clients import build_client_edges

pytestmark = pytest.mark.integration


def test_build_client_edges_only_unifi_filters_non_unifi():
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {"name": "Desk PC", "is_wired": True, "sw_mac": "aa:bb:cc:dd:ee:ff", "is_unifi": False},
        {"name": "Protect Cam", "is_wired": True, "sw_mac": "aa:bb:cc:dd:ee:ff", "is_unifi": True},
    ]
    edges = build_client_edges(clients, device_index, only_unifi=True)
    assert [edge.right for edge in edges] == ["Protect Cam"]


def test_build_client_edges_only_unifi_vendor_fallback():
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {
            "name": "UniFi Sensor",
            "is_wired": True,
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "oui": "Ubiquiti Inc.",
        }
    ]
    edges = build_client_edges(clients, device_index, only_unifi=True)
    assert edges[0].right == "UniFi Sensor"


def test_build_client_edges_only_unifi_ucore_managed():
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {
            "name": "Doorbell Lite",
            "is_wired": True,
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "unifi_device_info_from_ucore": {"managed": True},
        }
    ]
    edges = build_client_edges(clients, device_index, only_unifi=True)
    assert edges[0].right == "Doorbell Lite"


def test_build_client_edges_prefers_ucore_name_over_hostname():
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {
            "hostname": "espressif",
            "is_wired": True,
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "unifi_device_info_from_ucore": {"name": "Smart PoE Chime"},
        }
    ]
    edges = build_client_edges(clients, device_index, only_unifi=True)
    assert edges[0].right == "Smart PoE Chime"
