"""Tests for client inventory model."""

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


def test_build_client_inventory_joins_hostnames():
    clients = [
        {"name": "My Camera", "ip": "192.168.1.50", "mac": "aa:00:00:00:00:01", "is_wired": True},
    ]
    hostnames = {"192.168.1.50": "camera.local"}
    result = build_client_inventory(clients, hostnames)
    assert result[0].hostname == "camera.local"


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


def test_build_client_inventory_model_from_ucore():
    clients = [
        {
            "name": "G4 Doorbell",
            "ip": "192.168.1.60",
            "mac": "aa:00:00:00:00:01",
            "is_wired": True,
            "unifi_device_info_from_ucore": {
                "computed_model": "G4 Doorbell Pro",
                "product_line": "protect",
                "fw_version": "UVC.SAV539g.v5.2.52.67.39be8f1.260203.0900",
            },
        },
    ]
    result = build_client_inventory(clients)
    assert result[0].model_name == "G4 Doorbell Pro"
    assert result[0].device_type == "camera"
    assert result[0].firmware == "5.2.52.67"


def test_build_client_inventory_firmware_from_top_level():
    clients = [
        {
            "name": "Chime",
            "ip": "192.168.1.70",
            "mac": "aa:00:00:00:00:02",
            "is_wired": True,
            "fw_version": "UP.esp32.v1.7.20.0.402a5ff.240910.0649",
        },
    ]
    result = build_client_inventory(clients)
    assert result[0].firmware == "1.7.20.0"


def test_build_client_inventory_no_firmware():
    clients = [
        {
            "name": "Plain Client",
            "ip": "192.168.1.80",
            "mac": "aa:00:00:00:00:03",
            "is_wired": True,
        },
    ]
    result = build_client_inventory(clients)
    assert result[0].firmware == ""
