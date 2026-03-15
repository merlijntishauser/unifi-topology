"""Tests for classify client type decision paths."""

from unifi_topology.model.classify import classify_client_type


def test_classify_client_type_ucore_no_match_falls_to_name():
    client = {
        "name": "Living Room TV",
        "unifi_device_info_from_ucore": {"product_line": "Network"},
    }
    assert classify_client_type(client) == "tv"


def test_classify_client_type_ucore_no_match_name_no_match_falls_to_vendor():
    client = {
        "name": "Device123",
        "unifi_device_info_from_ucore": {"product_line": "Network"},
        "oui": "Synology",
    }
    assert classify_client_type(client) == "nas"


def test_classify_client_type_all_no_match_returns_client():
    client = {
        "name": "Device123",
        "unifi_device_info_from_ucore": {"product_line": "Network"},
        "oui": "Unknown Vendor",
    }
    assert classify_client_type(client) == "client"


def test_classify_client_type_name_no_match_vendor_no_match():
    client = {
        "name": "My Gadget",
        "oui": "FooBar Electronics",
    }
    assert classify_client_type(client) == "client"


def test_classify_client_type_no_name_no_vendor():
    client = {"mac": "aa:bb:cc:dd:ee:ff"}
    assert classify_client_type(client) == "client"


def test_classify_client_type_no_display_name():
    client = {"name": " ", "hostname": "", "mac": ""}
    assert classify_client_type(client) == "client"


def test_classify_client_type_ucore_no_match_no_name():
    client = {
        "name": " ",
        "hostname": "",
        "mac": "",
        "unifi_device_info_from_ucore": {"product_line": "Network"},
    }
    assert classify_client_type(client) == "client"
