"""Tests for model lookup from bundled store data."""

import pytest

from unifi_topology.model.model_lookup import lookup_model_name, lookup_model_url

pytestmark = pytest.mark.unit


def test_lookup_known_switch():
    name = lookup_model_name("USW-24")
    assert name == "Switch 24"


def test_lookup_known_gateway():
    name = lookup_model_name("UDM-Pro-Max")
    assert name == "Dream Machine Pro Max"


def test_lookup_case_insensitive():
    name = lookup_model_name("usw-24")
    assert name == "Switch 24"


def test_lookup_unknown_model():
    assert lookup_model_name("NONEXISTENT-999") == ""


def test_lookup_url_known():
    url = lookup_model_url("USW-24")
    assert url.startswith("https://store.ui.com/")
    assert url.endswith("/usw-24")


def test_lookup_url_unknown():
    assert lookup_model_url("NONEXISTENT-999") == ""


def test_model_name_fallback_in_coercion():
    """model_name should be resolved from lookup when API omits it."""
    from unifi_topology.model.device_stats_coerce import normalize_device_stats

    result = normalize_device_stats(
        [{"mac": "aa:bb:cc:dd:ee:ff", "model": "USW-Enterprise-24-PoE"}]
    )
    assert result[0].model_name != ""
    assert "Enterprise" in result[0].model_name


def test_api_model_name_takes_precedence():
    """model_name from API should not be overwritten by lookup."""
    from unifi_topology.model.device_stats_coerce import normalize_device_stats

    result = normalize_device_stats(
        [{"mac": "aa:bb:cc:dd:ee:ff", "model": "USW-24", "model_name": "My Switch"}]
    )
    assert result[0].model_name == "My Switch"
