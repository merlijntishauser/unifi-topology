"""Tests for device stats coercion helpers."""

import pytest

from unifi_topology.model.device_stats_coerce import (
    _as_float,
    _as_int,
    _resolve_temperature,
)

pytestmark = pytest.mark.unit


class TestAsFloat:
    def test_none_returns_default(self):
        assert _as_float(None) == 0.0

    def test_none_returns_custom_default(self):
        assert _as_float(None, default=5.0) == 5.0

    def test_unconvertible_returns_default(self):
        assert _as_float("not-a-number") == 0.0

    def test_unconvertible_object_returns_default(self):
        assert _as_float(object()) == 0.0


class TestAsInt:
    def test_none_returns_default(self):
        assert _as_int(None) == 0

    def test_none_returns_custom_default(self):
        assert _as_int(None, default=7) == 7

    def test_unconvertible_returns_default(self):
        assert _as_int("not-a-number") == 0

    def test_unconvertible_object_returns_default(self):
        assert _as_int(object()) == 0


class TestResolveTemperature:
    def test_general_temperature_invalid_type(self):
        raw = {"general_temperature": "not-a-number"}
        assert _resolve_temperature(raw) is None

    def test_general_temperature_invalid_object(self):
        raw = {"general_temperature": object()}
        assert _resolve_temperature(raw) is None

    def test_temps_dict_invalid_value(self):
        raw = {"system-stats": {"temps": {"CPU": "not-a-number"}}}
        assert _resolve_temperature(raw) is None

    def test_temps_dict_invalid_object_value(self):
        raw = {"system-stats": {"temps": {"CPU": object()}}}
        assert _resolve_temperature(raw) is None
