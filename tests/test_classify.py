"""Tests for classify.py to improve coverage."""

from types import SimpleNamespace

from unifi_topology.model.classify import (
    _classify_by_device_name,
    _classify_by_unifi_info,
    _classify_by_vendor,
    _ucore_has_device_info,
    classify_client_type,
    classify_device_type,
    client_is_unifi,
)

# --- _classify_by_device_name ---


def test_classify_by_device_name_returns_none_for_unknown():
    """Names that don't match gateway/switch/ap return None."""
    assert _classify_by_device_name("My Server") is None
    assert _classify_by_device_name("NAS") is None
    assert _classify_by_device_name("Printer") is None


# --- classify_device_type for "ux" type ---


def test_classify_device_type_ux_default_gateway():
    """UX type without in_gateway_mode field defaults to gateway."""
    device = SimpleNamespace(type="ux")
    assert classify_device_type(device) == "gateway"


def test_classify_device_type_ux_in_gateway_mode_false():
    """UX type with in_gateway_mode=False should be classified as ap."""
    device = SimpleNamespace(type="ux", in_gateway_mode=False)
    assert classify_device_type(device) == "ap"


def test_classify_device_type_ux_in_gateway_mode_true():
    """UX type with in_gateway_mode=True should be classified as gateway."""
    device = SimpleNamespace(type="ux", in_gateway_mode=True)
    assert classify_device_type(device) == "gateway"


# --- _classify_by_vendor ---


def test_classify_by_vendor_no_match():
    """Vendor that doesn't match any pattern returns None."""
    assert _classify_by_vendor("Unknown Vendor Inc.") is None
    assert _classify_by_vendor("Generic Electronics") is None


# --- _classify_by_unifi_info ---


def test_classify_by_unifi_info_product_line_no_match():
    """Product line that doesn't match any prefix returns None and falls through."""
    ucore: dict[str, object] = {"product_line": "Network"}
    assert _classify_by_unifi_info(ucore) is None


def test_classify_by_unifi_info_model_with_talk():
    """Model containing 'talk' should classify as phone."""
    ucore: dict[str, object] = {"product_shortname": "Talk Flex"}
    assert _classify_by_unifi_info(ucore) == "phone"


def test_classify_by_unifi_info_model_with_phone():
    """Model containing 'phone' should classify as phone."""
    ucore: dict[str, object] = {"computed_model": "VoIP Phone Pro"}
    assert _classify_by_unifi_info(ucore) == "phone"


def test_classify_by_unifi_info_no_matching_model():
    """Model keys present but no matching pattern returns None."""
    ucore: dict[str, object] = {"product_shortname": "USW Lite 8", "computed_model": "Switch 8"}
    assert _classify_by_unifi_info(ucore) is None


def test_classify_by_unifi_info_non_string_model_values():
    """Non-string model values should be skipped."""
    ucore = {"product_shortname": 123, "computed_model": None, "product_model": True}
    assert _classify_by_unifi_info(ucore) is None


def test_classify_by_unifi_info_empty_ucore():
    """Empty ucore dict returns None."""
    assert _classify_by_unifi_info({}) is None


# --- _ucore_has_device_info ---


def test_ucore_has_device_info_returns_false_for_empty():
    """Empty ucore dict returns False."""
    assert _ucore_has_device_info({}) is False


def test_ucore_has_device_info_returns_false_for_blank_strings():
    """Ucore with only blank string values returns False."""
    ucore = {"product_line": "  ", "name": "", "managed": False}
    assert _ucore_has_device_info(ucore) is False


# --- client_is_unifi ---


def test_client_is_unifi_false_no_vendor():
    """Client with no vendor info and no flag returns False."""
    client = {"name": "Generic Device"}
    assert client_is_unifi(client) is False


def test_client_is_unifi_false_no_flag_no_ucore_no_vendor():
    """Client without any UniFi indicators returns False."""
    client = SimpleNamespace(name="Unknown")
    assert client_is_unifi(client) is False


# --- classify_client_type branch coverage ---


def test_classify_client_type_ucore_no_match_falls_to_name():
    """When ucore exists but doesn't match, fall through to name classification."""
    client = {
        "name": "Living Room TV",
        "unifi_device_info_from_ucore": {"product_line": "Network"},
    }
    assert classify_client_type(client) == "tv"


def test_classify_client_type_ucore_no_match_name_no_match_falls_to_vendor():
    """When ucore and name don't match, fall through to vendor classification."""
    client = {
        "name": "Device123",
        "unifi_device_info_from_ucore": {"product_line": "Network"},
        "oui": "Synology",
    }
    assert classify_client_type(client) == "nas"


def test_classify_client_type_all_no_match_returns_client():
    """When ucore, name, and vendor all fail to match, return 'client'."""
    client = {
        "name": "Device123",
        "unifi_device_info_from_ucore": {"product_line": "Network"},
        "oui": "Unknown Vendor",
    }
    assert classify_client_type(client) == "client"


def test_classify_client_type_name_no_match_vendor_no_match():
    """When name and vendor exist but don't match, return 'client'."""
    client = {
        "name": "My Gadget",
        "oui": "FooBar Electronics",
    }
    assert classify_client_type(client) == "client"


def test_classify_client_type_no_name_no_vendor():
    """Client with no name or vendor returns 'client'."""
    client = {"mac": "aa:bb:cc:dd:ee:ff"}
    assert classify_client_type(client) == "client"


def test_classify_client_type_no_display_name():
    """Client where client_display_name returns None skips name classification."""
    client = {"name": " ", "hostname": "", "mac": ""}
    assert classify_client_type(client) == "client"


def test_classify_client_type_ucore_no_match_no_name():
    """Ucore exists but doesn't match, and no display name."""
    client = {
        "name": " ",
        "hostname": "",
        "mac": "",
        "unifi_device_info_from_ucore": {"product_line": "Network"},
    }
    assert classify_client_type(client) == "client"
