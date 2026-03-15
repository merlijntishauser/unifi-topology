"""Compatibility-focused topology tests for UniFi-aware client classification."""

from __future__ import annotations

from unifi_topology.model.classify import classify_client_type
from unifi_topology.model.clients import build_node_type_map


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
        {"name": "Living Room TV", "is_wired": True},
        {"name": "Sonos One", "is_wired": True},
        {"name": "Generic Client", "is_wired": True},
    ]
    node_types = build_node_type_map([], clients)
    assert node_types["Living Room TV"] == "tv"
    assert node_types["Sonos One"] == "speaker"
    assert node_types["Generic Client"] == "client"
