"""Compatibility-focused topology tests for client classification."""

from __future__ import annotations

from unifi_topology.model.classify import classify_client_type
from unifi_topology.model.clients import build_node_type_map


def test_classify_client_type_default_client():
    assert classify_client_type({"name": "John Laptop"}) == "client"


def test_classify_client_type_by_name_tv():
    assert classify_client_type({"name": "Living Room TV"}) == "tv"
    assert classify_client_type({"name": "Apple TV"}) == "tv"
    assert classify_client_type({"name": "Chromecast"}) == "tv"


def test_classify_client_type_by_name_camera():
    assert classify_client_type({"name": "Front Door Camera"}) == "camera"
    assert classify_client_type({"name": "Ring Doorbell"}) == "camera"
    assert classify_client_type({"name": "UVC-G4-Pro"}) == "camera"


def test_classify_client_type_by_name_phone():
    assert classify_client_type({"name": "John's iPhone"}) == "phone"
    assert classify_client_type({"name": "Office VoIP Phone"}) == "phone"


def test_classify_client_type_by_name_printer():
    assert classify_client_type({"name": "HP LaserJet Pro"}) == "printer"
    assert classify_client_type({"name": "Office Printer"}) == "printer"


def test_classify_client_type_by_name_nas():
    assert classify_client_type({"name": "DS920+ NAS"}) == "nas"
    assert classify_client_type({"name": "Synology"}) == "nas"
    assert classify_client_type({"name": "QNAP Storage"}) == "nas"


def test_classify_client_type_by_name_speaker():
    assert classify_client_type({"name": "Sonos One"}) == "speaker"
    assert classify_client_type({"name": "HomePod Mini"}) == "speaker"
    assert classify_client_type({"name": "Echo Dot"}) == "speaker"


def test_classify_client_type_by_name_game_console():
    assert classify_client_type({"name": "PlayStation 5"}) == "game_console"
    assert classify_client_type({"name": "Xbox Series X"}) == "game_console"
    assert classify_client_type({"name": "Nintendo Switch"}) == "game_console"


def test_classify_client_type_by_name_iot():
    assert classify_client_type({"name": "Hue Bridge"}) == "iot"
    assert classify_client_type({"name": "Nest Thermostat"}) == "iot"
    assert classify_client_type({"name": "Smart Plug"}) == "iot"


def test_classify_client_type_by_vendor():
    assert classify_client_type({"name": "DS920", "oui": "Synology"}) == "nas"
    assert classify_client_type({"name": "Device", "vendor": "QNAP"}) == "nas"


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
