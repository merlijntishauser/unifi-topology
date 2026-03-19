"""Tests for physical spec parsing from store API data."""

import importlib
import sys
from pathlib import Path

import pytest

_scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

parse_specs = importlib.import_module("parse_specs")
parse_dimensions = parse_specs.parse_dimensions
parse_weight = parse_specs.parse_weight
parse_max_power = parse_specs.parse_max_power
parse_rack_height = parse_specs.parse_rack_height
extract_specs = parse_specs.extract_specs

pytestmark = pytest.mark.unit


class TestParseDimensions:
    def test_standard_wxdxh(self):
        raw = '442 x 285 x 44 mm \n(17.4 x 11.2 x 1.7")'
        assert parse_dimensions(raw) == {"width": 442, "depth": 285, "height": 44}

    def test_diameter(self):
        raw = '⌀206 x 46 mm\n(⌀8.1 x 1.8")'
        assert parse_dimensions(raw) == {"diameter": 206, "height": 46}

    def test_fractional_mm(self):
        raw = '141.8 x 127.6 x 30 mm\n(5.6 x 5 x 1.2")'
        assert parse_dimensions(raw) == {"width": 141.8, "depth": 127.6, "height": 30}

    def test_empty_string(self):
        assert parse_dimensions("") is None

    def test_unparseable(self):
        assert parse_dimensions("unknown format") is None


class TestParseWeight:
    def test_kg(self):
        assert parse_weight("4.3 kg (9.5 lb)") == 4.3

    def test_grams(self):
        assert parse_weight("680 g (1.5 lb)") == 0.68

    def test_grams_small(self):
        assert parse_weight("150 g (5.3 oz)") == 0.15

    def test_empty(self):
        assert parse_weight("") is None

    def test_unparseable(self):
        assert parse_weight("unknown") is None

    def test_with_brackets_prefix(self):
        raw = "Without mounting brackets: 4.3 kg (9.5 lb)\nWith mounting brackets: 4.4 kg (9.7 lb)"
        assert parse_weight(raw) == 4.3


class TestParseMaxPower:
    def test_simple(self):
        assert parse_max_power("6.2W") == 6.2

    def test_multiline_takes_max(self):
        raw = "50W (Excluding PoE Output)\n450W (Including PoE Output)"
        assert parse_max_power(raw) == 450

    def test_integer(self):
        assert parse_max_power("21W") == 21

    def test_empty(self):
        assert parse_max_power("") is None

    def test_no_watt_values(self):
        assert parse_max_power("unknown") is None


class TestParseRackHeight:
    def test_rack_1u(self):
        assert parse_rack_height("Rack mount (1U)") == 1

    def test_rack_2u(self):
        assert parse_rack_height("Rack mount (2U)") == 2

    def test_desktop(self):
        assert parse_rack_height("Compact desktop") is None

    def test_empty(self):
        assert parse_rack_height("") is None


def _make_feature(slug: str, value: str) -> dict:
    return {
        "feature": {"slug": slug},
        "value": value,
    }


class TestExtractSpecs:
    def test_full_product(self):
        product = {
            "technicalSpecification": {
                "sections": [
                    {
                        "features": [
                            _make_feature("dimensions", "442 x 285 x 44 mm\n(...)"),
                            _make_feature("weight", "4.3 kg (9.5 lb)"),
                            _make_feature(
                                "maxdot-power-consumption",
                                "50W (Excl PoE)\n450W (Incl PoE)",
                            ),
                            _make_feature("form-factor", "Rack mount (1U)"),
                        ]
                    }
                ]
            }
        }
        specs = extract_specs(product)
        assert specs["dimensions_mm"] == {"width": 442, "depth": 285, "height": 44}
        assert specs["weight_kg"] == 4.3
        assert specs["max_power_w"] == 450
        assert specs["form_factor"] == "Rack mount (1U)"
        assert specs["rack_height_u"] == 1

    def test_ap_with_mounting(self):
        product = {
            "technicalSpecification": {
                "sections": [
                    {
                        "features": [
                            _make_feature("dimensions", '⌀206 x 46 mm\n(⌀8.1 x 1.8")'),
                            _make_feature("mounting", "Ceiling, Wall\n(Pro Mount Included)"),
                            _make_feature("weight", "680 g (1.5 lb)"),
                            _make_feature("maxdot-power-consumption", "21W"),
                        ]
                    }
                ]
            }
        }
        specs = extract_specs(product)
        assert specs["dimensions_mm"] == {"diameter": 206, "height": 46}
        assert specs["form_factor"] == "Ceiling, Wall"
        assert specs["weight_kg"] == 0.68
        assert specs["max_power_w"] == 21
        assert "rack_height_u" not in specs

    def test_missing_technical_specification(self):
        assert extract_specs({}) == {}

    def test_empty_values_omitted(self):
        product = {
            "technicalSpecification": {"sections": [{"features": [_make_feature("weight", "")]}]}
        }
        assert extract_specs(product) == {}

    def test_multiple_sections_merged(self):
        product = {
            "technicalSpecification": {
                "sections": [
                    {"features": [_make_feature("dimensions", "100 x 200 x 30 mm")]},
                    {"features": [_make_feature("weight", "1.5 kg")]},
                ]
            }
        }
        specs = extract_specs(product)
        assert specs["dimensions_mm"] == {"width": 100, "depth": 200, "height": 30}
        assert specs["weight_kg"] == 1.5

    def test_form_factor_preferred_over_mounting(self):
        product = {
            "technicalSpecification": {
                "sections": [
                    {
                        "features": [
                            _make_feature("form-factor", "Compact desktop"),
                            _make_feature("mounting", "Wall"),
                        ]
                    }
                ]
            }
        }
        specs = extract_specs(product)
        assert specs["form_factor"] == "Compact desktop"
