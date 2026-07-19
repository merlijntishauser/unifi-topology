"""Tests for classify UniFi signal helpers."""

from types import SimpleNamespace

from unifi_topology.model._classify_client import (
    _classify_by_unifi_info,
    _classify_by_vendor,
    _ucore_has_device_info,
)
from unifi_topology.model.classify import client_is_unifi


def test_classify_by_vendor_no_match():
    assert _classify_by_vendor("Unknown Vendor Inc.") is None
    assert _classify_by_vendor("Generic Electronics") is None


def test_classify_by_unifi_info_product_line_no_match():
    ucore: dict[str, object] = {"product_line": "Network"}
    assert _classify_by_unifi_info(ucore) is None


def test_classify_by_unifi_info_model_with_talk():
    ucore: dict[str, object] = {"product_shortname": "Talk Flex"}
    assert _classify_by_unifi_info(ucore) == "phone"


def test_classify_by_unifi_info_model_with_phone():
    ucore: dict[str, object] = {"computed_model": "VoIP Phone Pro"}
    assert _classify_by_unifi_info(ucore) == "phone"


def test_classify_by_unifi_info_no_matching_model():
    ucore: dict[str, object] = {"product_shortname": "USW Lite 8", "computed_model": "Switch 8"}
    assert _classify_by_unifi_info(ucore) is None


def test_classify_by_unifi_info_non_string_model_values():
    ucore = {"product_shortname": 123, "computed_model": None, "product_model": True}
    assert _classify_by_unifi_info(ucore) is None


def test_classify_by_unifi_info_empty_ucore():
    assert _classify_by_unifi_info({}) is None


def test_ucore_has_device_info_returns_false_for_empty():
    assert _ucore_has_device_info({}) is False


def test_ucore_has_device_info_returns_false_for_blank_strings():
    ucore = {"product_line": "  ", "name": "", "managed": False}
    assert _ucore_has_device_info(ucore) is False


def test_client_is_unifi_false_no_vendor():
    client = {"name": "Generic Device"}
    assert client_is_unifi(client) is False


def test_client_is_unifi_false_no_flag_no_ucore_no_vendor():
    client = SimpleNamespace(name="Unknown")
    assert client_is_unifi(client) is False


def test_narrow_negative_flag_does_not_override_ucore():
    # A wired UniFi Protect camera reports is_uap: False but has real ucore info.
    client = {
        "is_uap": False,
        "unifi_device_info_from_ucore": {"product_line": "protect", "name": "G4 Doorbell"},
    }
    assert client_is_unifi(client) is True


def test_positive_flag_is_decisive():
    assert client_is_unifi({"is_unifi": True}) is True


def test_authoritative_negative_flag_is_decisive():
    assert client_is_unifi({"is_unifi": False, "vendor": "Ubiquiti"}) is False
