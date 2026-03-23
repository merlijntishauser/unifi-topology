"""Compatibility-focused topology tests for UniFi-aware client classification."""

from __future__ import annotations

from unifi_topology.model.classify import classify_client_type
from unifi_topology.model.clients import build_node_type_map
from unifi_topology.model.helpers import normalize_mac


def test_classify_client_type_by_unifi_product_line():
    client = {
        "name": "Doorbell",
        "unifi_device_info_from_ucore": {"product_line": "Protect"},
    }
    assert classify_client_type(client) == "camera"
    client = {
        "name": "Office Phone",
        "unifi_device_info_from_ucore": {"product_line": "Talk"},
    }
    assert classify_client_type(client) == "phone"


def test_classify_client_type_by_unifi_model():
    client = {
        "name": "G4 Doorbell",
        "unifi_device_info_from_ucore": {"product_shortname": "UVC-G4-Doorbell"},
    }
    assert classify_client_type(client) == "camera"


def test_classify_client_type_unifi_takes_priority():
    client = {
        "name": "Smart PoE Chime",
        "unifi_device_info_from_ucore": {"product_line": "Protect"},
    }
    assert classify_client_type(client) == "camera"


def test_build_node_type_map_classifies_clients():
    clients = [
        {"name": "Living Room TV", "mac": "11:22:33:44:55:01", "is_wired": True},
        {"name": "Sonos One", "mac": "11:22:33:44:55:02", "is_wired": True},
        {"name": "Generic Client", "mac": "11:22:33:44:55:03", "is_wired": True},
    ]
    node_types = build_node_type_map([], clients)
    assert node_types[normalize_mac("11:22:33:44:55:01")] == "tv"
    assert node_types[normalize_mac("11:22:33:44:55:02")] == "speaker"
    assert node_types[normalize_mac("11:22:33:44:55:03")] == "client"
