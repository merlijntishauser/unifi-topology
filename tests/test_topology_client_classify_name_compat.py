"""Compatibility-focused topology tests for client classification by name/vendor."""

from __future__ import annotations

from unifi_topology.model.classify import classify_client_type


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
