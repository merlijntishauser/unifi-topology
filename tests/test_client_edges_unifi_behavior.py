"""Tests for UniFi-specific client edge filtering behavior."""

import pytest

from unifi_topology.model.clients import build_client_edges
from unifi_topology.model.helpers import normalize_mac

pytestmark = pytest.mark.integration


def test_build_client_edges_only_unifi_filters_non_unifi():
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {
            "name": "Desk PC",
            "mac": "11:22:33:44:55:01",
            "is_wired": True,
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "is_unifi": False,
        },
        {
            "name": "Protect Cam",
            "mac": "11:22:33:44:55:02",
            "is_wired": True,
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "is_unifi": True,
        },
    ]
    edges = build_client_edges(clients, device_index, only_unifi=True)
    assert len(edges) == 1
    assert edges[0].right == normalize_mac("11:22:33:44:55:02")


def test_build_client_edges_only_unifi_vendor_fallback():
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {
            "name": "UniFi Sensor",
            "mac": "11:22:33:44:55:03",
            "is_wired": True,
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "oui": "Ubiquiti Inc.",
        }
    ]
    edges = build_client_edges(clients, device_index, only_unifi=True)
    assert edges[0].right == normalize_mac("11:22:33:44:55:03")


def test_build_client_edges_only_unifi_ucore_managed():
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {
            "name": "Doorbell Lite",
            "mac": "11:22:33:44:55:04",
            "is_wired": True,
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "unifi_device_info_from_ucore": {"managed": True},
        }
    ]
    edges = build_client_edges(clients, device_index, only_unifi=True)
    assert edges[0].right == normalize_mac("11:22:33:44:55:04")


def test_build_client_edges_prefers_ucore_name_over_hostname():
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {
            "hostname": "espressif",
            "mac": "11:22:33:44:55:05",
            "is_wired": True,
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "unifi_device_info_from_ucore": {"name": "Smart PoE Chime"},
        }
    ]
    edges = build_client_edges(clients, device_index, only_unifi=True)
    assert edges[0].right == normalize_mac("11:22:33:44:55:05")
