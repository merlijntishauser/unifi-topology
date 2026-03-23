"""Tests for wireless client connection info mapping."""

import pytest

from unifi_topology.model.clients import build_client_edges

pytestmark = pytest.mark.integration


def test_build_client_edges_includes_connection_info_for_wireless():
    device_index = {"aa:bb:cc:dd:ee:ff": "AP One"}
    clients = [
        {
            "name": "Phone",
            "mac": "11:22:33:44:55:01",
            "ap_mac": "aa:bb:cc:dd:ee:ff",
            "is_wired": False,
            "signal": -55,
            "noise": -95,
            "tx_rate": 866,
            "rx_rate": 433,
            "satisfaction": 98,
        }
    ]
    edges = build_client_edges(clients, device_index, client_mode="wireless")
    assert len(edges) == 1
    conn = edges[0].connection
    assert conn is not None
    assert conn.signal_dbm == -55
    assert conn.noise_dbm == -95
    assert conn.tx_rate_mbps == 866
    assert conn.rx_rate_mbps == 433
    assert conn.satisfaction == 98
    assert conn.quality == "good"


def test_build_client_edges_no_connection_info_for_wired():
    device_index = {"aa:bb:cc:dd:ee:ff": "Switch A"}
    clients = [
        {
            "name": "Laptop",
            "mac": "11:22:33:44:55:02",
            "sw_mac": "aa:bb:cc:dd:ee:ff",
            "is_wired": True,
        }
    ]
    edges = build_client_edges(clients, device_index)
    assert len(edges) == 1
    assert edges[0].connection is None


def test_build_client_edges_connection_info_with_missing_fields():
    device_index = {"aa:bb:cc:dd:ee:ff": "AP One"}
    clients = [
        {
            "name": "Phone",
            "mac": "11:22:33:44:55:03",
            "ap_mac": "aa:bb:cc:dd:ee:ff",
            "is_wired": False,
            "signal": -70,
        }
    ]
    edges = build_client_edges(clients, device_index, client_mode="wireless")
    conn = edges[0].connection
    assert conn is not None
    assert conn.signal_dbm == -70
    assert conn.noise_dbm is None
    assert conn.tx_rate_mbps is None
    assert conn.quality == "fair"
