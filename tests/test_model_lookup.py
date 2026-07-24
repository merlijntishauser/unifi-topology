"""Tests for model lookup from bundled store data."""

import pytest

from unifi_topology.model.model_lookup import (
    list_all_models,
    lookup_firmware_changelog,
    lookup_model_docs,
    lookup_model_name,
    lookup_model_specs,
    lookup_model_url,
)

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


def test_firmware_platform_code_resolves():
    """Firmware platform codes (e.g. U6M) should resolve to product names."""
    assert lookup_model_name("U6M") == "Access Point U6 Mesh"
    assert lookup_model_name("UDMPRO") == "Dream Machine Pro"
    assert lookup_model_name("USL8LP") == "Switch Lite 8 PoE"


def test_docs_for_known_product():
    docs = lookup_model_docs("USW-24")
    assert "datasheet" in docs


def test_docs_for_firmware_code():
    docs = lookup_model_docs("U6M")
    assert "datasheet" in docs


def test_docs_for_unknown():
    assert lookup_model_docs("NONEXISTENT-999") == {}


def test_firmware_changelog():
    url = lookup_firmware_changelog("U6M")
    assert url.startswith("https://fw-update.ui.com/")


def test_firmware_changelog_unknown():
    assert lookup_firmware_changelog("NONEXISTENT-999") == ""


def test_list_all_models_returns_dict():
    models = list_all_models()
    assert isinstance(models, dict)
    assert len(models) > 0


def test_list_all_models_entries_have_name():
    models = list_all_models()
    for code, entry in models.items():
        assert "name" in entry, f"Model {code} missing 'name' key"


def test_list_all_models_contains_known_model():
    models = list_all_models()
    assert "USW-24" in models
    assert models["USW-24"]["name"] == "Switch 24"


def test_list_all_models_returns_copy():
    models = list_all_models()
    models["FAKE-MODEL"] = {"name": "Fake"}
    fresh = list_all_models()
    assert "FAKE-MODEL" not in fresh


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


def test_firmware_code_fallback_in_coercion():
    """Firmware platform codes should also resolve in coercion."""
    from unifi_topology.model.device_stats_coerce import normalize_device_stats

    result = normalize_device_stats([{"mac": "aa:bb:cc:dd:ee:ff", "model": "U6M"}])
    assert result[0].model_name == "Access Point U6 Mesh"


def test_specs_for_known_product():
    specs = lookup_model_specs("USW-Pro-24-POE")
    assert specs["dimensions_mm"] == {"width": 442, "depth": 285, "height": 44}
    assert specs["weight_kg"] == 4.3
    assert specs["max_power_w"] == 450
    assert specs["form_factor"] == "Rack mount (1U)"
    assert specs["rack_height_u"] == 1


def test_specs_for_unknown():
    assert lookup_model_specs("NONEXISTENT-999") == {}


def test_specs_for_firmware_code():
    specs = lookup_model_specs("U6M")
    assert "dimensions_mm" in specs
    assert "weight_kg" in specs


def test_lookup_resolves_sku_that_only_survives_as_a_name():
    """A model string that is only present as an entry's `name` still resolves.

    After the store->firmware re-keying, some SKUs (e.g. USW-Enterprise-24-PoE)
    are no longer keys but survive as the `name` of a firmware-code entry
    (US624P). The lookup documents that it accepts both SKUs and codes, so a
    name match must still resolve.
    """
    assert lookup_model_name("USW-Enterprise-24-PoE") != ""
    assert lookup_model_name("usw-enterprise-24-poe") != ""  # case-insensitive
