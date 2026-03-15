"""Tests for basic client inventory behavior."""

from unifi_topology.model.inventory import build_client_inventory


def test_build_client_inventory_basic():
    clients = [
        {
            "name": "Ring Doorbell",
            "ip": "192.168.1.50",
            "mac": "aa:bb:cc:00:11:22",
            "is_wired": True,
        },
    ]
    result = build_client_inventory(clients)
    assert len(result) == 1
    assert result[0].name == "Ring Doorbell"
    assert result[0].device_type == "camera"
    assert result[0].ip == "192.168.1.50"
    assert result[0].mac == "aa:bb:cc:00:11:22"
    assert result[0].firmware == ""


def test_build_client_inventory_sorted_by_ip():
    clients = [
        {"name": "Client B", "ip": "192.168.1.20", "mac": "aa:bb:cc:00:00:02", "is_wired": True},
        {"name": "Client A", "ip": "192.168.1.10", "mac": "aa:bb:cc:00:00:01", "is_wired": True},
    ]
    result = build_client_inventory(clients)
    assert [d.ip for d in result] == ["192.168.1.10", "192.168.1.20"]


def test_build_client_inventory_filters_by_client_mode():
    clients = [
        {
            "name": "Wired Client",
            "ip": "192.168.1.10",
            "mac": "aa:00:00:00:00:01",
            "is_wired": True,
        },
        {
            "name": "Wireless Client",
            "ip": "192.168.1.11",
            "mac": "aa:00:00:00:00:02",
            "is_wired": False,
        },
    ]
    result = build_client_inventory(clients, client_mode="wired")
    assert len(result) == 1
    assert result[0].name == "Wired Client"


def test_build_client_inventory_missing_ip():
    clients = [
        {"name": "No IP Client", "mac": "aa:00:00:00:00:01", "is_wired": True},
    ]
    result = build_client_inventory(clients)
    assert len(result) == 1
    assert result[0].ip == ""


def test_build_client_inventory_empty():
    result = build_client_inventory([])
    assert result == []
